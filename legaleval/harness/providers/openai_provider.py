"""GPT 5.5 under test — incognito, via the OpenAI chat-completions API."""

from ._openai_compat import OpenAICompatProvider


class GPT55(OpenAICompatProvider):
    name = "gpt-5.5"
    api_key_env = "OPENAI_API_KEY"
    default_model = "gpt-5.5"
    model_env = "OPENAI_MODEL"      # override the exact snapshot string here
    token_param = "max_completion_tokens"  # gpt-5.5 rejects the legacy max_tokens
    # base_url unset => OpenAI's own endpoint
