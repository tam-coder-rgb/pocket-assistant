"""Bảo đảm mỗi dòng tóm tắt bắt đầu bằng "• " (AI đôi khi quên), chạy được trên luồng stream."""
from collections.abc import AsyncIterator

BULLET = "• "
_BULLET_CHARS = "•-*"


async def ensure_line_bullets(tokens: AsyncIterator[str]) -> AsyncIterator[str]:
    at_line_start = True  # chưa gặp ký tự có nghĩa nào trên dòng hiện tại
    async for token in tokens:
        out: list[str] = []
        for ch in token:
            if ch == "\n":
                at_line_start = True
            elif at_line_start and not ch.isspace():
                at_line_start = False
                if ch in _BULLET_CHARS:
                    out.append(BULLET.strip())  # "-" / "*" -> "•"
                    continue
                out.append(BULLET)
            out.append(ch)
        yield "".join(out)
