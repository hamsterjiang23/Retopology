from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def write_polygon_obj(obj, path: Path) -> None:
    mesh = obj.data
    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"# Retopology benchmark Blender QuadriFlow output\n# vertices {len(mesh.vertices)} polygons {len(mesh.polygons)}\n")
        for vertex in mesh.vertices:
            co = obj.matrix_world @ vertex.co
            handle.write(f"v {co.x:.9g} {co.y:.9g} {co.z:.9g}\n")
        for polygon in mesh.polygons:
            indices = " ".join(str(index + 1) for index in polygon.vertices)
            handle.write(f"f {indices}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--target-faces", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=0)
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)

    import bpy

    args.output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if args.input.suffix.lower() in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(args.input))
    elif args.input.suffix.lower() == ".obj":
        bpy.ops.wm.obj_import(filepath=str(args.input))
    else:
        raise ValueError(f"unsupported input: {args.input}")
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not mesh_objects:
        raise RuntimeError("input contains no mesh objects")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in mesh_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objects[0]
    if len(mesh_objects) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    op_result = bpy.ops.object.quadriflow_remesh(
        mode="FACES",
        target_faces=args.target_faces,
        use_mesh_symmetry=False,
        use_preserve_sharp=True,
        use_preserve_boundary=True,
        preserve_attributes=False,
        smooth_normals=True,
        seed=args.seed,
    )
    output_glb = args.output_dir / "candidate.glb"
    output_obj = args.output_dir / "candidate.obj"
    if "FINISHED" not in op_result:
        report = {"status": "FAILED", "operator_result": sorted(op_result), "input": str(args.input), "target_faces": args.target_faces, "seed": args.seed, "duration_s": round(time.perf_counter() - started, 4)}
        (args.output_dir / "blender_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 1
    bpy.ops.export_scene.gltf(filepath=str(output_glb), export_format="GLB", export_apply=True)
    write_polygon_obj(obj, output_obj)
    report = {
        "status": "SUCCESS",
        "input": str(args.input),
        "output_glb": str(output_glb),
        "output_obj": str(output_obj),
        "target_faces": args.target_faces,
        "seed": args.seed,
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "duration_s": round(time.perf_counter() - started, 4),
    }
    (args.output_dir / "blender_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
