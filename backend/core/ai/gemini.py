"""Google Gemini qua Interactions API (khớp tests/test_vlm_gemini.py)."""
import base64
from collections.abc import AsyncIterator, Sequence

from google import genai

from backend.core.ai.base import BaseAIProvider, ChatMessage
from backend.core.config import settings

_ROLE_LABELS = {"user": "Người dùng", "assistant": "Trợ lý"}


def _transcript(messages: Sequence[ChatMessage]) -> str:
    """Gộp lịch sử hội thoại thành 1 đoạn văn bản và mời model viết tiếp lượt của 'Trợ lý'."""
    lines = [f"{_ROLE_LABELS.get(m.role, m.role)}: {m.content}" for m in messages]
    return "\n".join(lines) + "\nTrợ lý:"


class GeminiProvider(BaseAIProvider):
    name = "gemini"

    def __init__(self) -> None:
        self._client: genai.Client | None = None  # tạo 1 lần, dùng lại kết nối

    def is_available(self) -> bool:
        return bool(settings.GEMINI_API_KEY)

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    async def generate(self, prompt: str, image_jpeg: bytes | None = None) -> str:
        parts: list[dict] = [{"type": "text", "text": prompt}]
        if image_jpeg:
            parts.append(
                {
                    "type": "image",
                    "data": base64.b64encode(image_jpeg).decode(),
                    "mime_type": "image/jpeg",
                }
            )
        interaction = await self._get_client().aio.interactions.create(
            model=settings.GEMINI_VLM_MODEL, input=parts
        )
        return interaction.output_text or ""

    async def stream_chat(
        self, messages: Sequence[ChatMessage], system_prompt: str
    ) -> AsyncIterator[str]:
        stream = await self._get_client().aio.interactions.create(
            model=settings.GEMINI_VLM_MODEL,
            input=_transcript(messages),
            system_instruction=system_prompt,
            stream=True,
        )
        async for event in stream:
            delta = getattr(event, "delta", None)  # chỉ các sự kiện step.delta mới có `delta`
            if getattr(delta, "type", None) == "text" and delta.text:
                yield delta.text
