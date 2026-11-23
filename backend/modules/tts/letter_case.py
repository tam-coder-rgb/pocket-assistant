"""Đưa chữ IN HOA về chữ thường trước khi đọc (giọng đọc phát âm sai/đánh vần chữ in hoa).

- Dòng tiêu đề viết toàn chữ in hoa ("CẶP SỐ TƯƠNG ĐỒNG") -> chữ thường; riêng viết tắt đã biết
  (USB, API...) vẫn giữ in hoa để bước sau đánh vần.
- Từ tiếng Việt có dấu viết in hoa ở bất kỳ đâu ("ĐẶC TRỊ") -> chữ thường: từ có dấu không thể là viết tắt.
- Chữ không dấu in hoa ngắn ngoài tiêu đề (HIV, ABC123) không đụng tới: spell_out.py xử lý.

Chạy TRƯỚC bước đổi xuống dòng thành dấu chấm, vì tiêu đề được nhận ra theo từng dòng.
"""
import re

from backend.modules.tts.speech_lexicon import ACRONYM_NAMES

_WORD = re.compile(r"[^\W\d_]+")  # chuỗi chữ cái liền nhau


def _is_vietnamese_caps(word: str) -> bool:
    return len(word) > 1 and word.isupper() and not word.isascii()


def _is_caps_heading(line: str) -> bool:
    words = _WORD.findall(line)
    return (
        len(words) >= 2
        and not any(ch.islower() for ch in line)
        and any(_is_vietnamese_caps(w) for w in words)  # tiêu đề tiếng Việt luôn có chữ có dấu
    )


def _lower_word(match: re.Match) -> str:
    word = match.group()
    return word if word in ACRONYM_NAMES else word.lower()


def _soften_line(line: str) -> str:
    if _is_caps_heading(line):
        return _WORD.sub(_lower_word, line)
    return _WORD.sub(lambda m: m.group().lower() if _is_vietnamese_caps(m.group()) else m.group(), line)


def soften_caps(text: str) -> str:
    return "\n".join(_soften_line(line) for line in text.split("\n"))
