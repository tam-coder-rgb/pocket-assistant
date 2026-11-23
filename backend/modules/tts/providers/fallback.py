"""Thử lần lượt các engine theo thứ tự ưu tiên; engine trước lỗi thì chuyển sang engine sau.

Mỗi engine có giọng riêng (gTTS: mã ngôn ngữ, Cartesia: ID giọng) nên giọng được tra theo tên engine.
"""
import logging

from backend.modules.tts.providers.base import BaseTTSProvider

logger = logging.getLogger(__name__)


class FallbackTTSProvider(BaseTTSProvider):
    name = "fallback"

    def __init__(self, providers: list[BaseTTSProvider], voices: dict[str, str]):
        if not providers:
            raise ValueError("Cần ít nhất 1 engine giọng đọc")
        self._providers = providers
        self._voices = voices

    async def synthesize(self, text: str, voice: str) -> bytes:
        last_error: Exception | None = None
        for provider in self._providers:
            try:
                # `voice` là nhãn chung (dùng làm khóa cache); giọng thật lấy theo từng engine
                return await provider.synthesize(text, self._voices.get(provider.name, voice))
            except Exception as exc:  # noqa: BLE001 - engine ngoài có thể lỗi đủ kiểu
                last_error = exc
                logger.warning("TTS engine %s lỗi, thử engine kế tiếp: %s", provider.name, exc)
        raise RuntimeError("Mọi engine giọng đọc đều lỗi") from last_error
