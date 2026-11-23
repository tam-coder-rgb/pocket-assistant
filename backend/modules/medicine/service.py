"""Nghiệp vụ thuốc: tra cứu CSDL chuẩn (theo tên) và nhận diện từ ảnh.

Tra cứu tên:  tên -> safety -> CSDL chuẩn (RapidFuzz) -> kết quả (+ âm thanh)
Quét ảnh:     ảnh -> vision (mờ?) -> VLM (đọc tên) -> safety -> tra cứu tên (+ âm thanh)
"""
from backend.core import safety
from backend.core.ai import ai_client
from backend.core.config import settings
from backend.modules.medicine import audio, prompts, repository
from backend.modules.medicine.catalog import MedicineRecord
from backend.modules.medicine.image_store import image_store
from backend.modules.medicine.schemas import (
    AudioRef,
    MedicineInfo,
    MedicineListResponse,
    MedicineScanResponse,
    MedicineTextResponse,
    MedicineVLMResult,
)
from backend.modules.vision.service import prepare_image


def _to_info(med: MedicineRecord) -> MedicineInfo:
    """Thuốc trong kho -> schema trả cho client (bỏ tên gọi khác)."""
    return MedicineInfo(
        name=med.name,
        active_ingredient=med.active_ingredient,
        indication=med.indication,
        dosage_adult=med.dosage_adult,
        dosage_child=med.dosage_child,
        meal_timing=med.meal_timing,
        warning=med.warning,
    )


# ---------- Tra cứu theo tên (không cần ảnh) ----------
async def list_medicines(query: str = "") -> MedicineListResponse:
    items = [_to_info(m) for m in await repository.list_medicines(query)]
    return MedicineListResponse(data=items, total=len(items))


async def lookup_by_text(text: str) -> MedicineTextResponse:
    if safety.is_hazardous(text):
        return MedicineTextResponse(
            found_in_db=False, is_toxic=True, audio=AudioRef(audio_url=audio.notice("toxic"))
        )

    med = await repository.find_medicine(text)
    if med is None:
        return MedicineTextResponse(found_in_db=False, audio=AudioRef(audio_url=audio.notice("not_in_db")))

    info = _to_info(med)
    sound = await audio.for_database_medicine(info)
    return MedicineTextResponse(
        found_in_db=True,
        medicine=info,
        audio=AudioRef(audio_url=sound.main),
        warning_audio=AudioRef(audio_url=sound.warning),
    )


# ---------- Quét từ ảnh ----------
async def scan_medicine_image(raw: bytes) -> MedicineScanResponse:
    image = await prepare_image(raw)
    if image.is_blurry:
        return MedicineScanResponse(
            status="unreadable_image", is_unreadable=True, audio_url=audio.notice("blurry")
        )

    vlm = await ai_client.analyze(prompts.SCAN_IMAGE, MedicineVLMResult, image_jpeg=image.jpeg_bytes)

    if vlm.is_toxic or safety.is_hazardous(f"{vlm.name} {vlm.raw_text}"):
        return MedicineScanResponse(
            status="toxic", is_toxic=True, is_medicine=False,
            name=vlm.name, raw_text=vlm.raw_text, audio_url=audio.notice("toxic"),
        )
    if not vlm.is_medicine:
        return MedicineScanResponse(
            status="not_medicine", is_medicine=False, raw_text=vlm.raw_text,
            audio_url=audio.notice("not_medicine"),
        )

    found = await lookup_by_text(vlm.name)
    if found.found_in_db and found.medicine:
        return MedicineScanResponse(
            **found.medicine.model_dump(),
            status="success", found_in_db=True, raw_text=vlm.raw_text,
            audio_url=found.audio.audio_url if found.audio else None,
            warning_audio_url=found.warning_audio.audio_url if found.warning_audio else None,
        )
    return MedicineScanResponse(
        status="not_in_db", name=vlm.name, raw_text=vlm.raw_text,
        disclaimer=settings.DISCLAIMER_AI,
        image_token=image_store.put(image.jpeg_bytes),
        audio_url=audio.notice("not_in_db"),
    )
