"""Hợp đồng chung cho mọi nhà cung cấp VLM + tiện ích xử lý JSON dùng chung."""
import re
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel

from backend.core.exceptions import AIUnavailableError

T = TypeVar("T", bound=BaseModel)

_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)
_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "user" | "assistant"
    content: str


def unavailable_error(errors: Mapping[str, BaseException]) -> AIUnavailableError:
    """Gộp lỗi của các provider thành 1 lỗi 503 duy nhất."""
    detail = "; ".join(f"{name}: {type(exc).__name__}" for name, exc in errors.items())
    return AIUnavailableError(
        "Hệ thống AI đang bận. Vui lòng thử lại sau." + (f" ({detail})" if detail else "")
    )


class BaseAIProvider(ABC):
    """Mỗi provider chỉ làm 1 việc: gửi prompt (kèm ảnh nếu có) và trả về chuỗi văn bản thô."""

    name: str

    @abstractmethod
    def is_available(self) -> bool:
        """Đã có API key chưa."""

    @abstractmethod
    async def generate(self, prompt: str, image_jpeg: bytes | None = None) -> str:
        """Gửi prompt (+ ảnh JPEG nếu có), trả văn bản thô do model sinh ra."""

    def stream_chat(
        self, messages: Sequence[ChatMessage], system_prompt: str
    ) -> AsyncIterator[str]:
        """Hội thoại nhiều lượt, trả từng đoạn chữ ngay khi model sinh ra.

        Triển khai bằng `async def` + `yield`. Provider nào chưa hỗ trợ thì không cần ghi đè.
        """
        raise NotImplementedError(f"Provider '{self.name}' chưa hỗ trợ chat streaming")


_TYPE_HINTS = {"string": '"chuỗi"', "boolean": "true|false", "integer": "số nguyên", "number": "số"}


def _skeleton(schema: type[BaseModel]) -> str:
    """Khung JSON mẫu `{"khóa": kiểu, ...}` — gọn hơn JSON Schema nên model không bắt chước nhầm."""
    props = schema.model_json_schema()["properties"]
    fields = ", ".join(f'"{k}": {_TYPE_HINTS.get(v.get("type"), "...")}' for k, v in props.items())
    return "{" + fields + "}"


def build_json_prompt(prompt: str, schema: type[BaseModel]) -> str:
    """Gắn yêu cầu 'chỉ trả JSON đúng khung' vào prompt (dùng chung cho mọi provider)."""
    return (
        f"{prompt}\n\n"
        "Chỉ trả về MỘT đối tượng JSON phẳng, không giải thích, không markdown, "
        f"có đúng các khóa sau (thay kiểu bằng giá trị thật):\n{_skeleton(schema)}"
    )


def parse_json_result(text: str, schema: type[T]) -> T:
    """Lấy đối tượng JSON từ văn bản model trả về (bỏ <think>, ```json ...```) rồi kiểm tra schema."""
    cleaned = _THINK_BLOCK.sub("", text)
    match = _JSON_OBJECT.search(cleaned)
    if match is None:
        raise ValueError("Model không trả về JSON")
    return schema.model_validate_json(match.group(0))
