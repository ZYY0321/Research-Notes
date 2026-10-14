# 测试集/整理 case 表

生成时间：2026-09-19T23:40:32+08:00
源目录：`测试集/整理`（最新带 json 的版本。`整理 2` 和 `整理_older` 是旧的无 json 包，不要混用）

## 规模

- 条目 299（图 222，XML 参考 77）
- 按 json 判定：正例 151，负例 148
- 框总数 370
- 需要数据同学看一眼的条目 45

## 按设备（仅 image_*，按 json 正负）

| 设备 | 图 | json正例 | json负例 |
|---|---:|---:|---:|
| 直板 `phone` | 25 | 11 | 14 |
| 平板 `tablet` | 36 | 25 | 11 |
| 双折叠 `bifold` | 71 | 57 | 14 |
| 阔折叠 `widefold` | 28 | 12 | 16 |
| 三折叠 `trifold` | 62 | 35 | 27 |

## 质量问题汇总

| 问题 | 条数 | 含义 |
|---|---:|---|
| `inverted_bbox` | 13 | 矩形两点未按左上-右下，y2<y1 或 x2<x1 |
| `truncated_folder_empty_shapes` | 11 | 在 truncated 文件夹但没有框 |
| `xml_normal_has_shapes` | 11 | 在 xml_normal 文件夹但标了截断/遮盖 |
| `truncated_folder_marked_normal` | 10 | 在 truncated 文件夹但 flags.正常图=true |
| `occlusion_in_truncation_set` | 6 | 截断评测集里混了遮盖框 |
| `missing_jpg` | 4 | 有 json 没有 jpg |
| `tiny_bbox` | 3 | 框高或宽 < 8px |
| `normal_folder_has_shapes` | 1 | 在 image_normal 文件夹但标了框 |

明细见 `quality-issues.json`。完整字段见 `catalog.json`。

## 评测时怎么用

1. 题目 = jpg；GT = 同名 json。
2. 页级：`flags.正常图 == true` 且 `shapes` 为空 → 负例；有框 → 正例。
3. 框级：`shapes[].points` 像素矩形 + `flags` 方向。评测前先 `min/max` 纠正倒置框。
4. XML 只参考，不作为是否截断的依据。
5. 文件夹名和 json 冲突时，**以 json 为准**，冲突条目先排除或请数据同学改。
