"""Cấu hình tập trung (Single Source of Truth).

Bí mật (API key) nạp từ file .env ở thư mục gốc. Mọi module chỉ đọc từ `settings`.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- API keys (điền trong .env) ---
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # --- AI: thứ tự ưu tiên + tên model ---
    AI_PROVIDER_ORDER: list[str] = ["groq", "gemini"]  # nhanh nhất đứng trước
    GEMINI_VLM_MODEL: str = "gemini-3.1-flash-lite"
    GROQ_VLM_MODEL: str = "qwen/qwen3.8-27b"
    GROQ_API_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    AI_TIMEOUT_SECONDS: float = 30.0
    AI_HEDGE_DELAY_SECONDS: float = 2.5  # provider chính chậm hơn mức này -> chạy thêm provider dự phòng
    AI_CACHE_SIZE: int = 128  # số ảnh nhớ kết quả (0 = tắt cache)
    AI_STREAM_FIRST_TOKEN_TIMEOUT: float = 8.0  # chờ chữ đầu tiên quá lâu -> thử provider khác
    # (provider cuối cùng được chờ tới AI_TIMEOUT_SECONDS: không còn ai để chuyển sang)

    # --- Nhận diện giọng nói (STT, Groq Whisper) — đổi model tại đây ---
    GROQ_STT_MODEL: str = "whisper-large-v3-turbo"  # hoặc "whisper-large-v3" (chính xác hơn, chậm hơn)
    GROQ_STT_URL: str = "https://api.groq.com/openai/v1/audio/transcriptions"
    STT_LANGUAGE: str = "vi"  # mã ISO-639-1, giúp Whisper nhận đúng tiếng Việt
    STT_TIMEOUT_SECONDS: float = 20.0
    STT_MAX_AUDIO_BYTES: int = 10 * 1024 * 1024  # Groq giới hạn 25MB; câu hỏi ngắn không cần nhiều
    # Whisper hay "bịa" các câu này khi âm thanh im lặng/ồn -> coi như không nghe thấy (viết không dấu, thường)
    STT_HALLUCINATION_PHRASES: list[str] = [  # chứa cụm này ở bất kỳ đâu
        "subscribe", "ghien mi go", "dang ky kenh", "bo lo nhung video", "like va share",
        "cam on cac ban da theo doi", "cam on cac ban da xem",
    ]
    STT_HALLUCINATION_EXACT: list[str] = [  # chỉ khi cả câu đúng bằng cụm này
        "cam on", "cam on ban", "cam on cac ban", "xin chao",
    ]

    # --- Chat ---
    CHAT_MAX_HISTORY: int = 20  # số tin nhắn gần nhất gửi kèm cho AI
    CHAT_MAX_MESSAGE_CHARS: int = 1000
    CHAT_MAX_CONTEXT_CHARS: int = 800  # giới hạn mỗi ô thông tin thuốc
    CHAT_MAX_DOCUMENT_CHARS: int = 8000  # giới hạn mỗi phần (nguyên văn / bản tóm tắt) gửi kèm khi hỏi về văn bản

    # --- Tóm tắt văn bản (chế độ dyslexia) ---
    SUMMARY_MAX_INPUT_CHARS: int = 12000  # văn bản dài hơn sẽ bị cắt bớt trước khi gửi AI

    # --- Chuẩn hóa chữ trước khi đọc ---
    SPEECH_SPELL_MAX_LETTERS: int = 6  # viết hoa liền nhau dài tới mức này -> đọc từng chữ cái (API, ABCDF)
    SPEECH_WORD_ACRONYMS: list[str] = [  # viết tắt vốn đọc như một từ -> không đánh vần
        "COVID", "UNESCO", "UNICEF", "ASEAN", "NASA", "OPEC", "VIETNAM",
    ]

    # --- Tiền xử lý ảnh ---
    LAPLACIAN_BLUR_THRESHOLD: float = 100.0
    MAX_IMAGE_DIMENSION: int = 1920
    IMAGE_JPEG_QUALITY: int = 85
    MAX_UPLOAD_BYTES: int = 15 * 1024 * 1024

    # --- Ảnh chờ phân tích AI (Bước 2 sau khi quét) ---
    SCAN_TOKEN_TTL_SECONDS: int = 1800
    SCAN_TOKEN_MAX_ITEMS: int = 64

    # --- Giọng đọc (TTS) ---
    TTS_PROVIDER_ORDER: list[str] = ["cartesia", "gtts"]  # cấp 1 = cartesia, cấp 2 (dự phòng) = gtts
    TTS_VOICE: str = "nhung-24k"  # nhãn giọng chung, chỉ dùng làm khóa cache (đổi giọng -> đổi nhãn để bỏ cache cũ)
    TTS_VOICES: dict[str, str] = {  # giọng thật của từng engine
        "cartesia": "d2065f28-70d9-434a-8563-4769b06e8bc0",  # Nhung (Nữ - Sắc nét)
        "gtts": "vi",  # gTTS: mã ngôn ngữ
    }
    # Nhiều khóa (vd. nhiều tài khoản miễn phí): khóa này lỗi -> xoay sang khóa kia, hết khóa -> gTTS.
    # Trong .env viết dạng JSON: CARTESIA_API_KEYS=["sk_car_1", "sk_car_2"]  (bao nhiêu khóa cũng được)
    CARTESIA_API_KEYS: list[str] = []
    CARTESIA_API_KEY: str = ""  # cách cũ (1 khóa), vẫn nhận để không hỏng cấu hình đã deploy
    CARTESIA_MODEL: str = "sonic-3.5"
    CARTESIA_SAMPLE_RATE: int = 24000  # = gTTS: ghép câu của 2 engine vẫn đúng thời lượng (karaoke khớp)
    CARTESIA_BIT_RATE: int = 64000  # = gTTS
    CARTESIA_TIMEOUT_SECONDS: float = 8.0  # quá mức này -> chuyển sang gTTS ngay (phải nhỏ hơn TTS_TIMEOUT_SECONDS)
    TTS_CONCURRENCY: int = 6  # số câu tổng hợp chạy song song tối đa
    TTS_MAX_TEXT_CHARS: int = 3000
    TTS_CHUNK_CHARS: int = 90  # đoạn dài được chia thành các câu ~ngần này ký tự và tạo song song
    TTS_RETRIES: int = 3  # số lần thử lại mỗi câu khi engine ngoài lỗi thoáng qua
    TTS_TIMEOUT_SECONDS: float = 25.0  # tối đa cho 1 câu
    TTS_RETRY_BACKOFF_SECONDS: float = 1.0  # nghỉ giữa các lần thử (nhân với số lần đã lỗi)
    TTS_CLIP_TTL_SECONDS: int = 1800  # thời gian nhớ kịch bản đã đăng ký
    CACHE_TTL_SECONDS: int = 86400  # file âm thanh tạm quá hạn sẽ bị dọn

    # --- Đối chiếu CSDL thuốc ---
    RAPIDFUZZ_THRESHOLD: float = 80.0  # độ giống tối thiểu (0-100) của MỖI TỪ trong câu tìm với tên thuốc
    MEDICINE_GENERIC_WORDS: list[str] = [  # từ chung không giúp phân biệt thuốc -> bỏ khi so khớp (đã bỏ dấu)
        "thuoc", "vien", "nen", "nang", "cung", "bot", "uong", "goi", "ong", "sui",
    ]
    MEDICINE_UNIT_WORDS: list[str] = ["mg", "mcg", "g", "ml", "iu", "miu", "ui", "kg"]

    # --- Kho file dữ liệu: danh mục thuốc JSON + mp3 thu sẵn (xem core/storage/, docs/supabase_setup.md) ---
    DATA_STORAGE: str = "local"  # "local" = thư mục DATA_DIR | "supabase" = Supabase Storage (mọi server dùng chung)
    DATA_CACHE_SECONDS: float = 30.0  # đọc lại danh mục thuốc / mục lục giọng sau mỗi khoảng này (server khác sửa thì thấy)
    SUPABASE_URL: str = ""  # https://<mã-dự-án>.supabase.co
    SUPABASE_SECRET_KEY: str = ""  # sb_secret_... (hoặc service_role cũ). CHỈ đặt ở server, không bao giờ đưa vào app desktop
    SUPABASE_BUCKET: str = "medidocx-data"
    SUPABASE_TIMEOUT_SECONDS: float = 15.0
    # Khóa file trong kho = đường dẫn tương đối, giống cấu trúc thư mục data/
    MEDIC_DATA_KEY: str = "medic_data/medicines.json"
    VOICE_DATA_PREFIX: str = "voice_data"  # med_<mã>_main|warning.mp3, voice_index.json (tên -> mã), audio_hashes.json

    # --- Kho thuốc + quản trị (bác sĩ thêm / sửa / xóa thuốc từ app desktop) ---
    MEDICINE_CATALOG: str = "json"  # định dạng danh mục: "json" = file MEDIC_DATA_KEY (xem modules/medicine/catalog/)
    ADMIN_API_KEY: str = ""  # khóa cho API quản trị (đặt trong .env); để trống = tắt API quản trị
    MEDICINE_NAME_MAX_CHARS: int = 120
    MEDICINE_TEXT_MAX_CHARS: int = 3000
    MEDICINE_MAX_ALIASES: int = 20

    # --- Đường dẫn ---
    DATA_DIR: Path = ROOT_DIR / "data"  # kho "local"
    SUPABASE_CACHE_DIR: Path = ROOT_DIR / "storage" / "temp" / "supabase"  # mp3 tải từ Supabase để phát
    TTS_CACHE_DIR: Path = ROOT_DIR / "storage" / "temp" / "tts"
    WEB_DIR: Path = ROOT_DIR / "clients" / "web"

    # --- Server ---
    CORS_ORIGINS: list[str] = ["*"]

    DISCLAIMER_AI: str = (
        "Thông tin phân tích từ AI chỉ mang tính chất tham khảo, "
        "vui lòng hỏi ý kiến bác sĩ hoặc dược sĩ trước khi sử dụng."
    )

    @property
    def cartesia_api_keys(self) -> list[str]:
        """Mọi khóa Cartesia theo thứ tự ưu tiên, bỏ ô trống và khóa trùng."""
        keys = [k.strip() for k in [*self.CARTESIA_API_KEYS, self.CARTESIA_API_KEY]]
        return list(dict.fromkeys(k for k in keys if k))


settings = Settings()
