from __future__ import annotations

import io
from typing import Any, Optional, Dict, List

from backend.config import settings

try:
    from PIL import Image
    from PIL import ImageFilter, ImageStat
except Exception:  # pragma: no cover
    Image = None  # type: ignore
    ImageFilter = None  # type: ignore
    ImageStat = None  # type: ignore


def validate_image(image_bytes: bytes, filename: Optional[str] = None) -> bool:
    """
    Robust validator:
      - size check (MAX_IMAGE_SIZE_MB)
      - content-based check using Pillow (not just extension)
      - accepts JPEG/PNG/WEBP (JFIF is treated as JPEG)
    """
    if not image_bytes:
        return False

    max_mb = int(getattr(settings, "MAX_IMAGE_SIZE_MB", 10) or 10)
    if len(image_bytes) > max_mb * 1024 * 1024:
        return False

    if Image is None:
        return False

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
    except Exception:
        return False

    try:
        img = Image.open(io.BytesIO(image_bytes))
        fmt = (img.format or "").upper()
    except Exception:
        return False

    return fmt in {"JPEG", "PNG", "WEBP"}


def resize_image(img_or_bytes: Any, max_side: int = 1024, quality: int = 85) -> bytes:
    """
    Resizes to max_side preserving aspect ratio and returns JPEG bytes.
    Accepts:
      - bytes / bytearray / memoryview
      - PIL.Image.Image
    """
    if Image is None:
        raise RuntimeError("Pillow is required. Install it with: pip install pillow")

    # Normalize input to PIL.Image
    if isinstance(img_or_bytes, (bytes, bytearray, memoryview)):
        raw = bytes(img_or_bytes)
        img = Image.open(io.BytesIO(raw))
    else:
        img = img_or_bytes  # assume PIL image

    img = img.convert("RGB")
    w, h = img.size
    scale = min(1.0, float(max_side) / float(max(w, h)))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)))

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=int(quality), optimize=True)
    return out.getvalue()


# Backward-compatible aliases used elsewhere in your project
def resize_for_model(img_or_bytes: Any, max_side: int = 1024) -> bytes:
    return resize_image(img_or_bytes, max_side=max_side)


def validate_image_file(image_bytes: bytes, filename: Optional[str] = None) -> bool:
    return validate_image(image_bytes, filename)


def assess_image_quality(image_bytes: bytes) -> Dict[str, Any]:
    """Lightweight image-quality assessment.

    Returns a dict:
      {
        "quality": "good"|"moderate"|"poor"|"unknown",
        "warnings": [..],
        "metrics": {"width": int, "height": int, "brightness_mean": float, "contrast_std": float, "edge_variance": float}
      }

    Notes:
    - This is intentionally heuristic (no OpenCV dependency).
    - Used to increase confidence thresholds for blurry/low-light images.
    """
    if not image_bytes or Image is None or ImageFilter is None or ImageStat is None:
        return {"quality": "unknown", "warnings": ["image_quality_unavailable"], "metrics": {}}

    warnings: List[str] = []
    metrics: Dict[str, Any] = {}

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return {"quality": "unknown", "warnings": ["image_decode_failed"], "metrics": {}}

    w, h = img.size
    metrics["width"] = int(w)
    metrics["height"] = int(h)

    # Basic resolution check
    if min(w, h) < 350 or max(w, h) < 500:
        warnings.append("low_resolution")

    # Brightness/contrast
    gray = img.convert("L")
    stat = ImageStat.Stat(gray)
    brightness_mean = float(stat.mean[0]) if stat.mean else 0.0
    contrast_std = float(stat.stddev[0]) if stat.stddev else 0.0
    metrics["brightness_mean"] = round(brightness_mean, 3)
    metrics["contrast_std"] = round(contrast_std, 3)

    if brightness_mean < 50:
        warnings.append("too_dark")
    elif brightness_mean > 210:
        warnings.append("overexposed")

    if contrast_std < 25:
        warnings.append("low_contrast")

    # Blur proxy: edge energy variance (lower => blurrier)
    try:
        edges = gray.filter(ImageFilter.FIND_EDGES)
        e_stat = ImageStat.Stat(edges)
        edge_variance = float(e_stat.var[0]) if e_stat.var else 0.0
        metrics["edge_variance"] = round(edge_variance, 3)
        if edge_variance < 60:
            warnings.append("blurry")
    except Exception:
        # don't fail the request if edge filter fails
        metrics["edge_variance"] = None

    # Quality bucket
    # Major issues are blur + very low res; multiple minor issues -> poor.
    major = {"blurry", "low_resolution"}
    major_hits = sum(1 for w_ in warnings if w_ in major)
    total = len(warnings)

    if total == 0:
        quality = "good"
    elif major_hits >= 1 and total >= 2:
        quality = "poor"
    elif total >= 3:
        quality = "poor"
    else:
        quality = "moderate"

    return {"quality": quality, "warnings": warnings, "metrics": metrics}
