"""Bảo vệ API quản trị: yêu cầu header `X-Admin-Key` khớp settings.ADMIN_API_KEY.

Dùng chung cho mọi API quản trị: `APIRouter(..., dependencies=[Depends(require_admin_key)])`.
Khóa do app desktop (phần Python) giữ và chỉ gửi khi bác sĩ đã đăng nhập; giao diện không bao giờ thấy khóa.
"""
import hmac
from typing import Annotated

from fastapi import Header

from backend.core.config import settings
from backend.core.exceptions import AdminDisabledError, UnauthorizedError


async def require_admin_key(x_admin_key: Annotated[str | None, Header()] = None) -> None:
    expected = settings.ADMIN_API_KEY
    if not expected:
        raise AdminDisabledError("Máy chủ chưa bật chức năng quản trị: cần đặt ADMIN_API_KEY trong file .env.")
    if not x_admin_key or not hmac.compare_digest(x_admin_key.encode(), expected.encode()):
        raise UnauthorizedError("Khóa quản trị không đúng.")
