"""Chạy nhiều tác vụ "dự phòng" và lấy kết quả thành công đầu tiên (hedged requests).

Tác vụ #1 chạy trước. Nếu nó lỗi, hoặc chưa xong sau `delay` giây, tác vụ kế tiếp được chạy
THÊM (không hủy tác vụ cũ). Kết quả thành công đầu tiên thắng, các tác vụ còn lại bị hủy.
=> Giảm độ trễ khi provider chính chậm đột biến mà không tốn gấp đôi chi phí mọi lần gọi.
"""
import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)

Job = tuple[str, Callable[[], Awaitable[T]]]  # (tên, hàm tạo coroutine)


class AllJobsFailedError(Exception):
    def __init__(self, errors: dict[str, BaseException]):
        super().__init__(str(errors))
        self.errors = errors


async def first_success(jobs: Sequence[Job[T]], delay: float) -> T:
    queue = list(jobs)
    running: dict[asyncio.Task[T], str] = {}
    errors: dict[str, BaseException] = {}

    def start_next() -> None:
        name, make = queue.pop(0)
        running[asyncio.ensure_future(make())] = name

    try:
        start_next()
        while running:
            done, _ = await asyncio.wait(
                running,
                timeout=delay if queue else None,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in done:
                name = running.pop(task)
                if task.exception() is None:
                    return task.result()
                logger.warning("Provider %s lỗi: %s", name, task.exception())
                errors[name] = task.exception()
            if queue and (not done or not running):  # quá hạn chờ, hoặc không còn gì đang chạy
                start_next()
        raise AllJobsFailedError(errors)
    finally:
        for task in running:
            task.cancel()
