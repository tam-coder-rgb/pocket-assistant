from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    """Khớp api_client.js: summarizeText gửi {text, speed}; streamSummarizeText gửi {text, document_type}."""

    text: str = Field(min_length=1)
    document_type: str = Field(default="", max_length=100)
    speed: float = 1.0  # đọc nhanh/chậm do trình duyệt xử lý, server bỏ qua


class SummarizeResponse(BaseModel):
    summary: str
    plain_speech_text: str  # bản không có ký hiệu gạch đầu dòng, dùng để đọc/hiển thị thay thế
    audio_url: str | None = None
