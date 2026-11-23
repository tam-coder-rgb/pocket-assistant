"""Cartesia Sonic TTS: giọng tự nhiên, có nhiều giọng tiếng Việt. Cần CARTESIA_API_KEYS (1 hoặc nhiều khóa).

Với engine này, tham số `voice` là ID giọng của Cartesia (vd. giọng "Nhung").

Nhiều khóa: khóa đang dùng lỗi (hết hạn mức, sai khóa, ...) -> thử khóa kế tiếp (xem key_ring.py).
Mọi khóa đều lỗi -> báo lỗi để FallbackTTSProvider chuyển sang gTTS. Riêng lỗi mạng/quá giờ thì chuyển
gTTS ngay: lỗi đó không do khóa, thử khóa khác chỉ tốn thêm CARTESIA_TIMEOUT_SECONDS mỗi khóa.

QUAN TRỌNG: MP3 phải CÙNG định dạng với gTTS (24 kHz, 64 kbps, không thẻ ID3). Một kịch bản dài được ghép
từ nhiều câu, có câu do Cartesia, có câu do gTTS (khi Cartesia lỗi). Trình duyệt ước lượng thời lượng file
theo bitrate của khung đầu tiên -> lệch định dạng là sai thời lượng -> karaoke chạy lệch với giọng đọc.
"""
import logging

from cartesia import APIConnectionError, AsyncCartesia

from backend.core.config import settings
from backend.modules.tts.providers.base import BaseTTSProvider
from backend.modules.tts.providers.key_ring import KeyRing

logger = logging.getLogger(__name__)


class CartesiaProvider(BaseTTSProvider):
    name = "cartesia"

    def __init__(self) -> None:
        keys = settings.cartesia_api_keys
        if not keys:
            raise RuntimeError("Thiếu CARTESIA_API_KEYS")
        self._clients = KeyRing(
            [
                AsyncCartesia(api_key=key, timeout=settings.CARTESIA_TIMEOUT_SECONDS, max_retries=0)
                for key in keys
            ]
        )

    async def synthesize(self, text: str, voice: str) -> bytes:
        last_error: Exception | None = None
        for index, client in self._clients.in_order():
            try:
                return await _generate(client, text, voice)
            except APIConnectionError:  # gồm cả quá giờ: không do khóa -> để gTTS lo ngay
                raise
            except Exception as exc:  # noqa: BLE001 - hết hạn mức, sai khóa, lỗi máy chủ, ...
                last_error = exc
                self._clients.mark_failed(index)
                logger.warning("Cartesia khóa #%d/%d lỗi, thử khóa kế tiếp: %s", index + 1, len(self._clients), exc)
        raise RuntimeError(f"Cả {len(self._clients)} khóa Cartesia đều lỗi") from last_error


async def _generate(client: AsyncCartesia, text: str, voice: str) -> bytes:
    response = await client.tts.generate(
        model_id=settings.CARTESIA_MODEL,
        transcript=text,
        voice={"mode": "id", "id": voice},
        language="vi",
        output_format={
            "container": "mp3",
            "sample_rate": settings.CARTESIA_SAMPLE_RATE,
            "bit_rate": settings.CARTESIA_BIT_RATE,
        },
    )
    audio = _strip_id3(await response.read())
    if not audio:
        raise RuntimeError("Cartesia không trả về âm thanh")
    return audio


def _strip_id3(audio: bytes) -> bytes:
    """Bỏ thẻ ID3 ở đầu: thẻ nằm giữa file sau khi ghép các câu sẽ làm trình duyệt đọc sai khung MP3."""
    if len(audio) < 10 or audio[:3] != b"ID3":
        return audio
    size = (audio[6] << 21) | (audio[7] << 14) | (audio[8] << 7) | audio[9]
    footer = 10 if audio[5] & 0x10 else 0
    return audio[10 + size + footer :]
