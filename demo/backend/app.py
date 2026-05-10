"""
backend/app.py

FastAPI server for the sprinkler-tools demo.

Endpoints:
  GET  /                  — health check
  GET  /api/blueprint     — return the demo blueprint (so the frontend can render it)
  POST /api/analyze       — run all 50 agents + master agent, return placement
  GET  /api/agents        — list all 50 agents (for the UI roster panel)
  GET  /api/rules         — return the loaded rule set

Run:
    cd backend
    uvicorn app:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agents import ALL_AGENTS, MasterPlacementAgent
from agents._demo_data import get_demo_blueprint
from agents.master_agent import load_rules

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
)
logger = logging.getLogger("sprinkler.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting sprinkler-tools demo API")
    logger.info("loaded %d agents", len(ALL_AGENTS))
    rules = load_rules()
    logger.info("loaded rules: NFPA=%d, CA=%d, LAMC=%d",
                len(rules["NFPA13"]), len(rules["California"]), len(rules["LAMC"]))
    yield
    logger.info("shutting down")


app = FastAPI(
    title="Sprinkler Tools API",
    version="0.1.0",
    description="CNN + 50-agent fire sprinkler placement (Los Angeles jurisdiction)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def health() -> dict:
    return {"status": "ok", "service": "sprinkler-tools", "mode": "demo"}


@app.get("/api/blueprint")
async def get_blueprint() -> dict:
    """Return the demo blueprint so the frontend can render the same scene."""
    bp = get_demo_blueprint()
    return bp.model_dump()


@app.get("/api/agents")
async def list_agents() -> list[dict]:
    return [
        {"agent_id": a.agent_id, "name": a.name, "team": a.team.value}
        for a in ALL_AGENTS
    ]


@app.get("/api/rules")
async def get_rules() -> dict:
    rules = load_rules()
    return {
        "layers": [
            {"name": "NFPA 13 (2025)", "count": len(rules["NFPA13"]), "rules": rules["NFPA13"]},
            {"name": "California amendments", "count": len(rules["California"]),
             "rules": rules["California"]},
            {"name": "LAMC § 94.2010", "count": len(rules["LAMC"]),
             "rules": rules["LAMC"]},
        ],
    }


@app.post("/api/analyze")
async def analyze() -> JSONResponse:
    """Run the 50 agents + master agent on the demo blueprint."""
    blueprint = get_demo_blueprint()
    master = MasterPlacementAgent()
    placement = await master.run(blueprint)
    return JSONResponse(content=placement.model_dump(mode="json"))
