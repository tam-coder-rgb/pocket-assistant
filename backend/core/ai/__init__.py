"""Public interface của lớp AI: các module nghiệp vụ chỉ import từ đây."""
from backend.core.ai.base import ChatMessage
from backend.core.ai.client import ai_client

__all__ = ["ChatMessage", "ai_client"]
