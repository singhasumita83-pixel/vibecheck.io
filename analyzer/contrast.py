"""
VibeCheck — Contrast Measurement & Accessible Color Suggestions (WCAG 2.1)
Estimates foreground/background colors from cropped screenshot bounding boxes,
measures WCAG relative luminance contrast ratios, and suggests compliant foregrounds.
"""

from typing import Optional, Dict, Any, Tuple
from PIL import Image
from collections import Counter

def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Parse #RGB or #RRGGBB hex string to (r, g, b) tuple."""
    if not hex_str:
        return (0, 0, 0)
    s = hex_str.strip().lstrip('#')
    if len(s) == 3:
        s = ''.join([c * 2 for c in s])
    if len(s) != 6:
        return (0, 0, 0)
    try:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except ValueError:
        return (0, 0, 0)

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Format (r, g, b) to lowercase hex #rrggbb."""
    r_clamped = max(0, min(255, int(round(r))))
    g_clamped = max(0, min(255, int(round(g))))
    b_clamped = max(0, min(255, int(round(b))))
    return f"#{r_clamped:02x}{g_clamped:02x}{b_clamped:02x}"

def channel_luminance(val_8bit: int) -> float:
    """Convert an 8-bit sRGB color channel to relative luminance component."""
    c = max(0, min(255, val_8bit)) / 255.0
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

def relative_luminance(color: Any) -> float:
    """
    Calculate WCAG 2.1 relative luminance for a hex string or (r, g, b) tuple.
    Returns float in [0.0, 1.0].
    """
    if isinstance(color, str):
        rgb = hex_to_rgb(color)
    elif isinstance(color, (list, tuple)) and len(color) >= 3:
        rgb = (int(color[0]), int(color[1]), int(color[2]))
    else:
        rgb = (0, 0, 0)

    r_lum = channel_luminance(rgb[0])
    g_lum = channel_luminance(rgb[1])
    b_lum = channel_luminance(rgb[2])

    return 0.2126 * r_lum + 0.7152 * g_lum + 0.0722 * b_lum

def contrast_ratio(fg: Any, bg: Any) -> float:
    """
    Calculate WCAG 2.1 contrast ratio between two colors: (L1 + 0.05) / (L2 + 0.05).
    Returns ratio rounded to 2 decimal places (e.g. 4.48 or 21.0).
    """
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    ratio = (lighter + 0.05) / (darker + 0.05)
    return round(ratio, 2)

def quantize_channel(c: int, levels: int = 16) -> int:
    """Quantize 0..255 channel into 16 steps."""
    step = 256 // levels
    bucket = c // step
    return min(255, bucket * step + step // 2)

def estimate_colors(image: Image.Image, box: Any) -> Dict[str, Any]:
    """
    Crops normalized bounding box from image, quantizes to ~16 levels per channel,
    treats the most frequent color as background and the most luminance-distant
    color among top clusters as foreground.
    Handles empty/tiny boxes without crashing.
    """
    if not image:
        return {"fg": "#000000", "bg": "#ffffff", "ratio": 21.0}

    # Normalize image to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    w_img, h_img = image.size
    if w_img <= 0 or h_img <= 0:
        return {"fg": "#000000", "bg": "#ffffff", "ratio": 21.0}

    # Extract box values (dict, object, or None)
    if box is None:
        return {"fg": "#000000", "bg": "#ffffff", "ratio": 21.0}

    if isinstance(box, dict):
        bx = float(box.get("x", 0.0))
        by = float(box.get("y", 0.0))
        bw = float(box.get("w", 0.05))
        bh = float(box.get("h", 0.05))
    else:
        bx = float(getattr(box, "x", 0.0))
        by = float(getattr(box, "y", 0.0))
        bw = float(getattr(box, "w", 0.05))
        bh = float(getattr(box, "h", 0.05))

    # Guard tiny or negative box dimensions
    bw = max(0.001, bw)
    bh = max(0.001, bh)

    left = max(0, min(w_img - 1, int(bx * w_img)))
    top = max(0, min(h_img - 1, int(by * h_img)))
    right = max(left + 1, min(w_img, int((bx + bw) * w_img)))
    bottom = max(top + 1, min(h_img, int((by + bh) * h_img)))

    # Ensure at least 1x1 crop
    if right <= left:
        right = min(w_img, left + 1)
    if bottom <= top:
        bottom = min(h_img, top + 1)

    try:
        cropped = image.crop((left, top, right, bottom))
    except Exception:
        return {"fg": "#000000", "bg": "#ffffff", "ratio": 21.0}

    pixels = [cropped.getpixel((x, y)) for x in range(cropped.width) for y in range(cropped.height)]
    if not pixels:
        return {"fg": "#000000", "bg": "#ffffff", "ratio": 21.0}

    # Quantize colors into 16 steps per channel
    quantized_counts = Counter(
        (quantize_channel(p[0]), quantize_channel(p[1]), quantize_channel(p[2]))
        for p in pixels
    )

    most_common = quantized_counts.most_common(12)
    if not most_common:
        return {"fg": "#000000", "bg": "#ffffff", "ratio": 21.0}

    bg_rgb = most_common[0][0]
    bg_lum = relative_luminance(bg_rgb)

    # Pick the most luminance-distant color among top frequent colors as foreground
    best_fg_rgb = None
    max_lum_dist = -1.0

    for color_rgb, _ in most_common:
        dist = abs(relative_luminance(color_rgb) - bg_lum)
        if dist > max_lum_dist:
            max_lum_dist = dist
            best_fg_rgb = color_rgb

    # If all pixels are virtually uniform, default fg to opposite extreme
    if best_fg_rgb is None or max_lum_dist < 0.02:
        best_fg_rgb = (0, 0, 0) if bg_lum > 0.5 else (255, 255, 255)

    fg_hex = rgb_to_hex(*best_fg_rgb)
    bg_hex = rgb_to_hex(*bg_rgb)
    ratio = contrast_ratio(fg_hex, bg_hex)

    return {
        "fg": fg_hex,
        "bg": bg_hex,
        "ratio": ratio
    }

def suggest_accessible_fg(fg: str, bg: str, target: float = 4.5) -> Tuple[str, float]:
    """
    Shifts the foreground lightness toward black or white until the target ratio is met.
    Returns (suggested_fg_hex, suggested_ratio).
    """
    current_ratio = contrast_ratio(fg, bg)
    if current_ratio >= target:
        return (fg, current_ratio)

    fg_rgb = hex_to_rgb(fg)
    bg_lum = relative_luminance(bg)

    black_ratio = contrast_ratio("#000000", bg)
    white_ratio = contrast_ratio("#ffffff", bg)

    # Determine optimal extreme
    if black_ratio >= target and bg_lum >= 0.18:
        extreme_rgb = (0, 0, 0)
    elif white_ratio >= target:
        extreme_rgb = (255, 255, 255)
    else:
        extreme_rgb = (0, 0, 0) if black_ratio > white_ratio else (255, 255, 255)

    best_hex = rgb_to_hex(*extreme_rgb)
    best_ratio = contrast_ratio(best_hex, bg)

    # Stepwise interpolation from current fg toward extreme
    for step in range(1, 101):
        t = step / 100.0
        nr = int(round(fg_rgb[0] + t * (extreme_rgb[0] - fg_rgb[0])))
        ng = int(round(fg_rgb[1] + t * (extreme_rgb[1] - fg_rgb[1])))
        nb = int(round(fg_rgb[2] + t * (extreme_rgb[2] - fg_rgb[2])))
        cand_hex = rgb_to_hex(nr, ng, nb)
        cand_ratio = contrast_ratio(cand_hex, bg)
        if cand_ratio >= target:
            return (cand_hex, cand_ratio)

    return (best_hex, best_ratio)

def should_measure_contrast(finding: Any) -> bool:
    """Checks if finding is Accessibility or mentions contrast/legibility."""
    category = getattr(finding, "category", "") or ""
    if isinstance(finding, dict):
        category = finding.get("category", "")
        title = finding.get("title", "").lower()
        problem = finding.get("problem", "").lower()
        has_location = bool(finding.get("location"))
    else:
        title = getattr(finding, "title", "").lower()
        problem = getattr(finding, "problem", "").lower()
        has_location = bool(getattr(finding, "location", None))

    if not has_location:
        return False

    if category == "Accessibility":
        return True

    keywords = ("contrast", "faint", "low-contrast", "legibility")
    return any(kw in title or kw in problem for kw in keywords)

def apply_contrast_measurements(findings: list, image: Image.Image) -> None:
    """
    Applies measured contrast evidence to findings that meet criteria.
    Mutates finding objects / dicts in place.
    """
    if not image or not findings:
        return

    for finding in findings:
        if not should_measure_contrast(finding):
            continue

        loc = finding.get("location") if isinstance(finding, dict) else getattr(finding, "location", None)
        colors = estimate_colors(image, loc)
        fg = colors["fg"]
        bg = colors["bg"]
        ratio = colors["ratio"]

        sugg_fg, sugg_ratio = suggest_accessible_fg(fg, bg, target=4.5)

        measured_obj = {
            "ratio": ratio,
            "fg": fg,
            "bg": bg,
            "suggested_fg": sugg_fg,
            "suggested_ratio": sugg_ratio,
            "is_approximate": True
        }

        # If ratio is already >= 4.5, lower confidence and note it
        if ratio >= 4.5:
            conf = finding.get("confidence", 0.8) if isinstance(finding, dict) else getattr(finding, "confidence", 0.8)
            new_conf = round(max(0.2, conf - 0.4), 2)
            note = f"Measured contrast about {ratio}:1 meets WCAG 4.5:1 (approximate pixel sample). Confidence reduced."
            evidence = f"Measured contrast about {ratio}:1 (meets 4.5:1), sampled from screenshot."

            if isinstance(finding, dict):
                finding["confidence"] = new_conf
                finding["evidence"] = evidence
                finding["measured"] = measured_obj
            else:
                finding.confidence = new_conf
                finding.evidence = evidence
                finding.measured = measured_obj
        else:
            evidence = f"Measured contrast about {ratio}:1 (needs 4.5:1), sampled from screenshot"
            if isinstance(finding, dict):
                finding["evidence"] = evidence
                finding["measured"] = measured_obj
            else:
                finding.evidence = evidence
                finding.measured = measured_obj
