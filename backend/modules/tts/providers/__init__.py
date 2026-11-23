"""Đăng ký engine giọng đọc. Thêm engine mới: viết 1 file kế thừa BaseTTSProvider rồi thêm vào đây."""
import logging

from backend.core.config import settings
from backend.modules.tts.providers.base import BaseTTSProvider
from backend.modules.tts.providers.cartesia import CartesiaProvider
from backend.modules.tts.providers.fallback import FallbackTTSProvider
from backend.modules.tts.providers.gtts import GTTSProvider

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, type[BaseTTSProvider]] = {
    CartesiaProvider.name: CartesiaProvider,
    GTTSProvider.name: GTTSProvider,
}


def create_provider(name: str) -> BaseTTSProvider:
    try:
        return _REGISTRY[name]()
    except KeyError:
        raise ValueError(f"TTS engine '{name}' không tồn tại. Có: {', '.join(_REGISTRY)}") from None


def create_provider_chain() -> BaseTTSProvider:
    """Engine theo thứ tự TTS_PROVIDER_ORDER (cấp 1 đứng trước). Engine không khởi tạo được (vd. thiếu key) bị bỏ qua."""
    providers: list[BaseTTSProvider] = []
    for name in settings.TTS_PROVIDER_ORDER:
        try:
            providers.append(create_provider(name))
        except RuntimeError as exc:
            logger.warning("Bỏ qua TTS engine %s: %s", name, exc)
    return FallbackTTSProvider(providers, settings.TTS_VOICES)


__all__ = ["BaseTTSProvider", "create_provider", "create_provider_chain"]
