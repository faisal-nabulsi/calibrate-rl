"""Muse Spark (Meta AI) under test — incognito, via Meta's Llama API
OpenAI-compatible endpoint (key in MUSE_API_KEY).

If Meta hands you a different base URL or model string, override MUSE_BASE_URL /
MUSE_MODEL in .env rather than editing this file.
"""

from ._openai_compat import OpenAICompatProvider


class MuseSpark(OpenAICompatProvider):
    name = "muse-spark"
    api_key_env = "MUSE_API_KEY"
    default_model = "muse-spark"
    model_env = "MUSE_MODEL"
    base_url_env = "MUSE_BASE_URL"
    default_base_url = "https://api.llama.com/compat/v1"
