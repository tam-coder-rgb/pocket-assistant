"""Điểm vào duy nhất để gọi VLM: cache -> chạy provider theo thứ tự ưu tiên (có hedge).

Thêm provider mới: viết class kế thừa BaseAIProvider rồi thêm vào PROVIDERS.
"""
import asyncio
from collections.abc import AsyncIterator, Sequence
from functools import partial

from backend.core.ai.base import (
    BaseAIProvider,
    ChatMessage,
    T,
    build_json_prompt,
    parse_json_result,
    unavailable_error,
)
from backend.core.ai.cache import LRUCache, make_key
from backend.core.ai.gemini import GeminiProvider
from backend.core.ai.groq import GroqProvider
from backend.core.ai.hedge import AllJobsFailedError, first_success
from backend.core.ai.streaming import stream_with_fallback
from backend.core.config import settings
from backend.core.exceptions import AIUnavailableError

PROVIDERS: dict[str, BaseAIProvider] = {p.name: p for p in (GeminiProvider(), GroqProvider())}


async def _ask(
    provider: BaseAIProvider, prompt: str, image: bytes | None, schema: type[T]
) -> T:
    """1 provider: gửi prompt (+ảnh), nhận văn bản, kiểm tra đúng schema (JSON hỏng cũng tính là lỗi)."""
    async with asyncio.timeout(settings.AI_TIMEOUT_SECONDS):
        text = await provider.generate(prompt, image)
    return parse_json_result(text, schema)


class AIClient:
    def __init__(self) -> None:
        self._cache = LRUCache(settings.AI_CACHE_SIZE)

    def _active_providers(self) -> list[BaseAIProvider]:
        found = (PROVIDERS.get(name) for name in settings.AI_PROVIDER_ORDER)
        return [p for p in found if p is not None and p.is_available()]

    async def analyze(
        self, prompt: str, schema: type[T], *, image_jpeg: bytes | None = None
    ) -> T:
        """Gửi prompt (+ ảnh nếu có), trả về đối tượng `schema` đã kiểm tra."""
        full_prompt = build_json_prompt(prompt, schema)
        key = make_key(image_jpeg or b"", full_prompt)
        if (cached := self._cache.get(key)) is not None:
            return cached

        jobs = [
            (p.name, partial(_ask, p, full_prompt, image_jpeg, schema))
            for p in self._active_providers()
        ]
        if not jobs:
            raise AIUnavailableError("Hệ thống AI chưa được cấu hình (thiếu API key).")
        try:
            result = await first_success(jobs, settings.AI_HEDGE_DELAY_SECONDS)
        except AllJobsFailedError as exc:
            raise unavailable_error(exc.errors) from exc

        self._cache.put(key, result)
        return result

    def stream_chat(
        self, messages: Sequence[ChatMessage], system_prompt: str
    ) -> AsyncIterator[str]:
        """Hội thoại streaming: trả từng đoạn chữ; fallback chỉ khi chưa gửi chữ nào."""
        providers = self._active_providers()
        if not providers:
            raise AIUnavailableError("Hệ thống AI chưa được cấu hình (thiếu API key).")
        return stream_with_fallback(
            providers,
            messages,
            system_prompt,
            first_token_timeout=settings.AI_STREAM_FIRST_TOKEN_TIMEOUT,
            last_provider_timeout=settings.AI_TIMEOUT_SECONDS,  # Gemini có lúc >8s mới ra chữ đầu
        )


ai_client = AIClient()
