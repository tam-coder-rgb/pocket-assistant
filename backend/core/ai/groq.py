"""Groq (API chuẩn OpenAI) — khớp tests/test_vlm_groq.py."""
import base64
import json
from collections.abc import AsyncIterator, Sequence

import httpx

from backend.core.ai.base import BaseAIProvider, ChatMessage
from backend.core.config import settings

_SSE_DATA_PREFIX = "data: "
_SSE_DONE = "[DONE]"


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}


class GroqProvider(BaseAIProvider):
    name = "groq"

    def is_available(self) -> bool:
        return bool(settings.GROQ_API_KEY)

    async def generate(self, prompt: str, image_jpeg: bytes | None = None) -> str:
        content: list[dict] = [{"type": "text", "text": prompt}]
        if image_jpeg:
            data_url = f"data:image/jpeg;base64,{base64.b64encode(image_jpeg).decode()}"
            content.append({"type": "image_url", "image_url": {"url": data_url}})
        payload = {
            "model": settings.GROQ_VLM_MODEL,
            "messages": [{"role": "user", "content": content}],
        }
        async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as http:
            resp = await http.post(settings.GROQ_API_URL, json=payload, headers=_headers())
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"] or ""

    async def stream_chat(
        self, messages: Sequence[ChatMessage], system_prompt: str
    ) -> AsyncIterator[str]:
        payload = {
            "model": settings.GROQ_VLM_MODEL,
            "stream": True,
            "messages": [
                {"role": "system", "content": system_prompt},
                *({"role": m.role, "content": m.content} for m in messages),
            ],
        }
        async with (
            httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as http,
            http.stream("POST", settings.GROQ_API_URL, json=payload, headers=_headers()) as resp,
        ):
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith(_SSE_DATA_PREFIX):
                    continue
                data = line.removeprefix(_SSE_DATA_PREFIX)
                if data == _SSE_DONE:
                    return
                choices = json.loads(data).get("choices") or []
                if choices and (text := choices[0]["delta"].get("content")):
                    yield text
