# Sprinkler Tools

> Fire sprinkler design tools for Los Angeles projects — built around NFPA 13,
> California state amendments, and LAMC Section 94.2010.

This repo holds two related but separate things:

1. **HTML Calculators** — standalone field tools for quick estimates
2. **Sprinkler AI** — a Python project to identify sprinkler systems on
   architect drawings and produce AutoCAD output

---

## Sprinkler AI (active development)

An AI system that takes architect blueprints and identifies the sprinkler
system inside them. Output is generated in AutoCAD DXF format so designers
can open results directly in their existing tools.

### Where things stand

- **Phase 1–3 (complete):** Three-layer rule encoding from NFPA 13 +
  California amendments + LAMC. Rules live in [`Rules/`](Rules/).
- **Phase 4 (in progress):** DXF reader and writer. Reader lives in
  [`dxf-tools/`](dxf-tools/) — parses architect files into structured data
  the agents can consume. Writer is next.
- **Phase 5 (demo built):** A working proof-of-concept with 50-agent
  architecture, FastAPI backend, and HTML frontend lives in
  [`demo/`](demo/). Demonstrates the end-to-end flow with synthetic data.
- **Phase 6+:** Train a real CNN on labeled drawings (data collection
  underway with project partners).

### Key folders

| Folder        | What's in it                                                |
|---------------|-------------------------------------------------------------|
| `Rules/`      | NFPA 13, California, and LAMC rules as structured JSON      |
| `dxf-tools/`  | DXF reader/writer (Phase 4) — open and produce AutoCAD files |
| `demo/`       | Phase 5 proof-of-concept demo (50-agent architecture)       |

### Quick start (DXF reader)

```bash
cd dxf-tools
pip install -r requirements.txt
python3 tests/test_reader.py     # run smoke tests
python3 src/dxf_to_json.py samples/sample_blueprint.dxf
```

See [`dxf-tools/README.md`](dxf-tools/README.md) for full details.

### Design decisions on record

- **CNN + 50 specialist agents** organized into 6 teams (Structure,
  Openings, Obstructions, Classifiers, MEP, Code Math). Master Placement
  Agent aggregates findings and applies the three-layer rule hierarchy.
- **Three-layer rule system:** NFPA 13 base → California state amendments
  → LAMC local amendments. Each rule includes an `ai_impact` field
  distinguishing placement rules from validator rules.
- **Output format is AutoCAD DXF** (not just a screenshot or report).
  Designers need to open results in their existing tools.
- **Phase 1 goal is identify, not design.** Train the AI to find existing
  sprinklers on already-completed drawings before attempting layout.

---

## HTML Calculators

Standalone single-file tools for quick field estimates. No installation, no
internet required. Just open in a browser.

### Sprinkler Coverage Calculator
`sprinkler_calculator.html`

Estimates the minimum number of sprinkler heads needed for a rectangular
room based on NFPA 13 coverage limits.

**Inputs:** room length and width (ft); sprinkler type (Standard 130 sq ft,
Extended Coverage 200 sq ft, or Residential 144 sq ft).
**Outputs:** total room area, minimum head count, max allowable spacing,
coverage per head, visual room layout with head placement.

### Water Pressure Calculator
`water_pressure_calculator.html`

Estimates available water pressure at the most remote sprinkler based on
pipe length, elevation, friction loss, and supply pressure.

### Hydraulic Summary
`hydraulic_summary.html`

Quick hydraulic calculation summary for a single design area — flows,
pressures, and pipe sizing.

### K-Factor Calculator
`kfactor_calculator.html`

Computes sprinkler discharge from K-factor and pressure (and vice versa)
per NFPA 13 hydraulic equations.

### Pipe Sizing Calculator
`pipe_sizing_calculator.html`

Sizes branch and main piping for a given flow rate using Hazen-Williams
friction loss tables.

### Occupancy Classifier
`occupancy_classifier.html`

Walks through hazard classification (Light, Ordinary Group 1/2, Extra
Hazard 1/2) per NFPA 13 Chapter 5.

### Sprinkler AI Roadmap
`sprinkler_ai_roadmap.html`

Interactive view of the Phase 1–10 roadmap for the Sprinkler AI project.

---

## Jurisdiction

This tool set is built for **Los Angeles** sprinkler design and references:

- **NFPA 13** (2019 edition base)
- **California Building Code** amendments (Title 24)
- **LAMC Section 94.2010** (Los Angeles local amendments)

Rules outside LA may need adjustments — particularly for occupancy
overrides and the LA undetermined-use defaults.

---

## Status

Active development. The HTML calculators are stable and ready to use. The
Sprinkler AI project is iterating quickly — APIs and folder layouts may
change as we learn from real architect drawings.
