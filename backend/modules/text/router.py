"""HTTP tóm tắt văn bản. Web gọi:
  POST /api/v1/text/summarize-stream  {text, document_type} -> SSE (chữ tới đâu hiện tới đó, cuối là [DONE])
  POST /api/v1/text/summarize         {text, speed}         -> JSON
"""
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.sse import EventSourceResponse, ServerSentEvent

from backend.core.sse import to_sse_events
from backend.modules.text import service
from backend.modules.text.schemas import SummarizeRequest, SummarizeResponse

router = APIRouter(prefix="/api/v1/text", tags=["text"])


@router.post("/summarize-stream", response_class=EventSourceResponse)
async def summarize_stream(body: SummarizeRequest) -> AsyncIterator[ServerSentEvent]:
    async for event in to_sse_events(service.stream_summary(body)):
        yield event


@router.post("/summarize")
async def summarize(body: SummarizeRequest) -> SummarizeResponse:
    return await service.summarize(body)
