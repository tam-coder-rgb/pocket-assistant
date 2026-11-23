"""Hợp đồng chung của mọi engine giọng đọc (Adapter Pattern)."""
from abc import ABC, abstractmethod


class BaseTTSProvider(ABC):
    name: str

    @abstractmethod
    async def synthesize(self, text: str, voice: str) -> bytes:
        """Đọc `text` bằng giọng `voice`, trả về dữ liệu MP3. Lỗi/không có âm thanh -> ném Exception."""
