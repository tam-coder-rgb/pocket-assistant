"""Stream hội thoại có dự phòng: thử lần lượt các provider cho tới khi có chữ đầu tiên.

QUY TẮC QUAN TRỌNG: chỉ được chuyển provider khi CHƯA gửi chữ nào cho người dùng.
Đã gửi rồi mà đứt giữa chừng thì báo lỗi, vì chuyển sang provider khác sẽ bắt đầu lại từ đầu
và người dùng sẽ thấy câu trả lời bị lặp/lộn xộn.
"""
import asyncio
import logging
from collections.abc import AsyncIterator, Sequence
from contextlib import aclosing

from backend.core.ai.base import BaseAIProvider, ChatMessage, unavailable_error

logger = logging.getLogger(__name__)


async def stream_with_fallback(
    providers: Sequence[BaseAIProvider],
    messages: Sequence[ChatMessage],
    system_prompt: str,
    first_token_timeout: float,
    last_provider_timeout: float | None = None,
) -> AsyncIterator[str]:
    """first_token_timeout: chờ chữ đầu tối đa bao lâu trước khi chuyển sang provider kế tiếp.
    last_provider_timeout: mức chờ cho provider CUỐI (không còn ai để chuyển sang, cắt sớm chỉ gây lỗi);
    None = dùng first_token_timeout.
    """
    errors: dict[str, BaseException] = {}
    for index, provider in enumerate(providers):
        is_last = index == len(providers) - 1
        timeout = last_provider_timeout if is_last and last_provider_timeout else first_token_timeout
        started = False
        try:
            async with aclosing(provider.stream_chat(messages, system_prompt)) as stream:
                tokens = stream.__aiter__()
                try:
                    async with asyncio.timeout(timeout):
                        first = await anext(tokens)
                except StopAsyncIteration as exc:
                    raise ValueError("AI trả lời rỗng") from exc
                started = True
                yield first
                async for token in tokens:
                    yield token
            return
        except Exception as exc:
            if started:
                raise
            # Ghi cả tên lỗi: TimeoutError không có nội dung chữ, log từng để trống gây đoán sai nguyên nhân
            logger.warning("Provider %s lỗi khi stream (%s): %s", provider.name, type(exc).__name__, exc)
            errors[provider.name] = exc
    raise unavailable_error(errors)
