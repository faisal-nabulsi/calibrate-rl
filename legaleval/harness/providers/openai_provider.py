"""GPT 5.5 under test — incognito, via the OpenAI chat-completions API."""

from ._openai_compat import OpenAICompatProvider


class GPT55(OpenAICompatProvider):
    name = "gpt-5.5"
    api_key_env = "OPENAI_API_KEY"
    default_model = "gpt-5.5"
    model_env = "OPENAI_MODEL"      # override the exact snapshot string here
    # base_url unset => OpenAI's own endpoint
