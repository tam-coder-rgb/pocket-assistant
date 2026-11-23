"""Biến mã/viết tắt/đơn vị thành chữ giọng đọc nói trôi chảy (vd. "API_ABCDF" -> "ây pi ai ... a bê xê đê ép").

Chạy TRƯỚC bước bỏ ký tự lạ: nếu không, dấu "_" bị xóa và "API_ABCDF" dính thành một từ vô nghĩa.
"""
import re

from backend.core.config import settings
from backend.modules.tts.speech_lexicon import (
    ACRONYM_NAMES,
    DIGIT_NAMES,
    EMAIL_SPOKEN,
    LETTER_NAMES,
    UNIT_NAMES,
    URL_SPOKEN,
)

_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_UNDERSCORES = re.compile(r"_+")
_WORD = re.compile(r"[^\W_]+")  # chuỗi chữ/số liền nhau (không gồm "_")
_RUN = re.compile(r"[A-Za-z]+|\d+")


def _spell(chars: str) -> str:
    return " ".join(LETTER_NAMES.get(c, DIGIT_NAMES.get(c, c)) for c in chars.upper())


def _is_spelled_acronym(run: str) -> bool:
    return (
        run.isupper()
        and 2 <= len(run) <= settings.SPEECH_SPELL_MAX_LETTERS
        and run not in settings.SPEECH_WORD_ACRONYMS
    )


def _read_letters(run: str) -> str:
    if (unit := UNIT_NAMES.get(run.lower())) is not None:
        return unit
    if _is_spelled_acronym(run):
        return ACRONYM_NAMES.get(run) or _spell(run)
    if run.isupper() and len(run) > 1:
        return run.lower()  # từ in hoa dài (PARACETAMOL) hoặc viết tắt đọc như từ (COVID)
    return run


def _read_token(token: str) -> str:
    if not token.isascii() or token.isdigit():
        return token  # từ tiếng Việt có dấu và số thuần: giọng đọc tự xử lý
    runs = _RUN.findall(token)
    is_code = any(_is_spelled_acronym(r) for r in runs)  # mã như ABC123 -> đọc cả chữ số từng con
    parts = [(_spell(r) if is_code else r) if r.isdigit() else _read_letters(r) for r in runs]
    return " ".join(parts)


def read_links_aloud(text: str) -> str:
    """Thay đường dẫn/email bằng lời nói (phải chạy trước mọi bước đụng tới "/" và ".")."""
    text = _URL.sub(f" {URL_SPOKEN} ", text)
    return _EMAIL.sub(f" {EMAIL_SPOKEN} ", text)


def read_codes_aloud(text: str) -> str:
    text = read_links_aloud(text)
    text = _UNDERSCORES.sub(" ", text)
    return _WORD.sub(lambda m: _read_token(m.group()), text)
