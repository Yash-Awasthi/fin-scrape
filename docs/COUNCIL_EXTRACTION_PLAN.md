# Council Extraction Plan

## Goal

Extract finscrape's 7-agent council into a standalone, pip-installable Python package (`worldfin-council`) that any project can use for multi-agent deliberation.

## Current Coupling Points

The council code lives in `finscrape/agents/` and has these dependencies on finscrape:

| File | Dependency | Coupling Level | Fix |
|------|-----------|---------------|-----|
| `council.py` | `from finscrape.agents.base import AgentVerdict, BaseAgent` | HIGH | Move `base.py` into the package |
| `council.py` | `from finscrape.agents.judge import judge_debate` | HIGH | Move `judge.py` into the package |
| `judge.py` | `from finscrape.analysis.ai_client import call_ai` | HIGH | Define `AiClient` protocol, inject |
| `judge.py` | `from finscrape.agents.base import AgentVerdict` | HIGH | Already in base |
| `personas.py` | `from finscrape.agents.base import BaseAgent` | HIGH | Already in base |
| `base.py` | None (pure dataclasses + ABC) | NONE | Ready to extract |

## Extraction Steps

### Step 1: Create `worldfin-council` package structure

```
worldfin-council/
├── pyproject.toml
├── README.md
├── worldfin_council/
│   ├── __init__.py          # Public API: AgentCouncil, CouncilVerdict, BaseAgent, AgentVerdict
│   ├── base.py              # BaseAgent ABC, AgentVerdict dataclass (from finscrape/agents/base.py)
│   ├── council.py           # AgentCouncil class (from finscrape/agents/council.py)
│   ├── judge.py             # Judge role (from finscrape/agents/judge.py)
│   └── protocols.py         # AiClient protocol (replaces direct call_ai import)
```

### Step 2: Define `AiClient` protocol

The judge needs an LLM call. Instead of importing `finscrape.analysis.ai_client`, define a protocol:

```python
from typing import Protocol, Any

class AiClient(Protocol):
    def __call__(self, prompt: str, system: str, model: str | None = None) -> dict[str, Any] | None: ...
```

The host app (finscrape) provides its own implementation. The council doesn't know about HTTP, API keys, or model selection.

### Step 3: Move files

- `finscrape/agents/base.py` → `worldfin_council/base.py` (unchanged)
- `finscrape/agents/council.py` → `worldfin_council/council.py` (change imports)
- `finscrape/agents/judge.py` → `worldfin_council/judge.py` (accept AiClient protocol)
- `finscrape/agents/personas.py` → stays in finscrape (host-specific personas)

### Step 4: Update finscrape to use the package

```python
# Before
from finscrape.agents.council import AgentCouncil

# After
from worldfin_council import AgentCouncil
from worldfin_council.judge import set_ai_client
from finscrape.agents.personas import DEFAULT_AGENTS

set_ai_client(my_ai_client)
council = AgentCouncil(agents=DEFAULT_AGENTS, judge=True)
```

### Step 5: Add standalone tests

```python
# tests/test_council.py
from worldfin_council import AgentCouncil, AgentVerdict, BaseAgent

class MockAgent(BaseAgent):
    name = "mock"
    role = "test"
    weight = 1.0
    def analyze(self, title, text, metadata=None, market_facts=None):
        return AgentVerdict(agent_name="mock", verdict="OBSERVE", signal_score=1, confidence=0.8, reasoning="test")

def test_council_deliberation():
    council = AgentCouncil(agents=[MockAgent()])
    verdict = council.deliberate("Test", "Test article")
    assert verdict.consensus_verdict == "OBSERVE"
    assert verdict.consensus_score == 1
```

## What Stays in finscrape

- `personas.py` — Agent prompts are finscrape-specific (financial analyst personas)
- `council.py` factory function — Wires DEFAULT_AGENTS + judge + market_facts
- Pipeline integration — The council is called from `pipeline.py`

## Package Metadata

```toml
[project]
name = "worldfin-council"
version = "0.1.0"
description = "Multi-agent deliberation council with consensus scoring and judge override"
requires-python = ">=3.10"
dependencies = []  # Zero dependencies — pure Python

[project.optional-dependencies]
dev = ["pytest"]
```

**Zero dependencies** — the council is pure Python dataclasses + concurrent.futures. The host provides the AI client.

## Effort Estimate

| Step | Time |
|------|------|
| Package structure + pyproject.toml | 15 min |
| Move base.py, council.py, judge.py | 30 min |
| Define AiClient protocol | 10 min |
| Update imports in finscrape | 20 min |
| Standalone tests | 20 min |
| README + publish prep | 15 min |
| **Total** | **~2 hours** |

## Risk

Low — the council code is already well-separated. The only real coupling is the `call_ai` import in judge.py, which becomes a protocol injection.
