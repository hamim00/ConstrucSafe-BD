from __future__ import annotations

import io
from typing import Any, Optional

from backend.config import settings

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None  # type: ignore


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
