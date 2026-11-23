"""Kho thuốc là 1 file JSON trong kho file dữ liệu (core/storage: thư mục data/ hoặc Supabase), dạng gốc
của dự án, khóa tiếng Việt: ten_thuoc, lieu_nguoi_lon...

- Đọc vào bộ nhớ, đọc lại ở luồng nền sau mỗi `max_age` giây (core/storage/refresh.py): server khác
  (Render / máy bác sĩ) sửa thì server này cũng thấy, người tra cứu không phải chờ.
- Thêm / sửa / xóa: đọc bản MỚI NHẤT rồi mới sửa và ghi lại cả file (không đè mất thay đổi của server khác).
- Khóa luồng để 2 yêu cầu cùng lúc không ghi đè nhau.
"""
import threading

from backend.core.exceptions import (
    ConflictError,
    NotFoundError,
    StorageUnavailableError,
)
from backend.core.storage import BlobStore, json_bytes
from backend.core.storage.refresh import Refresher
from backend.modules.medicine.catalog.base import MedicineRecord, name_key

# Trường của MedicineRecord -> khóa trong file JSON, đúng thứ tự của file gốc (sửa 1 thuốc không làm xáo cả file)
_JSON_KEYS = {
    "name": "ten_thuoc",
    "dosage_adult": "lieu_nguoi_lon",
    "dosage_child": "lieu_tre_em",
    "meal_timing": "thoi_diem_uong",
    "warning": "luu_y",
    "active_ingredient": "hoat_chat",
    "indication": "cong_dung",
    "aliases": "ten_goi_khac",
}


def _parse_aliases(raw: object) -> tuple[str, ...]:
    """`ten_goi_khac` là danh sách (hoặc chuỗi cũ ngăn bằng dấu phẩy)."""
    items = raw if isinstance(raw, list) else str(raw or "").split(",")
    return tuple(a.strip() for a in items if a and str(a).strip())


def _from_json(item: dict) -> MedicineRecord:
    values = {field: str(item.get(key) or "") for field, key in _JSON_KEYS.items() if field != "aliases"}
    return MedicineRecord(aliases=_parse_aliases(item.get(_JSON_KEYS["aliases"])), **values)


def _to_json(record: MedicineRecord) -> dict:
    return {key: list(record.aliases) if field == "aliases" else getattr(record, field) for field, key in _JSON_KEYS.items()}


def _index_of(records: list[MedicineRecord], name: str) -> int | None:
    key = name_key(name)
    return next((i for i, record in enumerate(records) if name_key(record.name) == key), None)


class JsonCatalog:
    def __init__(self, store: BlobStore, key: str, max_age: float) -> None:
        self._store = store
        self._key = key
        self._refresher = Refresher(max_age, self._reload)
        self._lock = threading.RLock()
        self._records: list[MedicineRecord] = []
        self._raw: bytes | None = None  # nội dung file lần đọc gần nhất
        self._revision = 0

    @property
    def revision(self) -> int:
        return self._revision

    def all(self) -> list[MedicineRecord]:
        return list(self._loaded())

    def get(self, name: str) -> MedicineRecord | None:
        records = self._loaded()
        index = _index_of(records, name)
        return None if index is None else records[index]

    def add(self, record: MedicineRecord) -> MedicineRecord:
        with self._lock:
            records = self._reload()
            if _index_of(records, record.name) is not None:
                raise ConflictError(f"Đã có thuốc tên “{record.name}” trong danh mục.")
            self._commit([*records, record])
        return record

    def replace(self, name: str, record: MedicineRecord) -> MedicineRecord:
        with self._lock:
            records = self._reload().copy()
            index = self._require(records, name)
            other = _index_of(records, record.name)
            if other is not None and other != index:
                raise ConflictError(f"Đã có thuốc khác tên “{record.name}” trong danh mục.")
            records[index] = record
            self._commit(records)
        return record

    def delete(self, name: str) -> MedicineRecord:
        with self._lock:
            records = self._reload().copy()
            removed = records.pop(self._require(records, name))
            self._commit(records)
        return removed

    # ---------- nội bộ ----------
    def _loaded(self) -> list[MedicineRecord]:
        self._refresher.ensure()
        return self._records

    def _reload(self) -> list[MedicineRecord]:
        with self._lock:
            raw = self._store.read(self._key)
            if raw is None:  # không coi là danh mục rỗng: thường do cấu hình kho sai
                raise StorageUnavailableError(f"Không thấy danh mục thuốc “{self._key}” trong kho {self._store.name}.")
            if raw != self._raw:
                self._remember([_from_json(item) for item in json_bytes.loads(raw)], raw)
            self._refresher.mark_fresh()
            return self._records

    @staticmethod
    def _require(records: list[MedicineRecord], name: str) -> int:
        index = _index_of(records, name)
        if index is None:
            raise NotFoundError(f"Không tìm thấy thuốc “{name}” trong danh mục.")
        return index

    def _commit(self, records: list[MedicineRecord]) -> None:
        raw = json_bytes.dumps([_to_json(r) for r in records], like=self._raw)
        self._store.write(self._key, raw)
        self._remember(records, raw)

    def _remember(self, records: list[MedicineRecord], raw: bytes) -> None:
        self._records = records
        self._raw = raw
        self._refresher.mark_fresh()
        self._revision += 1
