"""Chuẩn hóa chữ để so khớp: bỏ dấu tiếng Việt, đ -> d, viết thường."""
import unicodedata


def fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
