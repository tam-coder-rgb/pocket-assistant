from pydantic import BaseModel


class MedicineInfo(BaseModel):
    """Thông tin 1 thuốc chuẩn (tên trường khớp những gì web đọc)."""

    name: str
    active_ingredient: str = ""
    indication: str = ""
    dosage_adult: str = ""
    dosage_child: str = ""
    meal_timing: str = ""
    warning: str = ""


class MedicineListResponse(BaseModel):
    """GET /list -> web đọc `data[].name` để dựng các nút gợi ý."""

    data: list[MedicineInfo]
    total: int


class MedicineTextRequest(BaseModel):
    text: str
    generate_audio: bool = False  # web gửi lên; giọng đọc sẽ làm ở tính năng TTS


class AudioRef(BaseModel):
    audio_url: str | None = None


class MedicineTextResponse(BaseModel):
    """POST /recognize-text -> web đọc found_in_db, medicine, audio.audio_url, warning_audio.audio_url."""

    found_in_db: bool
    is_toxic: bool = False  # tên gõ vào là hóa chất / chất độc (app desktop hiện cảnh báo đỏ, không mời AI)
    medicine: MedicineInfo | None = None
    audio: AudioRef | None = None
    warning_audio: AudioRef | None = None


class MedicineVLMResult(BaseModel):
    """Cấu trúc JSON mà VLM bắt buộc trả về khi nhìn ảnh thuốc."""

    is_medicine: bool
    is_toxic: bool = False  # hóa chất / thuốc trừ sâu / thuốc thú y...
    name: str = ""
    raw_text: str = ""


class MedicineScanResponse(MedicineInfo):
    """JSON trả về khi quét ảnh — khớp renderMedicineStep1() trong app.js."""

    name: str = ""
    status: str  # success | not_in_db | not_medicine | toxic | unreadable_image
    is_unreadable: bool = False
    is_medicine: bool = True
    is_toxic: bool = False
    found_in_db: bool = False
    raw_text: str = ""
    disclaimer: str = ""
    image_token: str | None = None  # mã để gọi "Phân tích bằng AI" (chỉ khi chưa có trong CSDL)
    audio_url: str | None = None
    warning_audio_url: str | None = None


class MedicineAIResult(BaseModel):
    """JSON mà AI trả về khi phân tích chuyên sâu (Bước 2)."""

    is_medicine: bool = True
    is_toxic: bool = False
    name: str  # bắt buộc: thiếu khóa này nghĩa là AI trả sai dạng -> thử provider khác
    active_ingredient: str = ""
    indication: str = ""
    dosage_adult: str = ""
    dosage_child: str = ""
    meal_timing: str = ""
    warning: str = ""
    expiry_date: str = ""
    unclear_info: str = ""
    raw_text: str = ""


class MedicineAIResponse(BaseModel):
    """Kết quả Bước 2 — khớp renderMedicineStep2AI() trong app.js."""

    status: str  # success | toxic | not_medicine
    is_toxic: bool = False
    safety_level: str = "SAFE"  # SAFE | LETHAL_TOXIC
    medicine: MedicineInfo
    expiry_date: str = ""
    unclear_info: str = ""
    raw_text: str = ""
    disclaimer: str = ""
    audio_url: str | None = None
    warning_audio_url: str | None = None
