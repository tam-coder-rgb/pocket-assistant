"""Giọng đọc THU SẴN của thuốc, nằm trong thư mục voice_data/ của kho file dữ liệu (core/storage):

  voice_index.json        {"next_id": 12950, "voices": {"<tên thuốc>": <mã giọng>}}
  med_<mã>_main.mp3       phần chính · med_<mã>_warning.mp3 phần lưu ý
  audio_hashes.json       {"<mã giọng>": "<md5 mp3 phần chính>"}

Thuốc không có file thu sẵn thì backend đọc bằng TTS lúc tra cứu. Bác sĩ thêm / sửa thuốc thì file mới được tạo
(voice_generator.py gọi register), xóa thuốc thì file bị xóa (remove). Mã giọng chỉ tăng, không dùng lại
(file mp3 đã đệm ở server khác không bao giờ bị nhầm sang thuốc khác).
"""
import copy
import hashlib
import threading
from collections.abc import Callable

from backend.core import storage
from backend.core.config import settings
from backend.core.storage import BlobStore, json_bytes
from backend.core.storage.refresh import Refresher
from backend.modules.medicine.catalog import MedicineRecord

STEM_FORMAT = "med_{voice_id}_{part}"  # tên file không đuôi, dùng cho /api/v1/speech/voice/<stem>
PARTS = ("main", "warning")
_INDEX_FILE = "voice_index.json"
_HASHES_FILE = "audio_hashes.json"
_EMPTY_INDEX = {"next_id": 1, "voices": {}}


class VoiceLibrary:
    def __init__(self, store: BlobStore, prefix: str, max_age: float) -> None:
        self._store = store
        self._prefix = prefix
        self._refresher = Refresher(max_age, self._load)
        self._lock = threading.Lock()
        self._ids: dict[str, int] = {}  # tên viết thường -> mã giọng
        self._files: set[str] = set()  # tên file đang có trong voice_data/

    def voice_id(self, name: str) -> int | None:
        """Mã file mp3 thu sẵn của thuốc, None nếu không có."""
        self._refresher.ensure()
        return self._ids.get(name.strip().lower())

    def recorded_stems(self, name: str) -> dict[str, str]:
        """{phần: tên file không đuôi} của các mp3 thu sẵn ĐANG CÓ (theo danh sách file đã đọc, không tải file)."""
        voice_id = self.voice_id(name)
        if voice_id is None:
            return {}
        stems = {part: STEM_FORMAT.format(voice_id=voice_id, part=part) for part in PARTS}
        return {part: stem for part, stem in stems.items() if f"{stem}.mp3" in self._files}

    def has_voice(self, name: str) -> bool:
        return bool(self.recorded_stems(name))

    def register(self, record: MedicineRecord, audio: dict[str, bytes]) -> int:
        """Lưu giọng đọc mới của thuốc (audio = {"main": mp3, "warning": mp3}); thay giọng cũ nếu có. Trả về mã giọng."""
        with self._lock:
            self._remove(record.name)
            index, raw = self._read_json(_INDEX_FILE, _EMPTY_INDEX)
            voice_id = index["next_id"]
            for part, data in audio.items():  # mp3 trước, mục lục sau: lỗi giữa chừng không để lại mã trỏ vào file thiếu
                self._store.write(self._key(self._file_name(voice_id, part)), data)
            index["next_id"] = voice_id + 1
            index["voices"][record.name] = voice_id
            self._write_json(_INDEX_FILE, index, raw)
            # File cũ không rõ cách băm; file mới ghi md5 của mp3 phần chính
            self._update_json(_HASHES_FILE, lambda h: h.__setitem__(str(voice_id), hashlib.md5(audio["main"]).hexdigest()))
            self._refresher.reset()
            return voice_id

    def remove(self, name: str) -> int:
        """Xóa hẳn giọng thu sẵn của thuốc (mp3, mã băm, dòng trong mục lục). Trả về số file mp3 đã xóa."""
        with self._lock:
            return self._remove(name)

    # ---------- nội bộ ----------
    def _remove(self, name: str) -> int:
        index, raw = self._read_json(_INDEX_FILE, _EMPTY_INDEX)
        wanted = name.strip().lower()
        names = [n for n in index["voices"] if n.strip().lower() == wanted]
        if not names:
            return 0
        voice_ids = {index["voices"].pop(n) for n in names}
        self._write_json(_INDEX_FILE, index, raw)  # mục lục trước: lỗi giữa chừng chỉ để lại file mồ côi, vô hại
        existing = self._store.list(self._prefix)
        removed = 0
        for file_name in (self._file_name(v, part) for v in voice_ids for part in PARTS):
            if file_name in existing:
                self._store.delete(self._key(file_name))
                removed += 1
        self._update_json(_HASHES_FILE, lambda h: [h.pop(str(v), None) for v in voice_ids])
        self._refresher.reset()
        return removed

    def _load(self) -> None:
        voices = self._read_json(_INDEX_FILE, _EMPTY_INDEX)[0]["voices"]
        ids = {name.strip().lower(): voice_id for name, voice_id in voices.items()}
        self._ids, self._files = ids, self._store.list(self._prefix)  # gán cùng lúc: luồng khác không thấy nửa cũ nửa mới

    def _key(self, file_name: str) -> str:
        return f"{self._prefix}/{file_name}"

    @staticmethod
    def _file_name(voice_id: int, part: str) -> str:
        return f"{STEM_FORMAT.format(voice_id=voice_id, part=part)}.mp3"

    def _read_json(self, file_name: str, default: dict) -> tuple[dict, bytes | None]:
        """(nội dung, bytes gốc để giữ kiểu xuống dòng khi ghi lại)."""
        raw = self._store.read(self._key(file_name))
        return (json_bytes.loads(raw) if raw else copy.deepcopy(default)), raw

    def _write_json(self, file_name: str, data: dict, like: bytes | None) -> None:
        self._store.write(self._key(file_name), json_bytes.dumps(data, like=like))

    def _update_json(self, file_name: str, change: Callable[[dict], object]) -> None:
        """change(data) sửa dict tại chỗ, rồi ghi lại file."""
        data, raw = self._read_json(file_name, {})
        change(data)
        self._write_json(file_name, data, raw)


_instance: VoiceLibrary | None = None


def current() -> VoiceLibrary:
    global _instance
    if _instance is None:
        _instance = VoiceLibrary(storage.current(), settings.VOICE_DATA_PREFIX, settings.DATA_CACHE_SECONDS)
    return _instance


def use(library: VoiceLibrary | None) -> None:
    """Thay thư viện giọng đang dùng (test dùng bản sao; None = tạo lại theo cấu hình)."""
    global _instance
    _instance = library
