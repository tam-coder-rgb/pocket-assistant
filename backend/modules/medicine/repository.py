"""Tra thuốc trong kho (catalog/) theo tên: so khớp từng từ (matching.py).

Bộ tên (tên chính + tên gọi khác) được dựng lại tự động khi kho đổi (bác sĩ thêm / sửa / xóa thuốc).
"""
import asyncio

from backend.modules.medicine import catalog, matching
from backend.modules.medicine.catalog import MedicineRecord

_cache: dict = {"key": None, "index": None}


def _index() -> tuple[list[MedicineRecord], list[tuple[int, str, bool]]]:
    """(danh sách thuốc, [(chỉ số thuốc, tên/biệt danh, là tên chính)]) của phiên bản kho hiện tại."""
    store = catalog.current()
    key = (id(store), store.revision)
    if _cache["key"] != key:
        medicines = store.all()
        names: list[tuple[int, str, bool]] = []
        for i, med in enumerate(medicines):
            names.append((i, med.name, True))
            names.extend((i, alias, False) for alias in med.aliases)
        _cache.update(key=key, index=(medicines, names))
    return _cache["index"]


def _find(query: str) -> MedicineRecord | None:
    medicines, names = _index()
    index = matching.pick_best(query, names)
    return None if index is None else medicines[index]


async def find_medicine(query: str) -> MedicineRecord | None:
    if not query.strip():
        return None
    return await asyncio.to_thread(_find, query)


def _search(query: str) -> list[MedicineRecord]:
    medicines, names = _index()
    q = query.strip().lower()
    if not q:
        return medicines
    hits = {i for i, name, _ in names if q in name.lower()}
    return [medicines[i] for i in sorted(hits)]


async def list_medicines(query: str = "") -> list[MedicineRecord]:
    """Danh sách thuốc (lọc theo chuỗi con trong tên/biệt danh nếu có `query`)."""
    return await asyncio.to_thread(_search, query)
