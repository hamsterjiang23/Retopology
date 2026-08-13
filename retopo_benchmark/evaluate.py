from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, stdev


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.results.read_text(encoding="utf-8"))
    groups: dict[str, list[dict]] = {}
    for result in payload.get("results", []):
        groups.setdefault(result["method"], []).append(result)
    summary = []
    for method, items in sorted(groups.items()):
        successes = [i for i in items if i.get("status") == "SUCCESS"]
        geos = [i.get("metrics", {}).get("geometry", {}) for i in successes]
        chamfers = [g["chamfer"] for g in geos if isinstance(g.get("chamfer"), (int, float))]
        summary.append({
            "method": method,
            "runs": len(items),
            "successes": len(successes),
            "success_rate": len(successes) / max(len(items), 1),
            "chamfer_mean": mean(chamfers) if chamfers else None,
            "chamfer_std": stdev(chamfers) if len(chamfers) > 1 else 0.0 if chamfers else None,
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"schema": "RetopologyCrossMethodSummary.v1", "methods": summary}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"methods": len(summary), "output": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
