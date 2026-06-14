"""Shared base for OpenAI chat-completions-compatible endpoints.

OpenAI (GPT), Alibaba DashScope (Qwen), and Meta's Llama API (Muse) all speak
the same chat-completions wire format, so they share one implementation and
differ only by key env / base_url / model string.

Incognito contract (same as every provider): a single stateless user turn, no
system prompt, no tools. The client is built lazily on first generate() so the
registry can be imported and instantiated with no keys present — only an actual
generation call needs the key.
"""

import os

from .base import MAX_TOKENS, GenerationResult, Provider


class OpenAICompatProvider(Provider):
    api_key_env: str = "OPENAI_API_KEY"
    default_model: str = ""
    model_env: str = ""             # optional env var that overrides default_model
    base_url_env: str = ""          # optional env var that overrides default_base_url
    default_base_url: str | None = None   # None => the openai SDK's own endpoint

    def __init__(self) -> None:
        self._client = None

    def _model(self) -> str:
        if self.model_env:
            return os.getenv(self.model_env) or self.default_model
        return self.default_model

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            base = os.getenv(self.base_url_env) if self.base_url_env else None
            self._client = OpenAI(
                api_key=os.environ[self.api_key_env],
                base_url=base or self.default_base_url,
            )
        return self._client

    def generate(self, prompt_text: str) -> GenerationResult:
        model = self._model()
        params = {"model": model, "max_tokens": MAX_TOKENS}
        response = self._get_client().chat.completions.create(
            **params,
            # Incognito: bare user turn, no system prompt, no tools.
            messages=[{"role": "user", "content": prompt_text}],
        )
        choice = response.choices[0]
        usage = response.usage
        return GenerationResult(
            model_id=response.model,
            response_text=choice.message.content or "",
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
            stop_reason=choice.finish_reason,
            truncated=choice.finish_reason == "length",
            params=params,
        )
