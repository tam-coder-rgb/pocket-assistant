"""Dữ liệu vào/ra của API quản trị thuốc (bác sĩ / dược sĩ dùng từ app desktop)."""
from pydantic import BaseModel, Field

from backend.core.config import settings

_TEXT = Field(default="", max_length=settings.MEDICINE_TEXT_MAX_CHARS)


class MedicineInput(BaseModel):
    """Thuốc bác sĩ nhập (thêm mới hoặc sửa)."""

    name: str = Field(max_length=settings.MEDICINE_NAME_MAX_CHARS)
    aliases: list[str] = Field(default_factory=list, max_length=settings.MEDICINE_MAX_ALIASES)
    active_ingredient: str = _TEXT
    indication: str = _TEXT
    dosage_adult: str = _TEXT
    dosage_child: str = _TEXT
    meal_timing: str = _TEXT
    warning: str = _TEXT


class MedicineAdminItem(MedicineInput):
    has_voice: bool = False  # còn giọng đọc thu sẵn (mp3) hay đọc bằng TTS


class MedicineAdminList(BaseModel):
    data: list[MedicineAdminItem]
    total: int


class MedicineDeleted(BaseModel):
    name: str
    voice_files_removed: int
