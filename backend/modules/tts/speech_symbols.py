"""Đọc ký hiệu toán/liều dùng thành chữ (vd. "1-2 viên/lần" -> "1 đến 2 viên mỗi lần").

Vì sao cần: giọng đọc gặp "/" thì đánh vần từng chữ cái ("V I E N gạch chéo L T N"), gặp "-" giữa hai số
thì đọc dính ("10-15" -> "một nghìn không trăm mười lăm"); dấu "<" còn bị bộ lọc ký tự xóa làm sai nghĩa.
Chạy SAU khi đã thay đường dẫn/email (có "/" và ".") và TRƯỚC khi đọc mã/đơn vị.
"""
import re

from backend.modules.tts.speech_lexicon import (
    COMPARISON_NAMES,
    NUMBER_UNIT_NAMES,
    PER_WORDS,
)

_DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b")
_THOUSANDS = re.compile(r"\b\d{1,3}(?:\.\d{3})+\b")  # 2.500.000 (kiểu Việt Nam)
_DECIMAL = re.compile(r"(\d)[.,](\d)")
_RANGE = re.compile(r"(\d)\s*[-–—]\s*(?=\d)")
_TIMES_NUMBERS = re.compile(r"(\d)\s*[x×]\s*(?=\d)")
_TIMES_WORD = re.compile(r"\s+[x×X]\s*(?=\d)")  # "1 viên x 3 lần" -> "1 viên, 3 lần"
_FRACTION = re.compile(r"(\d)\s*/\s*(?=\d)")
_PER = re.compile(r"\s*/\s*(?=(?:\d+(?:[.,]\d+)?\s*)?(?:" + "|".join(map(re.escape, PER_WORDS)) + r")\b)")
_AND_OR = re.compile(r"và\s*/\s*hoặc", re.IGNORECASE)
_SLASH = re.compile(r"\s*/\s*")
_DASH = re.compile(r"\s+[-–—]+\s+")  # gạch ngang làm dấu ngắt ý (có khoảng trắng hai bên)
_NUMBER_UNIT = re.compile(
    r"(\d)\s*(" + "|".join(map(re.escape, NUMBER_UNIT_NAMES)) + r")\b", re.IGNORECASE
)
_COMPARISONS = [(re.compile(re.escape(sign) + r"\s*(?=\d)"), f" {word} ") for sign, word in COMPARISON_NAMES]


def read_symbols_aloud(text: str) -> str:
    text = _DATE.sub(r"ngày \1 tháng \2 năm \3", text)
    text = _THOUSANDS.sub(lambda m: m.group().replace(".", ""), text)
    text = _DECIMAL.sub(r"\1 phẩy \2", text)
    text = _NUMBER_UNIT.sub(lambda m: f"{m.group(1)} {NUMBER_UNIT_NAMES[m.group(2).lower()]}", text)
    for pattern, spoken in _COMPARISONS:
        text = pattern.sub(spoken, text)
    text = _RANGE.sub(r"\1 đến ", text)
    text = _TIMES_NUMBERS.sub(r"\1 nhân ", text)
    text = _TIMES_WORD.sub(", ", text)
    text = _FRACTION.sub(r"\1 phần ", text)
    text = _PER.sub(" mỗi ", text)
    text = _AND_OR.sub("và hoặc", text)
    text = _SLASH.sub(" hoặc ", text)
    return _DASH.sub(", ", text)
