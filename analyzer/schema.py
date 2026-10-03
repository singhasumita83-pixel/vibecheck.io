from typing import List, Literal, Dict, Optional, Any
from pydantic import BaseModel, Field

CategoryType = Literal[
    "Usability",
    "Visual Hierarchy",
    "Accessibility",
    "Navigation",
    "Content & Copy",
    "Forms & Feedback",
    "Responsive"
]

SeverityType = Literal["Critical", "High", "Medium", "Low"]

class Location(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0, description="Normalized x coordinate (0.0 to 1.0)")
    y: float = Field(..., ge=0.0, le=1.0, description="Normalized y coordinate (0.0 to 1.0)")
    w: float = Field(0.05, ge=0.0, le=1.0, description="Normalized width (0.0 to 1.0)")
    h: float = Field(0.05, ge=0.0, le=1.0, description="Normalized height (0.0 to 1.0)")

class CodeLocation(BaseModel):
    file: str
    line_start: int
    line_end: int

class CodeFix(BaseModel):
    diff: str
    validated: bool = False
    explanation: Optional[str] = None

class Finding(BaseModel):
    id: str
    title: str
    category: CategoryType
    severity: SeverityType
    confidence: float = Field(..., ge=0.0, le=1.0)
    heuristic: str
    problem: str
    impact: str
    solution: str
    evidence: str
    source: str = "llm"
    location: Optional[Location] = None
    code_location: Optional[CodeLocation] = None
    snippet: Optional[str] = None
    fix: Optional[CodeFix] = None

class ModelInfo(BaseModel):
    name: str
    license: str
    served_by: Literal["local", "hosted", "embedded"]

class ImageDimensions(BaseModel):
    width: int
    height: int

class SummaryCounts(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0

class AnalysisSummary(BaseModel):
    counts: SummaryCounts
    scores: Dict[str, int]
    disclaimer: str = "AI heuristic indicators, not validated UX metrics."
    verified_fixes: int = 0

class FixPlanItem(BaseModel):
    priority: int
    title: str
    finding_ids: List[str]

class AnalysisResponse(BaseModel):
    run_id: str
    model: ModelInfo
    image: Optional[ImageDimensions] = None
    summary: AnalysisSummary
    findings: List[Finding]
    fix_plan: List[FixPlanItem]
    fix_prompt: str
    mode: Literal["screenshot", "repo"] = "screenshot"
    repo_info: Optional[Dict[str, Any]] = None
