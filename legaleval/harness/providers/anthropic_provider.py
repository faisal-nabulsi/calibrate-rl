"""Claude Sonnet 4.6 under test — incognito: bare user prompt, nothing else."""

import anthropic

from .base import MAX_TOKENS, GenerationResult, Provider


class ClaudeSonnet(Provider):
    name = "claude-sonnet-4-6"

    def __init__(self) -> None:
        self._client = None  # built lazily so the registry needs no key to instantiate

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        return self._client

    def generate(self, prompt_text: str) -> GenerationResult:
        params = {"model": "claude-sonnet-4-6", "max_tokens": MAX_TOKENS}
        response = self._get_client().messages.create(
            **params,
            # Incognito: no system prompt, no tools, no thinking config beyond default.
            messages=[{"role": "user", "content": prompt_text}],
        )
        text = "".join(b.text for b in response.content if b.type == "text")
        return GenerationResult(
            model_id=response.model,
            response_text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            stop_reason=response.stop_reason,
            truncated=response.stop_reason == "max_tokens",
            params=params,
        )
