# dxf-tools

> Reader and writer for AutoCAD DXF files. Turns architect blueprints into
> structured data the 50 specialist agents can consume, and turns AI findings
> back into DXF files designers can open in AutoCAD.

This is the foundation for Phase 4+ of the sprinkler-tools project, per
Steve's feedback that final output must be in AutoCAD format.

---

## What's in here

```
dxf-tools/
├── README.md                ← you are here
├── requirements.txt         ← Python dependencies
├── src/
│   ├── dxf_reader.py        ← parses DXF → Blueprint dataclass
│   └── dxf_to_json.py       ← CLI: inspect a DXF, dump to JSON
├── samples/
│   ├── make_sample_dxf.py   ← generates a synthetic blueprint for testing
│   ├── sample_blueprint.dxf ← the generated test file
│   ├── sample_blueprint.json← parsed output (after running the reader)
│   └── sample_blueprint_preview.png ← rendered visual
├── tests/
│   └── test_reader.py       ← smoke tests
└── docs/
    └── (future docs)
```

---

## Quick start

### One-time setup

```bash
pip install -r requirements.txt
```

This installs `ezdxf` (the only dependency — pure-Python, no compiler needed).

### Generate the test blueprint

```bash
cd samples
python3 make_sample_dxf.py
```

Produces `sample_blueprint.dxf` — a synthetic but realistic LA commercial
sprinkler drawing with 16 sprinkler heads, HVAC ducts, walls, doors,
columns, etc. Use this until Steve sends real drawings.

### Run the reader on any DXF

```bash
cd src
python3 dxf_to_json.py path/to/your/file.dxf
```

This prints a human-readable summary AND writes a JSON file alongside
the DXF that contains every entity, every layer, and every text label.
That JSON is what the agents will eventually consume.

Example summary output:

```
════════════════════════════════════════════════════════════
  DXF SUMMARY  —  sample_blueprint.dxf
════════════════════════════════════════════════════════════
  Format:        AC1032
  Units:         inches  (0.083333 ft/unit)
  Dimensions:    60.0 × 45.0 ft
  Total layers:  15
  Total entities:88

  Layers by AIA category:
    [ARCHITECTURAL]
      • A-WALL (9)
      • A-WALL-PRHT (7)
      ...
    [FIRE_PROTECTION]
      • FP-NOTE (17)
      • FP-SPRK (32)
      ...
```

### Run the tests

```bash
python3 tests/test_reader.py
```

Verifies layer classification and end-to-end parsing of the sample.

---

## How the reader works

```
   architect_file.dxf
            ↓
   ezdxf.recover.readfile()           ← tolerant of slightly malformed files
            ↓
   Walk every entity in modelspace
            ↓
   Classify each layer via AIA naming  (A-* = arch, FP-* = fire, etc.)
            ↓
   Convert each entity → EntityRecord  (normalized schema)
            ↓
   Group by layer name
            ↓
   Detect units ($INSUNITS) + scale
            ↓
   Compute overall bounding box
            ↓
   Return Blueprint(layers, entities_by_layer, dimensions, ...)
```

The `Blueprint` dataclass is the **canonical input** every one of the
50 agents will consume. It's intentionally JSON-serializable so we can
pass it across processes or over the network if needed.

---

## How the agents will use this

When you build the Sprinkler Head Agent (next session), it will:

1. Receive a `Blueprint` from this reader
2. Look at `blueprint.entities_by_layer["FP-SPRK"]` (and similar layers)
3. Filter for circle/block entities (the symbol)
4. Match each symbol to the nearest text label on `FP-NOTE`
5. Classify the symbol type (pendent / upright / sidewall / ESFR / etc.)
6. Return findings like `{type: "pendent", position: (108, 78), label: "SP-1"}`

The reader does NONE of this AI work — it just organizes the raw data so
the agent has clean inputs.

---

## What's missing (next session)

- [ ] `dxf_writer.py` — produces output DXF files with AI findings on
      labeled layers (`AI-SPRK`, `AI-PIPE`, etc.)
- [ ] Round-trip test: read → modify → write → verify it opens in AutoCAD
- [ ] PDF input path (for architects who don't send DXF)
- [ ] Block/INSERT entity handling for sprinkler symbols defined as blocks
- [ ] OCR for title block scale extraction when `$INSUNITS` is missing

---

## Decisions on record

### Why ezdxf (not the AutoCAD COM API)?
- Free, open source, pure Python — no AutoCAD license needed for users
- Mature library (since 2011), well-documented
- Reads AND writes DXF, including modern AC1032 (AutoCAD 2018) format
- Has tolerant `recover` mode for slightly broken files

### Why DXF (not DWG)?
- DWG is Autodesk's proprietary binary format — no free libraries write it
  reliably
- DXF is a text-based interchange format AutoCAD opens natively
- Round-trips perfectly: open a DXF in AutoCAD, save as DWG, reopen — no
  data loss

### Why classify layers by AIA convention?
- AIA naming is the de-facto standard in US construction
- Lets us write category-aware code: `layers_in_category("FIRE_PROTECTION")`
- Future-proof: if an architect uses oddball layer names, classification
  falls back to `UNKNOWN` rather than failing

---

Owner: Meatbot · Repo: `payrolls-ai/sprinkler-tools` · Jurisdiction: Los Angeles
