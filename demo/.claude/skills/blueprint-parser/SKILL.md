---
name: blueprint-parser
description: "Use this skill when modifying how the system reads architectural input files (PDF, DXF, DWG, or color-coded PNG floor plans). Triggers include: improving PDF-to-image conversion, parsing AutoCAD DXF layers, mapping color codes to hazard classes, normalizing scale and orientation, handling multi-page or multi-floor plans, or extracting the input the 50 agents consume. Do NOT use this skill for changes to the agents themselves (use agent-orchestration) or to rule encoding (use nfpa-rule-encoder)."
---

# Blueprint Parser Skill

The parser is the single entry point that turns a customer file (PDF / DXF /
PNG) into the canonical `Blueprint` object every agent consumes. If the parser
is wrong, every agent is wrong.

## The Blueprint object (canonical contract)

```python
class Blueprint(BaseModel):
    blueprint_id: str
    source_file: str
    width_px: int
    height_px: int
    scale_ft_per_px: float       # critical — agents measure in feet
    layers: dict[str, LayerData] # keyed by AutoCAD layer name
    pixel_array: np.ndarray      # H x W x 3, uint8, RGB
    color_map: dict[ColorCode, HazardClass]
    metadata: BlueprintMetadata
```

If you add a field, also update the demo blueprint in
`backend/agents/_demo_data.py` so the demo path keeps working.

## Color coding (input convention)

The training data uses this color scheme. The parser must preserve it.

| Color (RGB) | Meaning |
|-------------|---------|
| `(255,255,255)` white | Sprinklered space |
| `(160,160,160)` gray | Exempt space (shafts, stairs, closets) |
| `(0,100,255)` blue | Riser shaft location |
| `(180,255,180)` light green | Light Hazard zone |
| `(255,255,140)` yellow | Ordinary Hazard Group 1 |
| `(255,180,90)` orange | Ordinary Hazard Group 2 (LA default for undetermined use) |
| `(255,120,120)` red | Extra Hazard zone |

These constants live in `backend/models/color_codes.py`. **Do not redefine
them inside the parser.**

## DXF (AutoCAD Drawing Exchange Format) layer mapping

When a DXF file is supplied, the parser reads layers by name. The expected
layer names follow the AIA (American Institute of Architects) CAD layer
guidelines:

| Layer name | Maps to Blueprint field |
|------------|-------------------------|
| `A-WALL` | structural walls |
| `A-WALL-PRHT` | partition walls |
| `A-DOOR` | door openings |
| `A-GLAZ` | windows |
| `A-FLOR-CASE` | casework / built-ins |
| `M-HVAC-DUCT` | HVAC ducts (obstruction agents care!) |
| `M-HVAC-EQPM` | HVAC equipment |
| `E-LITE` | light fixtures |
| `P-SANR` | plumbing fixtures |
| `S-COLS` | structural columns |
| `S-BEAM` | beams |
| `FP-SPRK` | **sprinklers** — turn this layer OFF for input, ON for ground truth |

Unknown layers are preserved under `layers["unknown:<original_name>"]` and
logged at WARNING level. Do not silently drop them.

## Scale calibration

This is the most error-prone step. A mis-calibrated scale ruins every
spacing-rule check.

The parser detects scale in this priority order:

1. **DXF header `$INSUNITS`** — if present and unambiguous, use it.
2. **Title block annotation** — OCR (Optical Character Recognition) the
   bottom-right corner for strings like `1/8" = 1'-0"` or `SCALE: 1:96`.
3. **Reference dimension** — find a labeled dimension line and divide its
   pixel length by its annotated foot value.
4. **Fallback** — if all three fail, raise `ScaleAmbiguousError`. Do NOT
   guess. The frontend prompts the user to manually enter the scale.

## Multi-page and multi-floor handling

A single PDF often contains multiple floor plans. The parser:

1. Splits on page boundaries.
2. Classifies each page as `floor_plan`, `cover_sheet`, `detail`, or `schedule`
   using a small CNN classifier (`backend/models/page_classifier.py`).
3. Returns one `Blueprint` per floor_plan page.
4. Groups them in a `BlueprintBundle` keyed by floor designation
   (extracted from the title block).

## Performance budget

| File type | Target | Hard limit |
|-----------|--------|------------|
| PNG (already pixels) | 50 ms | 200 ms |
| PDF (1 page) | 300 ms | 800 ms |
| PDF (10 pages) | 2 s | 5 s |
| DXF | 500 ms | 1.5 s |

`pdftoppm` at 150 DPI hits the PDF target. Going higher than 200 DPI rarely
improves agent accuracy and blows the time budget.

## Things that have bitten us before

- **Smart quotes in title block OCR** — strip `\u201c\u201d\u2018\u2019` before
  parsing scale strings.
- **PDFs with rotated pages** — check `/Rotate` in the page dict and rotate
  pixels accordingly *before* handing to agents.
- **DXF files with locked layers** — read with `ezdxf.recover.read()`, not
  `ezdxf.readfile()`, to tolerate slightly malformed files.
- **Color drift from JPEG compression** — when a customer sends a JPEG instead
  of PNG, the color codes drift by ±5 RGB units. Use `color_codes.match_with_tolerance(rgb, tol=8)`.
