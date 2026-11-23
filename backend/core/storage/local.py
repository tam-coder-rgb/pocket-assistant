"""Kho file là 1 thư mục trên máy chạy server (mặc định: data/)."""
import os
from pathlib import Path


class LocalBlobStore:
    name = "local"

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def read(self, key: str) -> bytes | None:
        path = self._path(key)
        return path.read_bytes() if path.is_file() else None

    def write(self, key: str, data: bytes) -> None:
        """Ghi file tạm rồi thay: tắt máy giữa chừng cũng không hỏng file cũ."""
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.name}.tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def list(self, prefix: str) -> set[str]:
        folder = self._path(prefix)
        return {p.name for p in folder.iterdir() if p.is_file()} if folder.is_dir() else set()

    def local_file(self, key: str) -> Path | None:
        path = self._path(key)
        return path if path.is_file() else None

    def _path(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if not path.is_relative_to(self._root):  # chặn "../" thoát ra ngoài thư mục kho
            raise ValueError(f"Khóa file không hợp lệ: {key!r}")
        return path
