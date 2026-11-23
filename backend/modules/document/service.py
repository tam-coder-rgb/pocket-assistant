"""Luồng đọc văn bản từ ảnh: ảnh -> vision (mờ?) -> VLM trích 100% nguyên văn."""
from backend.core.ai import ai_client
from backend.modules.document.prompts import SCAN_DOCUMENT
from backend.modules.document.schemas import DocumentScanResponse, DocumentVLMResult
from backend.modules.vision.service import prepare_image


async def scan_document_image(raw: bytes) -> DocumentScanResponse:
    image = await prepare_image(raw)
    if image.is_blurry:
        return DocumentScanResponse(status="unreadable_image", is_unreadable=True)

    vlm = await ai_client.analyze(SCAN_DOCUMENT, DocumentVLMResult, image_jpeg=image.jpeg_bytes)
    text = vlm.raw_text.strip()
    return DocumentScanResponse(status="success" if text else "no_text", raw_text=text)
