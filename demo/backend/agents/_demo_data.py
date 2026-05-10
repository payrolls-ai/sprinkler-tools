"""
backend/agents/_demo_data.py

Bundled sample blueprint used in DEMO mode. This represents a small
~60ft x 40ft commercial floor plan with:
  - 6 rooms (offices, conference, kitchen, bathroom, electrical, stair)
  - 1 HVAC duct running through the open office (an obstruction!)
  - 2 deep beams creating water shadows
  - 1 smoke barrier opening that triggers LA water curtain rules
  - A water riser in the corner

The frontend renders the same scene at the same coordinates so what the
user sees on screen is exactly what the agents are inspecting.
"""
from __future__ import annotations

from .base_agent import Blueprint


def get_demo_blueprint() -> Blueprint:
    return Blueprint(
        blueprint_id="DEMO-LA-001",
        width_ft=60.0,
        height_ft=40.0,
        scale_ft_per_px=1.0,
        rooms=[
            # id, type, hazard, bbox(x, y, width, height)
            {"id": "R1", "type": "open_office",  "hazard": "Light",
             "bbox": {"x":  2, "y":  2, "width": 28, "height": 18}},
            {"id": "R2", "type": "conference",   "hazard": "Light",
             "bbox": {"x": 32, "y":  2, "width": 14, "height": 12}},
            {"id": "R3", "type": "kitchen",      "hazard": "Ordinary",
             "bbox": {"x": 48, "y":  2, "width": 10, "height": 12}},
            {"id": "R4", "type": "bathroom",     "hazard": "Light",
             "bbox": {"x": 32, "y": 16, "width":  8, "height":  8}},
            {"id": "R5", "type": "electrical",   "hazard": "Special",
             "bbox": {"x": 42, "y": 16, "width":  8, "height":  8}},
            {"id": "R6", "type": "stair",        "hazard": "Exempt",
             "bbox": {"x": 52, "y": 16, "width":  6, "height":  8}},
            {"id": "R7", "type": "open_office",  "hazard": "Light",
             "bbox": {"x":  2, "y": 22, "width": 28, "height": 16}},
            {"id": "R8", "type": "warehouse",    "hazard": "Ordinary",
             "bbox": {"x": 32, "y": 26, "width": 26, "height": 12}},
        ],
        raw_features={
            # Structure
            "exterior_walls": [
                {"x":  0, "y":  0, "width": 60, "height":  1},
                {"x":  0, "y": 39, "width": 60, "height":  1},
                {"x":  0, "y":  0, "width":  1, "height": 40},
                {"x": 59, "y":  0, "width":  1, "height": 40},
            ],
            "partition_walls": [
                {"x": 30, "y":  2, "width":  1, "height": 36},
                {"x": 47, "y":  2, "width":  1, "height": 12},
                {"x": 32, "y": 14, "width": 26, "height":  1},
                {"x": 40, "y": 16, "width":  1, "height":  8},
                {"x": 50, "y": 16, "width":  1, "height":  8},
                {"x":  2, "y": 21, "width": 28, "height":  1},
                {"x": 32, "y": 25, "width": 26, "height":  1},
            ],
            "columns": [[16, 12], [16, 30], [44, 30]],
            "beams": [
                {"x": 10, "y":  9, "width": 18, "height":  0.5, "depth_in": 14},
                {"x": 10, "y": 30, "width": 18, "height":  0.5, "depth_in": 12},
            ],
            "ceiling_heights": [9.0, 11.5, 9.0],
            "shear_walls": [],

            # Openings
            "doors": [[30.5, 11], [47.5,  8], [36, 14.5], [44, 14.5],
                       [56, 14.5], [30.5, 30], [32, 25.5]],
            "windows": [
                {"x":  4, "y":  0, "width":  6, "height":  0.5},
                {"x": 18, "y":  0, "width":  6, "height":  0.5},
                {"x": 36, "y":  0, "width":  6, "height":  0.5},
            ],
            "fire_rated_doors": [[30.5, 30]],
            "smoke_barrier_openings": [
                # Vertical opening in partition between open office (R1) and
                # conference (R2) → triggers LA-003 water curtain.
                {"x": 30, "y": 8, "width": 1.5, "height": 6}
            ],

            # Obstructions
            "hvac_ducts": [
                # 24-inch duct running along the open office ceiling
                {"x":  6, "y":  9.5, "width": 22, "height": 1, "width_in": 24},
                {"x":  6, "y": 30.5, "width": 22, "height": 1, "width_in": 24},
            ],
            "light_fixtures": [
                [10,  6], [22,  6], [10, 16], [22, 16],
                [10, 26], [22, 26], [10, 34], [22, 34],
            ],

            # MEP
            "water_riser": [58, 38],

            # Code-math
            "draft_stops": [
                {"x": 30, "y": 8, "width": 1.5, "height": 6, "depth_in": 18}
            ],
            "water_curtain_zones": [
                {"x": 30, "y": 8, "width": 1.5, "height": 6}
            ],
        },
    )
