"""Kho thuốc dùng chung cho tra cứu và quản trị.

  base.py          MedicineRecord + giao diện MedicineCatalog (mọi nguồn dữ liệu cài đặt giống nhau)
  json_catalog.py  định dạng "json": file medic_data/medicines.json trong kho file dữ liệu
                   (core/storage: thư mục data/ hoặc Supabase Storage, chọn bằng DATA_STORAGE)

Đổi định dạng lưu (vd. bảng database): viết thêm 1 lớp cài đặt MedicineCatalog, đăng ký trong `_FACTORIES`,
rồi đặt MEDICINE_CATALOG trong .env. Không phải sửa chỗ nào khác.
"""
from collections.abc import Callable

from backend.core import storage
from backend.core.config import settings
from backend.modules.medicine.catalog.base import (
    MedicineCatalog,
    MedicineRecord,
    name_key,
)
from backend.modules.medicine.catalog.json_catalog import JsonCatalog

__all__ = ["MedicineCatalog", "MedicineRecord", "current", "name_key", "use"]

_FACTORIES: dict[str, Callable[[], MedicineCatalog]] = {
    "json": lambda: JsonCatalog(storage.current(), settings.MEDIC_DATA_KEY, settings.DATA_CACHE_SECONDS),
}
_instance: MedicineCatalog | None = None


def current() -> MedicineCatalog:
    """Kho đang dùng (tạo ở lần gọi đầu theo settings.MEDICINE_CATALOG)."""
    global _instance
    if _instance is None:
        factory = _FACTORIES.get(settings.MEDICINE_CATALOG)
        if factory is None:
            raise ValueError(f"MEDICINE_CATALOG không hợp lệ: {settings.MEDICINE_CATALOG!r} (có: {list(_FACTORIES)})")
        _instance = factory()
    return _instance


def use(catalog: MedicineCatalog | None) -> None:
    """Thay kho đang dùng (test dùng bản sao; None = tạo lại theo cấu hình)."""
    global _instance
    _instance = catalog
