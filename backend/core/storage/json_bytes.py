"""Đọc / ghi file JSON dạng bytes, giữ đúng định dạng file gốc (thụt 2, tiếng Việt có dấu, kiểu xuống dòng cũ)
để ghi lại không đổi gì thì giống từng byte và Git chỉ thấy đúng chỗ đã sửa."""
import json


def loads(raw: bytes) -> object:
    return json.loads(raw.decode("utf-8-sig"))


def dumps(data: object, like: bytes | None = None) -> bytes:
    """`like` = nội dung cũ của file: dùng lại kiểu xuống dòng của nó (CRLF / LF)."""
    newline = "\r\n" if like and b"\r\n" in like else "\n"
    return json.dumps(data, ensure_ascii=False, indent=2).replace("\n", newline).encode("utf-8")
