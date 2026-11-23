"""HTTP cho thuốc (chỉ nhận/trả dữ liệu, logic nằm ở service / ai_analysis).

  GET  /api/v1/medicine/list?q=                      danh sách/tìm thuốc trong CSDL
  POST /api/v1/medicine/recognize-text               tra cứu theo tên (JSON)
  POST /api/v1/medicine/app-inventor                 nhận diện từ ảnh (form-data: file)
  POST /api/v1/medicine/analyze-ai?token=|text=      phân tích bằng AI (Bước 2)
"""
from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from backend.modules.medicine import ai_analysis, service
from backend.modules.medicine.schemas import (
    MedicineAIResponse,
    MedicineListResponse,
    MedicineScanResponse,
    MedicineTextRequest,
    MedicineTextResponse,
)

router = APIRouter(prefix="/api/v1/medicine", tags=["medicine"])


@router.get("/list", response_model=MedicineListResponse)
async def list_medicines(q: str = "") -> MedicineListResponse:
    return await service.list_medicines(q)


@router.post("/recognize-text", response_model=MedicineTextResponse)
async def recognize_text(body: MedicineTextRequest) -> MedicineTextResponse:
    return await service.lookup_by_text(body.text)


@router.post("/app-inventor", response_model=MedicineScanResponse)
async def scan_medicine(file: Annotated[UploadFile, File()]) -> MedicineScanResponse:
    return await service.scan_medicine_image(await file.read())


@router.post("/analyze-ai", response_model=MedicineAIResponse)
async def analyze_with_ai(
    token: str | None = None, text: str | None = None
) -> MedicineAIResponse:
    return await ai_analysis.analyze(token, text)
