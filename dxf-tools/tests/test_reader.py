"""
tests/test_reader.py

Smoke tests for the DXF reader. Run me to verify nothing's broken:

    cd dxf-tools
    python3 tests/test_reader.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow imports from src/
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dxf_reader import classify_layer, read_dxf   # noqa: E402

SAMPLE = HERE.parent / "samples" / "sample_blueprint.dxf"


# ─────────────────────────────────────────────────────────────────────────────
# Test helpers
# ─────────────────────────────────────────────────────────────────────────────

PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  {PASS} {name}")
    else:
        print(f"  {FAIL} {name}  —  {detail}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Layer classification (unit-level, no file needed)
# ─────────────────────────────────────────────────────────────────────────────

def test_classify_layer() -> None:
    print("\n  Layer classification")
    print("  " + "─" * 50)
    cases = [
        ("A-WALL",        "ARCHITECTURAL"),
        ("A-WALL-PRHT",   "ARCHITECTURAL"),
        ("S-COLS",        "STRUCTURAL"),
        ("S-BEAM",        "STRUCTURAL"),
        ("M-HVAC-DUCT",   "MECHANICAL"),
        ("E-LITE",        "ELECTRICAL"),
        ("P-SANR",        "PLUMBING"),
        ("FP-SPRK",       "FIRE_PROTECTION"),
        ("FP_HEAD",       "FIRE_PROTECTION"),
        ("F-SPRINK",      "FIRE_PROTECTION"),
        ("TITLEBLOCK",    "ANNOTATION"),
        ("DEFPOINTS",     "ANNOTATION"),
        ("0",             "ANNOTATION"),
        ("WeirdLayer",    "UNKNOWN"),
    ]
    for layer, expected in cases:
        actual = classify_layer(layer)
        check(f"{layer:18s} → {expected}",
              actual == expected,
              f"got {actual}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. End-to-end: read the sample blueprint
# ─────────────────────────────────────────────────────────────────────────────

def test_read_sample_blueprint() -> None:
    print(f"\n  End-to-end: {SAMPLE.name}")
    print("  " + "─" * 50)
    if not SAMPLE.exists():
        check("sample exists", False,
              f"missing: {SAMPLE}. Run samples/make_sample_dxf.py first.")
    check("sample exists", True)

    bp = read_dxf(SAMPLE)

    # Basic checks
    check(f"units = inches",        bp.units == "inches", bp.units)
    check(f"scale ≈ 1/12",          abs(bp.scale_factor - 1/12) < 1e-6,
          f"{bp.scale_factor}")
    check(f"dimensions ~60 ft wide", 55 < bp.width_ft < 65, f"{bp.width_ft}")
    check(f"dimensions ~45 ft tall", 40 < bp.height_ft < 50, f"{bp.height_ft}")
    check(f"≥ 80 entities total",   bp.total_entities >= 80,
          f"{bp.total_entities}")
    check(f"≥ 14 layers",            len(bp.layers) >= 14, f"{len(bp.layers)}")

    # AIA category checks
    fp_layers = bp.layers_in_category("FIRE_PROTECTION")
    check(f"FP_SPRK among fire-protection layers",
          "FP-SPRK" in fp_layers,
          f"found: {fp_layers}")

    arch_layers = bp.layers_in_category("ARCHITECTURAL")
    check(f"A-WALL among arch layers",
          "A-WALL" in arch_layers,
          f"found: {arch_layers}")

    annot_layers = bp.layers_in_category("ANNOTATION")
    check(f"TITLEBLOCK is now ANNOTATION (not TELECOM)",
          "TITLEBLOCK" in annot_layers,
          f"found: {annot_layers}")

    # Entity counts
    sprk = bp.entities_by_layer.get("FP-SPRK", [])
    check(f"FP-SPRK has entities", len(sprk) > 0, f"got {len(sprk)}")

    circles_on_sprk = [e for e in sprk if e.dxf_type == "CIRCLE"]
    check(f"FP-SPRK has CIRCLE entities (sprinkler symbols)",
          len(circles_on_sprk) >= 15,
          f"got {len(circles_on_sprk)} circles")

    fp_note = bp.entities_by_layer.get("FP-NOTE", [])
    text_labels = [e for e in fp_note if e.dxf_type == "TEXT"]
    check(f"FP-NOTE has TEXT entities (sprinkler labels)",
          len(text_labels) >= 10,
          f"got {len(text_labels)} text labels")

    # Print a sample sprinkler so we can see what an agent will receive
    if circles_on_sprk:
        s = circles_on_sprk[0]
        print()
        print(f"    Sample sprinkler entity:")
        print(f"      handle:   {s.handle}")
        print(f"      type:     {s.dxf_type}")
        print(f"      layer:    {s.layer}")
        print(f"      center:   {s.center}  (drawing units = inches)")
        print(f"      radius:   {s.radius}")
        # Find the nearest text label
        if text_labels:
            cx, cy = s.center
            nearest = min(text_labels,
                          key=lambda t: ((t.start[0]-cx)**2 + (t.start[1]-cy)**2)**0.5)
            d = ((nearest.start[0]-cx)**2 + (nearest.start[1]-cy)**2)**0.5
            print(f"      nearest text: '{nearest.text}' "
                  f"({d:.1f}\" away, at {nearest.start})")


# ─────────────────────────────────────────────────────────────────────────────
# Run all tests
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("  dxf-tools / reader smoke tests")

    test_classify_layer()
    test_read_sample_blueprint()

    print()
    print(f"  {PASS} All tests passed.")
    print()


if __name__ == "__main__":
    main()
