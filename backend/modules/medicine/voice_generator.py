"""Tạo giọng đọc thu sẵn (mp3) cho 1 thuốc khi bác sĩ thêm / sửa thuốc.

Đọc đúng kịch bản mà tra cứu dùng (audio_script.py, chữ thay thế của CSDL chuẩn) bằng engine TTS của dự án,
rồi lưu vào thư viện giọng (voice_library.py). Lỗi TTS không làm hỏng việc lưu thuốc: trả về False,
khi tra cứu backend vẫn tự đọc bằng TTS.
"""
import asyncio
import logging

from backend.core.exceptions import MedAIError
from backend.modules.medicine import audio_script as script
from backend.modules.medicine import voice_library
from backend.modules.medicine.catalog import MedicineRecord
from backend.modules.medicine.schemas import MedicineInfo
from backend.modules.tts.service import tts_service

logger = logging.getLogger(__name__)


def _scripts(record: MedicineRecord) -> dict[str, str]:
    info = MedicineInfo(
        name=record.name, active_ingredient=record.active_ingredient, indication=record.indication,
        dosage_adult=record.dosage_adult, dosage_child=record.dosage_child, meal_timing=record.meal_timing,
        warning=record.warning,
    )
    return {
        "main": script.main_script(info, script.DB_FALLBACKS, ai_disclaimer=False),
        "warning": script.warning_script(info, script.DB_FALLBACKS),
    }


async def generate(record: MedicineRecord) -> bool:
    """Tạo + lưu mp3 phần chính và phần lưu ý. True nếu thành công."""
    try:
        audio = {}
        for part, text in _scripts(record).items():
            path = await tts_service.audio_for_text(text)
            audio[part] = await asyncio.to_thread(path.read_bytes)
        await asyncio.to_thread(voice_library.current().register, record, audio)
        return True
    except (MedAIError, OSError) as exc:
        logger.warning("Không tạo được giọng đọc cho %s: %s", record.name, exc)
        return False
