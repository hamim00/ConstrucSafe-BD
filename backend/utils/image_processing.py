from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Tuple

from PIL import Image


@dataclass(frozen=True)
class ValidatedImage:
    image: Image.Image
    format: str
    size: Tuple[int, int]
    mime_type: str


def _lanczos_resample() -> int:
    """
    Pillow >= 9 uses Image.Resampling.LANCZOS.
    Older Pillow used Image.LANCZOS.
    This helper keeps runtime + type checkers happy.
    """
    try:
        return Image.Resampling.LANCZOS  # type: ignore[attr-defined]
    except Exception:
        return Image.LANCZOS  # type: ignore[attr-defined]


def validate_image(data: bytes, filename: str) -> ValidatedImage:
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("filename must be a non-empty string")

    try:
        img = Image.open(BytesIO(data))
        img.verify()  # verifies file integrity
    except Exception as e:
        raise ValueError(f"Invalid image file: {e}") from e

    # reopen after verify()
    img = Image.open(BytesIO(data)).convert("RGB")

    fmt = (img.format or "JPEG").upper()
    mime = "image/jpeg" if fmt in {"JPG", "JPEG"} else "image/png" if fmt == "PNG" else "application/octet-stream"

    return ValidatedImage(image=img, format=fmt, size=img.size, mime_type=mime)


def resize_for_model(img: Image.Image, max_side: int = 1024) -> Image.Image:
    """
    Keeps aspect ratio; resizes only if image larger than max_side.
    """
    w, h = img.size
    if max(w, h) <= max_side:
        return img

    if w >= h:
        new_w = max_side
        new_h = int(h * (max_side / w))
    else:
        new_h = max_side
        new_w = int(w * (max_side / h))

    return img.resize((new_w, new_h), resample=_lanczos_resample())
