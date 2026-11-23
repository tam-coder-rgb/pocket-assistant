"""Giao diện chung của KHO THUỐC.

Mọi nguồn dữ liệu (file JSON trên máy hiện nay, database online sau này) cài đặt đúng các hàm của
`MedicineCatalog`, nên phần tra cứu, API quản trị và app desktop không phải sửa khi đổi nguồn.
"""
from dataclasses import dataclass
from typing import Protocol

from backend.core.text_fold import fold


@dataclass(frozen=True)
class MedicineRecord:
    """1 thuốc trong kho (tên trường tiếng Anh; mỗi nguồn tự đổi sang dạng lưu của mình)."""

    name: str
    aliases: tuple[str, ...] = ()
    active_ingredient: str = ""
    indication: str = ""
    dosage_adult: str = ""
    dosage_child: str = ""
    meal_timing: str = ""
    warning: str = ""


def name_key(name: str) -> str:
    """Khóa so trùng tên: không phân biệt hoa/thường, dấu, khoảng trắng thừa ("Ambroxol" = "ambroxol ")."""
    return " ".join(fold(name).split())


class MedicineCatalog(Protocol):
    @property
    def revision(self) -> int:
        """Tăng mỗi khi dữ liệu đổi (phần tra tên dựa vào đây để dựng lại bộ tên)."""

    def all(self) -> list[MedicineRecord]: ...

    def get(self, name: str) -> MedicineRecord | None: ...

    def add(self, record: MedicineRecord) -> MedicineRecord:
        """Trùng tên với thuốc đã có -> ConflictError."""

    def replace(self, name: str, record: MedicineRecord) -> MedicineRecord:
        """Thay thuốc tên `name` (có thể đổi tên). Không có -> NotFoundError; tên mới trùng thuốc khác -> ConflictError."""

    def delete(self, name: str) -> MedicineRecord:
        """Xóa hẳn, trả về thuốc vừa xóa. Không có -> NotFoundError."""
