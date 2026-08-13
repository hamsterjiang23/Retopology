"""Helpers for the second retopology continuation batch.

This module deliberately does not download credentials or run models.  It
creates reproducible route directories and records external command outcomes;
model-specific commands are launched by the corresponding Windows/WSL/Mac
adapters so their native logs remain intact.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from retopo_benchmark.core import json_dump, sha256


STATUSES = {
    "SUCCESS", "FAILED", "AUTH_BLOCKED", "LICENSE_BLOCKED", "OFFICIAL_CODE_BLOCKED",
    "COMPONENT_SUCCESS", "CONTROLLED_DERIVED", "ENV_BLOCKED", "OUT_OF_BUDGET",
}


def write_status(route_dir: Path, status: str, *, exit_code: int | None = None,
                 note: str = "", duration_s: float | None = None,
                 command: list[str] | None = None) -> Path:
    if status not in STATUSES:
        raise ValueError(f"unsupported continuation status: {status}")
    route_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "exit_code": exit_code,
        "duration_s": duration_s,
        "note": note,
        "command": command or [],
    }
    json_dump(route_dir / "continuation_status.json", payload)
    lines = [f"STATUS={status}"]
    if exit_code is not None:
        lines.append(f"EXIT_CODE={exit_code}")
    if duration_s is not None:
        lines.append(f"DURATION_S={duration_s:.4f}")
    if note:
        lines.append(f"NOTE={note}")
    (route_dir / "run_status.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return route_dir / "run_status.txt"


def manifest(source: Path, output_root: Path) -> dict[str, object]:
    payload = {
        "schema": "RetopologyContinuationBatch.v1",
        "source": str(source),
        "source_sha256": sha256(source),
        "output_root": str(output_root),
        "routes": ["meshflow", "lato2", "meshanythingv2", "neurcross", "quadwild", "quadgpt", "squadgen", "quadlink", "triflow"],
    }
    json_dump(output_root / "reports" / "continuation_manifest.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    print(json.dumps(manifest(args.source, args.out), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
