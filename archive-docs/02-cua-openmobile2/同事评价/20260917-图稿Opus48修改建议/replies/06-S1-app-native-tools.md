# 06-S1-app-native-tools

- model: `claude-opus-4-8`
- elapsed_s: 55.0
- finish_reason: stop
- usage: {"prompt_tokens": 3647, "completion_tokens": 2562, "total_tokens": 6209, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 3647, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: S1-tool-call-and-state-details.png

---

# 审稿意见：工具机制放大图（Discover → Open → Edit → Verify）

## 1. 这张图现在在说什么

图分四块讲一个用例：agent 在 Kapi 里 `list_actions` 发现工具并选 `open_bill`，工具打开账单 b010 详情（此时 store 未写金额，"store writes so far: none"），随后 GUI 把 1500 改成 1580，最后读 store 前后差分证明 UI 与 store 一致、bill ID 不变。核心主张是"工具只做打开/定位，真实写入发生在 GUI，成败看 store 差分"。

## 2. 内容张力诊断

**主张方向对，但当前呈现把一个安全用例讲成了普遍规则，这正是你担心的风险：**

- **查询类工具和"必须 GUI 后验"的写入没分开** —— 图右下"Tool opens · GUI confirms the write"配合底栏 `GUI save(1580)`，读者会归纳出"tools 都要 GUI 后验才生效"。但按论文口径，Draft/预填也是工具能力，只是"预填不等于提交"；而查询/定位类工具本就不写 store，无所谓"GUI 后验"。现在把 open_bill（定位）和 save（GUI 写入）混在一条链里，反而模糊了"工具与 click 占同一动作槽、写同一 store"这个真正的贡献。

- **`list_actions` 看起来像内部实现**。左上"tools = list_actions(Kapi)"暴露的是运行时反射式发现机制，读者会怀疑这是试验脚手架而非环境契约。工具是"按每个 App 的业务对象设计、只暴露前台 App"，展示重点应是"工具挂在业务对象上"，不是"agent 能枚举实现"。

- **与 F2/F3 重复**。同一个 Kapi/账单/1500→1580 例子讲三遍，边际信息量低。

- **术语混用风险**。"App handler"、"tools"、"list_actions" 混着叫，容易踩"function/API/tools 混称"的红线。

- **好的部分**：三处对照（before/after ID 相同、amount 变、ledger unchanged）方向正确；"store writes so far: none"是这张图唯一真正有信息量的断言——它证明"工具打开不等于业务写入"。

**结论：内容张力偏弱且有误导风险。这张图不该以现在的形式留在正文。**

## 3. 若张力不够：改成什么

**首选方案 A（推荐）：退附录 / 并进 F2，正文只保留一个"工具能力分层"小图。**

正文新图不要再讲流程，改讲**工具能力矩阵**（这是当前所有工具图都缺的、能撑住主张的东西）：

| 工具类别 | 写 store？ | 需 GUI 提交？ | 示例 |
|---|---|---|---|
| Query（查询/搜索） | 否 | 不适用 | search bills by keyword |
| Navigate（定位/打开） | 否 | 不适用 | open_bill(b010) |
| Draft（预填草稿） | 否（草稿≠提交） | 是（提交在 GUI） | prefill editable bill |

- 一张表 + 一句话就把"查询类不写 store"和"预填需 GUI 提交"分开，直接消掉审稿人"以为 tools 都要 GUI 后验"的误读。
- caption 主张：*"Tools operate on each app's business objects and share the same action slot and store as GUI clicks; query/navigate tools do not write state, and drafts are not submissions."*

**若坚持保留流程图（方案 B）**：只保留一条链，删掉 `list_actions` 发现步骤，改成"工具 open_bill → store 未写 → GUI save → store 写入"的**单主张对照**，并在 open 步骤显式标注"query/navigate tools 到此为止就结束，不涉及 GUI 后验；只有 draft/edit 才走下一步 GUI 提交"。

**不该出现的数字**：本图不涉及成功率，别顺手加锁表数字。

## 4. 若张力基本成立：视觉逐项优化

（假设采用方案 B 保留精简流程）

- 三块伪代码密度过高，每块 4–6 行等宽字堆叠，10 秒读不完。每块砍到 2–3 行核心。
- "store writes so far: none"是全图关键句，应放大、加色块高亮，现在淹没在 Result 列表第 5 行。
- 两张截图裁得太满，实际信息只有金额 -¥1500 → -¥1580 一行；建议裁到只留金额条 + "已变更"标签，其余字段留 1–2 行示意即可，放大金额对比。
- "amount: 1500 / amount: 1580"用蓝/绿双色本身好，但 edit→save 绿箭头和金额绿色撞色，改箭头为中性灰。
- 底栏两块 State access / Same identity 是全图逻辑落点，字号却最小，应与上排同级。

## 5. 顶会可投稿重绘方案（方案 A）

**模块清单（单栏即可）：**
1. 顶部一句定义：Tools = actions on the app's business objects, sharing the action slot & store with GUI.
2. 三行能力矩阵表（Query / Navigate / Draft × writes-store? × needs-GUI-submit?）。
3. 右侧一个极简对照条：`open_bill(b010)` → store unchanged；`GUI save(1580)` → store writes；下标 `before.ID == after.ID`。

**阅读顺序**：定义 → 能力表（看清哪类写/不写）→ 一个"写入只在 GUI 提交"的最小证据条。

**英文 caption**：
> *App-native tools act on business objects in the same store and action slot as GUI clicks. Query/navigate tools return state without writing it, and a prefilled draft is not a submission; the actual write is confirmed by the pre/post store diff (amount 1500→1580, same bill ID).*

## 6. 必须删掉或改口的元素

- 删 `list_actions(Kapi)` 的运行时枚举呈现，改为"tool attached to business object bill"。
- 删/改"App handler"用词，统一为"tool" 或 "app-native tool"，全图术语一致，不出现 function/API 混称。
- 删"Tool opens · GUI confirms the write"这句总结——它是导致误读的源头；改为分类陈述。
- 与 F2/F3 的重复 1500→1580 例子：三张图只留一张用此例，其余换例或退附录。
- 底注"screenshots... come from the recorded example"保留，但把"mock"类隐含去掉（本图没写 mock，注意其他图不要出现）。

## 7. 优先级

- **P0**：把查询/定位类工具与"预填需 GUI 提交"的写入分开呈现（能力矩阵），删除"GUI confirms the write"总括语，消除"tools 都要 GUI 后验"的误读。
- **P0**：本图退附录或并进 F2，正文只留一张工具能力分层图，消除与 F2/F3 的三重复述。
- **P1**：删 `list_actions` 枚举、统一工具术语，避免暴露内部实现/术语混称。
- **P2**：若保留任何截图对照，裁到只剩金额条并放大 1500→1580，高亮"store writes so far: none"。
