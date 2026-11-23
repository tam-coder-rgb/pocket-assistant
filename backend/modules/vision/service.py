"""Tiền xử lý ảnh trước khi gửi VLM: giải mã, kiểm tra độ mờ, resize + nén JPEG."""
import asyncio
import io
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from backend.core.config import settings
from backend.core.exceptions import InvalidImageError


@dataclass
class PreparedImage:
    jpeg_bytes: bytes
    blur_score: float
    is_blurry: bool


def _prepare(raw: bytes) -> PreparedImage:
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImageError("File tải lên không phải ảnh hợp lệ.") from exc

    img.thumbnail((settings.MAX_IMAGE_DIMENSION, settings.MAX_IMAGE_DIMENSION))
    gray = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2GRAY)
    score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=settings.IMAGE_JPEG_QUALITY)
    return PreparedImage(buf.getvalue(), score, score < settings.LAPLACIAN_BLUR_THRESHOLD)


async def prepare_image(raw: bytes) -> PreparedImage:
    """Public interface của module vision (CPU-bound nên chạy trong thread)."""
    if len(raw) > settings.MAX_UPLOAD_BYTES:
        raise InvalidImageError("Ảnh quá lớn.")
    return await asyncio.to_thread(_prepare, raw)
