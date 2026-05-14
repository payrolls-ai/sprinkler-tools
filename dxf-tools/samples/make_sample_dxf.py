"""
samples/make_sample_dxf.py

Generates a synthetic but realistic sprinkler blueprint DXF file we can use
to develop and test the reader/writer. This stands in for real architect
files until Steve sends them.

The sample mimics what we'd expect from a typical commercial building
sprinkler design:
  - Standard AIA layer names (A-WALL, FP-SPRK, M-HVAC, etc.)
  - Realistic sprinkler symbols on the FP-SPRK layer
  - HVAC duct rectangles
  - Walls as polylines
  - Text labels with various abbreviations (SPRK, SP-1, PENDENT)
  - Title block with scale info

Run:
    python3 make_sample_dxf.py
Output:
    samples/sample_blueprint.dxf
"""
from __future__ import annotations

import math
from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment


OUTPUT = Path(__file__).parent / "sample_blueprint.dxf"


def main() -> None:
    # Create new DXF document. R2018 is AutoCAD 2018 format — modern and
    # widely supported by current architecture firms.
    doc = ezdxf.new(dxfversion="R2018", setup=True)
    doc.units = ezdxf.units.IN          # inches; very common in US construction
    doc.header["$INSUNITS"] = 1         # 1 = inches per the DXF spec

    msp = doc.modelspace()

    # ── Layers (using AIA naming convention, what real architects do) ──────
    layer_defs = [
        # name,             color, description
        ("A-WALL",          7,     "Architectural — exterior walls"),
        ("A-WALL-PRHT",     8,     "Architectural — partition walls"),
        ("A-DOOR",          5,     "Architectural — doors"),
        ("A-GLAZ",          4,     "Architectural — windows"),
        ("S-COLS",          6,     "Structural — columns"),
        ("S-BEAM",          9,     "Structural — beams"),
        ("M-HVAC-DUCT",    30,     "Mechanical — HVAC ducts"),
        ("E-LITE",          2,     "Electrical — light fixtures"),
        ("FP-SPRK",         1,     "Fire protection — sprinkler heads"),
        ("FP-PIPE",         3,     "Fire protection — pipes"),
        ("FP-RISR",        13,     "Fire protection — main riser"),
        ("FP-NOTE",       250,     "Fire protection — annotations"),
        ("TITLEBLOCK",      7,     "Title block / drawing info"),
        ("DEFPOINTS",       7,     "Reference points (non-printing)"),
    ]
    for name, color, desc in layer_defs:
        if name in doc.layers:
            continue  # skip defaults like DEFPOINTS
        layer = doc.layers.add(name, color=color)
        layer.description = desc

    # ── Building outline: 60ft × 40ft = 720" × 480" ───────────────────────
    # Floor plan corner at origin
    W, H = 720.0, 480.0    # inches
    msp.add_lwpolyline(
        [(0, 0), (W, 0), (W, H), (0, H), (0, 0)],
        close=True,
        dxfattribs={"layer": "A-WALL", "lineweight": 50},
    )

    # ── Partition walls between rooms ──────────────────────────────────────
    partitions = [
        # (x1, y1, x2, y2)
        (360, 0,   360, 480),    # central north-south wall
        (564, 0,   564, 144),    # kitchen / conference divider
        (360, 168, 720, 168),    # east half corridor
        (480, 168, 480, 264),    # bath wall
        (600, 168, 600, 264),    # electrical wall
        (0,   264, 360, 264),    # west half corridor
        (360, 312, 720, 312),    # warehouse top
    ]
    for x1, y1, x2, y2 in partitions:
        msp.add_line((x1, y1), (x2, y2),
                     dxfattribs={"layer": "A-WALL-PRHT", "lineweight": 30})

    # ── Doors (just arc symbols + opening line) ───────────────────────────
    doors = [
        # (x, y, rotation_deg)
        (360,  132, 0),     # office to conference
        (570,   96, 90),    # conference to kitchen
        (432,  174, 0),     # corridor to bath
        (528,  174, 0),     # corridor to electrical
        (672,  174, 0),     # corridor to stair
        (366,  360, 90),    # office to warehouse corridor
        (384,  306, 0),     # warehouse west door
    ]
    for x, y, rot in doors:
        # Door swing arc (3 ft = 36 in radius)
        msp.add_arc(
            center=(x, y), radius=36, start_angle=rot, end_angle=rot + 90,
            dxfattribs={"layer": "A-DOOR"},
        )

    # ── Structural columns (W-shape symbol as filled rectangle) ───────────
    columns = [(192, 144), (192, 360), (528, 360)]
    for cx, cy in columns:
        # 14" × 14" wide-flange column
        msp.add_lwpolyline(
            [(cx - 7, cy - 7), (cx + 7, cy - 7),
             (cx + 7, cy + 7), (cx - 7, cy + 7)],
            close=True,
            dxfattribs={"layer": "S-COLS", "lineweight": 70},
        )

    # ── Beams (dashed lines overhead) ─────────────────────────────────────
    beams = [
        (120, 108, 336, 108),   # north beam
        (120, 360, 336, 360),   # south beam in office area
    ]
    for x1, y1, x2, y2 in beams:
        msp.add_line((x1, y1), (x2, y2),
                     dxfattribs={"layer": "S-BEAM", "linetype": "DASHED"})

    # ── HVAC ducts (24" wide rectangles spanning the office) ──────────────
    ducts = [
        # (x, y, length, width_in)
        (72, 108, 264, 12),     # 24" duct: drawn as 12" wide line in plan
        (72, 360, 264, 12),
    ]
    for x, y, length, w in ducts:
        msp.add_lwpolyline(
            [(x, y), (x + length, y), (x + length, y + w), (x, y + w)],
            close=True,
            dxfattribs={"layer": "M-HVAC-DUCT"},
        )
        # Label
        msp.add_text(
            "24\"x12\" SA",
            height=4,
            dxfattribs={"layer": "M-HVAC-DUCT"},
        ).set_placement((x + length / 2, y + w + 4),
                        align=TextEntityAlignment.MIDDLE_CENTER)

    # ── Sprinkler heads ────────────────────────────────────────────────────
    # Mix of types and abbreviations to stress-test our agent's vocabulary.
    # Format: (x_in, y_in, label_text, head_type_for_block)
    sprinklers = [
        # Open office north (R1) — pendent sprinklers labeled "SP"
        (108,  78,  "SP-1",   "pendent"),
        (276,  78,  "SP-2",   "pendent"),
        (108, 186,  "SP-3",   "pendent"),
        (276, 186,  "SP-4",   "pendent"),
        # Conference room — labeled "SPRK"
        (468,  96,  "SPRK",   "pendent"),
        # Kitchen — Ordinary hazard, labeled with K-factor
        (636,  96,  "K8.0",   "pendent"),
        # Bathroom — concealed type
        (432, 240,  "CONC",   "concealed"),
        # Open office south (R7) — labeled "PENDENT"
        (108, 312,  "PENDENT", "pendent"),
        (276, 312,  "PENDENT", "pendent"),
        (108, 408,  "PENDENT", "pendent"),
        (276, 408,  "PENDENT", "pendent"),
        # Warehouse — ESFR for Ordinary hazard 2 + LA undetermined-use override
        (436, 384,  "ESFR",   "esfr"),
        (540, 384,  "ESFR",   "esfr"),
        (644, 384,  "ESFR",   "esfr"),
        # Water curtain at smoke barrier opening (LAMC LA-003)
        (369,  96,  "SP-WC",  "pendent"),
        (369, 168,  "SP-WC",  "pendent"),
    ]

    for x, y, label, head_type in sprinklers:
        # Symbol — circle with center dot (industry standard for pendent)
        msp.add_circle(
            (x, y), radius=4,
            dxfattribs={"layer": "FP-SPRK", "lineweight": 30},
        )
        if head_type == "pendent":
            # Filled dot in the middle
            msp.add_circle((x, y), radius=0.8,
                           dxfattribs={"layer": "FP-SPRK"})
        elif head_type == "esfr":
            # Larger ESFR symbol — bigger circle, no dot
            msp.add_circle((x, y), radius=6,
                           dxfattribs={"layer": "FP-SPRK", "lineweight": 50})
        elif head_type == "concealed":
            # Square inside circle
            msp.add_lwpolyline(
                [(x - 2, y - 2), (x + 2, y - 2),
                 (x + 2, y + 2), (x - 2, y + 2)],
                close=True,
                dxfattribs={"layer": "FP-SPRK"},
            )
        # Text label offset to the right
        msp.add_text(
            label, height=3,
            dxfattribs={"layer": "FP-NOTE"},
        ).set_placement((x + 8, y - 1.5),
                        align=TextEntityAlignment.LEFT)

    # ── Main water riser (in southeast corner) ─────────────────────────────
    riser_x, riser_y = 696, 456
    msp.add_circle((riser_x, riser_y), radius=8,
                   dxfattribs={"layer": "FP-RISR", "lineweight": 70})
    msp.add_text(
        "R", height=8,
        dxfattribs={"layer": "FP-RISR"},
    ).set_placement((riser_x, riser_y), align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_text(
        "MAIN RISER", height=4,
        dxfattribs={"layer": "FP-NOTE"},
    ).set_placement((riser_x - 16, riser_y - 16),
                    align=TextEntityAlignment.LEFT)

    # ── Room labels ────────────────────────────────────────────────────────
    rooms = [
        (180, 130, "OFFICE 101",  3),
        (180, 360, "OFFICE 102",  3),
        (450,  72, "CONFERENCE",  3),
        (630,  72, "KITCHEN",     3),
        (450, 216, "BATH",        3),
        (570, 216, "ELEC",        3),
        (660, 216, "STAIR",       3),
        (540, 384, "WAREHOUSE",   3),
    ]
    for x, y, name, height in rooms:
        msp.add_text(
            name, height=height,
            dxfattribs={"layer": "A-WALL"},
        ).set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)

    # ── Title block (bottom right corner) ─────────────────────────────────
    tb_x, tb_y = 480, -60
    msp.add_lwpolyline(
        [(tb_x, tb_y), (tb_x + 240, tb_y),
         (tb_x + 240, tb_y + 48), (tb_x, tb_y + 48)],
        close=True,
        dxfattribs={"layer": "TITLEBLOCK", "lineweight": 50},
    )
    title_lines = [
        ("PROJECT:   SAMPLE COMMERCIAL BUILDING",  tb_y + 36),
        ("DRAWING:   FP-1.00 FIRE SPRINKLER PLAN", tb_y + 24),
        ('SCALE:     1/8" = 1\'-0"',               tb_y + 12),
        ("DATE:      05/14/2026",                   tb_y +  2),
    ]
    for text, y in title_lines:
        msp.add_text(
            text, height=3,
            dxfattribs={"layer": "TITLEBLOCK"},
        ).set_placement((tb_x + 6, y), align=TextEntityAlignment.LEFT)

    # ── Save ───────────────────────────────────────────────────────────────
    doc.saveas(OUTPUT)
    print(f"✓ Sample blueprint saved: {OUTPUT}")
    print(f"  Size: {OUTPUT.stat().st_size:,} bytes")
    print(f"  Entities: {len(list(msp))} total")
    print(f"  Sprinklers: {len(sprinklers)}")


if __name__ == "__main__":
    main()
