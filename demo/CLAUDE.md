# CLAUDE.md — Sprinkler Tools Project Guide

> This file is the **source of truth** for any AI assistant (Claude, Cursor, etc.)
> working on this codebase. Read it first. It overrides assumptions from training data.

---

## 1. What this project is

**Sprinkler Tools** is an AI system that automatically places fire sprinkler heads
on architectural floor plans for buildings in **Los Angeles jurisdiction**.

**Compliance stack** (top layer wins on conflicts):
1. **LAMC § 94.2010.0** — Los Angeles Municipal Code, local amendments
2. **California state amendments** — seismic bracing, state-specific overrides
3. **NFPA 13 (2025 edition)** — National Fire Protection Association base standard

---

## 2. The core architectural decision (read this carefully)

We **rejected** the GAN (Generative Adversarial Network) / pix2pixHD approach
documented in earlier project notes.

We are using a **CNN (Convolutional Neural Network) + 50 Specialist Agents**
hybrid architecture. The reasons:

| Concern | GAN approach | Agent approach |
|--------|---------------|----------------|
| Explainability | Black box | Each agent reports findings |
| Obstruction handling | Hopes it learned it | Agents 19-28 explicitly hunt them |
| Code compliance | Separate validator pass | Built into each agent |
| Generalization to new layouts | Weak | Strong (agents are rule-driven) |
| Training data needed | 100-400 image pairs | Per-class detection annotations (more efficient) |

**Do not propose reverting to GAN/pix2pixHD without strong evidence.** That
decision has been made and is recorded in `docs/decisions/ADR-001-cnn-agents.md`.

---

## 3. The 50-agent system

Agents are organized into 6 teams. Each team lives in its own Python module
under `backend/agents/`. Every agent inherits from `BaseAgent` and returns a
standardized `AgentReport`.

| Team | Agents | Module | Responsibility |
|------|--------|--------|----------------|
| Structure | 1-10 | `structure_agents.py` | Walls, columns, beams, ceiling heights |
| Openings | 11-18 | `opening_agents.py` | Doors, windows, atriums, fire-rated openings |
| Obstructions | 19-28 | `obstruction_agents.py` | HVAC, deep beams, light fixtures, racks |
| Classifiers | 29-36 | `classifier_agents.py` | Room types, hazard classes, exempt spaces |
| MEP | 37-43 | `mep_agents.py` | Risers, existing pipes, electrical/mechanical rooms |
| Code Math | 44-50 | `code_math_agents.py` | Spacing, coverage, draft stops, water curtains |

The **Master Placement Agent** (`master_agent.py`) consumes all 50 reports and
produces the final sprinkler placement.

---

## 4. Code conventions

### Python (backend)
- **Python 3.10+** required (uses `match` / `case` and modern type hints)
- **Type hints everywhere.** Use `from __future__ import annotations` at the top of every file.
- **Pydantic v2** for all data models. No raw dicts crossing module boundaries.
- **Black** for formatting (line length 100). **Ruff** for linting.
- **No print statements.** Use `logging.getLogger(__name__)`.
- Async by default in route handlers; sync is fine inside agents.

### JavaScript (frontend)
- **Vanilla JS** in the demo (no build step — boss must be able to open `index.html` directly).
- A real production version would use React + Vite, but the demo is intentionally zero-deps.
- Use `data-*` attributes for state, not classes.
- All animations via CSS transitions or Web Animations API (no jQuery).

### Rules JSON
- Every rule object must include: `rule_id`, `source`, `ai_impact`, `condition`, `requirement`.
- `ai_impact` field is required and must be one of: `"placement"`, `"validator"`, `"both"`.
  - `placement`: the agent uses this rule when deciding where to put sprinklers
  - `validator`: only the post-placement validator checks this rule
  - `both`: used in both phases
- Rule IDs are prefixed by source: `NFPA-###`, `CA-###`, `LA-###`.

---

## 5. How an analysis run works (request flow)

```
User uploads blueprint (PDF or DXF)
        ↓
backend/app.py  →  POST /api/analyze
        ↓
Blueprint Parser extracts layers and pixel data
        ↓
50 agents run in parallel (asyncio.gather)
        ↓
Each agent returns an AgentReport(findings, confidence, layer)
        ↓
Master Placement Agent consumes all 50 reports
        ↓
Master Agent calls the rule engine (3-layer hierarchy)
        ↓
Final SprinklerPlacement object returned to frontend
        ↓
Frontend renders red dots over the blueprint
```

A full analysis must complete in **under 5 seconds** for a typical floor plan
(target: 2 seconds). Parallelism is mandatory for the agents.

---

## 6. Demo vs production mode

The current code ships in **DEMO mode** (set via `SPRINKLER_MODE=demo` env var).

In demo mode:
- Agents return **deterministic mock findings** based on the bundled sample blueprint
- No actual CNN model is loaded
- Latency is artificially staggered to make the agent activity visible in the UI

In production mode (`SPRINKLER_MODE=prod`):
- Agents call the real CNN detector (`backend/models/cnn_detector.py`)
- The CNN model file must be present at `backend/models/weights/sprinkler_cnn.pt`
- Without that file, the server fails fast on startup

**Do not delete the demo path.** It is what we show to non-technical stakeholders.

---

## 7. Things to never do

- **Never** hardcode jurisdiction-specific rules inside agent code. All such rules
  live in `backend/rules/*.json` and are loaded by the rule engine.
- **Never** combine agent teams into a single mega-class. The team boundaries are
  intentional and reflect the real-world expertise split.
- **Never** swallow exceptions inside an agent. Let them propagate; the master
  agent has retry and partial-failure handling.
- **Never** edit the three `*_amendments.json` files without bumping the
  `code_edition` field and adding an entry to `docs/changelog/rules.md`.

---

## 8. Where to look first

| If you're working on... | Read this first |
|--------------------------|-----------------|
| Adding/changing rules | `.claude/skills/nfpa-rule-encoder/SKILL.md` |
| Adding/modifying an agent | `.claude/skills/agent-orchestration/SKILL.md` |
| Blueprint input parsing | `.claude/skills/blueprint-parser/SKILL.md` |
| Frontend changes | `frontend/README.md` |
| Deployment | `docs/deployment.md` |

---

## 9. Project status

- **Phase 1-3:** ✅ Complete
- **Phase 4 (data collection):** 🟡 In progress — 7 of 30 minimum drawing pairs collected
- **Phase 5 (proof of concept):** 🟢 **This demo is the proof of concept.**
- **Phases 6-10:** ⚪ Not started

Owner: Meatbot · Repo: `payrolls-ai/sprinkler-tools` · Jurisdiction: Los Angeles
