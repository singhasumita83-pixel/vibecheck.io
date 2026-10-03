from typing import Any, Dict, Union, Tuple
from analyzer.schema import Location

def clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    return max(min_val, min(max_val, float(val)))

def to_normalized(
    box: Union[Dict[str, Any], list, tuple],
    convention: str = "normalized",
    img_w: int = 1440,
    img_h: int = 900
) -> Location:
    """
    Converts bounding box representations into normalized Location(x, y, w, h)
    where all values are floats in [0.0, 1.0].
    
    Supported conventions:
    - 'normalized': x, y, w, h already in [0.0, 1.0]
    - 'rel_1000': coordinates given in 0..1000 scale (common in Qwen-VL / Gemini box formats)
    - 'abs_pixels': pixel coordinates based on img_w and img_h
    """
    x, y, w, h = 0.1, 0.1, 0.1, 0.1
    
    if isinstance(box, dict):
        if "x" in box and "y" in box:
            x = float(box["x"])
            y = float(box["y"])
            w = float(box.get("w", 0.08))
            h = float(box.get("h", 0.05))
        elif "ymin" in box and "xmin" in box:
            ymin = float(box["ymin"])
            xmin = float(box["xmin"])
            ymax = float(box.get("ymax", ymin + 50))
            xmax = float(box.get("xmax", xmin + 80))
            x, y = xmin, ymin
            w, h = max(0.01, xmax - xmin), max(0.01, ymax - ymin)
    elif isinstance(box, (list, tuple)) and len(box) >= 4:
        # Standard format [x, y, w, h] or [ymin, xmin, ymax, xmax]
        val0, val1, val2, val3 = [float(v) for v in box[:4]]
        if convention in ("rel_1000", "abs_pixels") and (val2 > val0 and val3 > val1):
            # Check if likely [ymin, xmin, ymax, xmax] or [x, y, w, h]
            # If val2 > 1 and val3 > 1, handle as [ymin, xmin, ymax, xmax] if Qwen-VL standard
            if convention == "rel_1000" or val2 > val0:
                y = val0
                x = val1
                h = max(0.01, val2 - val0)
                w = max(0.01, val3 - val1)
            else:
                x, y, w, h = val0, val1, val2, val3
        else:
            x, y, w, h = val0, val1, val2, val3

    if convention == "rel_1000":
        x = x / 1000.0
        y = y / 1000.0
        w = w / 1000.0
        h = h / 1000.0
    elif convention == "abs_pixels":
        if img_w > 0:
            x = x / float(img_w)
            w = w / float(img_w)
        if img_h > 0:
            y = y / float(img_h)
            h = h / float(img_h)

    # Clamp bounds so markers and bounding boxes always stay within the image canvas
    norm_x = clamp(x, 0.0, 0.95)
    norm_y = clamp(y, 0.0, 0.95)
    norm_w = clamp(w, 0.01, 1.0 - norm_x)
    norm_h = clamp(h, 0.01, 1.0 - norm_y)

    return Location(
        x=round(norm_x, 4),
        y=round(norm_y, 4),
        w=round(norm_w, 4),
        h=round(norm_h, 4)
    )
