"""Vòng khóa API: luôn thử từ khóa đang dùng; khóa đó lỗi -> khóa kế tiếp thành khóa đang dùng.

Ví dụ 2 khóa [A, B]: A hết hạn mức -> chuyển sang B và các lần sau bắt đầu từ B (không tốn 1 lần gọi
vào A mỗi câu). B cũng hết -> quay lại A (có thể A đã được cấp lại hạn mức). Nhờ vậy dùng xoay vòng
qua lại giữa các khóa miễn phí.
"""
from collections.abc import Sequence
from typing import Generic, TypeVar

T = TypeVar("T")


class KeyRing(Generic[T]):
    def __init__(self, items: Sequence[T]):
        if not items:
            raise ValueError("Cần ít nhất 1 khóa")
        self._items = list(items)
        self._active = 0

    def __len__(self) -> int:
        return len(self._items)

    def in_order(self) -> list[tuple[int, T]]:
        """Mọi khóa kèm vị trí, bắt đầu từ khóa đang dùng."""
        count = len(self._items)
        return [((self._active + i) % count, self._items[(self._active + i) % count]) for i in range(count)]

    def mark_failed(self, index: int) -> None:
        # Chỉ chuyển nếu khóa lỗi vẫn là khóa đang dùng: nhiều câu chạy song song cùng lỗi trên 1 khóa
        # thì chỉ chuyển 1 bước, không nhảy lố qua khóa còn tốt.
        if index == self._active:
            self._active = (index + 1) % len(self._items)
