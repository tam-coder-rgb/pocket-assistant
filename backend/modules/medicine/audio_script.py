"""Kịch bản giọng đọc cho thuốc.

QUAN TRỌNG: thứ tự và chữ phải khớp với clients/web/karaoke.js (prepareMedicineMain / prepareMedicineWarning),
vì karaoke chia thời gian theo đúng các từ này để tô sáng. Đổi ở đây thì phải đổi cả bên đó.
"""
from dataclasses import dataclass

from backend.modules.medicine.schemas import MedicineInfo

AI_PREFIX = (
    "Thông tin trên được tra cứu bằng AI, có thể sai sót, thông tin này chỉ mang tính chất tham khảo, "
    "mọi cân nhắc xin vui lòng liên hệ bác sĩ hoặc dược sĩ."
)
NO_INFO = "Chưa có thông tin"
_UNKNOWN_CHILD_MARKERS = ("chưa rõ", "chưa có thông tin", "không rõ")


@dataclass(frozen=True)
class Fallbacks:
    """Chữ mà web hiển thị thay thế khi 1 ô trống (app.js) — giọng đọc phải đọc đúng chữ đó."""

    indication: str
    timing: str
    adult: str
    child: str
    warning: str


DB_FALLBACKS = Fallbacks(
    indication="Theo chỉ định bác sĩ",
    timing="Uống theo chỉ định",
    adult=NO_INFO,
    child=NO_INFO,
    warning="Không có lưu ý đặc biệt",
)
AI_FALLBACKS = Fallbacks(
    indication="Điều trị theo hướng dẫn y tế",
    timing="Uống theo hướng dẫn",
    adult="Theo chỉ định bác sĩ",
    child="Cần hỏi ý kiến bác sĩ",
    warning="Tham khảo ý kiến bác sĩ trước khi dùng",
)

# Thông báo đọc khi không có thông tin thuốc để đọc
NOTICES = {
    "blurry": "Ảnh chụp thuốc bị mờ. Vui lòng giữ chắc tay và chụp lại ảnh rõ nét hơn.",
    "not_medicine": (
        "Hình ảnh này không phải là thuốc. Đây là tài liệu hoặc sách báo thông thường. "
        "Bấm nút bên dưới để chuyển sang tab Văn bản và nghe đọc."
    ),
    "not_in_db": (
        "Không có dữ liệu thuốc này, vui lòng nhờ người thân hỗ trợ hoặc nhờ tư vấn của "
        "chuyên gia y tế, bác sĩ hoặc dược sĩ."
    ),
    "toxic": (
        "Cảnh báo nguy hiểm! Đây có thể là hóa chất hoặc chất độc, không phải thuốc. "
        "Tuyệt đối không uống. Để xa tầm tay trẻ em."
    ),
}


def main_script(info: MedicineInfo, fb: Fallbacks, *, ai_disclaimer: bool) -> str:
    """Tên thuốc, công dụng, cách dùng, liều người lớn, liều trẻ em (bỏ ô không có nghĩa)."""
    indication = info.indication.strip() or fb.indication
    timing = info.meal_timing.strip() or fb.timing
    adult = info.dosage_adult.strip() or fb.adult
    child = info.dosage_child.strip() or fb.child

    parts: list[str] = []
    if ai_disclaimer:
        parts.append(AI_PREFIX)
    if info.name.strip():
        parts.append(f"Tên thuốc: {info.name.strip()}")
    parts.append(f"Công dụng: {indication}")
    if timing != NO_INFO and timing.lower() not in adult.lower():  # đã nằm trong liều người lớn thì không đọc lặp
        parts.append(f"Cách dùng: {timing}")
    parts.append(f"Liều dùng cho người lớn: {adult}")
    if not any(marker in child.lower() for marker in _UNKNOWN_CHILD_MARKERS):
        parts.append(f"Liều dùng cho trẻ em: {child}")
    return "\n".join(parts)


def warning_script(info: MedicineInfo, fb: Fallbacks) -> str:
    warning = info.warning.strip() or fb.warning
    name = f" {info.name.strip()}" if info.name.strip() else ""
    return f"Lưu ý quan trọng khi sử dụng thuốc{name}: {warning}"
