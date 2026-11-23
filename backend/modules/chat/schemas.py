from typing import Literal

from pydantic import BaseModel, Field

from backend.core.config import settings


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class MedicineContext(BaseModel):
    """Thông tin thuốc đang xem — web gửi kèm để AI trả lời đúng thuốc (tên khóa khớp app.js)."""

    medicine_name: str = ""
    active_ingredient: str = ""
    indication: str = ""
    dosage_adult: str = ""
    dosage_child: str = ""
    timing: str = ""
    warnings: str = ""
    source: str = ""  # "DB" = CSDL đã kiểm định; khác = AI tra cứu


class DocumentContext(BaseModel):
    """Văn bản đang xem: nguyên văn quét được và bản tóm tắt (nếu đã có)."""

    raw_text: str = ""
    summary: str = ""


class _ChatBase(BaseModel):
    message: str = Field(min_length=1, max_length=settings.CHAT_MAX_MESSAGE_CHARS)
    history: list[ChatTurn] = []


class ChatRequest(_ChatBase):
    context: MedicineContext = MedicineContext()


class DocumentChatRequest(_ChatBase):
    context: DocumentContext = DocumentContext()
