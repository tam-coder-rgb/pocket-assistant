"""Lời nhắc của chatbot thuốc — muốn đổi giọng điệu/quy tắc trả lời chỉ cần sửa file này."""
from backend.core.config import settings
from backend.modules.chat.schemas import MedicineContext

SYSTEM_PROMPT = (
    "Bạn là trợ lý y tế thân thiện của MedAI, hỗ trợ người cao tuổi và người chăm sóc. "
    "Chỉ trả lời câu hỏi liên quan đến thuốc đang xem ở phần 'Thông tin thuốc' bên dưới "
    "(và sức khỏe liên quan trực tiếp); câu hỏi không liên quan thì từ chối lịch sự. "
    "Trả lời bằng tiếng Việt, tối đa 5 câu ngắn, từ ngữ đơn giản, không dùng ký hiệu markdown. "
    "Tuyệt đối không đưa đường link, tên website hay số điện thoại (trừ số cấp cứu 115). "
    "Ưu tiên thông tin trong phần 'Thông tin thuốc'; nếu không chắc chắn hãy nói rõ và khuyên hỏi "
    "bác sĩ hoặc dược sĩ. Không chẩn đoán bệnh, không kê đơn, không tự đổi liều. "
    "Nếu có dấu hiệu nguy hiểm (khó thở, phát ban nặng, quá liều, uống nhầm hóa chất) "
    "hãy bảo gọi cấp cứu 115 ngay."
)

# (trường trong MedicineContext, nhãn hiển thị cho AI)
_CONTEXT_FIELDS = (
    ("medicine_name", "Tên thuốc"),
    ("active_ingredient", "Hoạt chất"),
    ("indication", "Công dụng"),
    ("dosage_adult", "Liều người lớn"),
    ("dosage_child", "Liều trẻ em"),
    ("timing", "Thời điểm uống"),
    ("warnings", "Lưu ý"),
)


def _source_note(context: MedicineContext) -> str:
    if context.source == "DB":
        return "Nguồn: cơ sở dữ liệu thuốc đã kiểm định."
    return "Nguồn: do AI tra cứu, chỉ mang tính tham khảo."


def build_system_prompt(context: MedicineContext) -> str:
    limit = settings.CHAT_MAX_CONTEXT_CHARS
    lines = [
        f"- {label}: {value[:limit]}"
        for field, label in _CONTEXT_FIELDS
        if (value := getattr(context, field).strip())
    ]
    info = "\n".join(lines) if lines else "- (chưa có thông tin thuốc)"
    return f"{SYSTEM_PROMPT}\n\nThông tin thuốc:\n{info}\n{_source_note(context)}"
