"""Nghiệp vụ chat: dựng ngữ cảnh -> chặn chất nguy hiểm -> stream câu trả lời từ AI."""
from collections.abc import AsyncIterator

from backend.core import safety
from backend.core.ai import ChatMessage, ai_client
from backend.core.config import settings
from backend.core.exceptions import InvalidRequestError
from backend.modules.chat import document_prompts, prompts
from backend.modules.chat.schemas import ChatRequest, DocumentChatRequest


def _build_messages(request: ChatRequest | DocumentChatRequest) -> list[ChatMessage]:
    recent = request.history[-settings.CHAT_MAX_HISTORY :]
    turns = [ChatMessage(t.role, t.content) for t in recent]
    return [*turns, ChatMessage("user", request.message)]


async def stream_reply(request: ChatRequest) -> AsyncIterator[str]:
    ctx = request.context
    if safety.is_hazardous(f"{ctx.medicine_name} {ctx.active_ingredient}"):
        # Đang xem hóa chất/chất độc: không để AI "tư vấn cách dùng", chỉ nhắc cảnh báo
        yield safety.TOXIC_WARNING
        return

    async for token in ai_client.stream_chat(_build_messages(request), prompts.build_system_prompt(ctx)):
        yield token


async def stream_document_reply(request: DocumentChatRequest) -> AsyncIterator[str]:
    ctx = request.context
    if not (ctx.raw_text.strip() or ctx.summary.strip()):
        raise InvalidRequestError("Chưa có văn bản để hỏi.")
    async for token in ai_client.stream_chat(
        _build_messages(request), document_prompts.build_system_prompt(ctx)
    ):
        yield token
