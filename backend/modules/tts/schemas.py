from pydantic import BaseModel, Field


class SpeechRequest(BaseModel):
    """Web có gửi kèm `speed`, nhưng tốc độ do trình duyệt xử lý (playbackRate) nên server bỏ qua."""

    text: str = Field(min_length=1)
