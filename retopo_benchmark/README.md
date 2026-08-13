# Retopology Cross-Method Benchmark

This package benchmarks multiple retopology/remeshing routes on one fixed mesh.

## Smoke run

```powershell
E:\skills\asset_pipeline_tools_v2\isolated-runs\bone-overture-v22-20260729\runtime\asset-pipeline-venv\Scripts\python.exe -m retopo_benchmark.benchmark --existing-only
```

The default input is the existing Meshy high-resolution asset. Outputs are written to the configured external artifact directory under `E:\skills\model_process\meshy\retopo_cross_method_20260812` so large meshes do not enter git.
