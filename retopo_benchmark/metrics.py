from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np


def load_trimesh(path: Path):
    import trimesh

    loaded = trimesh.load(path, force="scene", process=False)
    if isinstance(loaded, trimesh.Scene):
        meshes = [g for g in loaded.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not meshes:
            raise ValueError(f"no mesh geometry in {path}")
        return trimesh.util.concatenate(meshes)
    return loaded


def obj_polygon_counts(path: Path) -> dict[str, int]:
    counts = {"triangles": 0, "quads": 0, "ngons": 0}
    if path.suffix.lower() != ".obj" or not path.exists():
        return counts
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("f "):
            continue
        sides = len(line.split()) - 1
        if sides == 3:
            counts["triangles"] += 1
        elif sides == 4:
            counts["quads"] += 1
        elif sides > 4:
            counts["ngons"] += 1
    return counts


def topology_metrics(path: Path) -> dict[str, Any]:
    mesh = load_trimesh(path)
    # OBJ loaders split a shared position whenever face-normal or UV indices
    # differ.  Topology metrics must operate on geometric vertices instead.
    mesh.merge_vertices(merge_tex=True, merge_norm=True)
    faces = np.asarray(mesh.faces)
    vertices = np.asarray(mesh.vertices)
    polygon_counts = obj_polygon_counts(path)
    edge_lengths = mesh.edges_unique_length if len(mesh.edges_unique) else np.array([], dtype=float)
    values = edge_lengths[edge_lengths > 1e-12]
    edge_cv = float(np.std(values) / np.mean(values)) if len(values) else None
    valence = np.bincount(mesh.edges_unique.reshape(-1), minlength=len(vertices)) if len(mesh.edges_unique) else np.array([], dtype=int)
    edge_use = np.bincount(mesh.edges_unique_inverse, minlength=len(mesh.edges_unique)) if len(mesh.edges_unique) else np.array([], dtype=int)
    boundary_edges = int(np.sum(edge_use == 1)) if len(edge_use) else None
    non_manifold_edges = int(np.sum(edge_use > 2)) if len(edge_use) else None
    return {
        "vertices": int(len(vertices)),
        "triangles": int(len(faces)),
        "components": int(len(mesh.split(only_watertight=False))),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "open_boundary_edges": boundary_edges,
        "non_manifold_edges": non_manifold_edges,
        "degenerate_faces": int(np.sum(mesh.area_faces < 1e-12)),
        "self_intersection_pairs": None,
        "has_uv": bool(getattr(mesh.visual, "uv", None) is not None),
        "material_count": int(len(mesh.visual.materials)) if hasattr(mesh.visual, "materials") else 0,
        "polygon_counts": polygon_counts,
        "quad_ratio": float(polygon_counts["quads"] / max(sum(polygon_counts.values()), 1)) if path.suffix.lower() == ".obj" else None,
        "edge_length_cv": edge_cv,
        "valence_mean": float(np.mean(valence)) if len(valence) else None,
        "valence_std": float(np.std(valence)) if len(valence) else None,
    }


def sample_points(path: Path, count: int = 50_000, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    import trimesh

    mesh = load_trimesh(path)
    sample_count = min(count, max(len(mesh.faces) * 3, 1))
    points, face_idx = trimesh.sample.sample_surface(mesh, sample_count, seed=seed)
    normals = np.asarray(mesh.face_normals)[face_idx]
    return np.asarray(points, dtype=np.float64), np.asarray(normals, dtype=np.float64)


def geometric_metrics(reference: Path, candidate: Path, count: int = 50_000) -> dict[str, Any]:
    try:
        from scipy.spatial import cKDTree

        if _sha256(reference) == _sha256(candidate):
            return {"chamfer": 0.0, "hausdorff_p95": 0.0, "hausdorff_p99": 0.0, "hausdorff_max": 0.0, "normal_consistency": 1.0, "samples": 0, "identical_sha256": True}

        ref_points, ref_normals = sample_points(reference, count=count, seed=0)
        out_points, out_normals = sample_points(candidate, count=count, seed=0)
        ref_tree = cKDTree(ref_points)
        out_tree = cKDTree(out_points)
        ref_dist, ref_idx = ref_tree.query(out_points)
        out_dist, out_idx = out_tree.query(ref_points)
        distances = np.concatenate([ref_dist, out_dist])
        normal_cos = np.abs(np.sum(out_normals * ref_normals[ref_idx], axis=1))
        return {
            "chamfer": float(np.mean(distances)),
            "hausdorff_p95": float(np.percentile(distances, 95)),
            "hausdorff_p99": float(np.percentile(distances, 99)),
            "hausdorff_max": float(np.max(distances)),
            "normal_consistency": float(np.mean(normal_cos)),
            "samples": int(len(distances)),
        }
    except Exception as exc:
        return {"status": "not_evaluated", "reason": str(exc)}


def inspect_candidate(reference: Path, candidate: Path | None) -> dict[str, Any]:
    if candidate is None or not candidate.exists():
        return {"status": "missing"}
    try:
        topology = topology_metrics(candidate)
        topology["bytes"] = candidate.stat().st_size
        topology["sha256"] = _sha256(candidate)
        topology["geometry"] = geometric_metrics(reference, candidate)
        topology["status"] = "success"
        return topology
    except Exception as exc:
        return {"status": "inspection_failed", "reason": str(exc)}


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
