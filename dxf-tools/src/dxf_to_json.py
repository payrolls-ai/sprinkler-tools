"""
src/dxf_to_json.py

Serializes a Blueprint to JSON so we can inspect what the reader
extracted from a DXF file. Useful for debugging and for feeding
the data to non-Python agents over a wire.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from dxf_reader import Blueprint, EntityRecord, LayerInfo, read_dxf


def blueprint_to_dict(bp: Blueprint) -> dict:
    """Turn a Blueprint dataclass into plain Python dicts for json.dump."""
    return {
        "source_file": bp.source_file,
        "dxf_version": bp.dxf_version,
        "units": bp.units,
        "scale_factor": bp.scale_factor,
        "dimensions": {
            "width_drawing_units":  bp.width_drawing_units,
            "height_drawing_units": bp.height_drawing_units,
            "width_ft":  bp.width_ft,
            "height_ft": bp.height_ft,
        },
        "metadata": bp.metadata,
        "total_entities": bp.total_entities,
        "layers": {
            name: {
                "aia_category":  info.aia_category,
                "color":         info.color,
                "description":   info.description,
                "entity_count":  info.entity_count,
                "is_visible":    info.is_visible,
                "is_locked":     info.is_locked,
            }
            for name, info in bp.layers.items()
        },
        "entities_by_layer": {
            name: [entity_to_dict(e) for e in entities]
            for name, entities in bp.entities_by_layer.items()
        },
    }


def entity_to_dict(e: EntityRecord) -> dict:
    out = {
        "dxf_type": e.dxf_type,
        "layer":    e.layer,
        "handle":   e.handle,
    }
    if e.center is not None:  out["center"] = list(e.center)
    if e.radius is not None:  out["radius"] = e.radius
    if e.start is not None:   out["start"]  = list(e.start)
    if e.end is not None:     out["end"]    = list(e.end)
    if e.points:              out["points"] = [list(p) for p in e.points]
    if e.text is not None:    out["text"]   = e.text
    if e.height is not None:  out["height"] = e.height
    if e.color is not None:   out["color"]  = e.color
    if e.linetype is not None:out["linetype"] = e.linetype
    if e.raw_attribs:         out["attribs"]  = e.raw_attribs
    return out


def save_blueprint_json(bp: Blueprint, out_path: str | Path) -> None:
    """Write a Blueprint to a JSON file."""
    data = blueprint_to_dict(bp)
    Path(out_path).write_text(json.dumps(data, indent=2, default=str))


# ─────────────────────────────────────────────────────────────────────────────
# CLI: python3 dxf_to_json.py path/to/file.dxf  →  prints summary + writes JSON
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="Inspect a DXF file's contents")
    p.add_argument("dxf_path", help="Path to the DXF to read")
    p.add_argument("-o", "--out", help="Output JSON path (default: <input>.json)")
    args = p.parse_args()

    bp = read_dxf(args.dxf_path)

    out_path = args.out or Path(args.dxf_path).with_suffix(".json")
    save_blueprint_json(bp, out_path)

    # Print human-readable summary
    print()
    print("═" * 60)
    print(f"  DXF SUMMARY  —  {Path(args.dxf_path).name}")
    print("═" * 60)
    print(f"  Format:        {bp.dxf_version}")
    print(f"  Units:         {bp.units}  ({bp.scale_factor:.6f} ft/unit)")
    print(f"  Dimensions:    {bp.width_ft:.1f} × {bp.height_ft:.1f} ft")
    print(f"                 ({bp.width_drawing_units:.1f} × "
          f"{bp.height_drawing_units:.1f} {bp.units})")
    print(f"  Total layers:  {len(bp.layers)}")
    print(f"  Total entities:{bp.total_entities}")
    print()
    print("  Layers by AIA category:")
    by_cat: dict[str, list[str]] = {}
    for name, info in bp.layers.items():
        by_cat.setdefault(info.aia_category, []).append(
            f"{name} ({info.entity_count})")
    for cat in sorted(by_cat):
        print(f"    [{cat}]")
        for layer_str in sorted(by_cat[cat]):
            print(f"      • {layer_str}")
    print()
    print(f"  JSON output:   {out_path}")
    print("═" * 60)


if __name__ == "__main__":
    main()
