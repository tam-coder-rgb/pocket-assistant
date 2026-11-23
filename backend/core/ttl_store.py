"""Kho tạm trong RAM: giữ giá trị theo khóa, tự hết hạn và giới hạn số lượng (xóa cái cũ nhất)."""
import time
from collections import OrderedDict
from typing import Generic, TypeVar

V = TypeVar("V")


class TTLStore(Generic[V]):
    def __init__(self, ttl_seconds: float, max_items: int):
        self._ttl = ttl_seconds
        self._max_items = max_items
        self._items: OrderedDict[str, tuple[float, V]] = OrderedDict()

    def put(self, key: str, value: V) -> None:
        self._items[key] = (time.monotonic() + self._ttl, value)
        self._items.move_to_end(key)
        while len(self._items) > self._max_items:
            self._items.popitem(last=False)

    def get(self, key: str) -> V | None:
        """Trả giá trị nếu còn hạn, ngược lại None."""
        item = self._items.get(key)
        if item is None:
            return None
        expires_at, value = item
        if time.monotonic() > expires_at:
            del self._items[key]
            return None
        return value
