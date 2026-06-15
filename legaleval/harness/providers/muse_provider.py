"""Meta Llama under test — incognito. The Meta-AI key (MUSE_API_KEY) is an
OpenRouter key, so we reach the best Llama model (Llama 4 Maverick) through
OpenRouter's OpenAI-compatible endpoint. Override MUSE_BASE_URL / MUSE_MODEL in
.env to point at a different host or Llama snapshot.
"""

from ._openai_compat import OpenAICompatProvider


class LlamaMaverick(OpenAICompatProvider):
    name = "llama-4-maverick"
    api_key_env = "MUSE_API_KEY"
    default_model = "meta-llama/llama-4-maverick"
    model_env = "MUSE_MODEL"
    base_url_env = "MUSE_BASE_URL"
    default_base_url = "https://openrouter.ai/api/v1"
