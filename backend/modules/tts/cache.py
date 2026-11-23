"""Bộ nhớ đệm âm thanh trên đĩa (storage/temp/tts). Tên file = hash của (giọng + văn bản).

File cũng là thứ được phát ra cho trình duyệt (FileResponse hỗ trợ tua/Range), nên không giữ bản thứ hai trong RAM.
"""
import hashlib
import os
import time
from pathlib import Path


def make_key(text: str, voice: str) -> str:
    return hashlib.sha256(f"{voice}\0{text}".encode()).hexdigest()[:40]


class AudioCache:
    def __init__(self, directory: Path, ttl_seconds: int):
        self._dir = directory
        self._ttl = ttl_seconds

    def path_for(self, key: str) -> Path:
        return self._dir / f"{key}.mp3"

    def get(self, key: str) -> Path | None:
        path = self.path_for(key)
        return path if path.is_file() else None

    def put(self, key: str, audio: bytes) -> Path:
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self.path_for(key)
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_bytes(audio)
        os.replace(tmp, path)  # ghi nguyên tử: không bao giờ phát ra file dở dang
        return path

    def purge_expired(self) -> int:
        """Xóa file quá hạn. Trả về số file đã xóa."""
        if not self._dir.is_dir():
            return 0
        cutoff = time.time() - self._ttl
        removed = 0
        for file in self._dir.iterdir():
            if file.is_file() and file.stat().st_mtime < cutoff:
                file.unlink(missing_ok=True)
                removed += 1
        return removed
