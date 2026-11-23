"""Giữ dữ liệu đọc từ kho (Supabase: mỗi lần đọc ~0,5 s) luôn mới mà không bắt người dùng chờ.

Lần đầu: chờ đọc. Quá `max_age` giây: trả bản đang có NGAY và đọc lại ở luồng nền (lỗi thì giữ bản cũ, lần sau thử lại).
max_age <= 0: luôn đọc lại ngay (test). Thao tác ghi không dựa vào đây: luôn đọc bản mới nhất trước khi sửa.
"""
import logging
import threading
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


class Refresher:
    def __init__(self, max_age: float, reload: Callable[[], object]) -> None:
        self._max_age = max_age
        self._reload = reload
        self._loaded_at: float | None = None
        self._running = threading.Lock()  # chỉ 1 luồng nền đọc lại mỗi lúc

    def ensure(self) -> None:
        """Gọi trước mỗi lần đọc dữ liệu đã đệm."""
        if self._loaded_at is None or self._max_age <= 0:
            self._reload()
            self.mark_fresh()
        elif time.monotonic() - self._loaded_at >= self._max_age and self._running.acquire(blocking=False):
            threading.Thread(target=self._background, daemon=True).start()

    def mark_fresh(self) -> None:
        self._loaded_at = time.monotonic()

    def reset(self) -> None:
        """Lần đọc sau phải chờ đọc lại (sau khi chính server này vừa ghi)."""
        self._loaded_at = None

    def _background(self) -> None:
        try:
            self._reload()
            self.mark_fresh()
        except Exception as exc:  # noqa: BLE001 - luồng nền không được chết; giữ bản cũ
            logger.warning("Đọc lại dữ liệu từ kho thất bại, tạm dùng bản cũ: %s", exc)
        finally:
            self._running.release()
