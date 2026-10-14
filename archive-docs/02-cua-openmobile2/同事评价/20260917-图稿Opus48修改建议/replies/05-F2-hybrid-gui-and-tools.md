# 05-F2-hybrid-gui-and-tools

- model: `claude-opus-4-8`
- elapsed_s: 69.1
- finish_reason: stop
- usage: {"prompt_tokens": 3649, "completion_tokens": 3216, "total_tokens": 6865, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 3649, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: F2-hybrid-gui-and-tools.png

---

# 审稿意见：Hybrid GUI + App-native Tool 主图

## 1. 这张图现在在说什么

这张图想说明：同一个日历任务（Add Project Review），在同一初态（events[]=0）、同一判定（checker 读 title/date/start/end）下，有两条通道——GUI channel（纯视觉路径点保存）和 Tool channel（`calendar_prepare_event_draft` 只预填草稿，返回可编辑草稿）——最终都要经过 GUI 点 Save 才写入 shared state 的 `apps.calendar.events[]`，`events: 0→1`，Terminal check 读状态差分判定成功。核心命题："预填≠提交""同任务同初态同判定""两条通道都能完成"。

## 2. 内容张力诊断

**主张方向是对的，但当前布局把"预填≠提交"这个最硬的点讲糊了，反而容易触发你担心的误读。**

问题清单：

- **误读风险仍在**：Tool channel 里 `calendar_prepare_event_draft` 直接紧挨着 Shared state 的 `events[]`，且中间的箭头是实线，视觉上像"工具→写入 events[]"。真正的因果链应该是 tool prefill → GUI review/save → events[]。当前 `tool prefill 0` 和 `GUI save 1` 藏在 Shared state 框内部，太小、太晚，读者 10 秒内看不到"工具那步 events 还是 0"。
- **"tool prefill 0" 是全图最重要的证据，却是最弱的视觉元素**。这一行应该被放大到与 `events: 0→1` 同级。当前它被埋在表格里。
- **两条通道的"汇合点"没画出来**。GUI channel 和 Tool channel 都必须经过"GUI 点 Save"才写入——这个交汇是全图逻辑核心，现在是一条虚线（tap Save）随便连着，语义不清。
- **中英混排 + 中文截图**：`创建日程/开始时间/结束时间` 中文，伪代码/label 英文。对国际会议审稿人，中文截图里的 `2026年7月15日`、`14:00`、`15:30` 无法验证与右侧 `date: 15 Jul / start 14:00 / end 15:30` 对应。这是硬伤——你在讲"同一 event fields"，但读者对不上号。
- **日期口径打架**：GUI 截图顶栏 `9月14日`，日历翻到 `7月`，草稿写 `15 Jul 2026`，checker 写 `date: 15 Jul`。三处日期不自洽，审稿人会当作 bug。
- **Task package 的 check 写 `title·startTs·endTs`，Terminal check 写 `title/date/start/end`**。字段命名两处不一致，读者会问 checker 到底读几个字段。统一。
- **右下角灰底截图**（Shared state 框下面那张半张手机图）没有 label，像多余装饰，反而挤压 Shared state 框。
- **合规性**：文中用 "MobileGym++" 作环境名可以，但不要暗示工具与 GUI 完全等价——当前 caption "two channels, one app state" 是对的，保持。**不要**加任何"Hybrid 更强/涨分"暗示——目前没有，保持。

## 3. 若张力不够：应该怎么改（本图属于"逻辑要重排"，不是推倒）

不换图种（这是机制图），但要**重排为"两条通道纵向并列 → 强制汇合于 GUI Save → 单一写入 → 单一 checker"的四段式**，并把"预填≠提交"做成显式对照块：

- **新增一个显式对照小表**（放在图中央或底部），两行：
  - `After tool prefill:  events[] = 0  (draft only, not committed)`
  - `After GUI Save:      events[] = 1  (title/date/start/end written)`
  这才是全图第一证据，字号要大、要放中轴。
- **两条通道用同色终点收束到一个"GUI Save"节点**，从该节点单一箭头指向 `events[] 0→1`。让读者看到：无论哪条通道，写入口只有一个。
- **合法数字口径**：本图只讲机制，不该出现任何锁表成功率（58.6/68.4 等）。当前没放，正确，保持——不要为了"对照 GUI-only"而塞成功率数字。
- **该用的对照**："GUI-only 完整视觉路径" vs "Hybrid：tool 预填 + GUI 确认"——现在底部两行文字已有，但应升级为图内两条可视路径（见第 5 节）。
- **caption 主张**：只讲"same task/state/checker，tool 仅预填草稿，提交仍走 GUI"，不讲性能。

## 4. 视觉元素逐项优化

- **箭头语义**：把 Tool channel → events[] 的实线**删掉**。tool 只能指向"draft"，draft 指向"GUI review/edit"，再到"GUI Save"。虚线只用于"可选/未提交"，实线只用于"真实写入"。当前虚实混用无规则，统一：实线=业务写入，虚线=草稿/预填。
- **配色**：GUI channel 蓝、Tool channel 另一色（如紫/青）、写入/成功绿。当前蓝绿两色不足以区分三种角色。`events:0→1` 和 `✓` 用同一绿收尾。
- **字号层级**：`tool prefill 0` 与 `events 0→1` 提到同级大字。Shared state 内部小表可保留但缩小从属地位。
- **截图裁切**：两张手机截图裁到只显示"创建日程表单"和"保存按钮"关键区，去掉状态栏、农历、无关行（重复/提醒/闹钟提醒/日历账户），减少中文噪声。
- **中英统一**：截图字段旁加英文小标注（title/start/end 对齐箭头到伪代码同名字段），让 `项目复盘=Project Review`、`开始时间=start` 可对照。
- **日期统一**：三处全改成同一天（建议全 15 Jul 2026，截图顶栏也改 7月15日）。
- **右下角无 label 灰截图**：删除或合并进 Shared state 说明。
- **留白**：橙色大框内元素偏挤，Tool channel 三个代码块叠太近，拉开垂直间距。

## 5. 顶会可投稿重绘方案

**模块清单（左→右，上下分带）：**
1. **Task package**（左）：user goal / initial events[]=0 / checker fields（统一为 title·date·start·end）。
2. **中带上下两条通道并列**：
   - 上：GUI channel —（裁切表单截图）— 直接到 GUI Save。
   - 下：Tool channel — `calendar_prepare_event_draft` → returns editable draft → **draft, events[]=0** → 汇入 GUI review/edit。
3. **汇合节点 "GUI Save (tap 保存)"**（居中，两条通道箭头收束于此）。
4. **单一写入**：GUI Save →（实线，绿）→ Shared state `apps.calendar.events[] : 0→1`。
5. **对照证据块**（醒目）：tool prefill → 0；GUI save → 1；预填≠提交。
6. **Terminal check**（右）：read state diff，title/date/start/end matches，✓。

**阅读顺序**：Task package → 两通道并列 → 都汇入 GUI Save → 单一写入 events[] → checker。一眼看到"工具那步 events 仍为 0"。

**建议英文 caption：**
> *Hybrid GUI + app-native tool on a shared app state. For the same task, same initial state, and same state-diff checker, the tool only prefills an editable draft (events[] stays 0); committing still requires a GUI Save, after which events[] becomes 1. Prefill ≠ commit.*

## 6. 必须删掉或改口的元素

- **删** Tool channel → events[] 的实线箭头（防"工具已创建事件"误读）。
- **删/合并** 右下角无 label 的灰底半截图。
- **改** 三处日期统一为同一天。
- **改** check 字段命名两处统一（`title·startTs·endTs` vs `title/date/start/end` 择一）。
- **改** 中文截图字段加英文对照标注。
- **不得** 加入任何成功率数字或 Hybrid 优于 GUI 的暗示。
- **不称** tool 为 function/API；保持 "app-native tool / prepare draft"。

## 7. 优先级

- **P0**：删掉 tool→events[] 实线；把 "tool prefill: events[]=0" 与 "GUI Save: events[]=1" 做成图中轴大字对照块，明确"预填≠提交"。
- **P0**：三处日期统一，checker 字段两处统一。
- **P1**：两条通道纵向并列并收束到单一 "GUI Save" 汇合节点，写入箭头唯一。
- **P1**：截图裁切+英文字段对照标注，消除中英对不上号。
- **P2**：配色三角色区分（GUI/Tool/write-success）、拉开 Tool channel 代码块间距、删右下角无名截图、按建议英文 caption 替换。
