"""Qwen 3.7 Plus under test — incognito, via Alibaba DashScope's
OpenAI-compatible endpoint (key in QWEN_API_KEY)."""

from ._openai_compat import OpenAICompatProvider


class QwenPlus(OpenAICompatProvider):
    name = "qwen-3.7-plus"
    api_key_env = "QWEN_API_KEY"
    default_model = "qwen-plus"     # DashScope model id; set the exact string via QWEN_MODEL
    model_env = "QWEN_MODEL"
    base_url_env = "QWEN_BASE_URL"
    default_base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
