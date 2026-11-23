"""Chuyển giọng nói thành chữ bằng Groq Whisper (API chuẩn OpenAI /audio/transcriptions)."""
import httpx

from backend.core.config import settings
from backend.core.exceptions import AIUnavailableError, InvalidRequestError
from backend.modules.stt.hallucination import is_hallucination


async def transcribe(audio: bytes, filename: str, content_type: str) -> str:
    """Trả về chữ đã nhận diện ("" nếu không nghe thấy gì)."""
    if not audio:
        raise InvalidRequestError("Không nhận được âm thanh.")
    if len(audio) > settings.STT_MAX_AUDIO_BYTES:
        raise InvalidRequestError("Đoạn ghi âm quá dài. Hãy nói ngắn gọn hơn.")
    if not settings.GROQ_API_KEY:
        raise AIUnavailableError("Chưa cấu hình GROQ_API_KEY để nhận diện giọng nói.")

    try:
        async with httpx.AsyncClient(timeout=settings.STT_TIMEOUT_SECONDS) as http:
            resp = await http.post(
                settings.GROQ_STT_URL,
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                data={
                    "model": settings.GROQ_STT_MODEL,
                    "language": settings.STT_LANGUAGE,
                    "response_format": "json",
                    "temperature": "0",
                },
                files={"file": (filename, audio, content_type)},
            )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise AIUnavailableError("Không nhận diện được giọng nói lúc này. Hãy thử lại.") from exc

    text = (resp.json().get("text") or "").strip()
    return "" if is_hallucination(text) else text
