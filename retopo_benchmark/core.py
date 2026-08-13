from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


STATUS = {
    "SUCCESS",
    "FAILED",
    "OUT_OF_BUDGET",
    "ENV_BLOCKED",
    "INTERACTIVE_ONLY",
    "AUTH_BLOCKED",
    "LICENSE_BLOCKED",
    "OFFICIAL_CODE_BLOCKED",
    "COMPONENT_SUCCESS",
    "CONTROLLED_DERIVED",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None or Path(command).exists()


def run_command(command: list[str], *, cwd: Path | None, log_dir: Path, timeout_s: int = 3600) -> dict[str, Any]:
    log_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            check=False,
        )
        status = "SUCCESS" if completed.returncode == 0 else "FAILED"
        result = {
            "status": status,
            "returncode": completed.returncode,
            "duration_s": round(time.perf_counter() - started, 4),
            "command": command,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        result = {
            "status": "FAILED",
            "returncode": None,
            "duration_s": round(time.perf_counter() - started, 4),
            "command": command,
            "stdout": exc.stdout or "",
            "stderr": (exc.stderr or "") + "\nTIMEOUT",
        }
    json_dump(log_dir / "command.json", result)
    (log_dir / "stdout.log").write_text(result["stdout"], encoding="utf-8")
    (log_dir / "stderr.log").write_text(result["stderr"], encoding="utf-8")
    return result


def environment_snapshot() -> dict[str, Any]:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cwd": os.getcwd(),
        "executable": sys.executable,
    }


@dataclass
class RouteResult:
    method: str
    lane: str
    budget: str
    seed: int | None
    status: str
    input_path: str
    output_path: str | None = None
    duration_s: float | None = None
    command: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    error: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_status(status: str) -> str:
    if status not in STATUS:
        raise ValueError(f"unsupported route status: {status}")
    return status


def copy_with_hash(source: Path, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {"source": str(source), "destination": str(destination), "sha256": sha256(destination), "bytes": destination.stat().st_size}


def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
