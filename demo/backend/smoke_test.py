"""
backend/smoke_test.py

Run me to verify the whole stack works without needing the API server:

    cd backend
    python3 smoke_test.py
"""
from __future__ import annotations

import asyncio
import json
import sys

from agents import ALL_AGENTS, MasterPlacementAgent
from agents._demo_data import get_demo_blueprint
from agents.master_agent import load_rules


def _ok(msg: str) -> None:
    print(f"  \033[32m✓\033[0m {msg}")


def _fail(msg: str) -> None:
    print(f"  \033[31m✗\033[0m {msg}")
    sys.exit(1)


async def main() -> None:
    print("\n  sprinkler-tools smoke test\n  " + "─" * 40)

    # 1. Agent registry
    if len(ALL_AGENTS) == 50:
        _ok(f"50 agents registered ({len(ALL_AGENTS)})")
    else:
        _fail(f"expected 50 agents, got {len(ALL_AGENTS)}")

    if len({a.agent_id for a in ALL_AGENTS}) == 50:
        _ok("all agent_ids unique")
    else:
        _fail("duplicate agent_ids found")

    # 2. Rules
    rules = load_rules()
    total = sum(len(v) for v in rules.values())
    if total == 18:
        _ok(f"18 rules loaded ({rules['NFPA13'].__len__()} NFPA + "
            f"{rules['California'].__len__()} CA + {rules['LAMC'].__len__()} LAMC)")
    else:
        _fail(f"expected 18 rules, got {total}")

    # 3. Blueprint
    bp = get_demo_blueprint()
    _ok(f"demo blueprint loaded ({bp.width_ft}×{bp.height_ft} ft, {len(bp.rooms)} rooms)")

    # 4. End-to-end run
    result = await MasterPlacementAgent().run(bp)
    _ok(f"50 agents executed in {result.total_elapsed_ms} ms")
    _ok(f"{len(result.sprinklers)} sprinklers placed")

    # 5. Compliance
    fails = [c for c in result.compliance if c.status == "fail"]
    if fails:
        for c in fails:
            _fail(f"{c.rule_id}: {c.detail}")
    _ok("all applicable code checks pass")

    # 6. JSON serialization (frontend compatibility)
    try:
        json.dumps(result.model_dump(mode="json"))
        _ok("output is JSON-serializable")
    except Exception as e:
        _fail(f"JSON serialization failed: {e}")

    print("\n  All checks passed. Ready to demo.\n")


if __name__ == "__main__":
    asyncio.run(main())
