"""Gemini 3.1 Pro under test — incognito, via the google-genai SDK
(key in GEMINI_API_KEY). Pro is the strongest Gemini for this legal-NLP suite;
override to flash (or any snapshot) with GEMINI_MODEL if rate limits bite."""

import os

from .base import MAX_TOKENS, GenerationResult, Provider


class GeminiPro(Provider):
    name = "gemini-3.1-pro"

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        return self._client

    def generate(self, prompt_text: str) -> GenerationResult:
        from google.genai import types

        model = os.getenv("GEMINI_MODEL", "gemini-3.1-pro-preview")
        params = {"model": model, "max_output_tokens": MAX_TOKENS}
        # Incognito: prompt as the sole user content, no system_instruction, no tools.
        response = self._get_client().models.generate_content(
            model=model,
            contents=prompt_text,
            config=types.GenerateContentConfig(max_output_tokens=MAX_TOKENS),
        )
        usage = getattr(response, "usage_metadata", None)
        finish = None
        truncated = False
        if response.candidates:
            finish = str(getattr(response.candidates[0], "finish_reason", "") or "")
            truncated = finish.endswith("MAX_TOKENS")
        return GenerationResult(
            model_id=model,
            response_text=response.text or "",
            input_tokens=getattr(usage, "prompt_token_count", None),
            output_tokens=getattr(usage, "candidates_token_count", None),
            stop_reason=finish,
            truncated=truncated,
            params=params,
        )
