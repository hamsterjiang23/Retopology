from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .core import command_exists, environment_snapshot, json_dump


def version(command: list[str]) -> dict[str, Any]:
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
        return {"available": process.returncode == 0, "returncode": process.returncode, "stdout": process.stdout[-2000:], "stderr": process.stderr[-2000:]}
    except Exception as exc:
        return {"available": False, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    checks: dict[str, Any] = {"environment": environment_snapshot(), "executables": {}}
    for name, command in {
        "python": ["python", "--version"],
        "git": ["git", "--version"],
        "blender": [r"E:\Blender 4.5.11\blender.exe", "--version"],
        "autoremesher": [r"E:\skills\autoremesher-master\release\autoremesher.exe", "--help"],
    }.items():
        checks["executables"][name] = version(command) if command_exists(command[0]) else {"available": False, "reason": "not found"}
    checks["external_repos"] = {
        "meshflow": {"status": "not_cloned", "reason": "requires explicit dependency setup"},
        "lato2": {"status": "cuda_required", "reason": "official setup requires CUDA 12.4/NVCC"},
        "meshanythingv2": {"status": "cuda_required", "reason": "official environment uses A800/CUDA/flash-attn"},
        "neurcross": {"status": "cuda_required", "reason": "official requirements specify CUDA 11.7"},
        "quadwild": {"status": "build_required", "reason": "Boost and optional Gurobi/CoMISo dependencies"},
        "instant_meshes": {"status": "mac_or_windows_binary", "reason": "interactive reference route"},
    }
    checks["decision"] = "run_existing_baselines_first; install research dependencies only after smoke evidence"
    json_dump(args.out / "preflight.json", checks)
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
