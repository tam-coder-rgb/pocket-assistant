"""Kho file là 1 bucket Supabase Storage (REST qua httpx): mọi máy chạy backend dùng chung 1 bộ dữ liệu.

Bucket để RIÊNG TƯ, chỉ backend giữ khóa bí mật. mp3 được tải về thư mục đệm trên máy ở lần phát đầu
(FileResponse hỗ trợ Range cho trình duyệt tua); mã giọng không bao giờ dùng lại nên file đệm không bị cũ.
"""
from pathlib import Path
from urllib.parse import quote

import httpx

from backend.core.exceptions import StorageUnavailableError
from backend.core.storage.base import content_type
from backend.core.storage.local import LocalBlobStore

_PAGE = 1000  # số file mỗi lần liệt kê


class SupabaseBlobStore:
    name = "supabase"

    def __init__(self, url: str, key: str, bucket: str, cache_dir: Path, timeout: float,
                 transport: httpx.BaseTransport | None = None) -> None:
        if not url or not key:
            raise ValueError("DATA_STORAGE=supabase cần SUPABASE_URL và SUPABASE_SECRET_KEY trong .env")
        headers = {"apikey": key}
        if key.startswith("eyJ"):  # khóa service_role cũ là JWT -> gửi thêm Authorization
            headers["Authorization"] = f"Bearer {key}"
        self._http = httpx.Client(base_url=f"{url.rstrip('/')}/storage/v1", headers=headers,
                                  timeout=timeout, transport=transport)
        self._bucket = bucket
        self._cache = LocalBlobStore(cache_dir / bucket)

    def read(self, key: str) -> bytes | None:
        res = self._request("GET", self._object(key))
        return None if res is None else res.content

    def write(self, key: str, data: bytes) -> None:
        headers = {"content-type": content_type(key), "x-upsert": "true", "cache-control": "no-cache"}
        self._request("POST", self._object(key), content=data, headers=headers)
        self._cache.delete(key)

    def delete(self, key: str) -> None:
        self._request("DELETE", f"/object/{self._bucket}", json={"prefixes": [key]})
        self._cache.delete(key)

    def list(self, prefix: str) -> set[str]:
        names: set[str] = set()
        offset = 0
        while True:
            body = {"prefix": prefix.strip("/"), "limit": _PAGE, "offset": offset}
            items = self._request("POST", f"/object/list/{self._bucket}", json=body).json()
            names.update(item["name"] for item in items if item.get("id"))  # thư mục con có id = null
            if len(items) < _PAGE:
                return names
            offset += _PAGE

    def local_file(self, key: str) -> Path | None:
        cached = self._cache.local_file(key)
        if cached is None and (data := self.read(key)) is not None:
            self._cache.write(key, data)
            cached = self._cache.local_file(key)
        return cached

    def ensure_bucket(self) -> bool:
        """Tạo bucket riêng tư nếu chưa có. True = vừa tạo."""
        res = self._http.post("/bucket", json={"id": self._bucket, "name": self._bucket, "public": False})
        if res.is_success:
            return True
        if "already exists" in res.text or "Duplicate" in res.text:
            return False
        raise StorageUnavailableError(f"Không tạo được bucket {self._bucket!r}: {res.status_code} {res.text[:200]}")

    # ---------- nội bộ ----------
    def _object(self, key: str) -> str:
        return f"/object/{self._bucket}/{quote(key)}"

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response | None:
        """Trả None khi file không tồn tại; lỗi mạng / khóa sai / thiếu bucket -> StorageUnavailableError."""
        try:
            res = self._http.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            raise StorageUnavailableError(f"Không kết nối được Supabase Storage: {exc}") from exc
        if _is_missing_object(res):
            return None
        if res.is_error:
            raise StorageUnavailableError(f"Supabase Storage lỗi {res.status_code}: {res.text[:200]}")
        return res


def _is_missing_object(res: httpx.Response) -> bool:
    """Supabase báo thiếu file bằng 404 hoặc 400 {"error": "not_found"}; thiếu BUCKET là lỗi cấu hình, không phải thiếu file."""
    text = res.text.lower()
    return res.status_code in (400, 404) and ("not_found" in text or "not found" in text) and "bucket" not in text
