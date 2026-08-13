from __future__ import annotations

import tempfile
from pathlib import Path

from retopo_benchmark.core import sha256, validate_status
from retopo_benchmark.metrics import inspect_candidate, obj_polygon_counts


def write_tetrahedron(path: Path) -> None:
    path.write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
        "f 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n",
        encoding="utf-8",
    )


def test_topology_and_geometry_metrics() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        reference = root / "reference.obj"
        candidate = root / "candidate.obj"
        write_tetrahedron(reference)
        write_tetrahedron(candidate)
        metrics = inspect_candidate(reference, candidate)
        assert metrics["status"] == "success"
        assert metrics["triangles"] == 4
        assert metrics["components"] == 1
        assert metrics["watertight"] is True
        assert metrics["geometry"]["chamfer"] == 0.0
        assert obj_polygon_counts(candidate)["triangles"] == 4
        assert sha256(reference) == sha256(candidate)


def test_status_validation() -> None:
    assert validate_status("ENV_BLOCKED") == "ENV_BLOCKED"

