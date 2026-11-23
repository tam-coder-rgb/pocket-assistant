"""HTTP cho chat. Web gọi (JSON) -> SSE từng đoạn chữ, cuối là [DONE]:
  POST /api/v1/chat/medicine  hỏi về thuốc đang xem
  POST /api/v1/chat/document  hỏi về văn bản đã quét/tóm tắt
"""
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.sse import EventSourceResponse, ServerSentEvent

from backend.core.sse import to_sse_events
from backend.modules.chat import service
from backend.modules.chat.schemas import ChatRequest, DocumentChatRequest

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/medicine", response_class=EventSourceResponse)
async def chat_medicine(body: ChatRequest) -> AsyncIterator[ServerSentEvent]:
    async for event in to_sse_events(service.stream_reply(body)):
        yield event


@router.post("/document", response_class=EventSourceResponse)
async def chat_document(body: DocumentChatRequest) -> AsyncIterator[ServerSentEvent]:
    async for event in to_sse_events(service.stream_document_reply(body)):
        yield event
