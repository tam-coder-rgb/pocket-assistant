"""Bảo đảm mỗi dòng tóm tắt kết thúc bằng dấu câu để giọng đọc ngắt nghỉ đúng chỗ.

Web gộp các dòng thành một đoạn trước khi đọc, nên dòng thiếu dấu câu sẽ bị đọc liền sang dòng sau.
"""
from collections.abc import AsyncIterator

_END_MARKS = ".!?:;…"
_BULLET_ONLY = "•-* \t"


async def ensure_line_punctuation(tokens: AsyncIterator[str]) -> AsyncIterator[str]:
    last = ""  # ký tự có nghĩa cuối cùng của dòng đang viết
    async for token in tokens:
        out: list[str] = []
        for ch in token:
            if ch == "\n":
                if last and last not in _END_MARKS:
                    out.append(".")
                last = ""
            elif not ch.isspace() and ch not in _BULLET_ONLY:
                last = ch
            out.append(ch)
        yield "".join(out)
    if last and last not in _END_MARKS:
        yield "."
