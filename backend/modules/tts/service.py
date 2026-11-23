"""Giao diện công khai của module giọng đọc (các module khác CHỈ import từ file này).

  tts_service.url_for_text(text)        -> URL phát giọng đọc của đoạn văn (tạo âm thanh khi được tải)
  tts_service.url_for_voice_file(stem)  -> URL phát file mp3 thu sẵn (voice_data/ trong kho file dữ liệu); không đọc kho,
                                           người gọi đã biết file có (file chỉ được tải khi trình duyệt phát)
"""
import logging
import re
from pathlib import Path

from backend.core import storage
from backend.core.config import settings
from backend.core.exceptions import (
    InvalidRequestError,
    NotFoundError,
    StorageUnavailableError,
)
from backend.core.ttl_store import TTLStore
from backend.modules.tts.cache import AudioCache, make_key
from backend.modules.tts.engine import TTSEngine
from backend.modules.tts.providers import create_provider_chain
from backend.modules.tts.speech_text import clean_for_speech

logger = logging.getLogger(__name__)

ROUTE_PREFIX = "/api/v1/speech"
_VOICE_STEM = re.compile(r"^med_\d+_(main|warning)$")  # chặn tên file lạ (path traversal)
_MAX_CLIPS = 512


class TTSService:
    def __init__(self, engine: TTSEngine, voice: str, voice_prefix: str):
        self._engine = engine
        self._voice = voice
        self._voice_prefix = voice_prefix
        self._clips: TTLStore[str] = TTLStore(settings.TTS_CLIP_TTL_SECONDS, _MAX_CLIPS)

    # ---------- đọc văn bản tùy ý ----------
    def _prepare(self, text: str) -> str:
        cleaned = clean_for_speech(text)
        if not cleaned:
            raise InvalidRequestError("Không có nội dung để đọc.")
        if len(cleaned) > settings.TTS_MAX_TEXT_CHARS:
            raise InvalidRequestError(f"Văn bản dài quá {settings.TTS_MAX_TEXT_CHARS} ký tự.")
        return cleaned

    async def audio_for_text(self, text: str) -> Path:
        return await self._engine.ensure_audio(self._prepare(text), self._voice)

    # ---------- kịch bản do backend đăng ký (thuốc...) ----------
    def url_for_text(self, text: str) -> str | None:
        """Đăng ký đoạn văn và trả URL phát. Rỗng -> None. Âm thanh được tạo khi trình duyệt tải URL."""
        cleaned = clean_for_speech(text)
        if not cleaned or len(cleaned) > settings.TTS_MAX_TEXT_CHARS:
            return None
        key = make_key(cleaned, self._voice)
        self._clips.put(key, cleaned)
        return f"{ROUTE_PREFIX}/clip/{key}"

    async def audio_for_clip(self, key: str) -> Path:
        text = self._clips.get(key)
        if text is None:
            raise NotFoundError("Đoạn âm thanh đã hết hạn. Vui lòng thực hiện lại thao tác.")
        return await self._engine.ensure_audio(text, self._voice)

    # ---------- mp3 thu sẵn ----------
    def _voice_path(self, stem: str) -> Path | None:
        if not _VOICE_STEM.fullmatch(stem):
            return None
        try:
            return storage.current().local_file(f"{self._voice_prefix}/{stem}.mp3")
        except StorageUnavailableError as exc:  # kho lỗi -> người gọi đọc bằng TTS thay vì hỏng cả kết quả
            logger.warning("Không lấy được %s: %s", stem, exc)
            return None

    def url_for_voice_file(self, stem: str) -> str | None:
        return f"{ROUTE_PREFIX}/voice/{stem}" if _VOICE_STEM.fullmatch(stem) else None

    def voice_file(self, stem: str) -> Path:
        path = self._voice_path(stem)
        if path is None:
            raise NotFoundError("Không tìm thấy file âm thanh.")
        return path

    # ---------- vận hành ----------
    async def warm_up(self) -> None:
        """Gọi thử 1 lần để mở sẵn kết nối tới engine (lần đầu thường chậm vài giây)."""
        try:
            await self.audio_for_text("Xin chào")
        except Exception as exc:  # noqa: BLE001 - khởi động không được chết vì TTS
            logger.warning("Warm-up TTS thất bại: %s", exc)

    def purge_cache(self) -> int:
        return self._engine.purge_cache()


def _build_service() -> TTSService:
    engine = TTSEngine(
        create_provider_chain(),
        AudioCache(settings.TTS_CACHE_DIR, settings.CACHE_TTL_SECONDS),
        concurrency=settings.TTS_CONCURRENCY,
        retries=settings.TTS_RETRIES,
        chunk_chars=settings.TTS_CHUNK_CHARS,
        timeout=settings.TTS_TIMEOUT_SECONDS,
        backoff=settings.TTS_RETRY_BACKOFF_SECONDS,
    )
    return TTSService(engine, settings.TTS_VOICE, settings.VOICE_DATA_PREFIX)


tts_service = _build_service()
