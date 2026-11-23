"""HTTP cho giọng đọc — mọi route trả về `audio/mpeg` (FileResponse: có Content-Length, hỗ trợ Range để tua).

  GET|POST /api/v1/speech/stream     đọc văn bản tùy ý (trình phát từng câu ở chế độ văn bản)
  GET      /api/v1/speech/clip/{key}  đọc kịch bản mà backend đã đăng ký (thuốc...)
  GET      /api/v1/speech/voice/{stem} phát file mp3 thu sẵn (kho file dữ liệu)
"""
import asyncio
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from backend.modules.tts.schemas import SpeechRequest
from backend.modules.tts.service import ROUTE_PREFIX, tts_service

router = APIRouter(prefix=ROUTE_PREFIX, tags=["tts"])

# Tên file là hash nội dung nên không bao giờ đổi -> cho phép trình duyệt giữ lại
_CACHE_HEADERS = {"Cache-Control": "public, max-age=86400"}


def _mp3(path: Path) -> FileResponse:
    return FileResponse(path, media_type="audio/mpeg", headers=_CACHE_HEADERS)


@router.get("/stream")
async def stream_get(text: Annotated[str, Query(min_length=1)]) -> FileResponse:
    return _mp3(await tts_service.audio_for_text(text))


@router.post("/stream")
async def stream_post(body: SpeechRequest) -> FileResponse:
    return _mp3(await tts_service.audio_for_text(body.text))


@router.get("/clip/{key}")
async def clip(key: str) -> FileResponse:
    return _mp3(await tts_service.audio_for_clip(key))


@router.get("/voice/{stem}")
async def voice_file(stem: str) -> FileResponse:
    return _mp3(await asyncio.to_thread(tts_service.voice_file, stem))  # kho Supabase: tải về lần đầu
