"""Bước 2 — "Phân tích bằng AI" cho thuốc chưa có trong CSDL chuẩn.

Hai nguồn đầu vào:  token ảnh (đã quét ở Bước 1)  |  tên thuốc gõ tay.
Luôn qua safety; hàng nguy hiểm tuyệt đối không được trả liều dùng; kết quả luôn kèm DISCLAIMER_AI.
"""
from backend.core import safety
from backend.core.ai import ai_client
from backend.core.config import settings
from backend.core.exceptions import ExpiredTokenError, InvalidRequestError
from backend.modules.medicine import audio, prompts
from backend.modules.medicine.image_store import image_store
from backend.modules.medicine.schemas import (
    MedicineAIResponse,
    MedicineAIResult,
    MedicineInfo,
)


def _toxic_response(name: str, raw_text: str = "") -> MedicineAIResponse:
    """Phản hồi cảnh báo đỏ: không liều dùng, không công dụng."""
    info = MedicineInfo(
        name=name or "Chất nguy hiểm",
        indication="Không phải thuốc",
        dosage_adult=safety.TOXIC_REFUSAL,
        dosage_child=safety.TOXIC_REFUSAL,
        meal_timing="Không sử dụng",
        warning=safety.TOXIC_WARNING,
    )
    sound = audio.for_toxic_medicine(info)
    return MedicineAIResponse(
        status="toxic",
        is_toxic=True,
        safety_level="LETHAL_TOXIC",
        medicine=info,
        raw_text=raw_text,
        audio_url=sound.main,
        warning_audio_url=sound.warning,
    )


def _to_response(result: MedicineAIResult) -> MedicineAIResponse:
    # Disclaimer đi cùng `warning` vì đó là ô web luôn hiển thị
    warning = f"{result.warning}\n\n⚠️ {settings.DISCLAIMER_AI}".strip()
    info = MedicineInfo(
        name=result.name,
        active_ingredient=result.active_ingredient,
        indication=result.indication,
        dosage_adult=result.dosage_adult,
        dosage_child=result.dosage_child,
        meal_timing=result.meal_timing,
        warning=warning,
    )
    sound = audio.for_ai_medicine(info)
    return MedicineAIResponse(
        status="success" if result.is_medicine else "not_medicine",
        medicine=info,
        expiry_date=result.expiry_date,
        unclear_info=result.unclear_info,
        raw_text=result.raw_text,
        disclaimer=settings.DISCLAIMER_AI,
        audio_url=sound.main,
        warning_audio_url=sound.warning,
    )


async def analyze(token: str | None, text: str | None) -> MedicineAIResponse:
    if bool(token) == bool(text):
        raise InvalidRequestError("Cần truyền đúng một trong hai: token ảnh hoặc tên thuốc.")

    if token:
        jpeg = image_store.get(token)
        if jpeg is None:
            raise ExpiredTokenError("Ảnh đã hết hạn lưu. Vui lòng chụp lại ảnh thuốc.")
        result = await ai_client.analyze(prompts.ANALYZE_IMAGE, MedicineAIResult, image_jpeg=jpeg)
    else:
        name = text.strip()
        if safety.is_hazardous(name):
            return _toxic_response(name)
        result = await ai_client.analyze(
            prompts.ANALYZE_TEXT.format(name=name), MedicineAIResult
        )

    if result.is_toxic or safety.is_hazardous(f"{result.name} {result.raw_text}"):
        return _toxic_response(result.name, result.raw_text)
    return _to_response(result)
