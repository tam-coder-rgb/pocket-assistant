"""Quy tắc quản trị thuốc: kiểm tra dữ liệu, thêm / sửa / xóa trong kho, giữ giọng đọc thu sẵn khớp nội dung.

- Không nhận tên trống, thiếu công dụng hoặc liều người lớn, tên thuộc nhóm chất nguy hiểm.
- Thêm thuốc: lưu vào kho rồi tạo mp3 thu sẵn (phần chính + lưu ý).
- Sửa nội dung giọng đọc (tên, công dụng, liều, cách dùng, lưu ý): mp3 cũ đọc thông tin CŨ nên bị thay bằng mp3 mới.
- Xóa thuốc: xóa hẳn khỏi kho và xóa mp3 thu sẵn của thuốc đó.
Tạo mp3 lỗi (TTS hết hạn mức...) thì thuốc vẫn được lưu; `has_voice` = False cho giao diện biết.
"""
import asyncio
from dataclasses import fields

from backend.core import safety
from backend.core.exceptions import InvalidRequestError
from backend.modules.medicine import catalog, voice_generator, voice_library
from backend.modules.medicine.admin_schemas import (
    MedicineAdminItem,
    MedicineAdminList,
    MedicineDeleted,
    MedicineInput,
)
from backend.modules.medicine.catalog import MedicineRecord, name_key

_REQUIRED = {"name": "tên thuốc", "indication": "công dụng", "dosage_adult": "liều dùng cho người lớn"}
_SPOKEN_FIELDS = ("name", "indication", "meal_timing", "dosage_adult", "dosage_child", "warning")


def _clean(data: MedicineInput) -> MedicineRecord:
    name = " ".join(data.name.split())
    texts = {f.name: getattr(data, f.name).strip() for f in fields(MedicineRecord) if f.name not in ("name", "aliases")}
    missing = [label for key, label in _REQUIRED.items() if not (name if key == "name" else texts[key])]
    if missing:
        raise InvalidRequestError(f"Vui lòng nhập {', '.join(missing)}.")

    aliases: list[str] = []
    seen = {name_key(name)}
    for alias in (" ".join(a.split()) for a in data.aliases):
        if alias and name_key(alias) not in seen:
            seen.add(name_key(alias))
            aliases.append(alias)

    if any(safety.is_hazardous(n) for n in (name, *aliases)):
        raise InvalidRequestError("Tên này thuộc nhóm hóa chất / chất nguy hiểm, không thể thêm vào danh mục thuốc.")
    return MedicineRecord(name=name, aliases=tuple(aliases), **texts)


def _to_item(record: MedicineRecord) -> MedicineAdminItem:
    values = {f.name: getattr(record, f.name) for f in fields(MedicineRecord)}
    values["aliases"] = list(record.aliases)
    return MedicineAdminItem(**values, has_voice=voice_library.current().has_voice(record.name))


def _speech_changed(old: MedicineRecord, new: MedicineRecord) -> bool:
    return any(getattr(old, field) != getattr(new, field) for field in _SPOKEN_FIELDS)


def _list() -> MedicineAdminList:
    items = sorted((_to_item(r) for r in catalog.current().all()), key=lambda item: name_key(item.name))
    return MedicineAdminList(data=items, total=len(items))


def _replace(name: str, data: MedicineInput) -> tuple[MedicineRecord, bool]:
    """Ghi thuốc đã sửa; nội dung giọng đọc đổi thì xóa mp3 cũ. Trả về (thuốc mới, có cần tạo mp3 mới)."""
    store = catalog.current()
    old = store.get(name)
    new = store.replace(name, _clean(data))  # không có thuốc / trùng tên -> lỗi trước khi động vào mp3
    changed = old is None or _speech_changed(old, new)
    if changed and old is not None:
        voice_library.current().remove(old.name)
    return new, changed


def _delete(name: str) -> MedicineDeleted:
    removed = catalog.current().delete(name)
    return MedicineDeleted(name=removed.name, voice_files_removed=voice_library.current().remove(removed.name))


# Ghi file / db là thao tác chặn: chạy ở luồng phụ để không treo server
async def list_all() -> MedicineAdminList:
    return await asyncio.to_thread(_list)


async def add(data: MedicineInput) -> MedicineAdminItem:
    record = await asyncio.to_thread(lambda: catalog.current().add(_clean(data)))
    await voice_generator.generate(record)
    return await asyncio.to_thread(_to_item, record)


async def update(name: str, data: MedicineInput) -> MedicineAdminItem:
    record, needs_voice = await asyncio.to_thread(_replace, name, data)
    if needs_voice:
        await voice_generator.generate(record)
    return await asyncio.to_thread(_to_item, record)


async def delete(name: str) -> MedicineDeleted:
    return await asyncio.to_thread(_delete, name)
