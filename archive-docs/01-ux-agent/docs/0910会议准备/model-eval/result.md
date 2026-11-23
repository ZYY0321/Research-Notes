# 模型评测实验（构造坏数据）

接口：`http://10.176.44.15:8000/detect`。bbox 空间 norm1000。命中规则：IoU≥0.2，或框心落在对方框内。

- 正例召回（按图）：**1/5**
- 负例未误报：**3/3**
- 只露一点 `p_sliver`：**hit**
- 大号中切 `p_mid_glyph`：**miss**

| 用例 | 极性 | 判定 | 模型框数 | TP/FP/FN | 最好 IoU | 说明 |
|---|---|---|---:|---|---:|---|
| `p_right_clip` | positive | miss | 0 | 0/0/1 | 0.00 | 局部容器右侧裁切，长标题超出卡片 |
| `p_bottom_clip` | positive | miss | 0 | 0/0/1 | 0.00 | 卡片底部裁切，末行字形被切 |
| `p_sliver` | positive | hit | 1 | 1/0/0 | 0.62 | 只露出约一行高度的 14px，测模型漏检 |
| `p_screen_bottom` | positive | miss | 0 | 0/0/1 | 0.00 | 最后一项被屏幕底边裁切，不可滚尽的视觉效果 |
| `p_mid_glyph` | positive | miss | 0 | 0/0/1 | 0.00 | 大号标题从字中间纵向切开，排除‘像完整标签’的歧义 |
| `n_clean` | negative | clean | 0 | 0/0/0 | 0.00 | 全部文字完整，负例 |
| `n_ellipsis` | negative | clean | 0 | 0/0/0 | 0.00 | 省略号，字形完整，按规则不算截断 |
| `n_wrap` | negative | clean | 0 | 0/0/0 | 0.00 | 正常换行，字符完整 |
| `w_settings` | wild | pred | 1 | 0/0/0 | 0.00 | 真实设置页（演示产物），历史模型曾报底部存储 |
| `w_lock` | wild | empty | 0 | 0/0/0 | 0.00 | 真实锁屏截图 |
| `w_settings_dump` | wild | pred | 1 | 0/0/0 | 0.00 | 实机 dump 对应截图 20260907-181501-290 |

原始 JSON 见同目录 `result.json`。构造图在 `HarmonyArena-fdu_agent/scripts/model-eval/cases/`。
