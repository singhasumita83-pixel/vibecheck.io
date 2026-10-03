import os
import uuid
from io import BytesIO
from typing import Optional, Tuple
from PIL import Image

from analyzer.schema import AnalysisResponse, ImageDimensions
from analyzer.llm_client import LLMClient
from analyzer.scoring import rank_findings, calculate_summary
from analyzer.fixprompt import build_fix_plan, build_fix_prompt
from analyzer.contrast import apply_contrast_measurements

MAX_IMAGE_PX = int(os.getenv("MAX_IMAGE_PX", 1568))

def validate_and_resize_image(file_bytes: bytes) -> Tuple[bytes, int, int]:
    """
    Validates that bytes represent a valid image, converts to RGB,
    resizes if exceeding MAX_IMAGE_PX, and returns (processed_bytes, width, height).
    """
    try:
        img = Image.open(BytesIO(file_bytes))
        img.verify()
        # Re-open after verify()
        img = Image.open(BytesIO(file_bytes))
    except Exception as e:
        raise ValueError("Invalid image file. Please upload a valid PNG or JPG.")

    if img.format not in ("PNG", "JPEG", "JPG", "WEBP"):
        raise ValueError(f"Unsupported image format: {img.format}. Please upload PNG or JPG.")

    # Convert to RGB if needed (handling RGBA or palette)
    if img.mode != "RGB":
        img = img.convert("RGB")

    w, h = img.size
    max_dim = max(w, h)
    if max_dim > MAX_IMAGE_PX:
        scale = MAX_IMAGE_PX / float(max_dim)
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        w, h = new_w, new_h

    out_buf = BytesIO()
    img.save(out_buf, format="JPEG", quality=92)
    processed_bytes = out_buf.getvalue()
    
    return processed_bytes, w, h

class AnalysisPipeline:
    def __init__(self):
        self.llm_client = LLMClient()
        self._cache = {}

    def analyze(
        self,
        image_bytes: bytes,
        persona: str = "",
        goal: str = "",
        viewport: str = "desktop",
        url: Optional[str] = None
    ) -> AnalysisResponse:
        """
        Executes the complete analysis pipeline with in-memory caching.
        """
        import hashlib
        cache_key = hashlib.sha256(image_bytes + persona.encode() + goal.encode()).hexdigest()
        if cache_key in self._cache:
            cached_resp = self._cache[cache_key]
            # Refresh run_id for new request
            cached_dict = cached_resp.model_dump()
            cached_dict["run_id"] = str(uuid.uuid4())
            return AnalysisResponse(**cached_dict)

        processed_bytes, img_w, img_h = validate_and_resize_image(image_bytes)
        
        # 1. Vision & Heuristic Analysis
        raw_findings = self.llm_client.analyze_image(
            image_bytes=processed_bytes,
            img_w=img_w,
            img_h=img_h,
            persona=persona,
            goal=goal,
            viewport=viewport
        )
        
        # 1b. Measured contrast evidence (WCAG 2.1)
        try:
            with Image.open(BytesIO(processed_bytes)) as pil_img:
                apply_contrast_measurements(raw_findings, pil_img)
        except Exception as e:
            print(f"[Contrast measurement warning]: {e}")

        # 2. Ranking and sequential ID assignment (f1, f2...)
        ranked_findings = rank_findings(raw_findings)
        
        # 3. Honest category scoring and counts
        summary = calculate_summary(ranked_findings)
        
        # 4. Actionable Fix Plan and AI Prompt
        fix_plan = build_fix_plan(ranked_findings, max_items=5)
        fix_prompt = build_fix_prompt(ranked_findings, persona=persona, goal=goal, max_findings=7)
        
        # 5. Model Transparency metadata
        model_info = self.llm_client.get_model_info()
        
        response = AnalysisResponse(
            run_id=str(uuid.uuid4()),
            model=model_info,
            image=ImageDimensions(width=img_w, height=img_h),
            summary=summary,
            findings=ranked_findings,
            fix_plan=fix_plan,
            fix_prompt=fix_prompt
        )
        self._cache[cache_key] = response
        return response
