"""Chuyển luồng chữ thành sự kiện SSE đúng giao thức mà web (api_client.js) đang đọc.

Quy ước với web:  `data: <chữ>`  cho mỗi đoạn;  xuống dòng gửi dạng `\\n` (2 ký tự);
kết thúc bằng `data: [DONE]`.  Dùng chung cho chat và tóm tắt văn bản.
"""
import logging
from collections.abc import AsyncIterator

from fastapi.sse import ServerSentEvent

from backend.core.exceptions import MedAIError

logger = logging.getLogger(__name__)

DONE_MARKER = "[DONE]"
GENERIC_STREAM_ERROR = "Xin lỗi, có sự cố khi trả lời. Vui lòng thử lại."


def _event(text: str) -> ServerSentEvent:
    # raw_data: gửi nguyên chữ, không bọc JSON; xuống dòng thật sẽ phá khung SSE nên phải escape
    return ServerSentEvent(raw_data=text.replace("\n", "\\n"))


async def to_sse_events(tokens: AsyncIterator[str]) -> AsyncIterator[ServerSentEvent]:
    """Mỗi đoạn chữ -> 1 sự kiện. Lỗi giữa chừng được báo bằng chính câu trả lời rồi vẫn đóng luồng."""
    try:
        async for token in tokens:
            yield _event(token)
    except MedAIError as exc:
        yield _event(f"\n⚠️ {exc.detail}")
    except Exception:
        logger.exception("Lỗi khi stream")
        yield _event(f"\n⚠️ {GENERIC_STREAM_ERROR}")
    yield ServerSentEvent(raw_data=DONE_MARKER)
