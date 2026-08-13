# Meshy 幽灵乐手：重拓扑 A/B 对照

同一公共输入分别走 raw（原始 GLB 转 geometry-only OBJ）与 controlled（CGAL 修复后的 OBJ）两条线；几何误差都以原始高模为 reference。

## 可运行路线

| 方法 | 输入线 | 预算 | 状态 | 顶点 | 三角形 | Quad ratio | 组件 | Chamfer | Hausdorff p99 | 时间(s) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| blender_quadriflow | raw | low_faces | FAILED | — | — | — | — | — | — | 4.614000 |
| blender_quadriflow | raw | medium_faces | FAILED | — | — | — | — | — | — | 1.053900 |
| blender_quadriflow | controlled | low_faces | FAILED | — | — | — | — | — | — | 0.791600 |
| blender_quadriflow | controlled | medium_faces | FAILED | — | — | — | — | — | — | 0.761500 |
| instant_meshes | controlled | low_faces | SUCCESS | 6796.000000 | 12920.000000 | 1.000000 | 291.000000 | 0.008500 | 0.055274 | 0.000000 |
| instant_meshes | controlled | medium_faces | SUCCESS | 14917.000000 | 29442.000000 | 1.000000 | 229.000000 | 0.005298 | 0.020810 | 2.845285 |
| quadri_flow | controlled | low_faces | SUCCESS | 1278.000000 | 2522.000000 | 1.000000 | 12.000000 | 0.032853 | 0.217201 | 13.365892 |
| quadri_flow | controlled | medium_faces | SUCCESS | 3327.000000 | 6650.000000 | 1.000000 | 35.000000 | 0.012838 | 0.091535 | 14.856856 |
| instant_meshes | raw | low_faces | SUCCESS | 7140.000000 | 11546.000000 | 1.000000 | 1713.000000 | 0.011329 | 0.060520 | 2.663073 |
| instant_meshes | raw | medium_faces | SUCCESS | 15687.000000 | 25202.000000 | 1.000000 | 1532.000000 | 0.006700 | 0.027857 | 2.788959 |
| quadri_flow | raw | low_faces | SUCCESS | 1581.000000 | 2546.000000 | 1.000000 | 286.000000 | 0.047895 | 0.236049 | 16.170332 |
| quadri_flow | raw | medium_faces | SUCCESS | 3763.000000 | 6230.000000 | 1.000000 | 521.000000 | 0.020424 | 0.111415 | 26.399921 |

## 读法

- 原生 QuadriFlow 与 Instant Meshes 均对 raw/controlled 四格成功；两者输出均为纯四边形 OBJ。
- controlled 通常比 raw 降低几何误差与组件碎裂，但不保证 watertight；组件数和边界边必须结合预览检查。
- Blender 4.5.11 的同名 QuadriFlow operator 对四格均 FAILED，而原生 CLI 成功；这不是算法结论，而是入口/前置条件差异。
- 生成式/研究路线必须等到有 candidate mesh 后才进入同一表格；仅有 tokenizer、论文或未完成权重不计作 SUCCESS。

## 研究部署状态

详见正式报告的 `results.json`、各 run 目录日志和 `DEPLOYMENT_STATUS.json`。状态只描述实测环境与阻塞证据，不把论文声称当作本地结果。
