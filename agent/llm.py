"""The one door to Claude: send a prompt, get back a validated Pydantic object, count the cost."""
from datetime import date
from typing import Literal, TypeVar

import anthropic
from pydantic import BaseModel

from agent import cache, config
from agent.models import RunStats

Stage = Literal["extract", "match", "judge"]
T = TypeVar("T", bound=BaseModel)

MODEL_FOR: dict[Stage, str] = {
    "extract": config.EXTRACT_MODEL,
    "match": config.MATCH_MODEL,
    "judge": config.JUDGE_MODEL,
}

_client: anthropic.AsyncAnthropic | None = None


class LLMError(Exception):
    """Claude answered, but not with something we can use (refusal, cut off, unparseable)."""


def _get_client() -> anthropic.AsyncAnthropic:
    # Created on first use, so importing this module needs no API key (tests run offline).
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(timeout=config.LLM_TIMEOUT_S)  # SDK retries 429/5xx
    return _client


def add_cost(stats: RunStats, model: str, input_tokens: int, output_tokens: int) -> None:
    """Add one call's tokens and dollars to the run totals."""
    price_in, price_out = config.PRICE_PER_MTOK[model]
    stats.input_tokens += input_tokens
    stats.output_tokens += output_tokens
    stats.cost_usd += (input_tokens * price_in + output_tokens * price_out) / 1_000_000


async def ask(stage: Stage, system: str, prompt: str, schema: type[T], stats: RunStats,
              max_tokens: int = 16000) -> T:
    """Call the model for this stage and return its answer as a `schema` object.

    Answers are cached per day by the exact model, settings and prompts, so re-running a company
    on the same day gives the same result for free (the cached call adds no cost to `stats`).
    """
    model = MODEL_FOR[stage]
    key = (f"{model} | effort={config.EFFORT[stage]} | max_tokens={max_tokens} | {schema.__name__} | "
           f"day={date.today()}\n{system}\n---\n{prompt}")
    if (saved := cache.get("llm", key)) is not None:
        return schema.model_validate(saved)

    response = await _get_client().messages.parse(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        output_format=schema,
        output_config={"effort": config.EFFORT[stage]},
    )
    add_cost(stats, model, response.usage.input_tokens, response.usage.output_tokens)

    if response.stop_reason == "refusal":
        raise LLMError(f"{stage}: model refused")
    if response.stop_reason == "max_tokens":
        raise LLMError(f"{stage}: answer cut off at max_tokens={max_tokens}")
    if response.parsed_output is None:
        raise LLMError(f"{stage}: answer did not match {schema.__name__}")
    cache.put("llm", key, response.parsed_output.model_dump(mode="json"))  # only good answers are cached
    return response.parsed_output
