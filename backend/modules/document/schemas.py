from pydantic import BaseModel


class DocumentVLMResult(BaseModel):
    raw_text: str  # bắt buộc (có thể rỗng): thiếu khóa = AI trả sai dạng


class DocumentScanResponse(BaseModel):
    """JSON trả về cho web — khớp renderDocumentResult() trong app.js."""

    status: str  # success | no_text | unreadable_image
    is_unreadable: bool = False
    raw_text: str = ""
    audio_url: str | None = None  # TTS: bổ sung ở tính năng giọng đọc
