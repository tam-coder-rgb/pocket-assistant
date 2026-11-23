"""Google Translate TTS (thư viện gTTS): miễn phí, không cần API key, chỉ có 1 giọng cho mỗi ngôn ngữ.

Với engine này, tham số `voice` chính là mã ngôn ngữ (vd. "vi").
"""
import asyncio
import io

from gtts import gTTS

from backend.modules.tts.providers.base import BaseTTSProvider


def _synthesize_blocking(text: str, lang: str) -> bytes:
    buffer = io.BytesIO()
    gTTS(text=text, lang=lang).write_to_fp(buffer)
    return buffer.getvalue()


class GTTSProvider(BaseTTSProvider):
    name = "gtts"

    async def synthesize(self, text: str, voice: str) -> bytes:
        # gTTS dùng thư viện requests (đồng bộ) nên phải chạy trong thread để không chặn event loop
        audio = await asyncio.to_thread(_synthesize_blocking, text, voice)
        if not audio:
            raise RuntimeError("gTTS không trả về âm thanh")
        return audio
