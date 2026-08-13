from __future__ import annotations

import csv
import json
from pathlib import Path


FORMAL_ROOT = Path(r"E:\skills\model_process\meshy\retopo_cross_method_20260812")
REPO_ROOT = Path(__file__).resolve().parents[1]


def f(value: str | None) -> str:
    if value in (None, "", "None"):
        return "—"
    try:
        return f"{float(value):.6f}"
    except ValueError:
        return value


def main() -> int:
    rows = list(csv.DictReader((FORMAL_ROOT / "reports" / "summary.csv").open(encoding="utf-8-sig")))
    focus = [row for row in rows if row["method"] in {"instant_meshes", "quadri_flow", "blender_quadriflow"}]
    lines = [
        "# Meshy 幽灵乐手：重拓扑 A/B 对照",
        "",
        "同一公共输入分别走 raw（原始 GLB 转 geometry-only OBJ）与 controlled（CGAL 修复后的 OBJ）两条线；几何误差都以原始高模为 reference。",
        "",
        "## 可运行路线",
        "",
        "| 方法 | 输入线 | 预算 | 状态 | 顶点 | 三角形 | Quad ratio | 组件 | Chamfer | Hausdorff p99 | 时间(s) |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in focus:
        lines.append(
            f"| {row['method']} | {row['lane']} | {row['budget']} | {row['status']} | {f(row['vertices'])} | {f(row['triangles'])} | {f(row['quad_ratio'])} | {f(row['components'])} | {f(row['chamfer'])} | {f(row['hausdorff_p99'])} | {f(row['duration_s'])} |"
        )
    lines += [
        "",
        "## 读法",
        "",
        "- 原生 QuadriFlow 与 Instant Meshes 均对 raw/controlled 四格成功；两者输出均为纯四边形 OBJ。",
        "- controlled 通常比 raw 降低几何误差与组件碎裂，但不保证 watertight；组件数和边界边必须结合预览检查。",
        "- Blender 4.5.11 的同名 QuadriFlow operator 对四格均 FAILED，而原生 CLI 成功；这不是算法结论，而是入口/前置条件差异。",
        "- 生成式/研究路线必须等到有 candidate mesh 后才进入同一表格；仅有 tokenizer、论文或未完成权重不计作 SUCCESS。",
        "",
        "## 研究部署状态",
        "",
        "详见正式报告的 `results.json`、各 run 目录日志和 `DEPLOYMENT_STATUS.json`。状态只描述实测环境与阻塞证据，不把论文声称当作本地结果。",
    ]
    text = "\n".join(lines) + "\n"
    (FORMAL_ROOT / "reports" / "AB_COMPARISON.md").write_text(text, encoding="utf-8-sig")
    (REPO_ROOT / "reports").mkdir(exist_ok=True)
    (REPO_ROOT / "reports" / "AB_COMPARISON.md").write_text(text, encoding="utf-8")

    deployment = {
        "schema": "RetopologyDeploymentEvidence.v1",
        "source_sha256": "afca7c28c2d9b2dacf9f6eee4c2067c1150c8ab15c15428bb50935f5c44a563a",
        "routes": [
            {"method": "instant_meshes", "status": "SUCCESS", "evidence": "official Windows binary batch CLI; raw/controlled × low/medium all exit 0"},
            {"method": "quadri_flow", "status": "SUCCESS", "evidence": "official source cloned and built in WSL; raw/controlled × low/medium all exit 0"},
            {"method": "blender_quadriflow", "status": "FAILED", "evidence": "Blender 4.5.11 operator CANCELLED on all four inputs"},
            {"method": "sato_tokenizer", "status": "COMPONENT_TESTED_RESOURCE_BLOCKED", "evidence": "official test_tokenizer.py: 17 tests OK; raw/controlled full Meshy tokenizer smoke exceeded four minutes at about 2.1GB RAM; no generator/checkpoint released"},
            {"method": "meshmosaic", "status": "ENV_BLOCKED", "evidence": "official repo cloned; README release todo still lists checkpoints/inference/preprocessing/training"},
            {"method": "meshflow", "status": "ENV_BLOCKED", "evidence": "official pins were unsatisfiable; corrected torch 2.7.1/torchvision 0.22.1 CUDA install was attempted but stalled before torch import, and HF facebook/meshflow denied access: Mac HTTP 403, Windows HTTP 401"},
            {"method": "lato2", "status": "ENV_BLOCKED", "evidence": "Mac MPS smoke failed on missing TRELLIS o_voxel custom extension"},
            {"method": "meshanythingv2", "status": "FAILED_RESOURCE", "evidence": "Mac local checkpoints loaded; raw and controlled MPS plus CPU-fallback generation both terminated with code 137 before candidate output"},
            {"method": "neurcross", "status": "COMPONENT_AB_TESTED", "evidence": "Mac controlled one-iteration cross-field training completed; raw failed in non-manifold rotation precompute; no final mesh extraction"},
            {"method": "quadwild", "status": "ENV_BLOCKED", "evidence": "source build blocked by unconditional gurobi_c++.h include"},
            {"method": "retopoflow", "status": "INTERACTIVE_ONLY", "evidence": "official Blender plugin cloned; not a stable batch adapter"},
            {"method": "autoremesher", "status": "CLONED_NOT_RUN", "evidence": "official source cloned; native GUI/build adapter remains to be wired"},
        ],
    }
    (FORMAL_ROOT / "reports" / "DEPLOYMENT_STATUS.json").write_text(json.dumps(deployment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPO_ROOT / "reports" / "DEPLOYMENT_STATUS.json").write_text(json.dumps(deployment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
