# Dashboard 展示核查 + DPO 模板模式混乱归因（0708）

> 回答用户三问：①dashboard 是否有展示 bug（"生成失败的案例不少"）②DPO 模板模式很多页面混乱是模型还是展示问题 ③prod=adda7bc8 dpov1 模板模式显示 done 但没文件。
> 方法：把 dashboard `/api/index` 的每 case 页数 与 各批 `batch_summary.json` 的 `terminal_class`/`deck_quality` 对账，并回盘核验 deck 目录、mtime、图片资源。

---

## 结论速览

1. **dashboard 没有展示 bug**。你看到的"生成失败/空白"绝大多数是**生成侧真实问题**，看板如实反映（甚至它的"防假 deck"守卫是对的，见下）。
2. **DPO 模板模式页面混乱 = 模型问题，不是展示问题**。deck 解析、图片资源、`/deck` 端点全部正常；混乱来自模型自己产出的 HTML（大面积空白占位、卡片叠压、内容不足）。
3. **prod_adda7bc8 dpov1 done 无文件 = 生成侧本次没落地 deck**，看板正确判"无产物"。

---

## 一、"done 但看板无页"全量对账（11 例，全为生成侧）

| 分类 | 数量 | 性质 |
|---|---|---|
| deck_root 陈旧（指向 7-02/7-03 旧 deck，非本次产物） | 10 | 生成侧 |
| 自报有页但盘上无 deck | 1 | 生成侧 |

明细：flashv1_1(7)、step3kdpo_tpl(2: prod_1289b84a/prod_adda7bc8)、step3kdpo(1)、flash3k_tpl(1)。

**为什么看板不显示**：这些 case 的 `deck_scan_root` 指向 `output/sandbox/batch_xxx_<旧后缀>`，该目录**确实存在且有页**，但：
- 它的 basename ≠ 本次 `conv_id`；
- 回盘看 mtime 是 **07-02/07-03**，而批次跑在 **07-06/07-07** → 是**上一轮/别的日期残留在共享 sandbox 里的旧 deck**，不是本次产物。

dashboard 的 `_effective_scan_root()` 守卫（server.py:170）正是为此设计：`deck_scan_root` 只在 `basename==conv_id` 时可信，否则按 conv_id 去 `sandbox_root` 重新定位；定位不到就判无产物。**这行为是对的**——若放开，看板会把 7-02 的旧 PPT 冒充成本次结果展示，更糟。

**根因在生成侧**：本次跑批时 deck 没有以 `conv_id` 落地（skip/复用了历史 sandbox 目录，或 deck_dir 写成了旧通配路径）。`batch_summary` 里 `deck_quality.html_pages` 记的是**那个旧 deck** 的页数，所以出现"自报 8 页但看板 0 页"的错位。

> 影响：这类 case **判分侧也拿不到本次 deck** → 无分（如 flashv1_1 done 35 例里仅 34 有分）。属于生成落盘 bug，不是看板 bug。

---

## 二、DPO 模板模式"页面混乱" = 模型问题

抽 step3kdpo_tpl 最低分 3 例，读判分逐页短评 + 回盘核验原始 HTML/资源：

- **q1495**(ov=0.38) content_integrity 通过率仅 **0.16**：判分短评"页面主体内容严重缺失，仅两处黄色色块""柱状图全年加班数据均为 0"。回盘 HTML 确认：模型产出的页面本身就是**大面积空白占位 + 表格无数据**。
- **q0134**(ov=0.53)：p0/p2 判分说"主体完全空白"。回盘 page_003 原始 HTML 可见文本仅 121 字（"01 概念总览…第3页"），**图片资源 `slide-001-bg.png` 存在且能解析**——即不是图没加载，是模型只写了标题没写正文。p4"三张卡片相互叠压"也是模型 HTML 布局本身的问题。
- **q912**(ov=0.54)：p0"图片加载失败破损图标"（模型引用了不存在的图）、p3"标题称六大类型正文仅 4 项"（模型内容不自洽）。

**验证展示链路无误**：
- deck_root 选层正确（选到 `pptid_xxx/`，页在 `htmls/`，图在 `htmls_png/`）；
- `/deck/<run>/<case>/htmls/page_001.html` → 200，引用的 `../htmls_png/*.png` → 200，相对路径 `../` 跳出也 200；
- 空壳页守卫（<100B 过滤）与判分同口径。

**归因**：DPO 模板模式的混乱是**模型缺陷**——套模板时常见①占位区不填内容（content_integrity 低）②卡片/容器叠压越界（occlusion/boundary）③内容量不足撑不满版面。与失败根因分析里 DPO"premature_report_stop/爱输出文字轻落地"一致。

---

## 三、prod_adda7bc8（dpov1 模板模式）done 无文件

- `terminal_class=done`，`conv_id=batch_prod_adda7bc8_311a61`，但 **`output/sandbox/batch_prod_adda7bc8_311a61` 不存在**（本次没落地）。
- `deck_scan_root` 指向 `..._d6f363`，该目录有 19 页但 **mtime=07-02 22:18**，是旧产物（批次跑在 07-07）→ 被守卫正确拒绝。
- 同名还有 `_07638e`(07-07 20:41)、`_46ea97`(07-06) 等多个残留，均非本次 conv_id。

**即：本次生成没有以 conv_id 落盘 deck**，看板判"无产物"正确。属生成侧落盘问题，与 §一同源。

---

## 建议（生成侧修，非看板）

1. **落盘用 conv_id**：跑批时 deck 目录名应等于 `conv_id`，`deck_scan_root` 写本次真实路径，别复用/通配到历史 sandbox。
2. **清理共享 sandbox**：`output/sandbox/` 混着多日残留 deck，是"陈旧 deck 冒充"的温床；跑批前清或按批次隔离目录。
3. **deck_quality 对齐**：`html_pages` 应统计本次 deck，避免"自报 N 页盘上 0 页"。
4. 看板侧**无需改**——守卫策略正确；如需更友好，可把这类"done 但无本次产物"在看板单独标一个徽章（如 `done·产物丢失`）以区别真 done，但这只是展示优化。

复现：`python3 scripts/analyze_failures.py`（失败根因）；对账脚本见本会话（api/index vs batch_summary）。
