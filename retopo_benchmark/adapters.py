from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .core import RouteResult, command_exists, run_command, validate_status
from .metrics import inspect_candidate


class Adapter:
    method = "base"

    def preflight(self) -> tuple[bool, str]:
        return True, ""

    def run(self, input_path: Path, out_dir: Path, *, lane: str, budget: str, seed: int | None) -> RouteResult:
        raise NotImplementedError


class ExistingOutputAdapter(Adapter):
    def __init__(self, method: str, existing_path: Path, reference: Path, note: str = "") -> None:
        self.method = method
        self.existing_path = existing_path
        self.reference = reference
        self.note = note

    def run(self, input_path: Path, out_dir: Path, *, lane: str, budget: str, seed: int | None) -> RouteResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        if not self.existing_path.exists():
            return RouteResult(self.method, lane, budget, seed, "FAILED", str(input_path), notes="existing result missing")
        output = out_dir / self.existing_path.name
        if output.resolve() != self.existing_path.resolve():
            shutil.copy2(self.existing_path, output)
        return RouteResult(
            self.method, lane, budget, seed, "SUCCESS", str(input_path), str(output),
            metrics=inspect_candidate(self.reference, output), notes=self.note,
        )


class CommandAdapter(Adapter):
    def __init__(self, method: str, command: list[str], output_name: str, reference: Path, *, cwd: Path | None = None, timeout_s: int = 3600, notes: str = "") -> None:
        self.method, self.command, self.output_name, self.reference = method, command, output_name, reference
        self.cwd, self.timeout_s, self.notes = cwd, timeout_s, notes

    def preflight(self) -> tuple[bool, str]:
        if not self.command:
            return False, "empty command"
        if not command_exists(self.command[0]):
            return False, f"missing executable: {self.command[0]}"
        return True, ""

    def run(self, input_path: Path, out_dir: Path, *, lane: str, budget: str, seed: int | None) -> RouteResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        ok, reason = self.preflight()
        if not ok:
            return RouteResult(self.method, lane, budget, seed, validate_status("ENV_BLOCKED"), str(input_path), notes=reason)
        command = [arg.replace("{input}", str(input_path)).replace("{output}", str(out_dir / self.output_name)).replace("{seed}", str(seed or 0)) for arg in self.command]
        run = run_command(command, cwd=self.cwd, log_dir=out_dir)
        output = out_dir / self.output_name
        status = run["status"] if output.exists() else "FAILED"
        result = RouteResult(self.method, lane, budget, seed, status, str(input_path), str(output) if output.exists() else None, run["duration_s"], command, notes=self.notes, error=run.get("stderr", ""))
        if output.exists():
            result.metrics = inspect_candidate(self.reference, output)
        return result
