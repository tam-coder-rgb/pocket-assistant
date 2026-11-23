"""Điểm vào FastAPI: chỉ khởi tạo app, CORS, handler lỗi, router và phục vụ web.

LUỒNG KHI NGƯỜI DÙNG CHỌN ẢNH TRÊN WEB
  clients/web/app.js  handleImageFile()
    -> api_client.js  POST /api/v1/medicine/app-inventor   (chế độ thuốc)
                      POST /api/v1/process/app-inventor    (chế độ văn bản)
       -> modules/<x>/router.py       nhận file, không có logic
          -> modules/<x>/service.py   điều phối nghiệp vụ
             |- modules/vision/service.py   kiểm tra mờ, resize/nén
             |- core/ai/                    gọi VLM (Gemini -> Groq)
       <- JSON (schemas.py) quay lại app.js -> renderMedicineStep1 / renderDocumentResult

GIỌNG ĐỌC: kết quả thuốc trả `audio_url` -> trình duyệt tải /api/v1/speech/clip|voice/... (modules/tts);
  chế độ văn bản gọi /api/v1/speech/stream từng câu. Karaoke chạy ở trình duyệt, khớp medicine/audio_script.py

CHAT ("Hỏi thêm"): app.js sendChatMessage() -> POST /api/v1/chat/medicine
  -> modules/chat/router.py -> service.py -> core/ai (stream) -> core/sse.py -> SSE về web

NÓI CÂU HỎI: voice_input.js ghi âm -> api_client.js POST /api/v1/stt/transcribe
  -> modules/stt (Groq Whisper) -> chữ -> app.js tự gửi vào chat
"""
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.core.config import settings
from backend.core.exceptions import MedAIError
from backend.modules.chat.router import router as chat_router
from backend.modules.document.router import router as document_router
from backend.modules.medicine.admin_router import router as medicine_admin_router
from backend.modules.medicine.router import router as medicine_router
from backend.modules.stt.router import router as stt_router
from backend.modules.text.router import router as text_router
from backend.modules.tts.router import router as tts_router
from backend.modules.tts.service import tts_service


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await asyncio.to_thread(tts_service.purge_cache)  # dọn âm thanh tạm quá hạn
    warm_up = asyncio.create_task(tts_service.warm_up())  # mở sẵn kết nối TTS, không chặn khởi động
    yield
    warm_up.cancel()


app = FastAPI(title="MedAI (MediDocX AI)", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(MedAIError)
async def medai_error_handler(_: Request, exc: MedAIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )


@app.get("/health")
@app.get("/api/health")
async def health() -> dict:
    return {"status": "connected", "ok": True}


app.include_router(medicine_router)
app.include_router(medicine_admin_router)  # bác sĩ thêm / sửa / xóa thuốc (cần X-Admin-Key)
app.include_router(document_router)
app.include_router(chat_router)
app.include_router(text_router)
app.include_router(tts_router)
app.include_router(stt_router)

# Phục vụ giao diện web tại "/" (đặt cuối để không che các route API)
app.mount("/", StaticFiles(directory=settings.WEB_DIR, html=True), name="web")
