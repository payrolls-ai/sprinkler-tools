# 🔥 Sprinkler Tools

> AI-driven fire sprinkler placement for Los Angeles jurisdiction.
> CNN (Convolutional Neural Network) + 50-agent specialist architecture.

This repo is the **Phase 5 proof-of-concept** for `sprinkler-tools`: an
end-to-end demo showing how 50 specialist AI agents, organized into 6 teams,
collaborate to place fire sprinklers on an architectural floor plan while
honoring NFPA 13, California amendments, and Los Angeles Municipal Code.

---

## What's in this repo

```
sprinkler-tools/
├── CLAUDE.md                    ← project rule book (read this first)
├── README.md                    ← you are here
├── start.bat                    ← Windows: install + run backend
├── start.sh                     ← Mac/Linux: install + run backend
│
├── .claude/
│   ├── skills/                  ← skill files for AI assistants
│   │   ├── agent-orchestration/
│   │   ├── nfpa-rule-encoder/
│   │   └── blueprint-parser/
│   └── hooks/
│       ├── pre-commit           ← validates rule JSON + agent registry
│       └── install.sh           ← links the hook into .git/hooks
│
├── backend/                     ← Python · FastAPI
│   ├── app.py                   ← REST endpoints
│   ├── agents/
│   │   ├── base_agent.py        ← BaseAgent contract
│   │   ├── all_agents.py        ← all 50 specialist agents
│   │   ├── master_agent.py      ← orchestrates the 50 + applies rules
│   │   └── _demo_data.py        ← bundled sample blueprint
│   ├── rules/
│   │   ├── nfpa13_rules.json
│   │   ├── california_amendments.json
│   │   └── lamc_amendments.json
│   └── requirements.txt
│
├── frontend/                    ← single-file HTML demo
│   ├── index.html               ← open this directly in any browser
│   ├── styles.css
│   └── app.js                   ← falls back to offline mode if backend is down
│
└── docs/
    └── demo-instructions.md     ← script for showing the boss
```

---

## Quick start

### Option A — Just show the boss the visual demo (no Python needed)

1. Double-click `frontend/index.html`.
2. Click **Run AI Analysis**.
3. The demo runs in offline mode (status shows "Offline mode") — every
   sprinkler position and every code-compliance result is the same one the
   live backend produces, just pre-computed.

### Option B — Full live stack (backend + frontend)

**Windows:**
```
start.bat
```

**Mac/Linux:**
```
./start.sh
```

Either script:
1. Creates a Python virtual environment in `backend/.venv`
2. Installs FastAPI / uvicorn / pydantic
3. Starts the API on `http://localhost:8000`

Then open `frontend/index.html` — the status indicator turns green and shows
"Connected to API". The frontend will now call the live FastAPI backend.

---

## How the 50 agents are organized

| # | Team | Agents | Job |
|---|------|--------|-----|
| 1 | Structure | 1–10 | Walls, columns, beams, ceiling heights |
| 2 | Openings | 11–18 | Doors, windows, atriums, fire-rated openings |
| 3 | Obstructions | 19–28 | HVAC ducts, deep beams, light fixtures |
| 4 | Classifiers | 29–36 | Room types, hazard classes, exempt spaces |
| 5 | MEP | 37–43 | Risers, electrical/mechanical rooms |
| 6 | Code Math | 44–50 | Spacing, coverage, draft stops, water curtains |

The **Master Placement Agent** (`backend/agents/master_agent.py`) consumes
all 50 reports and produces the final sprinkler layout, applying rules in
this priority order:

1. **LAMC § 94.2010** (Los Angeles Municipal Code) — wins all conflicts
2. **California amendments** — middle layer
3. **NFPA 13 (2025)** — base standard

---

## Demo specs

The bundled demo blueprint (`DEMO-LA-001`) is a **60 ft × 40 ft** commercial
floor plan with:

- 8 rooms (open offices, conference, kitchen, bathroom, electrical, stair,
  warehouse)
- 2 HVAC ducts triggering the NFPA-005 obstruction rule
- 1 smoke barrier opening triggering the LAMC water-curtain rule (LA-003)
- 1 exempt stair (LA exempt space)
- 1 electrical room (no water required)

**Output (live and offline modes match):**
- 16 sprinklers placed
- 50 agents OK
- 85 findings reported
- All applicable code rules: pass

End-to-end runtime: ~100 ms in live mode; ~1.1 s in offline mode (animation
delay added on purpose so the boss can see the work happening).

---

## Production roadmap

This is the Phase 5 demo. The roadmap continues:

- **Phase 6** — train the CNN backbone on the 30+ drawing pairs being collected
- **Phase 7** — replace the mock `_detect()` methods with real CNN inference
- **Phase 8** — placement engine accounts for obstruction findings
  (currently only detects them)
- **Phase 9** — AutoCAD plug-in so designers can run analysis from inside their tool
- **Phase 10** — production deployment + customer pilots

---

## Setup git hooks (one-time, optional)

```
bash .claude/hooks/install.sh
```

This links the `pre-commit` hook into `.git/hooks/`. The hook validates rule
JSON, the agent registry, and forbidden patterns before every commit.

---

Owner: Meatbot · Repo: `payrolls-ai/sprinkler-tools` · Jurisdiction: Los Angeles
