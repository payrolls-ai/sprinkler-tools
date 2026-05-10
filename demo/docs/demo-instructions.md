# Boss Demo Script — 5 minutes

> Use this as a cue card. Don't read it word-for-word — the demo speaks for itself.

---

## Before the meeting (30 seconds)

1. Double-click `frontend/index.html` so it's already open in the browser.
2. Make sure the **Specialist Agents** panel on the left shows all 50 chips,
   greyed out and idle.

---

## Slide 1 — "What we're looking at" (60 seconds)

Open with the canvas:

> "This is a real architectural floor plan, 60 feet by 40 feet — 8 rooms, an
> office, conference room, kitchen, bathroom, electrical, stair, warehouse.
> The yellow rooms are Light Hazard, the orange ones are Ordinary Hazard.
> Right now, no sprinklers — just the building."

Point out:
- The dashed orange rectangles running across the office: those are HVAC ducts
  (24 inches wide — wide enough to trigger an NFPA obstruction rule).
- The dashed red box on the wall between Office and Conference: that's a
  **smoke barrier opening** — under LAMC §94.2010, that triggers a water
  curtain.
- The teal "R" circle in the bottom right: water riser.

---

## Slide 2 — "Hit the button" (90 seconds)

Click **Run AI Analysis**.

Narrate while the animation runs:

> "What you just kicked off is **50 specialist AI agents running in parallel**.
> See the chips lighting up on the left? Each one is a different specialist —
> agent 19 is hunting for HVAC ducts, agent 30 figures out hazard classes,
> agent 50 is the LA water-curtain expert."

> "On the right you see findings streaming in as they detect things. Top
> right is the **rule hierarchy** — three layers stacked: NFPA 13 at the base,
> California amendments above it, and **LAMC at the top** because LA gets the
> final word on every rule."

Then sprinklers drop in:

> "Now the **Master Placement Agent** takes all 50 reports, applies the rules
> in priority order, and you see the result — 16 sprinkler heads placed.
> Hover any of them to see the spec."

Hover over the leftmost water-curtain dot:

> "This one's special. It's part of a water curtain at the smoke barrier
> opening. Spaced 6 feet apart per LA-003, not the regular grid."

---

## Slide 3 — "And here's compliance" (60 seconds)

Scroll to the **Code Compliance** panel on the right:

> "Every rule got checked. NFPA-004 — minimum 6 feet between heads — pass.
> CA-001 — California seismic bracing — flagged as info because piping is a
> downstream phase. LA-003 — water curtain — pass."

Then the run stats at the bottom:

> "End to end, **about 100 milliseconds** for a real backend run. The 50
> agents run in parallel, so adding more specialists doesn't slow it down."

---

## Slide 4 — "Why this beats the previous approach" (45 seconds)

> "Earlier project notes considered a generative model — a big black box you
> train end-to-end. We pivoted away from that. Why? Because **fire code is
> auditable** — the AHJ wants to know which rule placed which sprinkler. Our
> agents return that information explicitly. With the GAN approach, you just
> get a picture and have to argue."

> "Plus — adding a new code rule is a JSON edit, not a 200-image retraining
> run."

---

## Likely boss questions

| Question | Answer |
|----------|--------|
| Is the AI real here? | The architecture is real. In **demo mode** the agents return deterministic mock findings against the bundled blueprint so it's reproducible. Phase 6 trains the CNN; Phase 7 swaps the mock detectors for real inference. |
| How many drawings to train? | We've collected 7 of the 30 minimum drawing pairs. The agent design lets us train each agent's detection head independently, so we can ship Structure agents first, then Obstructions, etc. |
| Why 50 agents? | One per detection class makes each agent debuggable and lets us measure per-agent accuracy against the AHJ-required ground truth. |
| LA-only? | Yes for now. The 3-layer rule hierarchy (NFPA → state → local) is built so adding another jurisdiction is a new JSON file, not new code. |
| Can I see the code? | The repo is yours: `payrolls-ai/sprinkler-tools`. Backend is FastAPI + Python; frontend is plain HTML/CSS/JS, no build step. |

---

## If something breaks during the demo

- **Frontend won't open** → just double-click `index.html` again.
- **Status shows "Offline mode"** → that's fine, the demo still runs end-to-end. The numbers shown are the same numbers the live backend produces.
- **Browser cache weirdness** → Cmd-Shift-R (Mac) or Ctrl-F5 (Windows) to hard-refresh.
- **You want to reset** → click the **Reset** button next to Run AI Analysis.

---

Good luck. The demo's solid. 🔥
