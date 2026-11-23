"""Giao diện chung của KHO FILE DỮ LIỆU (danh mục thuốc JSON + mp3 thu sẵn).

Khóa file là đường dẫn tương đối giống cấu trúc thư mục data/ ("medic_data/medicines.json",
"voice_data/med_7778_main.mp3"), nên kho trên máy và kho Supabase chứa y hệt nhau.
"""
import mimetypes
from pathlib import Path
from typing import Protocol


class BlobStore(Protocol):
    name: str  # "local" | "supabase" (hiện trong thông báo lỗi)

    def read(self, key: str) -> bytes | None:
        """Nội dung file, None nếu không có."""

    def write(self, key: str, data: bytes) -> None:
        """Tạo mới hoặc ghi đè."""

    def delete(self, key: str) -> None:
        """Xóa file; không có thì thôi."""

    def list(self, prefix: str) -> set[str]:
        """Tên các file (không kèm `prefix/`) nằm ngay trong thư mục `prefix`."""

    def local_file(self, key: str) -> Path | None:
        """File trên máy chạy server để phát bằng FileResponse (hỗ trợ Range); None nếu không có."""


def content_type(key: str) -> str:
    return mimetypes.guess_type(key)[0] or "application/octet-stream"
