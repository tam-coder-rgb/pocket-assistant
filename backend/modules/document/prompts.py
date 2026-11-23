"""Lời nhắc chép văn bản từ ảnh — muốn đổi cách AI chép/chấm câu chỉ cần sửa file này."""

SCAN_DOCUMENT = (
    "Chép lại CHÍNH XÁC văn bản trong ảnh: giữ nguyên từng chữ, tên riêng, tên thuốc, liều lượng, số liệu "
    "và chữ in hoa như trong ảnh. Không tóm tắt, không sửa chính tả, không thêm hay bớt chữ nào. "
    "Văn bản sẽ được đọc to và tô sáng theo TỪNG CÂU (ngắt ở dấu chấm), nên trình bày như sau: "
    "1) Nối các dòng bị ngắt giữa chừng do khổ giấy thành một dòng liền; "
    "chỉ xuống dòng giữa các đoạn văn, sau tiêu đề và giữa các mục liệt kê. "
    "2) Mỗi câu kết thúc bằng dấu chấm, chấm hỏi hoặc chấm than; "
    "câu nào trong ảnh thiếu dấu kết thúc thì thêm dấu chấm (chỉ được thêm dấu câu, không thêm chữ), "
    "kể cả câu cuối đoạn và câu kết thúc bằng con số hoặc phép tính (vd. '... = 6' -> '... = 6.'). "
    "3) Tiêu đề đứng riêng một dòng, không thêm dấu chấm. "
    "Trả JSON với trường raw_text."
)
