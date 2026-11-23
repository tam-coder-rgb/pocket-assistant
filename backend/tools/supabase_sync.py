"""Chép dữ liệu giữa thư mục data/ và Supabase Storage (đọc SUPABASE_* trong .env).

  python -m backend.tools.supabase_sync push              data/ -> Supabase (tự tạo bucket; bỏ qua file đã có)
  python -m backend.tools.supabase_sync push --overwrite  ghi đè cả file đã có trên Supabase
  python -m backend.tools.supabase_sync pull <thư-mục>     Supabase -> thư mục sao lưu (bỏ qua file đã có)

Mặc định KHÔNG ghi đè: dữ liệu bác sĩ đã sửa trên Supabase không bị bản cũ trong data/ đè mất.
"""
import argparse
from pathlib import Path, PurePosixPath

from backend.core import storage
from backend.core.config import settings
from backend.core.storage import BlobStore, LocalBlobStore, SupabaseBlobStore

FOLDERS = (str(PurePosixPath(settings.MEDIC_DATA_KEY).parent), settings.VOICE_DATA_PREFIX)
SKIP_SUFFIXES = (".db", ".tmp")  # medicines.db không còn dùng


def copy_all(source: BlobStore, target: BlobStore, overwrite: bool) -> tuple[int, int]:
    """Chép mọi file trong FOLDERS. Trả về (số file đã chép, số file bỏ qua vì đã có)."""
    copied = skipped = 0
    for folder in FOLDERS:
        existing = set() if overwrite else target.list(folder)
        for name in sorted(source.list(folder)):
            if name.endswith(SKIP_SUFFIXES):
                continue
            if name in existing:
                skipped += 1
                continue
            data = source.read(f"{folder}/{name}")
            if data is not None:
                target.write(f"{folder}/{name}", data)
                copied += 1
                print(f"  {folder}/{name} ({len(data) // 1024} KB)")
    return copied, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["push", "pull"])
    parser.add_argument("folder", nargs="?", help="thư mục đích khi pull")
    parser.add_argument("--overwrite", action="store_true", help="ghi đè file đã có ở nơi nhận")
    args = parser.parse_args()

    remote = storage.create("supabase")
    assert isinstance(remote, SupabaseBlobStore)
    if args.action == "push":
        if remote.ensure_bucket():
            print(f"Đã tạo bucket riêng tư {settings.SUPABASE_BUCKET!r}")
        copied, skipped = copy_all(LocalBlobStore(settings.DATA_DIR), remote, args.overwrite)
    else:
        if not args.folder:
            parser.error("pull cần thư mục đích, vd: pull backup/data_2026-11-23")
        copied, skipped = copy_all(remote, LocalBlobStore(Path(args.folder)), args.overwrite)
    print(f"Xong: chép {copied} file, bỏ qua {skipped} file đã có.")


if __name__ == "__main__":
    main()
