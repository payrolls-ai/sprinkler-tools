"""
backend/agents/base_agent.py

Base class and shared types for all 50 specialist agents.
Every agent inherits BaseAgent and returns an AgentReport.
"""
from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Shared data types
# ─────────────────────────────────────────────────────────────────────────────

class Team(str, Enum):
    STRUCTURE      = "structure"
    OPENINGS       = "openings"
    OBSTRUCTIONS   = "obstructions"
    CLASSIFIERS    = "classifiers"
    MEP            = "mep"
    CODE_MATH      = "code_math"


class BoundingBox(BaseModel):
    """Pixel-space rectangle on the blueprint."""
    x: float
    y: float
    width: float
    height: float


class Finding(BaseModel):
    """A single thing an agent detected on the blueprint."""
    label: str                      # e.g., "hvac_duct", "exterior_wall"
    bbox: BoundingBox | None = None
    point: tuple[float, float] | None = None     # for point-like findings
    attributes: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)


class AgentStatus(str, Enum):
    OK         = "ok"
    TIMED_OUT  = "timed_out"
    FAILED     = "failed"
    SKIPPED    = "skipped"


class AgentReport(BaseModel):
    """Standardized output every agent must return."""
    agent_id: int
    agent_name: str
    team: Team
    status: AgentStatus = AgentStatus.OK
    findings: list[Finding] = Field(default_factory=list)
    elapsed_ms: float = 0.0
    error: str | None = None

    @property
    def finding_count(self) -> int:
        return len(self.findings)


# ─────────────────────────────────────────────────────────────────────────────
# The Blueprint object — what every agent receives
# ─────────────────────────────────────────────────────────────────────────────

class Blueprint(BaseModel):
    """Canonical input shared by all 50 agents."""
    blueprint_id: str
    width_ft: float
    height_ft: float
    scale_ft_per_px: float = 1.0   # 1 ft = 1 pixel for the demo
    rooms: list[dict[str, Any]] = Field(default_factory=list)
    raw_features: dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}


# ─────────────────────────────────────────────────────────────────────────────
# BaseAgent — every specialist agent inherits this
# ─────────────────────────────────────────────────────────────────────────────

class BaseAgent(ABC):
    """
    Every agent has:
      - A unique agent_id (1-50)
      - A team (one of 6)
      - A name (human-readable)
      - An async analyze() method that returns an AgentReport

    The base class handles timing, error capture, and the timeout budget.
    """

    agent_id: int = 0
    team: Team = Team.STRUCTURE
    name: str = "Unnamed Agent"
    timeout_seconds: float = 1.5    # NFPA hard budget per agent

    @abstractmethod
    async def _detect(self, blueprint: Blueprint) -> list[Finding]:
        """Subclasses implement detection logic here."""
        ...

    async def analyze(self, blueprint: Blueprint) -> AgentReport:
        """Run detection with timing and error handling."""
        start = time.perf_counter()
        report = AgentReport(
            agent_id=self.agent_id,
            agent_name=self.name,
            team=self.team,
        )
        try:
            findings = await asyncio.wait_for(
                self._detect(blueprint),
                timeout=self.timeout_seconds,
            )
            report.findings = findings
        except asyncio.TimeoutError:
            report.status = AgentStatus.TIMED_OUT
            report.error = f"Agent {self.agent_id} exceeded {self.timeout_seconds}s budget"
            logger.warning(report.error)
        except Exception as exc:  # noqa: BLE001
            report.status = AgentStatus.FAILED
            report.error = f"{type(exc).__name__}: {exc}"
            logger.exception("Agent %d failed", self.agent_id)
        finally:
            report.elapsed_ms = (time.perf_counter() - start) * 1000

        return report
