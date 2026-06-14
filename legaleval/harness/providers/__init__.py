"""Provider registry. Add a provider here once its module is implemented."""

from .anthropic_provider import ClaudeSonnet
from .base import GenerationResult, Provider
from .gemini_provider import GeminiPro
from .muse_provider import MuseSpark
from .openai_provider import GPT55
from .qwen_provider import QwenPlus

# The five models under test. Each enforces the incognito contract (base.py):
# bare user prompt, no system prompt, no tools, single stateless call.
REGISTRY: dict[str, type[Provider]] = {
    cls.name: cls
    for cls in (ClaudeSonnet, GPT55, GeminiPro, QwenPlus, MuseSpark)
}

__all__ = ["Provider", "GenerationResult", "REGISTRY"]
