"""Nghiệp vụ tóm tắt: cắt văn bản quá dài -> AI tóm tắt (stream) -> gom lại khi cần bản đầy đủ."""
from collections.abc import AsyncIterator

from backend.core.ai import ChatMessage, ai_client
from backend.core.config import settings
from backend.core.exceptions import InvalidRequestError
from backend.modules.text import prompts
from backend.modules.text.bullets import ensure_line_bullets
from backend.modules.text.punctuation import ensure_line_punctuation
from backend.modules.text.schemas import SummarizeRequest, SummarizeResponse
from backend.modules.tts.service import tts_service


def _source_text(request: SummarizeRequest) -> str:
    text = request.text.strip()
    if not text:
        raise InvalidRequestError("Không có nội dung để tóm tắt.")
    return text[: settings.SUMMARY_MAX_INPUT_CHARS]


def _stream(request: SummarizeRequest) -> AsyncIterator[str]:
    """Luồng chữ AI đã chuẩn hóa: dòng nào cũng có "• " ở đầu và dấu câu ở cuối."""
    raw = ai_client.stream_chat(
        [ChatMessage("user", _source_text(request))], prompts.build_system_prompt(request.document_type)
    )
    return ensure_line_punctuation(ensure_line_bullets(raw))


async def stream_summary(request: SummarizeRequest) -> AsyncIterator[str]:
    async for token in _stream(request):
        yield token


async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    summary = "".join([token async for token in _stream(request)]).strip()
    # Giọng đọc làm sạch ký hiệu và đọc mã/viết tắt (API_ABCDF...) trong tts, không xử lý lại ở đây
    return SummarizeResponse(
        summary=summary,
        plain_speech_text=summary.replace("•", "").strip(),
        audio_url=tts_service.url_for_text(summary),
    )
