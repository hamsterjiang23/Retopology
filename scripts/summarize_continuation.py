"""Inspect continuation route directories and write deterministic A/B summaries."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from retopo_benchmark.metrics import inspect_candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows: list[dict[str, object]] = []
    runs = args.out / "runs"
    for status_file in sorted(runs.rglob("continuation_status.json")):
        route = status_file.parent
        rel = route.relative_to(runs).parts
        if len(rel) < 3:
            continue
        method, lane, budget = rel[0], rel[1], rel[2]
        status = json.loads(status_file.read_text(encoding="utf-8"))
        candidates = [route / name for name in ("candidate.obj", "candidate.glb", "candidate.ply", "candidate.stl")]
        candidate = next((p for p in candidates if p.exists()), None)
        metrics = inspect_candidate(args.source, candidate) if candidate else {}
        rows.append({
            "method": method,
            "lane": lane,
            "budget": budget,
            "status": "SUCCESS" if candidate and metrics.get("status") == "success" else status["status"],
            "candidate": str(candidate) if candidate else "",
            "duration_s": status.get("duration_s"),
            "exit_code": status.get("exit_code"),
            "note": status.get("note", ""),
            "metrics": metrics,
        })
    args.out.joinpath("reports").mkdir(parents=True, exist_ok=True)
    args.out.joinpath("reports", "continuation_results.json").write_text(
        json.dumps({"schema": "RetopologyContinuationResults.v1", "source": str(args.source), "results": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with args.out.joinpath("reports", "continuation_summary.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", "lane", "budget", "status", "candidate", "duration_s", "exit_code", "note"])
        writer.writeheader()
        writer.writerows({k: row[k] for k in writer.fieldnames} for row in rows)
    print(json.dumps({"results": len(rows), "successful_candidates": sum(row["status"] == "SUCCESS" for row in rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
