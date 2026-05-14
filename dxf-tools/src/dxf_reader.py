"""
src/dxf_reader.py

Reads an architect's DXF file and produces a structured Blueprint object
the 50 specialist agents can consume.

The reader does five things:
  1. Open the DXF file (tolerant of slightly malformed files)
  2. Inventory all layers (with AIA classification)
  3. Walk every entity, group by layer
  4. Detect units and scale
  5. Hand back a Blueprint dataclass with all findings

What this reader is NOT:
  - It does not "find sprinklers" itself. That's the agents' job.
  - It does not run AI. It just structures the geometric/text data so
    agents can reason about it.
  - It does not write — see dxf_writer.py for that.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import ezdxf
from ezdxf import recover
from ezdxf.document import Drawing

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data types — the canonical Blueprint the agents consume
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EntityRecord:
    """One geometric entity from the DXF, normalized to our schema."""
    dxf_type: str                  # CIRCLE, LWPOLYLINE, LINE, TEXT, ARC, etc.
    layer: str
    handle: str                    # DXF entity handle (unique within file)
    # Geometric properties (filled where applicable)
    center: tuple[float, float] | None = None
    radius: float | None = None
    start: tuple[float, float] | None = None
    end: tuple[float, float] | None = None
    points: list[tuple[float, float]] = field(default_factory=list)
    text: str | None = None
    height: float | None = None    # text height (used as visual scale hint)
    # Additional attributes from the DXF
    color: int | None = None
    linetype: str | None = None
    # The original entity for advanced agents that need full access
    raw_attribs: dict[str, Any] = field(default_factory=dict)


@dataclass
class LayerInfo:
    """Metadata about one CAD layer."""
    name: str
    aia_category: str              # ARCHITECTURAL, FIRE_PROTECTION, etc.
    color: int
    description: str = ""
    entity_count: int = 0
    is_visible: bool = True
    is_locked: bool = False


@dataclass
class Blueprint:
    """The canonical input every agent receives."""
    source_file: str
    dxf_version: str
    units: str                     # 'inches', 'feet', 'millimeters', etc.
    scale_factor: float            # multiplier to convert drawing units → feet
    width_drawing_units: float
    height_drawing_units: float
    width_ft: float
    height_ft: float
    layers: dict[str, LayerInfo] = field(default_factory=dict)
    entities_by_layer: dict[str, list[EntityRecord]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_entities(self) -> int:
        return sum(len(v) for v in self.entities_by_layer.values())

    def layers_in_category(self, category: str) -> list[str]:
        """Return layer names that fall in a given AIA category."""
        return [name for name, info in self.layers.items()
                if info.aia_category == category]

    def entities_on_layers(self, layer_names: list[str]) -> list[EntityRecord]:
        """Flatten all entities across multiple layers."""
        out: list[EntityRecord] = []
        for name in layer_names:
            out.extend(self.entities_by_layer.get(name, []))
        return out


# ─────────────────────────────────────────────────────────────────────────────
# AIA (American Institute of Architects) layer classification
# ─────────────────────────────────────────────────────────────────────────────

# Maps the first letter of an AIA layer name to a category.
# Reference: AIA CAD Layer Guidelines, US National CAD Standard
AIA_PREFIX_MAP = {
    "A": "ARCHITECTURAL",
    "S": "STRUCTURAL",
    "M": "MECHANICAL",
    "E": "ELECTRICAL",
    "P": "PLUMBING",
    "FP": "FIRE_PROTECTION",       # Fire Protection — what we care about most
    "F": "FIRE_PROTECTION",        # Some firms use F-* instead of FP-*
    "C": "CIVIL",
    "L": "LANDSCAPE",
    "T": "TELECOM",
    "Q": "EQUIPMENT",
    "G": "GENERAL",
}


def classify_layer(layer_name: str) -> str:
    """Map a layer name to an AIA category."""
    name_upper = layer_name.upper().strip()
    # Special-case common annotation layers that don't follow AIA prefixes
    if name_upper in {"TITLEBLOCK", "TITLE", "TB", "NOTES", "LEGEND",
                      "DEFPOINTS", "0", "VIEWPORT"}:
        return "ANNOTATION"
    # FP-* has priority over F-* because it's more specific
    if name_upper.startswith("FP-") or name_upper.startswith("FP_"):
        return "FIRE_PROTECTION"
    # Check single-letter prefix
    if "-" in name_upper:
        prefix = name_upper.split("-", 1)[0]
    elif "_" in name_upper:
        prefix = name_upper.split("_", 1)[0]
    else:
        # No separator — try the first character
        prefix = name_upper[:1]
    return AIA_PREFIX_MAP.get(prefix, "UNKNOWN")


# ─────────────────────────────────────────────────────────────────────────────
# Unit detection and scale calibration
# ─────────────────────────────────────────────────────────────────────────────

# DXF $INSUNITS code → human-readable unit
INSUNITS_MAP = {
    0: "unitless",
    1: "inches",
    2: "feet",
    3: "miles",
    4: "millimeters",
    5: "centimeters",
    6: "meters",
    7: "kilometers",
    8: "microinches",
    9: "mils",
    10: "yards",
}

# Multiplier to convert drawing-units → feet
UNITS_TO_FEET = {
    "inches":      1.0 / 12.0,
    "feet":        1.0,
    "millimeters": 0.003280839895,
    "centimeters": 0.03280839895,
    "meters":      3.280839895,
    "yards":       3.0,
    "unitless":    1.0 / 12.0,    # safest guess for US construction; flagged in metadata
}


def detect_units_and_scale(doc: Drawing) -> tuple[str, float]:
    """
    Return (units_name, scale_factor_to_feet).
    Falls back to inches → feet if $INSUNITS is missing or zero.
    """
    insunits_code = doc.header.get("$INSUNITS", 0)
    units = INSUNITS_MAP.get(insunits_code, "unitless")
    if units == "unitless":
        logger.warning("DXF has no $INSUNITS — assuming inches (most common in US)")
    scale = UNITS_TO_FEET.get(units, 1.0 / 12.0)
    return units, scale


# ─────────────────────────────────────────────────────────────────────────────
# The main reader
# ─────────────────────────────────────────────────────────────────────────────

class DXFReader:
    """Parses an architect's DXF into a structured Blueprint."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"DXF file not found: {self.path}")
        self.doc: Drawing | None = None

    def read(self) -> Blueprint:
        """Open the file and produce a Blueprint."""
        logger.info("Reading %s (%.1f KB)",
                    self.path.name, self.path.stat().st_size / 1024)

        # ezdxf.recover.read is tolerant of slightly malformed files —
        # important because real architect files often have minor issues.
        try:
            self.doc, auditor = recover.readfile(str(self.path))
            if auditor.has_errors:
                logger.warning("DXF has %d recoverable errors", len(auditor.errors))
        except Exception as exc:
            raise RuntimeError(f"Could not read DXF file: {exc}") from exc

        units, scale = detect_units_and_scale(self.doc)
        layers = self._inventory_layers()
        entities_by_layer = self._walk_entities()
        bounds = self._compute_bounds(entities_by_layer)

        bp = Blueprint(
            source_file=str(self.path.resolve()),
            dxf_version=self.doc.dxfversion,
            units=units,
            scale_factor=scale,
            width_drawing_units=bounds["width"],
            height_drawing_units=bounds["height"],
            width_ft=bounds["width"] * scale,
            height_ft=bounds["height"] * scale,
            layers=layers,
            entities_by_layer=entities_by_layer,
            metadata={
                "dxf_handles_seen": bounds["count"],
                "min_x": bounds["min_x"],
                "min_y": bounds["min_y"],
                "max_x": bounds["max_x"],
                "max_y": bounds["max_y"],
            },
        )
        # Fill per-layer entity counts now that we have everything
        for name, info in layers.items():
            info.entity_count = len(entities_by_layer.get(name, []))

        logger.info(
            "Blueprint: %.1f×%.1f ft, %d entities across %d layers",
            bp.width_ft, bp.height_ft, bp.total_entities, len(bp.layers),
        )
        return bp

    # ── Layer inventory ──────────────────────────────────────────────────
    def _inventory_layers(self) -> dict[str, LayerInfo]:
        out: dict[str, LayerInfo] = {}
        for layer in self.doc.layers:
            name = layer.dxf.name
            description = getattr(layer, "description", "") or ""
            out[name] = LayerInfo(
                name=name,
                aia_category=classify_layer(name),
                color=int(layer.dxf.color),
                description=description,
                is_visible=not layer.is_off(),
                is_locked=layer.is_locked(),
            )
        return out

    # ── Walk every entity in modelspace ──────────────────────────────────
    def _walk_entities(self) -> dict[str, list[EntityRecord]]:
        out: dict[str, list[EntityRecord]] = {}
        msp = self.doc.modelspace()
        for entity in msp:
            record = self._entity_to_record(entity)
            if record is None:
                continue
            out.setdefault(record.layer, []).append(record)
        return out

    def _entity_to_record(self, e: Any) -> EntityRecord | None:
        """Convert one ezdxf entity to our normalized EntityRecord."""
        dxf_type = e.dxftype()
        layer = getattr(e.dxf, "layer", "0")
        handle = getattr(e.dxf, "handle", "")
        color = getattr(e.dxf, "color", None)
        linetype = getattr(e.dxf, "linetype", None)

        rec = EntityRecord(
            dxf_type=dxf_type,
            layer=layer,
            handle=handle,
            color=color,
            linetype=linetype,
        )

        try:
            if dxf_type == "CIRCLE":
                rec.center = (e.dxf.center.x, e.dxf.center.y)
                rec.radius = float(e.dxf.radius)

            elif dxf_type == "LINE":
                rec.start = (e.dxf.start.x, e.dxf.start.y)
                rec.end = (e.dxf.end.x, e.dxf.end.y)

            elif dxf_type == "ARC":
                rec.center = (e.dxf.center.x, e.dxf.center.y)
                rec.radius = float(e.dxf.radius)
                rec.raw_attribs["start_angle"] = float(e.dxf.start_angle)
                rec.raw_attribs["end_angle"] = float(e.dxf.end_angle)

            elif dxf_type == "LWPOLYLINE":
                rec.points = [(p[0], p[1]) for p in e.get_points("xy")]
                rec.raw_attribs["is_closed"] = bool(e.closed)

            elif dxf_type == "POLYLINE":
                rec.points = [(v.dxf.location.x, v.dxf.location.y)
                              for v in e.vertices]
                rec.raw_attribs["is_closed"] = bool(e.is_closed)

            elif dxf_type == "TEXT":
                rec.text = e.dxf.text
                rec.height = float(e.dxf.height)
                rec.start = (e.dxf.insert.x, e.dxf.insert.y)

            elif dxf_type == "MTEXT":
                rec.text = e.text
                rec.height = float(e.dxf.char_height)
                rec.start = (e.dxf.insert.x, e.dxf.insert.y)

            elif dxf_type == "INSERT":   # block reference
                rec.center = (e.dxf.insert.x, e.dxf.insert.y)
                rec.raw_attribs["block_name"] = e.dxf.name
                rec.raw_attribs["rotation"] = float(e.dxf.rotation)
                rec.raw_attribs["scale"] = (
                    float(e.dxf.xscale), float(e.dxf.yscale))

            elif dxf_type == "ELLIPSE":
                rec.center = (e.dxf.center.x, e.dxf.center.y)
                rec.raw_attribs["major_axis"] = (
                    e.dxf.major_axis.x, e.dxf.major_axis.y)
                rec.raw_attribs["ratio"] = float(e.dxf.ratio)

            elif dxf_type == "HATCH":
                # Just record presence and area; advanced agents can dig in
                rec.raw_attribs["pattern_name"] = e.dxf.pattern_name
                rec.raw_attribs["solid_fill"] = bool(e.dxf.solid_fill)

            else:
                # Unknown type — preserve it but log
                logger.debug("Unhandled DXF type: %s on layer %s",
                             dxf_type, layer)
        except AttributeError as exc:
            logger.debug("Skipping malformed %s on layer %s: %s",
                         dxf_type, layer, exc)
            return None

        return rec

    # ── Bounding-box calculation ─────────────────────────────────────────
    @staticmethod
    def _compute_bounds(by_layer: dict[str, list[EntityRecord]]) -> dict[str, float]:
        xs: list[float] = []
        ys: list[float] = []
        count = 0
        for records in by_layer.values():
            for r in records:
                count += 1
                # collect any point-like coordinates
                for pt in [r.center, r.start, r.end]:
                    if pt:
                        xs.append(pt[0]); ys.append(pt[1])
                for px, py in r.points:
                    xs.append(px); ys.append(py)
        if not xs or not ys:
            return {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0,
                    "width": 0, "height": 0, "count": 0}
        return {
            "min_x": min(xs), "min_y": min(ys),
            "max_x": max(xs), "max_y": max(ys),
            "width":  max(xs) - min(xs),
            "height": max(ys) - min(ys),
            "count":  count,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Convenience entry point
# ─────────────────────────────────────────────────────────────────────────────

def read_dxf(path: str | Path) -> Blueprint:
    """One-line API. Open a DXF and get a Blueprint back."""
    return DXFReader(path).read()
