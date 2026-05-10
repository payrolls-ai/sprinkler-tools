"""
backend/agents/all_agents.py

The full roster of 50 specialist agents, organized into 6 teams.

In DEMO mode (SPRINKLER_MODE=demo, the default), each agent returns
deterministic mock findings from the bundled sample blueprint. In PROD mode
each agent would call the real CNN detector with an agent-specific head.

Splitting all 50 into separate files would be cleaner; we keep them in one
file here so the demo is easy to read end-to-end. In production we'd split
by team into structure_agents.py / opening_agents.py / etc.
"""
from __future__ import annotations

import asyncio
import random
from typing import Any

from .base_agent import BaseAgent, Blueprint, BoundingBox, Finding, Team


# ─────────────────────────────────────────────────────────────────────────────
# Helper: simulate inference latency so the UI can show the work happening
# ─────────────────────────────────────────────────────────────────────────────

async def _simulate_inference(agent_id: int, base_ms: float = 40) -> None:
    """Stagger work across agents so the frontend sees a realistic ripple."""
    # Deterministic but spread-out delay: agent N gets between 20 and 120 ms
    rng = random.Random(agent_id)
    await asyncio.sleep((base_ms + rng.randint(0, 60)) / 1000)


def _features(bp: Blueprint, key: str, default: Any = None) -> Any:
    return bp.raw_features.get(key, default if default is not None else [])


# ═════════════════════════════════════════════════════════════════════════════
# TEAM 1 — STRUCTURE (Agents 1-10)
# ═════════════════════════════════════════════════════════════════════════════

class ExteriorWallAgent(BaseAgent):
    agent_id = 1
    team = Team.STRUCTURE
    name = "Exterior Wall Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="exterior_wall", bbox=BoundingBox(**w), confidence=0.97)
                for w in _features(bp, "exterior_walls")]


class PartitionWallAgent(BaseAgent):
    agent_id = 2
    team = Team.STRUCTURE
    name = "Partition Wall Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="partition_wall", bbox=BoundingBox(**w), confidence=0.93)
                for w in _features(bp, "partition_walls")]


class ColumnAgent(BaseAgent):
    agent_id = 3
    team = Team.STRUCTURE
    name = "Structural Column Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="column", point=tuple(p), confidence=0.95,
                        attributes={"width_in": 14})
                for p in _features(bp, "columns")]


class BeamAgent(BaseAgent):
    agent_id = 4
    team = Team.STRUCTURE
    name = "Overhead Beam Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="beam", bbox=BoundingBox(**b), confidence=0.88,
                        attributes={"depth_in": b.get("depth_in", 12)})
                for b in _features(bp, "beams")]


class CeilingHeightAgent(BaseAgent):
    agent_id = 5
    team = Team.STRUCTURE
    name = "Ceiling Height Reader"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="ceiling_height", attributes={"height_ft": h},
                        confidence=0.99) for h in _features(bp, "ceiling_heights", [])]


class LoadBearingAgent(BaseAgent):
    agent_id = 6
    team = Team.STRUCTURE
    name = "Load-Bearing Wall Identifier"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="load_bearing", bbox=BoundingBox(**w), confidence=0.86)
                for w in _features(bp, "exterior_walls")]   # all exterior walls assumed bearing in demo


class ShearWallAgent(BaseAgent):
    agent_id = 7
    team = Team.STRUCTURE
    name = "Shear Wall Detector (Seismic)"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="shear_wall", bbox=BoundingBox(**w), confidence=0.82,
                        attributes={"jurisdiction": "California"})
                for w in _features(bp, "shear_walls", [])]


class MaterialAgent(BaseAgent):
    agent_id = 8
    team = Team.STRUCTURE
    name = "Wall Material Classifier"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="wall_material",
                        attributes={"material": "concrete", "regions": len(_features(bp, "exterior_walls"))},
                        confidence=0.84)]


class SlabEdgeAgent(BaseAgent):
    agent_id = 9
    team = Team.STRUCTURE
    name = "Slab Edge Finder"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="slab_edge", confidence=0.91,
                        attributes={"perimeter_ft": 2 * (bp.width_ft + bp.height_ft)})]


class FoundationAgent(BaseAgent):
    agent_id = 10
    team = Team.STRUCTURE
    name = "Foundation Element Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []   # foundation rarely visible on a typical floor plan


# ═════════════════════════════════════════════════════════════════════════════
# TEAM 2 — OPENINGS (Agents 11-18)
# ═════════════════════════════════════════════════════════════════════════════

class DoorAgent(BaseAgent):
    agent_id = 11
    team = Team.OPENINGS
    name = "Door Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="door", point=tuple(p), confidence=0.94)
                for p in _features(bp, "doors")]


class WindowAgent(BaseAgent):
    agent_id = 12
    team = Team.OPENINGS
    name = "Window Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="window", bbox=BoundingBox(**w), confidence=0.92)
                for w in _features(bp, "windows", [])]


class ArchwayAgent(BaseAgent):
    agent_id = 13
    team = Team.OPENINGS
    name = "Archway / Open Opening Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="archway", point=tuple(p), confidence=0.78)
                for p in _features(bp, "archways", [])]


class SkylightAgent(BaseAgent):
    agent_id = 14
    team = Team.OPENINGS
    name = "Skylight Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class AtriumAgent(BaseAgent):
    agent_id = 15
    team = Team.OPENINGS
    name = "Atrium Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class CurtainWallAgent(BaseAgent):
    agent_id = 16
    team = Team.OPENINGS
    name = "Curtain Wall Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class FireRatedDoorAgent(BaseAgent):
    agent_id = 17
    team = Team.OPENINGS
    name = "Fire-Rated Door Identifier"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="fire_rated_door", point=tuple(p), confidence=0.81,
                        attributes={"rating_minutes": 60})
                for p in _features(bp, "fire_rated_doors", [])]


class SmokeBarrierOpeningAgent(BaseAgent):
    agent_id = 18
    team = Team.OPENINGS
    name = "Smoke Barrier Opening (LAMC water-curtain trigger)"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        # This is what triggers the LAMC water curtain rule
        return [Finding(label="smoke_barrier_opening", bbox=BoundingBox(**o), confidence=0.87,
                        attributes={"requires_water_curtain": True})
                for o in _features(bp, "smoke_barrier_openings", [])]


# ═════════════════════════════════════════════════════════════════════════════
# TEAM 3 — OBSTRUCTIONS (Agents 19-28) ← the most important team for placement
# ═════════════════════════════════════════════════════════════════════════════

class HVACDuctAgent(BaseAgent):
    agent_id = 19
    team = Team.OBSTRUCTIONS
    name = "HVAC Duct Detector (>4 in width)"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="hvac_duct", bbox=BoundingBox(**d), confidence=0.92,
                        attributes={"width_in": d.get("width_in", 18),
                                    "triggers_nfpa_obstruction_rule": True})
                for d in _features(bp, "hvac_ducts")]


class DeepBeamAgent(BaseAgent):
    agent_id = 20
    team = Team.OBSTRUCTIONS
    name = "Deep Beam Pocket Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        deep = [b for b in _features(bp, "beams") if b.get("depth_in", 0) >= 12]
        return [Finding(label="deep_beam", bbox=BoundingBox(**b), confidence=0.88,
                        attributes={"depth_in": b["depth_in"]}) for b in deep]


class LightFixtureAgent(BaseAgent):
    agent_id = 21
    team = Team.OBSTRUCTIONS
    name = "Light Fixture Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="light_fixture", point=tuple(p), confidence=0.79)
                for p in _features(bp, "light_fixtures", [])]


class PipeBundleAgent(BaseAgent):
    agent_id = 22
    team = Team.OBSTRUCTIONS
    name = "Pipe / Conduit Bundle Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class CableTrayAgent(BaseAgent):
    agent_id = 23
    team = Team.OBSTRUCTIONS
    name = "Cable Tray Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class StorageRackAgent(BaseAgent):
    agent_id = 24
    team = Team.OBSTRUCTIONS
    name = "Storage Rack Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class MezzanineEdgeAgent(BaseAgent):
    agent_id = 25
    team = Team.OBSTRUCTIONS
    name = "Mezzanine Edge Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class DroppedCeilingAgent(BaseAgent):
    agent_id = 26
    team = Team.OBSTRUCTIONS
    name = "Dropped/Suspended Ceiling Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class SoffitAgent(BaseAgent):
    agent_id = 27
    team = Team.OBSTRUCTIONS
    name = "Soffit Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class EquipmentAgent(BaseAgent):
    agent_id = 28
    team = Team.OBSTRUCTIONS
    name = "Floor Equipment Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


# ═════════════════════════════════════════════════════════════════════════════
# TEAM 4 — CLASSIFIERS (Agents 29-36)
# ═════════════════════════════════════════════════════════════════════════════

class RoomTypeAgent(BaseAgent):
    agent_id = 29
    team = Team.CLASSIFIERS
    name = "Room Type Classifier"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="room_type", bbox=BoundingBox(**r["bbox"]),
                        attributes={"room_id": r["id"], "type": r["type"]},
                        confidence=0.90) for r in bp.rooms]


class HazardClassAgent(BaseAgent):
    agent_id = 30
    team = Team.CLASSIFIERS
    name = "Hazard Class Assigner"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="hazard_class", bbox=BoundingBox(**r["bbox"]),
                        attributes={"room_id": r["id"], "hazard_class": r["hazard"]},
                        confidence=0.93) for r in bp.rooms]


class WetAreaAgent(BaseAgent):
    agent_id = 31
    team = Team.CLASSIFIERS
    name = "Wet Area Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        wet = [r for r in bp.rooms if r["type"] in ("bathroom", "kitchen")]
        return [Finding(label="wet_area", bbox=BoundingBox(**r["bbox"]),
                        attributes={"room_id": r["id"]}, confidence=0.96)
                for r in wet]


class HighCeilingAgent(BaseAgent):
    agent_id = 32
    team = Team.CLASSIFIERS
    name = "High Ceiling Detector (>10 ft)"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        high = [h for h in _features(bp, "ceiling_heights", []) if h > 10]
        return [Finding(label="high_ceiling", attributes={"height_ft": h}, confidence=0.89)
                for h in high]


class ConcealedSpaceAgent(BaseAgent):
    agent_id = 33
    team = Team.CLASSIFIERS
    name = "Concealed Space Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class AtticAgent(BaseAgent):
    agent_id = 34
    team = Team.CLASSIFIERS
    name = "Attic Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class CrawlSpaceAgent(BaseAgent):
    agent_id = 35
    team = Team.CLASSIFIERS
    name = "Crawl Space Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class ExemptSpaceAgent(BaseAgent):
    agent_id = 36
    team = Team.CLASSIFIERS
    name = "Exempt Space Marker (stairs, shafts, closets)"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        exempt = [r for r in bp.rooms if r["type"] in ("stair", "elevator_shaft", "closet")]
        return [Finding(label="exempt_space", bbox=BoundingBox(**r["bbox"]),
                        attributes={"room_id": r["id"], "type": r["type"]},
                        confidence=0.94) for r in exempt]


# ═════════════════════════════════════════════════════════════════════════════
# TEAM 5 — MEP (Mechanical Electrical Plumbing) (Agents 37-43)
# ═════════════════════════════════════════════════════════════════════════════

class WaterRiserAgent(BaseAgent):
    agent_id = 37
    team = Team.MEP
    name = "Main Water Riser Locator"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        riser = _features(bp, "water_riser")
        if riser:
            return [Finding(label="water_riser", point=tuple(riser), confidence=0.97)]
        return []


class ExistingPipeAgent(BaseAgent):
    agent_id = 38
    team = Team.MEP
    name = "Existing Pipe Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class ElectricalRoomAgent(BaseAgent):
    agent_id = 39
    team = Team.MEP
    name = "Electrical Room Identifier"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        elec = [r for r in bp.rooms if r["type"] == "electrical"]
        return [Finding(label="electrical_room", bbox=BoundingBox(**r["bbox"]),
                        attributes={"room_id": r["id"], "no_water_required": True},
                        confidence=0.94) for r in elec]


class MechanicalRoomAgent(BaseAgent):
    agent_id = 40
    team = Team.MEP
    name = "Mechanical Room Identifier"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        mech = [r for r in bp.rooms if r["type"] == "mechanical"]
        return [Finding(label="mechanical_room", bbox=BoundingBox(**r["bbox"]),
                        attributes={"room_id": r["id"]}, confidence=0.91) for r in mech]


class PlumbingFixtureAgent(BaseAgent):
    agent_id = 41
    team = Team.MEP
    name = "Plumbing Fixture Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class GasEquipmentAgent(BaseAgent):
    agent_id = 42
    team = Team.MEP
    name = "Gas Equipment Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return []


class ElevatorShaftAgent(BaseAgent):
    agent_id = 43
    team = Team.MEP
    name = "Elevator Shaft Detector"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        elev = [r for r in bp.rooms if r["type"] == "elevator_shaft"]
        return [Finding(label="elevator_shaft", bbox=BoundingBox(**r["bbox"]),
                        attributes={"room_id": r["id"]}, confidence=0.93) for r in elev]


# ═════════════════════════════════════════════════════════════════════════════
# TEAM 6 — CODE MATH (Agents 44-50)
# ═════════════════════════════════════════════════════════════════════════════

class RoomAreaAgent(BaseAgent):
    agent_id = 44
    team = Team.CODE_MATH
    name = "Room Area Calculator"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        out: list[Finding] = []
        for r in bp.rooms:
            area = r["bbox"]["width"] * r["bbox"]["height"]
            out.append(Finding(label="room_area", confidence=0.99,
                               attributes={"room_id": r["id"], "area_sqft": round(area, 1)}))
        return out


class SpacingAgent(BaseAgent):
    agent_id = 45
    team = Team.CODE_MATH
    name = "Sprinkler Spacing Checker"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        # max spacing depends on hazard class, looked up by master agent
        return [Finding(label="spacing_constraint", confidence=0.99,
                        attributes={"max_ft_light": 15, "max_ft_ordinary": 15,
                                    "max_ft_extra": 12, "min_ft_any": 6})]


class CoverageAgent(BaseAgent):
    agent_id = 46
    team = Team.CODE_MATH
    name = "Coverage Zone Calculator"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="coverage_constraint", confidence=0.99,
                        attributes={"max_sqft_light": 225, "max_sqft_ordinary": 130,
                                    "max_sqft_extra": 100})]


class WallDistanceAgent(BaseAgent):
    agent_id = 47
    team = Team.CODE_MATH
    name = "Sprinkler-to-Wall Distance Checker"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="wall_distance_constraint", confidence=0.99,
                        attributes={"max_ft_light": 7.5, "max_ft_ordinary": 7.5,
                                    "max_ft_extra": 6})]


class ObstructionDistanceAgent(BaseAgent):
    agent_id = 48
    team = Team.CODE_MATH
    name = "Sprinkler-to-Obstruction Distance Checker (3× rule)"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="obstruction_distance_rule", confidence=0.99,
                        attributes={"formula": "min_distance = 3 * obstruction_width",
                                    "cap_in": 24})]


class DraftStopAgent(BaseAgent):
    agent_id = 49
    team = Team.CODE_MATH
    name = "Draft Stop Detector (LAMC water-curtain prerequisite)"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        return [Finding(label="draft_stop", bbox=BoundingBox(**d), confidence=0.85,
                        attributes={"depth_in": 18, "material": "noncombustible"})
                for d in _features(bp, "draft_stops", [])]


class WaterCurtainZoneAgent(BaseAgent):
    agent_id = 50
    team = Team.CODE_MATH
    name = "LA Water Curtain Zone Identifier"
    async def _detect(self, bp: Blueprint) -> list[Finding]:
        await _simulate_inference(self.agent_id)
        # Triggered by LA-003 when a smoke barrier opening + draft stop coexist
        zones = _features(bp, "water_curtain_zones", [])
        return [Finding(label="water_curtain_zone", bbox=BoundingBox(**z), confidence=0.86,
                        attributes={"max_spacing_ft": 6,
                                    "rule_triggered": "LA-003"}) for z in zones]


# ─────────────────────────────────────────────────────────────────────────────
# Registry (used by master_agent.py and the pre-commit hook)
# ─────────────────────────────────────────────────────────────────────────────

ALL_AGENTS: list[BaseAgent] = [
    # Structure
    ExteriorWallAgent(), PartitionWallAgent(), ColumnAgent(), BeamAgent(),
    CeilingHeightAgent(), LoadBearingAgent(), ShearWallAgent(), MaterialAgent(),
    SlabEdgeAgent(), FoundationAgent(),
    # Openings
    DoorAgent(), WindowAgent(), ArchwayAgent(), SkylightAgent(),
    AtriumAgent(), CurtainWallAgent(), FireRatedDoorAgent(), SmokeBarrierOpeningAgent(),
    # Obstructions
    HVACDuctAgent(), DeepBeamAgent(), LightFixtureAgent(), PipeBundleAgent(),
    CableTrayAgent(), StorageRackAgent(), MezzanineEdgeAgent(),
    DroppedCeilingAgent(), SoffitAgent(), EquipmentAgent(),
    # Classifiers
    RoomTypeAgent(), HazardClassAgent(), WetAreaAgent(), HighCeilingAgent(),
    ConcealedSpaceAgent(), AtticAgent(), CrawlSpaceAgent(), ExemptSpaceAgent(),
    # MEP
    WaterRiserAgent(), ExistingPipeAgent(), ElectricalRoomAgent(),
    MechanicalRoomAgent(), PlumbingFixtureAgent(), GasEquipmentAgent(),
    ElevatorShaftAgent(),
    # Code Math
    RoomAreaAgent(), SpacingAgent(), CoverageAgent(), WallDistanceAgent(),
    ObstructionDistanceAgent(), DraftStopAgent(), WaterCurtainZoneAgent(),
]

assert len(ALL_AGENTS) == 50, f"Expected 50 agents, got {len(ALL_AGENTS)}"
assert len({a.agent_id for a in ALL_AGENTS}) == 50, "Duplicate agent IDs"
