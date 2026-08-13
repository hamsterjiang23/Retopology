"""Export a GLB/GLTF scene as one geometry-only OBJ for native remesh tools."""
from __future__ import annotations

import argparse
from pathlib import Path

import bpy


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    import sys
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(Path(args.input)))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("input contains no mesh objects")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = "geometry"
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.obj_export(filepath=str(Path(args.output)), export_materials=False, export_uv=False, export_normals=False)
    print(f"EXPORTED {args.output} vertices={len(obj.data.vertices)} polygons={len(obj.data.polygons)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
