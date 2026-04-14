# Sprinkler Tools

A set of standalone HTML calculators for fire sprinkler system design — built for quick field estimates on Los Angeles projects. No installation, no internet required. Just open in a browser.

---

## Tools

### Sprinkler Coverage Calculator
`sprinkler_calculator.html`

Estimates the minimum number of sprinkler heads needed for a rectangular room based on NFPA 13 coverage limits.

**Inputs**
- Room length and width (ft)
- Sprinkler type: Standard (130 sq ft), Extended Coverage (200 sq ft), or Residential (144 sq ft)

**Outputs**
- Total room area
- Minimum head count
- Max allowable spacing
- Coverage per head
- Visual room layout with head placement

---

### Water Pressure Calculator
`water_pressure_calculator.html`

Calculates residual pressure at the farthest sprinkler head using city fire flow test data and Hazen-Williams friction loss formula — the same method required by NFPA 13.

**Inputs — from city fire flow test report**
- Static pressure (PSI) — hydrant at rest
- Residual pressure (PSI) — hydrant under flow
- Flow at residual (GPM) — gallons per minute during test

**Inputs — system configuration**
- Elevation above supply (ft)
- Pipe length to farthest head (ft)
- Pipe diameter
- System demand flow (GPM)

**Outputs**
- Available city pressure at demand flow
- Elevation loss (0.433 PSI per ft)
- Friction loss via Hazen-Williams (C=120)
- Pressure at sprinkler head
- Pass / Marginal / Fail status vs 7 PSI NFPA 13 minimum
- Pipe pressure profile diagram
- City flow curve with operating point

---

## How to Use

1. Download the `.html` file you need
2. Open it in any web browser (Chrome, Safari, Edge, Firefox)
3. No internet connection required after download

---

## Disclaimer

These tools are for **reference and estimation only**. Always verify designs with a licensed fire protection engineer or NICET-certified designer. Calculations use Hazen-Williams C=120 for steel pipe. Minimum head pressure per NFPA 13 section 7.2.1 is 7 PSI.

---

## Jurisdiction

Designed with Los Angeles projects in mind — LAMC, LAFD requirements, and California amendments to NFPA 13 apply. Always confirm with the Authority Having Jurisdiction (AHJ) before finalizing any design.
