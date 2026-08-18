# PassiveTree 候選評分與排序

本圖表使用 `pob optimize-tree-matrix` 的實際官方 PoB Headless 計算結果，資料來源為 `tree_matrix_result.json`。排序以 HC 硬性條件通過優先，再比較官方 `TotalDPS`、`TotalEHP` 與最大承受傷害 scalar delta。

| 排名 | 候選 | HC | Total DPS 變化 | Total EHP 變化 |
|---:|---|---|---:|---:|
| 1 | `remove-intelligence` | FAIL | -16.30% | -0.09% |
| 2 | `same-node-mastery` | FAIL | 0.00% | 0.00% |

本次共有 2 個候選，2 個官方重算成功，0 個候選因 TreeData 或計算錯誤失敗。兩個候選都未達 HC 硬性條件，因此圖表中的紅色標記代表 `HC FAIL`，不能直接視為可採用的 HC 升級方案。`remove-intelligence` 雖排名第一，但其 DPS 下降約 16.30%，應視為排序結果而非推薦結論。

![PassiveTree candidate ranking](tree_candidate_ranking.png)
