"""HTTP quản trị thuốc (chỉ nhận/trả dữ liệu, quy tắc ở admin_service). Mọi route cần header X-Admin-Key.

  GET    /api/v1/medicine/admin/medicines             danh sách đầy đủ (kèm tên gọi khác, còn mp3 hay không)
  POST   /api/v1/medicine/admin/medicines             thêm thuốc
  PUT    /api/v1/medicine/admin/medicines?name=<tên>  sửa thuốc (đổi tên được)
  DELETE /api/v1/medicine/admin/medicines?name=<tên>  xóa hẳn thuốc + mp3 thu sẵn

Tên thuốc đi trong query (không đặt trong đường dẫn) vì có tên chứa "/" như "Amoxicillin/Acid clavulanic".
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from backend.core.admin_auth import require_admin_key
from backend.modules.medicine import admin_service
from backend.modules.medicine.admin_schemas import (
    MedicineAdminItem,
    MedicineAdminList,
    MedicineDeleted,
    MedicineInput,
)

router = APIRouter(
    prefix="/api/v1/medicine/admin/medicines", tags=["medicine-admin"], dependencies=[Depends(require_admin_key)],
)
NameQuery = Annotated[str, Query(min_length=1)]


@router.get("", response_model=MedicineAdminList)
async def list_medicines() -> MedicineAdminList:
    return await admin_service.list_all()


@router.post("", response_model=MedicineAdminItem, status_code=status.HTTP_201_CREATED)
async def add_medicine(body: MedicineInput) -> MedicineAdminItem:
    return await admin_service.add(body)


@router.put("", response_model=MedicineAdminItem)
async def update_medicine(name: NameQuery, body: MedicineInput) -> MedicineAdminItem:
    return await admin_service.update(name, body)


@router.delete("", response_model=MedicineDeleted)
async def delete_medicine(name: NameQuery) -> MedicineDeleted:
    return await admin_service.delete(name)
