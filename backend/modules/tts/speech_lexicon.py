"""Bảng tra để đọc mã/viết tắt/đơn vị bằng tiếng Việt. Thêm đơn vị hay đổi cách đọc chữ cái: sửa ở đây."""

LETTER_NAMES = {
    "A": "a", "B": "bê", "C": "xê", "D": "đê", "E": "e", "F": "ép", "G": "giê", "H": "hát",
    "I": "i", "J": "chây", "K": "ca", "L": "eo", "M": "em", "N": "en", "O": "o", "P": "pê",
    "Q": "cu", "R": "e rờ", "S": "ét", "T": "tê", "U": "u", "V": "vê", "W": "vê kép",
    "X": "ích", "Y": "i dài", "Z": "dét",
}

DIGIT_NAMES = {
    "0": "không", "1": "một", "2": "hai", "3": "ba", "4": "bốn",
    "5": "năm", "6": "sáu", "7": "bảy", "8": "tám", "9": "chín",
}

# Khóa viết thường. Không có "g" riêng lẻ vì quá dễ nhầm với chữ khác.
UNIT_NAMES = {
    "mg": "mi li gam", "mcg": "mi crô gam", "ml": "mi li lít", "kg": "ki lô gam",
    "cm": "xen ti mét", "mm": "mi li mét", "kcal": "ki lô ca lo",
}

# Viết tắt công nghệ quen đọc theo tên chữ cái tiếng Anh. Khóa viết hoa. Không có trong bảng -> đọc theo LETTER_NAMES.
ACRONYM_NAMES = {
    "AI": "ây ai", "API": "ây pi ai", "URL": "diu a eo", "USB": "diu ét bi", "WIFI": "oai phai",
}

# Đơn vị chỉ được hiểu là đơn vị khi đứng NGAY SAU một con số (vd. "4g", "8h"). Khóa viết thường.
NUMBER_UNIT_NAMES = {"g": "gam", "l": "lít", "h": "giờ", "iu": "đơn vị", "ui": "đơn vị", "µg": "mi crô gam"}

# Dấu "/" đứng trước các từ này (có thể kèm số, vd. "mg/5ml") được đọc là "mỗi". Còn lại đọc là "hoặc".
PER_WORDS = (
    "lần", "ngày", "giờ", "tuần", "tháng", "năm", "phút", "đêm", "bữa", "liều", "viên", "gói", "ống",
    "kg", "ml", "l", "m2", "m²",
)

# So sánh đứng trước con số (vd. "trẻ < 12 tuổi"). Dấu 2 ký tự phải đứng trước dấu 1 ký tự.
COMPARISON_NAMES = (
    ("<=", "không quá"), ("≤", "không quá"), (">=", "từ"), ("≥", "từ"),
    ("<", "dưới"), (">", "trên"), ("~", "khoảng"), ("≈", "khoảng"),
)

URL_SPOKEN = "đường dẫn"
EMAIL_SPOKEN = "địa chỉ thư điện tử"
