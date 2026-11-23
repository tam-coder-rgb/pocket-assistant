"""Rào chắn an toàn dùng chung (medicine, chat...): chặn hóa chất / thuốc trừ sâu / thuốc thú y, kể cả khi AI bỏ sót."""
import re

from backend.core.text_fold import fold

HAZARD_KEYWORDS = (
    "thuốc trừ sâu", "thuốc diệt chuột", "bả chuột", "thuốc diệt cỏ", "thuốc diệt gián",
    "thuốc chuột", "thuốc sâu", "thuốc cỏ", "thuốc độc", "thuốc diệt muỗi", "thuốc diệt kiến",
    "thuốc diệt mối", "thuốc diệt côn trùng", "thuốc diệt ruồi", "thuốc xịt muỗi",
    "paraquat", "glyphosate", "xyanua", "cyanide", "thạch tín", "arsenic", "thủy ngân",
    "nước tẩy", "javel", "xút", "thuốc thú y", "veterinary", "animal use only",
)
# Cụm hợp lệ có chứa từ nguy hiểm -> loại trừ trước khi dò
SAFE_PHRASES = ("thuốc tẩy giun",)

# So khớp không phân biệt dấu ("thuoc chuot" cũng bị chặn) và theo ranh giới từ
_pattern = re.compile(
    r"(?<![a-z0-9])(?:" + "|".join(re.escape(fold(k)) for k in HAZARD_KEYWORDS) + r")(?![a-z0-9])"
)
_safe_folded = tuple(fold(p) for p in SAFE_PHRASES)


def is_hazardous(text: str) -> bool:
    cleaned = fold(text)
    for phrase in _safe_folded:
        cleaned = cleaned.replace(phrase, " ")
    return bool(_pattern.search(cleaned))


# Hiển thị thay cho liều dùng khi phát hiện chất nguy hiểm (không bao giờ đưa hướng dẫn uống)
TOXIC_REFUSAL = "KHÔNG ĐƯỢC UỐNG HOẶC SỬ DỤNG"
TOXIC_WARNING = (
    "Đây không phải thuốc dùng cho người mà là hóa chất hoặc chất độc. "
    "Không uống, không bôi. Để xa tầm tay trẻ em. Nếu đã tiếp xúc, hãy gọi cấp cứu 115 ngay."
)
