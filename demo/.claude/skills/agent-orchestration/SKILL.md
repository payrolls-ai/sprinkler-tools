---
name: agent-orchestration
description: "Use this skill when adding, modifying, or debugging any of the 50 specialist agents in the sprinkler-tools project, or when changing how the Master Placement Agent coordinates them. Triggers include: requests to add a new detection agent, modify an existing agent's findings, change parallel execution behavior, adjust confidence thresholds, fix race conditions in master_agent.py, or refactor team boundaries (Structure / Openings / Obstructions / Classifiers / MEP / Code Math). Do NOT use this skill for changes to the rules JSON files (use nfpa-rule-encoder) or to blueprint parsing (use blueprint-parser)."
---

# Agent Orchestration Skill

This skill defines how the 50-agent + Master Placement system fits together.
Read this end-to-end before touching any file under `backend/agents/`.

## The contract every agent must satisfy

```python
from backend.agents.base_agent import BaseAgent, AgentReport, Finding

class MyAgent(BaseAgent):
    agent_id: int = 19           # 1-50, MUST be unique
    team: str = "obstructions"   # one of: structure, openings, obstructions,
                                 #         classifiers, mep, code_math
    name: str = "HVAC Duct Detector"

    async def analyze(self, blueprint: Blueprint) -> AgentReport:
        # Inspect the blueprint, return findings
        return AgentReport(
            agent_id=self.agent_id,
            findings=[...],  # list of Finding objects
            confidence=0.92,
            elapsed_ms=...,
        )
```

## Adding a new agent — checklist

1. Pick an unused `agent_id`. The current ceiling is 50; if you need 51+,
   discuss with the project owner first — adding agents has architectural
   implications for the master agent's coordination logic.
2. Place the new agent in the correct team module. Do not create new modules.
3. Implement `analyze()` as `async`. Even if your agent does CPU-bound work,
   wrap it in `asyncio.to_thread()` so it doesn't block the event loop.
4. Register the agent in `backend/agents/__init__.py` in the `ALL_AGENTS` list.
5. Add a demo finding for the sample blueprint in `backend/agents/_demo_data.py`
   so the demo path keeps working.
6. Add a unit test in `tests/agents/test_agent_<id>.py`.

## Confidence values

Confidence is a float in `[0.0, 1.0]`. Calibrate as follows:

| Range | Meaning | Master agent behavior |
|-------|---------|------------------------|
| 0.90+ | High confidence, definitely present | Use directly |
| 0.70-0.89 | Likely present | Cross-check with adjacent agents |
| 0.50-0.69 | Possible, needs corroboration | Require ≥2 supporting findings |
| <0.50 | Discard | Do not include in report |

**Never** report confidence > 0.95 unless your detection is geometric/measured
rather than learned. The CNN backbone caps inference confidence at 0.95.

## Master Placement Agent rules

The master agent (`backend/agents/master_agent.py`) follows this order:

1. Run all 50 agents via `asyncio.gather(..., return_exceptions=True)`.
2. Drop any agent that raised; log the error but do not fail the whole run.
3. Build a unified spatial map keyed by `(x, y)` cells of 6 inches.
4. Apply rules in jurisdiction order: NFPA → California → LAMC. Each layer
   can override the previous.
5. Place sprinklers using the heuristic in `_placement.py`.
6. Run the post-placement validator (rules with `ai_impact: "validator"`).
7. Return the `SprinklerPlacement` result.

## Failure modes you must handle

- **Agent timeout**: each agent has a 1.5 second budget. Past that, the master
  marks the agent as `TIMED_OUT` and proceeds without its findings.
- **Conflicting findings**: e.g., one agent says "wall here," another says
  "open archway here." The master agent's `_resolve_conflicts()` method uses
  the higher-confidence finding and lowers the loser's confidence to log it.
- **No findings at all**: if every agent returns empty findings, the master
  raises `BlankBlueprintError`. The frontend renders a friendly message.

## Performance budget

| Stage | Target | Hard limit |
|-------|--------|------------|
| Blueprint parsing | 200 ms | 500 ms |
| All 50 agents (parallel) | 1.5 s | 2.0 s |
| Master agent reduction | 300 ms | 800 ms |
| Validator pass | 200 ms | 500 ms |
| **Total** | **2.2 s** | **5.0 s** |

If you blow the budget, profile with `py-spy` before optimizing — most agents
are I/O-bound waiting on the CNN, not CPU-bound.
