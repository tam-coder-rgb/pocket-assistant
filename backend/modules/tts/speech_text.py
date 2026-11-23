"""Làm sạch văn bản trước khi đọc: bỏ biểu tượng/emoji/gạch đầu dòng mà giọng đọc sẽ đọc lung tung."""
import re
import unicodedata

from backend.modules.tts.letter_case import soften_caps
from backend.modules.tts.speech_symbols import read_symbols_aloud
from backend.modules.tts.spell_out import read_codes_aloud, read_links_aloud

_BULLETS = set("•═*#_~`|<>[]{}\\")
_ZERO_WIDTH = {"️", "‍"}  # bộ chọn biểu tượng cảm xúc
_REPLACEMENTS = (("°C", " độ C"), ("°", " độ "), ("+", " cộng "), ("%", " phần trăm"))
_NEWLINES = re.compile(r"\s*\n+\s*")
_DOUBLE_STOP = re.compile(r"([.!?:;,])\s*\.\s")
_SPACES = re.compile(r"[ \t]+")


def clean_for_speech(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    for old, new in _REPLACEMENTS:
        text = text.replace(old, new)
    text = read_links_aloud(text)
    text = soften_caps(text)  # "CẶP SỐ TƯƠNG ĐỒNG" -> "cặp số tương đồng" (giọng đọc đọc sai chữ in hoa)
    text = read_symbols_aloud(text)  # "1-2 viên/lần" -> "1 đến 2 viên mỗi lần"
    text = read_codes_aloud(text)
    kept = (
        ch
        for ch in text
        if ch not in _BULLETS and ch not in _ZERO_WIDTH and unicodedata.category(ch)[0] != "S"
    )
    text = "".join(kept)
    text = _NEWLINES.sub(". ", text)  # xuống dòng -> ngắt câu để giọng đọc nghỉ đúng chỗ
    text = _DOUBLE_STOP.sub(r"\1 ", text)
    return _SPACES.sub(" ", text).strip(" .")


# Chỉ chia ở dấu kết thúc câu: tách ở ":" sẽ làm nhãn "Công dụng:" lìa khỏi nội dung của nó
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_CLAUSE_END = re.compile(r"(?<=,)\s+")
_HARD_LIMIT_FACTOR = 2  # câu dài quá gấp đôi mức chia thì chia tiếp theo dấu phẩy rồi theo từ


def _split_long(piece: str, limit: int) -> list[str]:
    """Chia 1 câu quá dài: theo dấu phẩy trước, không được nữa thì theo từ."""
    out: list[str] = []
    current = ""
    for part in _CLAUSE_END.split(piece):
        for word in part.split(" "):
            if current and len(current) + 1 + len(word) > limit:
                out.append(current)
                current = word
            else:
                current = f"{current} {word}".strip()
    if current:
        out.append(current)
    return out


def split_for_synthesis(text: str, max_chars: int) -> list[str]:
    """Chia văn bản đã làm sạch thành các đoạn ngắn theo ranh giới câu để tạo giọng song song.

    Câu ngắn được gộp lại cho tới ~max_chars (để không tạo quá nhiều yêu cầu nhỏ).
    """
    sentences: list[str] = []
    for sentence in _SENTENCE_END.split(text):
        if len(sentence) > max_chars * _HARD_LIMIT_FACTOR:
            sentences.extend(_split_long(sentence, max_chars * _HARD_LIMIT_FACTOR))
        elif sentence:
            sentences.append(sentence)

    chunks: list[str] = []
    for sentence in sentences:
        if chunks and len(chunks[-1]) + 1 + len(sentence) <= max_chars:
            chunks[-1] = f"{chunks[-1]} {sentence}"
        else:
            chunks.append(sentence)
    return chunks
