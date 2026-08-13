# 未闭环路线继续执行状态

本轮继续实验使用同一 Meshy 幽灵乐手模型，独立输出目录为
`E:\\skills\\model_process\\meshy\\retopo_cross_method_20260813`。

| 路线 | raw | controlled | 当前结论 |
|---|---|---|---|
| MeshFlow | ENV_BLOCKED | ENV_BLOCKED | gated checkpoint 需要 HF_TOKEN；WSL 修正版依赖安装在 torch import 前停滞 |
| LATO.2 | ENV_BLOCKED | ENV_BLOCKED | WSL 无 nvcc；CUDA toolkit 安装恢复后仍未提供编译器，o_voxel 未构建 |
| MeshAnything V2 | ENV_BLOCKED（候选待取回） | ENV_BLOCKED（候选待取回） | Mac mc_level=4、batch=1、MPS 已进入 Generation Start；随后 Mac Studio SSH 不可达 |
| NeurCross | FAILED / COMPONENT_SUCCESS 既有证据 | COMPONENT_SUCCESS 既有证据 | 已 clone libQEx/OpenMesh；OpenMesh 构建成功，libQEx demo 与 OpenMesh 11 API 不兼容 |
| QuadWild | LICENSE_BLOCKED | LICENSE_BLOCKED | 未配置 Gurobi license，保留 `gurobi_c++.h` 阻塞 |
| QuadGPT | OFFICIAL_CODE_BLOCKED | OFFICIAL_CODE_BLOCKED | 未验证到完整官方本地 inference/checkpoint |
| SQuadGen | OFFICIAL_CODE_BLOCKED | OFFICIAL_CODE_BLOCKED | 项目页未提供完整官方本地 inference |
| QuadLink | OFFICIAL_CODE_BLOCKED | OFFICIAL_CODE_BLOCKED | 未验证到完整官方本地 inference/checkpoint |
| TriFlow | OFFICIAL_CODE_BLOCKED | OFFICIAL_CODE_BLOCKED | 项目页/代码路线未提供完整官方本地 inference package |

状态不是成功结果：只有生成并通过统一 inspector 的 candidate 才进入几何评分。

机器状态：RTX 4070 空闲；WSL2 Ubuntu 22.04 可用；Mac Studio 在低分辨率 MPS 推理后暂时无法通过 SSH 访问。源模型 SHA-256 保持 `afca7c28c2d9b2dacf9f6eee4c2067c1150c8ab15c15428bb50935f5c44a563a`。
