"""Chọn nguồn âm thanh cho kết quả thuốc: mp3 tạo sẵn (thuốc trong CSDL) hoặc giọng đọc TTS.

Chỉ trả về URL; âm thanh thật chỉ được tạo khi trình duyệt tải URL (không làm chậm phản hồi).
"""
import asyncio
from dataclasses import dataclass

from backend.modules.medicine import audio_script as script
from backend.modules.medicine import voice_library
from backend.modules.medicine.schemas import MedicineInfo
from backend.modules.tts.service import tts_service


@dataclass(frozen=True)
class MedicineAudio:
    main: str | None = None
    warning: str | None = None


def _recorded(name: str) -> MedicineAudio:
    """URL mp3 thu sẵn của thuốc (ô None = không có). Có thể đọc mục lục từ kho -> gọi ở luồng phụ."""
    stems = voice_library.current().recorded_stems(name)
    return MedicineAudio(*(stems.get(part) and tts_service.url_for_voice_file(stems[part])
                           for part in voice_library.PARTS))


async def for_database_medicine(info: MedicineInfo) -> MedicineAudio:
    """Thuốc đã kiểm định: ưu tiên file mp3 thu sẵn, thiếu file mới dùng TTS."""
    recorded = await asyncio.to_thread(_recorded, info.name)
    main, warning = recorded.main, recorded.warning
    return MedicineAudio(
        main=main or tts_service.url_for_text(script.main_script(info, script.DB_FALLBACKS, ai_disclaimer=False)),
        warning=warning or tts_service.url_for_text(script.warning_script(info, script.DB_FALLBACKS)),
    )


def for_ai_medicine(info: MedicineInfo) -> MedicineAudio:
    """Thuốc do AI phân tích: đọc kèm câu khuyến cáo AI ở đầu (khớp karaoke)."""
    return MedicineAudio(
        main=tts_service.url_for_text(script.main_script(info, script.AI_FALLBACKS, ai_disclaimer=True)),
        warning=tts_service.url_for_text(script.warning_script(info, script.AI_FALLBACKS)),
    )


def for_toxic_medicine(info: MedicineInfo) -> MedicineAudio:
    """Cảnh báo chất nguy hiểm (không có câu khuyến cáo AI, vì giao diện hiện huy hiệu đỏ)."""
    return MedicineAudio(
        main=tts_service.url_for_text(script.main_script(info, script.AI_FALLBACKS, ai_disclaimer=False)),
        warning=tts_service.url_for_text(script.warning_script(info, script.AI_FALLBACKS)),
    )


def notice(kind: str) -> str | None:
    """Âm thanh cho thông báo (ảnh mờ, không phải thuốc, chưa có dữ liệu, chất độc)."""
    return tts_service.url_for_text(script.NOTICES[kind])
