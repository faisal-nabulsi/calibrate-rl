"""Provider registry. Add a provider here once its module is implemented."""

from .anthropic_provider import ClaudeSonnet
from .base import GenerationResult, Provider

# TODO: implement and register the other four models under test:
#   openai_provider.GPT55        (OPENAI_API_KEY)
#   gemini_provider.GeminiFlash  (GEMINI_API_KEY)
#   qwen_provider.QwenPlus       (QWEN_API_KEY)
#   muse_provider.MuseSpark      (MUSE_API_KEY)
REGISTRY: dict[str, type[Provider]] = {
    ClaudeSonnet.name: ClaudeSonnet,
}

__all__ = ["Provider", "GenerationResult", "REGISTRY"]
