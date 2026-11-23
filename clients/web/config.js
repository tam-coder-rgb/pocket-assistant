/**
 * MEDIDOCX AI - CẤU HÌNH LIÊN KẾT TĨNH GIỮA WEB VÀ SERVER
 * 
 * Khi bạn public Web lên GitHub Pages:
 * Web sẽ TỰ ĐỘNG kết nối thẳng vào địa chỉ SERVER_URL này 24/7.
 * Người dùng chỉ việc mở web là dùng được ngay, KHÔNG cần thao tác thủ công.
 */
const MEDIDOCX_CONFIG = {
    // ⬇️ ĐIỀN ĐỊA CHỈ VPS CỐ ĐỊNH HOẶC CLOUDFLARE CỦA BẠN VÀO ĐÂY (BẮT BUỘC CÓ https://):
    // Ví dụ VPS có domain: "https://api.yourdomain.com"
    // Ví dụ Hugging Face: "https://username-medidocx.hf.space"
    // Ví dụ Cloudflare Tunnel cố định: "https://medidocx-api.yourdomain.com"
    SERVER_URL: "https://api.yourdomain.com"
};
