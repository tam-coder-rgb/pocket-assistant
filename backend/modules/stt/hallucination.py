"""Nhận ra câu Whisper tự "bịa" khi nghe im lặng/tiếng ồn (vd. "Hãy subscribe cho kênh Ghiền Mì Gõ").

Groq trả no_speech_prob = 0 cả với âm thanh im lặng nên không lọc bằng chỉ số đó được;
lọc theo danh sách câu quen thuộc trong config.
"""
import re

from backend.core.config import settings
from backend.core.text_fold import fold

_NON_WORD = re.compile(r"[^\w\s]")
_SPACES = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _SPACES.sub(" ", _NON_WORD.sub(" ", fold(text))).strip()


def is_hallucination(text: str) -> bool:
    normalized = _normalize(text)
    if normalized in settings.STT_HALLUCINATION_EXACT:
        return True
    return any(phrase in normalized for phrase in settings.STT_HALLUCINATION_PHRASES)
