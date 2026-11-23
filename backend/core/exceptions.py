"""Lỗi nghiệp vụ chuẩn hóa. main.py đăng ký handler để trả JSON `{detail, error_code}`.

Web đọc `err.detail` để hiển thị, nên giữ nguyên khóa `detail`.
"""


class MedAIError(Exception):
    status_code = 500
    error_code = "INTERNAL_ERROR"

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class InvalidImageError(MedAIError):
    status_code = 422
    error_code = "INVALID_IMAGE"


class AIUnavailableError(MedAIError):
    status_code = 503
    error_code = "AI_SERVICE_UNAVAILABLE"


class InvalidRequestError(MedAIError):
    status_code = 422
    error_code = "INVALID_REQUEST"


class ExpiredTokenError(MedAIError):
    status_code = 410
    error_code = "TOKEN_EXPIRED"


class NotFoundError(MedAIError):
    status_code = 404
    error_code = "NOT_FOUND"


class UnauthorizedError(MedAIError):
    status_code = 401
    error_code = "UNAUTHORIZED"


class ConflictError(MedAIError):
    status_code = 409
    error_code = "CONFLICT"


class AdminDisabledError(MedAIError):
    status_code = 503
    error_code = "ADMIN_DISABLED"


class TTSUnavailableError(MedAIError):
    status_code = 503
    error_code = "TTS_UNAVAILABLE"


class StorageUnavailableError(MedAIError):
    status_code = 503
    error_code = "STORAGE_UNAVAILABLE"
