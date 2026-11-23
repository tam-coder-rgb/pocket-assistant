"""Giữ tạm ảnh vừa quét (trong RAM) để Bước 2 "Phân tích bằng AI" dùng lại mà không phải tải ảnh lên lần nữa.

Web nhận một mã `img_...` ở Bước 1 và gửi lại mã đó ở Bước 2. Mã tự hết hạn.
"""
import uuid

from backend.core.config import settings
from backend.core.ttl_store import TTLStore

TOKEN_PREFIX = "img_"  # api_client.js nhận ra mã ảnh qua tiền tố này


class ImageStore:
    def __init__(self, ttl_seconds: int, max_items: int):
        self._store: TTLStore[bytes] = TTLStore(ttl_seconds, max_items)

    def put(self, jpeg: bytes) -> str:
        token = TOKEN_PREFIX + uuid.uuid4().hex
        self._store.put(token, jpeg)
        return token

    def get(self, token: str) -> bytes | None:
        return self._store.get(token)


image_store = ImageStore(settings.SCAN_TOKEN_TTL_SECONDS, settings.SCAN_TOKEN_MAX_ITEMS)
