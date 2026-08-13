from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
from pathlib import Path
from typing import Any

from .adapters import ExistingOutputAdapter
from .core import RouteResult, copy_with_hash, environment_snapshot, json_dump, run_command, sha256
from .metrics import inspect_candidate


DEFAULT_SOURCE = Path(r"E:\skills\model_process\meshy\remesh_evaluation_20260806\00_source\meshy_high_original.glb")
DEFAULT_EXISTING_ROOT = Path(r"E:\skills\model_process\meshy\remesh_evaluation_20260806")
DEFAULT_OUT = Path(r"E:\skills\model_process\meshy\retopo_cross_method_20260812")


def snapshot_inputs(source: Path, out_root: Path) -> dict[str, Any]:
    inputs = out_root / "00_inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    raw = inputs / "raw.glb"
    copy_with_hash(source, raw)
    raw_hash = sha256(raw)
    controlled_source = DEFAULT_EXISTING_ROOT / "02_remesh_backends" / "cgal-local" / "run" / "candidates" / "cgal-local" / "candidate.glb"
    controlled = inputs / "controlled_cgal.glb"
    controlled_info = None
    if controlled_source.exists():
        controlled_info = copy_with_hash(controlled_source, controlled)
    payload = {
        "source": str(source),
        "source_sha256": sha256(source),
        "raw_snapshot": str(raw),
        "raw_snapshot_sha256": raw_hash,
        "controlled_snapshot": str(controlled) if controlled_info else None,
        "controlled_snapshot_sha256": controlled_info["sha256"] if controlled_info else None,
        "source_unchanged": sha256(source) == raw_hash,
        "environment": environment_snapshot(),
    }
    json_dump(inputs / "manifest.json", payload)
    return payload


def existing_adapters(source: Path, out_root: Path) -> list[ExistingOutputAdapter]:
    root = DEFAULT_EXISTING_ROOT
    candidates = {
        "openvdb": root / "02_remesh_backends" / "openvdb" / "run" / "selected" / "candidate.glb",
        "manifold_autoremesher": root / "04_autoremesher" / "meshy_manifold_autoremesher.glb",
        "remote_retopology": root / "05_remote" / "retopology" / "meshy_remote_retopology.glb",
        "fast_simplification_300k": root / "06_local_comparators" / "01_fast_simplification_300k" / "candidate.glb",
        "cgal_repair": root / "02_remesh_backends" / "cgal-local" / "run" / "candidates" / "cgal-local" / "candidate.glb",
    }
    notes = {
        "openvdb": "existing local baseline; voxel reconstruction",
        "manifold_autoremesher": "existing two-stage baseline",
        "remote_retopology": "existing remote PyMeshLab triangle retopology",
        "fast_simplification_300k": "existing decimation control, not retopology",
        "cgal_repair": "existing controlled-quality input candidate",
    }
    return [ExistingOutputAdapter(name, path, source, notes[name]) for name, path in candidates.items()]


def run_existing(source: Path, out_root: Path, input_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    controlled_input = Path(input_manifest["controlled_snapshot"]) if input_manifest.get("controlled_snapshot") else source
    for adapter in existing_adapters(source, out_root):
        for lane, budget in (("raw", "native"), ("controlled", "native")):
            input_path = source if lane == "raw" else controlled_input
            result = adapter.run(input_path, out_root / "runs" / lane / adapter.method / budget, lane=lane, budget=budget, seed=None)
            results.append(result.as_dict())
    return results


def discovered_results(source: Path, out_root: Path) -> list[dict[str, Any]]:
    """Import normalized outputs produced by native, remote, or model adapters."""
    ignored = {"openvdb", "manifold_autoremesher", "remote_retopology", "fast_simplification_300k", "cgal_repair", "blender_quadriflow"}
    results: list[dict[str, Any]] = []
    runs_root = out_root / "runs"
    if not runs_root.exists():
        return results
    for lane_dir in sorted(path for path in runs_root.iterdir() if path.is_dir()):
        for method_dir in sorted(path for path in lane_dir.iterdir() if path.is_dir() and path.name not in ignored):
            for budget_dir in sorted(path for path in method_dir.iterdir() if path.is_dir()):
                candidates = [budget_dir / f"candidate{suffix}" for suffix in (".obj", ".glb", ".ply", ".stl")]
                output = next((path for path in candidates if path.exists()), None)
                duration = 0.0
                status_file = budget_dir / "run_status.txt"
                run_status = ""
                run_note = "discovered normalized adapter output"
                if status_file.exists():
                    run_status = status_file.read_text(encoding="utf-8", errors="replace")
                    match = re.search(r"DURATION_S=([0-9.]+)", run_status)
                    if match:
                        duration = float(match.group(1))
                    note_match = re.search(r"NOTE=(.+)", run_status)
                    if note_match:
                        run_note = note_match.group(1).strip()
                status_match = re.search(r"STATUS=([A-Z_]+)", run_status)
                declared_status = status_match.group(1) if status_match else ""
                supported_statuses = {
                    "FAILED", "AUTH_BLOCKED", "LICENSE_BLOCKED", "OFFICIAL_CODE_BLOCKED",
                    "COMPONENT_SUCCESS", "CONTROLLED_DERIVED", "OUT_OF_BUDGET", "ENV_BLOCKED",
                }
                if output is None and declared_status not in supported_statuses:
                    continue
                if output is None:
                    results.append({
                        "method": method_dir.name, "lane": lane_dir.name, "budget": budget_dir.name,
                        "seed": 0, "status": declared_status or "FAILED", "input_path": str(source), "output_path": None,
                        "duration_s": duration, "command": [], "metrics": {}, "notes": run_note,
                        "error": run_note,
                    })
                    continue
                results.append({
                    "method": method_dir.name,
                    "lane": lane_dir.name,
                    "budget": budget_dir.name,
                    "seed": 0,
                    "status": "SUCCESS",
                    "input_path": str(source),
                    "output_path": str(output),
                    "duration_s": duration,
                    "command": [],
                    "metrics": inspect_candidate(source, output),
                    "notes": run_note,
                    "error": "",
                })
    return results


def blocked_research_results(source: Path, out_root: Path, completed_methods: set[str] | None = None) -> list[dict[str, Any]]:
    routes = [
        ("meshflow", "research", "native", "official facebook/meshflow checkpoint is gated; Hugging Face returned HTTP 403 on Mac and HTTP 401 on Windows"),
        ("lato2", "research", "native", "Mac MPS smoke reached import but failed because TRELLIS custom extension o_voxel is unavailable; upstream setup requires CUDA 12.4/NVCC"),
        ("meshanythingv2", "research", "low_faces", "Mac local checkpoints loaded and SDPA/MPS fallback reached generation for raw and controlled; both processes terminated with code 137 before candidate output"),
        ("neurcross", "research", "native", "Mac controlled one-iteration cross-field training completed but no final mesh extraction; raw A/B failed in rotation precompute with non-manifold adjacency KeyError"),
        ("quadwild", "traditional_quad", "native", "source build reaches qr_ilp.h but fails on unconditional gurobi_c++.h include; Gurobi SDK/license is required"),
        ("instant_meshes", "interactive", "native", "interactive GUI route; no stable batch adapter yet"),
        ("retopoflow", "interactive", "native", "official Blender plugin cloned; artist-guided route intentionally excluded from automatic score"),
        ("sato_tokenizer", "research", "native", "tokenizer-only release; no complete inference route"),
        ("meshmosaic", "research", "native", "official repository cloned; README release checklist still marks pretrained checkpoints, inference, preprocessing and training as pending"),
        ("quadgpt", "research", "native", "no complete local inference code verified"),
        ("squadgen", "research", "native", "paper-stage reproduction route"),
        ("quadlink", "research", "native", "paper/preprint-stage reproduction route"),
        ("triflow", "research", "native", "code announced but not available in local inventory"),
    ]
    results = []
    completed_methods = completed_methods or set()
    for method, lane, budget, note in routes:
        if method in completed_methods:
            continue
        status = "INTERACTIVE_ONLY" if lane == "interactive" else "ENV_BLOCKED"
        results.append({"method": method, "lane": lane, "budget": budget, "seed": None, "status": status, "input_path": str(source), "output_path": None, "duration_s": 0.0, "command": [], "metrics": {}, "notes": note, "error": note})
    return results


def run_blender_quadriflow(source: Path, out_root: Path, input_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    blender = Path(r"E:\Blender 4.5.11\blender.exe")
    script = Path(__file__).with_name("blender_quadriflow.py")
    if not blender.exists():
        return [{"method": "blender_quadriflow", "lane": "raw", "budget": "low_faces", "seed": 0, "status": "ENV_BLOCKED", "input_path": str(source), "notes": "Blender executable missing"}]
    results: list[dict[str, Any]] = []
    controlled = Path(input_manifest["controlled_snapshot"]) if input_manifest.get("controlled_snapshot") else source
    for lane, input_path in (("raw", source), ("controlled", controlled)):
        for budget, target in (("low_faces", 2000), ("medium_faces", 4000)):
            route_dir = out_root / "runs" / lane / "blender_quadriflow" / budget
            command = [str(blender), "--background", "--python", str(script), "--", "--input", str(input_path), "--output-dir", str(route_dir), "--target-faces", str(target), "--seed", "0"]
            execution = run_command(command, cwd=out_root, log_dir=route_dir, timeout_s=900)
            report_path = route_dir / "blender_report.json"
            report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
            output = Path(report["output_glb"]) if report.get("status") == "SUCCESS" and report.get("output_glb") else None
            status = report.get("status", execution["status"])
            results.append({
                "method": "blender_quadriflow", "lane": lane, "budget": budget, "seed": 0,
                "status": status, "input_path": str(input_path), "output_path": str(output) if output else None,
                "duration_s": execution["duration_s"], "command": command,
                "metrics": inspect_candidate(source, output) if output else {},
                "notes": "Blender 4.5.11 QuadriFlow operator",
                "error": execution.get("stderr", "") if status != "SUCCESS" else "",
            })
    return results


def build_report(out_root: Path, input_manifest: dict[str, Any], results: list[dict[str, Any]]) -> None:
    payload = {
        "schema": "RetopologyCrossMethodEvaluation.v1",
        "input": input_manifest,
        "results": results,
    }
    json_dump(out_root / "reports" / "results.json", payload)
    rows = []
    for item in results:
        metrics = item.get("metrics", {})
        geometry = metrics.get("geometry", {}) if isinstance(metrics, dict) else {}
        rows.append({
            "method": item["method"], "lane": item["lane"], "budget": item["budget"], "seed": item.get("seed"),
            "status": item["status"], "vertices": metrics.get("vertices"), "triangles": metrics.get("triangles"),
            "quad_ratio": metrics.get("quad_ratio"), "watertight": metrics.get("watertight"),
            "components": metrics.get("components"), "chamfer": geometry.get("chamfer"),
            "hausdorff_p99": geometry.get("hausdorff_p99"), "normal_consistency": geometry.get("normal_consistency"),
            "duration_s": item.get("duration_s"), "notes": item.get("notes", ""),
        })
    import csv

    csv_path = out_root / "reports" / "summary.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["method", "status"])
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# 重拓扑跨方法横评（Meshy 幽灵乐手）",
        "",
        f"- 输入：`{input_manifest['source']}`",
        f"- SHA-256：`{input_manifest['source_sha256']}`",
        "- 当前阶段：已有基线、原生工具输出和可定位的研究模型部署状态统一纳入。",
        "",
        "## 结果入口",
        "",
        "- [结构化结果](results.json)",
        "- [CSV 汇总](summary.csv)",
        "- [运行目录](../runs/)",
        "",
        "## 状态统计",
        "",
    ]
    counts: dict[str, int] = {}
    for item in results:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    lines.extend(f"- `{status}`：{count}" for status, count in sorted(counts.items()))
    lines.extend(["", "## 说明", "", "几何距离以原始高模为 reference；quad ratio 只对保留 polygon face 的 OBJ 有效。生成式方法的几何变化、孔洞和组件变化必须结合统一预览人工复核。"])
    (out_root / "reports" / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--existing-only", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = snapshot_inputs(args.source, args.out)
    discovered = discovered_results(args.source, args.out)
    completed_methods = {item["method"] for item in discovered if item["status"] == "SUCCESS"}
    results = run_existing(args.source, args.out, manifest) + run_blender_quadriflow(args.source, args.out, manifest) + discovered + blocked_research_results(args.source, args.out, completed_methods)
    build_report(args.out, manifest, results)
    print(json.dumps({"out": str(args.out), "results": len(results), "source_unchanged": manifest["source_unchanged"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
