from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh

def run(input_path: Path, serialize, deserialize) -> dict[str, object]:
    mesh = trimesh.load(input_path, force="mesh", process=False)
    vertices = np.asarray(mesh.vertices, dtype=np.float32)
    faces = np.asarray(mesh.faces, dtype=np.int64)
    center = (vertices.min(axis=0) + vertices.max(axis=0)) / 2
    scale = np.abs(vertices - center).max()
    normalized = (vertices - center) / max(float(scale), 1e-8)
    class Mesh:
        pass
    m = Mesh()
    m.vertices, m.faces = normalized, faces
    tokens = serialize(m, max_strip_faces=20)
    decoded_vertices, decoded_faces, uv_labels = deserialize(tokens)
    return {
        "input": str(input_path),
        "input_vertices": int(len(vertices)),
        "input_faces": int(len(faces)),
        "tokens": int(len(tokens)),
        "decoded_vertices": int(len(decoded_vertices)),
        "decoded_faces": int(len(decoded_faces)),
        "uv_components": int(len(np.unique(uv_labels))),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    import sys
    sys.path.insert(0, str(root / "vendor" / "sato"))
    global serialize, deserialize
    from sato_tokenizer import deserialize, serialize
    rows = [run(root / "inputs" / name, serialize, deserialize) for name in ("raw.obj", "controlled.obj")]
    out = root / "reports" / "sato_ab.json"
    out.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rows, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
