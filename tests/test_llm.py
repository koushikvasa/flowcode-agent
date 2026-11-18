"""Offline test for the Claude answer cache: a fake client stands in for the API."""
import asyncio
from types import SimpleNamespace

from pydantic import BaseModel

from agent import cache, llm
from agent.models import RunStats


class Answer(BaseModel):
    text: str


class FakeClient:
    """Mimics client.messages.parse: counts calls and returns a fixed answer."""

    def __init__(self) -> None:
        self.calls = 0
        self.messages = self

    async def parse(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(stop_reason="end_turn", parsed_output=Answer(text=f"answer {self.calls}"),
                               usage=SimpleNamespace(input_tokens=1000, output_tokens=100))


def test_same_prompt_same_day_is_answered_from_cache_for_free(monkeypatch, tmp_path):
    fake = FakeClient()
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(llm, "_get_client", lambda: fake)
    first_stats, second_stats = RunStats(), RunStats()

    first = asyncio.run(llm.ask("match", "system", "prompt", Answer, first_stats))
    second = asyncio.run(llm.ask("match", "system", "prompt", Answer, second_stats))
    other = asyncio.run(llm.ask("match", "system", "a different prompt", Answer, RunStats()))

    assert fake.calls == 2  # the repeat was not sent; the different prompt was
    assert first == second == Answer(text="answer 1") and other == Answer(text="answer 2")
    assert first_stats.cost_usd > 0 and second_stats.cost_usd == 0 and second_stats.input_tokens == 0
