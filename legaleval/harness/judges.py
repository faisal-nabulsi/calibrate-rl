"""Judge registry + structured grading schema (LegalEval v6 §6.5 Tier 1/2).

Two design rules live here:

Decomposition — the schema forces per-criterion sub-judgments with evidence
quotes instead of five holistic floats. "Score Directionality 0-4" becomes
"classify each edit/criterion, then band" — constrained classification is
where LLM judges are reliable; holistic quality ratings are where they are not.

Cross-family judging — the eval's gold keys were authored with Claude
assistance and a Claude judge grades a Claude model under test, so a
same-family-only grading run has a criterion-contamination channel that
blinding cannot close. Headline numbers should come from (at least) two
judge families; score.py reports cross-judge gate disagreements.
"""

import os
from typing import Literal

import anthropic
from pydantic import BaseModel


class SubJudgment(BaseModel):
    unit_id: str | None                 # gold-unit ID (task.unit-type.slug) when one applies
    criterion: str                      # the gold-rubric criterion being checked
    verdict: Literal["met", "partial", "not_met", "not_applicable"]
    evidence_quote: str | None          # exact response span; null only for omissions
    note: str


class DimensionGrade(BaseModel):
    sub_judgments: list[SubJudgment]    # one per gold criterion — never holistic
    score: float                        # banded from sub-judgments per the rubric's rules


class Finding(BaseModel):
    """One concern/edit/issue the response reported, classified per v7 §6.2a.

    Detection & diagnosis prompts (open variant) only; left empty for pure
    extraction/drafting prompts whose construct is not 'what did you notice'.
    """

    finding_text: str
    classification: Literal[
        "gold_matched",          # maps to a gold-unit ID -> Coverage credit
        "defensible_ungraded",   # legitimate concern outside gold -> precision-positive, no penalty
        "false_misattributed",   # misquotes/invents about the instance -> Faithfulness territory
    ]
    gold_unit_id: str | None    # set iff classification == gold_matched
    evidence_quote: str
    note: str


class GateCheck(BaseModel):
    tripped: bool
    evidence_quote: str | None
    needs_human_confirm: bool
    reasoning: str


class PromptGrade(BaseModel):
    findings: list[Finding]             # v7 §6.2a; [] for non-detection prompts
    faithfulness: DimensionGrade
    directionality: DimensionGrade
    coverage: DimensionGrade
    soundness: DimensionGrade
    actionability: DimensionGrade
    gate_faithfulness: GateCheck
    gate_directionality: GateCheck
    overall_notes: str


class Judge:
    """One judge family. name doubles as the grades/<name>/ artifact dir."""

    name: str = "base"
    model: str = ""

    def grade(self, system_text: str, user_text: str) -> PromptGrade:
        raise NotImplementedError


class OpusJudge(Judge):
    name = "claude-opus-4-8"
    model = "claude-opus-4-8"

    def __init__(self) -> None:
        self.client = anthropic.Anthropic()

    def grade(self, system_text: str, user_text: str) -> PromptGrade:
        result = self.client.messages.parse(
            model=self.model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=[{
                "type": "text",
                "text": system_text,
                "cache_control": {"type": "ephemeral"},  # reused across models/samples
            }],
            messages=[{"role": "user", "content": user_text}],
            output_format=PromptGrade,
        )
        return result.parsed_output


class GPTProJudge(Judge):
    """The cross-family judge (gpt-5.5-pro). Pro/reasoning models are Responses-API
    only — they reject chat completions — so this uses `responses.parse` for
    structured grading. Needs OPENAI_API_KEY; model overridable via
    OPENAI_PRO_JUDGE_MODEL. Slower + pricier; run alongside Opus for the headline
    cross-check. (Note: gpt-5.5 non-pro is a model UNDER TEST, not a judge.)"""

    name = "gpt-5.5-pro"

    def __init__(self) -> None:
        import openai  # optional dep — only needed when this judge is requested

        self.model = os.environ.get("OPENAI_PRO_JUDGE_MODEL", "gpt-5.5-pro")
        self.name = self.model
        self.client = openai.OpenAI()

    def grade(self, system_text: str, user_text: str) -> PromptGrade:
        result = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_text},
            ],
            text_format=PromptGrade,
            max_output_tokens=16000,  # pro models spend tokens on hidden reasoning
        )
        return result.output_parsed


class GPTProJudge(Judge):
    """Higher-capability cross-check judge. Pro/reasoning models (gpt-5.5-pro) are
    Responses-API only — they reject chat completions — so this uses
    `responses.parse` for structured grading. Needs OPENAI_API_KEY; model
    overridable via OPENAI_PRO_JUDGE_MODEL. Slower + pricier than gpt-5.5; intended
    for a final cross-family check, not every run."""

    name = "gpt-5.5-pro"

    def __init__(self) -> None:
        import openai  # optional dep — only needed when this judge is requested

        self.model = os.environ.get("OPENAI_PRO_JUDGE_MODEL", "gpt-5.5-pro")
        self.name = self.model
        self.client = openai.OpenAI()

    def grade(self, system_text: str, user_text: str) -> PromptGrade:
        result = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_text},
            ],
            text_format=PromptGrade,
            max_output_tokens=16000,  # pro models spend tokens on hidden reasoning
        )
        return result.output_parsed


JUDGES: dict[str, type[Judge]] = {
    "claude-opus-4-8": OpusJudge,
    "gpt-5.5": OpenAIJudge,
    "gpt-5.5-pro": GPTProJudge,
}
