---
name: nfpa-rule-encoder
description: "Use this skill whenever adding, modifying, or auditing rules in the three rule JSON files: nfpa13_rules.json, california_amendments.json, or lamc_amendments.json. Triggers include: encoding a new NFPA section into structured form, capturing a California state amendment, adding a Los Angeles Municipal Code (LAMC) provision, fixing an incorrect spacing or coverage value, or tagging rules with ai_impact metadata. This skill enforces the schema, the three-layer override hierarchy, and the ai_impact taxonomy. Do NOT use this skill for agent code changes (use agent-orchestration) or for blueprint parsing changes (use blueprint-parser)."
---

# NFPA Rule Encoder Skill

This skill governs the three rule files in `backend/rules/`. Every rule encoded
here is consumed by both the agent system (during placement) and the validator
(after placement).

## The three layers

```
LAMC (Los Angeles Municipal Code)        ← top layer, wins all conflicts
        ↓ overrides
California state amendments              ← middle layer
        ↓ overrides
NFPA 13 (2025 edition)                   ← base layer
```

Higher layers can **override**, **add**, or **tighten** lower layers — but
never loosen them. If you find a LAMC rule that appears to relax NFPA, double
check; it is almost always wrong. Document any such case in
`docs/changelog/rules.md`.

## Rule schema (required for every rule)

```json
{
  "rule_id": "LA-007",
  "source": "LAMC",
  "section": "94.2010.3",
  "nfpa_section_modified": "9.3.5.5",
  "rule_type": "water_curtain",
  "ai_impact": "placement",
  "condition": {
    "applies_to": "openings requiring fire separation"
  },
  "requirement": {
    "max_sprinkler_spacing_ft": 6,
    "distance_from_draft_stop_in": {"min": 6, "max": 12},
    "draft_stop_depth_in": {"min": 18},
    "draft_stop_material": "noncombustible"
  },
  "overrides": "NFPA-104",
  "code_edition": "2022_CBC",
  "effective_date": "2026-01-01",
  "human_summary": "Sprinklers at fire-separation openings: max 6 ft apart, 6-12 in from a noncombustible draft stop ≥18 in deep."
}
```

### Required fields

- `rule_id` — `NFPA-###` / `CA-###` / `LA-###`. Must be unique across all 3 files.
- `source` — `"NFPA13"`, `"California"`, or `"LAMC"`.
- `section` — the section number in the source document.
- `rule_type` — short snake_case category (e.g., `spacing`, `coverage`,
  `obstruction`, `water_curtain`, `seismic`, `floor_control_valve`).
- `ai_impact` — exactly one of:
  - `"placement"` — agents use this rule when deciding where to place sprinklers
  - `"validator"` — only the post-placement validator checks this
  - `"both"` — used in both phases
- `condition` — a structured predicate describing when this rule fires
- `requirement` — the structured constraint to enforce
- `human_summary` — one plain-English sentence (used in UI tooltips)

### Optional but encouraged

- `nfpa_section_modified` — only on California / LAMC rules; cite the NFPA
  section being amended.
- `overrides` — `rule_id` of the lower-layer rule this one supersedes.
- `code_edition` — for amendments, the code edition that introduced this rule.
- `effective_date` — ISO 8601 date when the rule became enforceable.

## ai_impact tagging — how to decide

Ask: *"Could this rule change the (x, y) location of a sprinkler?"*

- **Yes, directly** → `placement` (e.g., max spacing of 15 ft)
- **Only after placement, as a yes/no check** → `validator` (e.g., min flow rate)
- **Both** → `both` (e.g., obstruction clearance — agents avoid them, validator confirms)

When in doubt, choose `validator`. It is safer to catch a violation late than
to bias the placement engine with a rule it cannot actually enforce.

## Key LA-specific rules (already encoded — don't duplicate)

| ID | Section | Rule |
|----|---------|------|
| `LA-001` | 94.2010.4 | Floor control valves inside stairway/smokeproof enclosures |
| `LA-002` | 94.2010.2 | Water curtain definition |
| `LA-003` | 94.2010.3 | Water curtain spacing (6 ft max, 6-12 in from draft stop) |
| `LA-004` | 94.2010.5 | Undetermined-use buildings → minimum Ordinary Hazard Group 2, 3000 sqft design area |
| `CA-001` | CBC 9.3.5 | Seismic bracing required for sprinkler piping |

## Validation

Every PR (Pull Request) that touches a rule file is checked by the
`pre-commit` hook in `.claude/hooks/`. The hook runs:

```bash
python backend/rules/_validate.py
```

This validator enforces:
1. JSON well-formed
2. All required fields present
3. `rule_id` unique across all three files
4. `ai_impact` is one of the three allowed values
5. `overrides` references an existing lower-layer rule
6. `effective_date` is in the past (or annotated `future_dated: true`)

**Do not bypass the hook with `--no-verify`.** If the validator is wrong,
fix the validator.
