"""Provider interface for models under test.

Incognito contract (applies to EVERY provider):
  - no system prompt (or provider-required empty minimum, identical across models)
  - single turn, stateless: one fresh API call per prompt
  - no tools, no web search, no files, no memory, no conversation carry-over
"""

from dataclasses import dataclass, field

# One ceiling for every provider — identical treatment is part of the incognito
# contract. High enough that D1 (full NDA draft) cannot silently truncate.
MAX_TOKENS = 16384


@dataclass
class GenerationResult:
    model_id: str          # exact snapshot/model string the API reports back
    response_text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    stop_reason: str | None = None      # provider-native; normalized via `truncated`
    truncated: bool = False             # set by the provider when output hit the token cap
    params: dict = field(default_factory=dict)  # sampling params actually sent (reproducibility)


class Provider:
    """Subclass per vendor. name is the key used in runs/ and results/."""

    name: str = "base"

    def generate(self, prompt_text: str) -> GenerationResult:
        raise NotImplementedError
