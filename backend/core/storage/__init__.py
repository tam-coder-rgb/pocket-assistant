"""Kho file dữ liệu dùng chung (danh mục thuốc JSON + mp3 thu sẵn).

  base.py        giao diện BlobStore (read / write / delete / list / local_file)
  local.py       "local": thư mục DATA_DIR trên máy chạy server
  supabase.py    "supabase": bucket Supabase Storage (mọi server dùng chung; desktop dùng qua API backend)
  json_bytes.py  đọc / ghi JSON giữ đúng định dạng file gốc

Chọn bằng DATA_STORAGE trong .env. Thêm nơi lưu khác: viết 1 lớp có đủ hàm của BlobStore rồi đăng ký trong `_FACTORIES`.
"""
from collections.abc import Callable

from backend.core.config import settings
from backend.core.storage.base import BlobStore
from backend.core.storage.local import LocalBlobStore
from backend.core.storage.supabase import SupabaseBlobStore

__all__ = ["BlobStore", "LocalBlobStore", "SupabaseBlobStore", "create", "current", "use"]

_FACTORIES: dict[str, Callable[[], BlobStore]] = {
    "local": lambda: LocalBlobStore(settings.DATA_DIR),
    "supabase": lambda: SupabaseBlobStore(
        settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY, settings.SUPABASE_BUCKET,
        settings.SUPABASE_CACHE_DIR, settings.SUPABASE_TIMEOUT_SECONDS,
    ),
}
_instance: BlobStore | None = None


def create(kind: str) -> BlobStore:
    factory = _FACTORIES.get(kind)
    if factory is None:
        raise ValueError(f"DATA_STORAGE không hợp lệ: {kind!r} (có: {list(_FACTORIES)})")
    return factory()


def current() -> BlobStore:
    """Kho đang dùng (tạo ở lần gọi đầu theo settings.DATA_STORAGE)."""
    global _instance
    if _instance is None:
        _instance = create(settings.DATA_STORAGE)
    return _instance


def use(store: BlobStore | None) -> None:
    """Thay kho đang dùng (test dùng bản sao; None = tạo lại theo cấu hình)."""
    global _instance
    _instance = store
