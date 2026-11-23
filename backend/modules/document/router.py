"""HTTP cho văn bản. Web gọi: POST /api/v1/process/app-inventor (form-data: file)."""
from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from backend.modules.document import service
from backend.modules.document.schemas import DocumentScanResponse

router = APIRouter(prefix="/api/v1/process", tags=["document"])


@router.post("/app-inventor", response_model=DocumentScanResponse)
async def scan_document(file: Annotated[UploadFile, File()]) -> DocumentScanResponse:
    return await service.scan_document_image(await file.read())
