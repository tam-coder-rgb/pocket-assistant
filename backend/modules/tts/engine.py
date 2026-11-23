"""Tạo âm thanh: cache đĩa -> dùng chung lần tạo đang chạy -> giới hạn song song -> engine.

Vì sao chia nhỏ: kịch bản dài được chia thành các câu rồi tạo song song (rút ngắn thời gian chờ), và
từng câu được nhớ riêng nên câu lặp lại giữa các kịch bản (vd. câu khuyến cáo AI) có sẵn tức thì.
Các đoạn MP3 do cùng một engine tạo ra có cùng định dạng nên ghép nối trực tiếp được.
"""
import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

from backend.core.exceptions import TTSUnavailableError
from backend.modules.tts.cache import AudioCache, make_key
from backend.modules.tts.providers import BaseTTSProvider
from backend.modules.tts.speech_text import split_for_synthesis

logger = logging.getLogger(__name__)


class TTSEngine:
    def __init__(
        self,
        provider: BaseTTSProvider,
        cache: AudioCache,
        *,
        concurrency: int,
        retries: int,
        chunk_chars: int = 90,
        timeout: float = 25.0,
        backoff: float = 1.0,
    ):
        self._provider = provider
        self._cache = cache
        self._retries = retries
        self._chunk_chars = chunk_chars
        self._timeout = timeout
        self._backoff = backoff
        self._semaphore = asyncio.Semaphore(concurrency)
        self._inflight: dict[str, asyncio.Task[Path]] = {}

    async def ensure_audio(self, text: str, voice: str) -> Path:
        """Trả đường dẫn file mp3 của `text` (đã làm sạch), tạo mới nếu chưa có."""
        return await self._once(make_key(text, voice), lambda: self._build(text, voice))

    async def _once(self, key: str, factory: Callable[[], Awaitable[Path]]) -> Path:
        """Cache đĩa + chỉ 1 lần tạo cho mỗi khóa dù có nhiều yêu cầu cùng lúc."""
        if cached := self._cache.get(key):
            return cached
        task = self._inflight.get(key)
        if task is None:
            task = asyncio.create_task(factory())
            self._inflight[key] = task
            task.add_done_callback(lambda _: self._inflight.pop(key, None))
        return await asyncio.shield(task)  # người dùng ngắt kết nối không hủy việc của người khác

    async def _build(self, text: str, voice: str) -> Path:
        chunks = split_for_synthesis(text, self._chunk_chars)
        if len(chunks) <= 1:
            return await self._synthesize(text, voice)
        paths = await asyncio.gather(*(self.ensure_chunk(chunk, voice) for chunk in chunks))
        audio = await asyncio.to_thread(lambda: b"".join(p.read_bytes() for p in paths))
        return await asyncio.to_thread(self._cache.put, make_key(text, voice), audio)

    async def ensure_chunk(self, chunk: str, voice: str) -> Path:
        return await self._once(make_key(chunk, voice), lambda: self._synthesize(chunk, voice))

    async def _synthesize(self, text: str, voice: str) -> Path:
        last_error: Exception | None = None
        for attempt in range(1 + self._retries):
            if attempt:  # nghỉ ngoài hàng đợi để không chiếm chỗ của câu khác
                await asyncio.sleep(self._backoff * attempt)
            async with self._semaphore:
                try:
                    async with asyncio.timeout(self._timeout):
                        audio = await self._provider.synthesize(text, voice)
                    return await asyncio.to_thread(self._cache.put, make_key(text, voice), audio)
                except Exception as exc:  # noqa: BLE001 - engine ngoài có thể lỗi đủ kiểu
                    last_error = exc
                    logger.warning("TTS lần %d lỗi: %s", attempt + 1, exc)
        raise TTSUnavailableError("Không tạo được giọng đọc lúc này. Vui lòng thử lại.") from last_error

    def purge_cache(self) -> int:
        return self._cache.purge_expired()
