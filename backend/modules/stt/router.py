"""HTTP nhận diện giọng nói. Web gọi:
  POST /api/v1/stt/transcribe  (form-data: file = đoạn ghi âm)  ->  {"text": "..."}
"""
from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from backend.modules.stt import service
from backend.modules.stt.schemas import TranscribeResponse

router = APIRouter(prefix="/api/v1/stt", tags=["stt"])


@router.post("/transcribe")
async def transcribe(file: Annotated[UploadFile, File()]) -> TranscribeResponse:
    text = await service.transcribe(
        await file.read(), file.filename or "voice.webm", file.content_type or "audio/webm"
    )
    return TranscribeResponse(text=text)
