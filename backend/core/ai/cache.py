"""Bộ nhớ đệm LRU trong RAM: quét lại cùng một ảnh thì trả kết quả tức thì, không gọi AI."""
import hashlib
from collections import OrderedDict
from typing import Any


def make_key(image: bytes, prompt: str) -> str:
    return hashlib.sha256(image + b"\0" + prompt.encode()).hexdigest()


class LRUCache:
    def __init__(self, max_size: int):
        self._max_size = max_size
        self._data: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Any | None:
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: str, value: Any) -> None:
        if self._max_size <= 0:
            return
        self._data[key] = value
        self._data.move_to_end(key)
        while len(self._data) > self._max_size:
            self._data.popitem(last=False)
