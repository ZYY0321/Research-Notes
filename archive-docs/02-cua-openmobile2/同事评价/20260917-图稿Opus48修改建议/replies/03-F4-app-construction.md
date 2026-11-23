# 03-F4-app-construction

- model: `claude-opus-4-8`
- elapsed_s: 77.7
- finish_reason: stop
- usage: {"prompt_tokens": 4430, "completion_tokens": 3516, "total_tokens": 7946, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 4430, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: F4-app-construction-process.png, 数据标注app制作参考流程图.jpeg

---

# 审稿意见：App 构建流程图

## 1. 这张图现在在说什么

这张图用五个卡片描述一个 App 的构建流水线：（1）Scope/capture/clarify——采集截图证据、整理 Q&A 与 gaps；（2）Review/freeze spec——写伪代码 spec 与 store contract，人做 review page 打勾；（3）Implement/self-check——coding agent 生成 navigation/pages/state/defaults 并自查；（4）Walk-through/repair——视觉走查发现失败（tap amount 无响应），送回 spec 修正再 replay；（5）Deliver/iterate——交付可执行 app + seed + checks。上方标题给出"Evidence → Reviewed Spec → Executable App"主线，中间一条虚线回折"Corrections update the spec before code"，底部列 artifacts 清单。核心想说：先证据/对象模型/spec 再写页面，走查失败回同一条流水线，业务闭环不是皮肤。

## 2. 内容张力诊断

**主线是对的，但被布局和冗余稀释，10 秒读不出。**

- **主张能撑住的部分**：store contract（`confirm → write bills[id].amount`）、replay checks 看 UI+store 双写、走查回折——这三点正好对应"业务闭环不是皮肤""成败看业务状态差分"，方向正确。
- **致命问题：阅读顺序反 Z 字**。卡片编号是 1→2→3 在上排（左→右），4→5 在下排却是 **右→左**（4 在右下，5 在左下）。人眼下排默认左→右，会先读到"5. Deliver"再读"4. Walk-through"，把交付读成走查之前。参考图 ScienceBoard 下排也是右→左，但它用了清晰的箭头方向引导；你这里下排箭头是 `4 → 5`（右指左）和回折虚线交织，方向混乱。
- **回折比参考图碎**：你有两条虚线（"Corrections update spec"从 4 回到 2；4→5 的交付虚线；还有 3→4 的右侧竖虚线），三条虚线在右下角打结。参考图只有一条 Check&Validation 回折，干净。
- **伪代码重复**：bill/amount/1580 这个例子在卡片 2（`write bills[id].amount`）、卡片 4（`tap amount → no response`）、卡片 5（`confirm → UI and store show 1580`）出现三次。信息增量低，占了大量版面。
- **人机分工不清**（你自己点到的痛）：参考图用 icon 明确 human vs machine（Learn/Curate/Formalize 是人，Write eval 是人+机）。你只在卡片 1 和 3 之间放了两个人形 icon（capture / review），卡片 3 的"build"是谁做的、卡片 4 走查是人还是 agent，没有视觉区分。coding agent 这个主角在图上根本没有出现符号。
- **口径检查**：图上没有出现锁表成功率、64/215/tools 等敏感数字，**未触发口径打架**，安全。但注意——这是"构建流水线"图，不要在此图或 caption 里塞环境 census（64）或 Bench 215，那是别的图的事。
- **"self-check"措辞**：卡片 3 写"Implement and self-check"，容易被读成 agent 自动验收。真正的验收在卡片 4 的 human 走查。需要区分 agent 自查 vs human 走查。

## 3. 若张力不够：应改成什么展示

**保留五步内容，但重构为"单向主链 + 单条回折 + 泳道分工"，仿参考图的清晰度但更硬。**

- **图种**：横向单排 5 步（若双栏太窄，改 2 行但强制 Z 字：上排 1→2→3，下排 4→5 保持左→右，回折虚线单独走底部）。
- **加人机泳道**：顶部两条淡色泳道标签 **Human annotator** / **Coding agent**，每一步的卡片挂在对应泳道，跨泳道的步（如 spec review、walk-through）用一个"人+机"合并 icon。这直接对标参考图的 Learn→Curate→Formalize→Configure→Write eval。
  - 建议映射：Capture（human）→ Spec draft（agent 起草）+ Review/freeze（human 批准）→ Build（agent）→ Walk-through（human）→ repair（回 agent）→ Deliver。
- **回折只留一条**：`Walk-through failure → revise spec → rebuild`，一条虚线从卡片 4 回到卡片 2，caption 里点明"failures return to the same spec pipeline, not patched on the UI"。删掉 3→4、4→5 的多余虚线（那些是正向流，用实箭头）。
- **伪代码去重**：bill 例子只保留一处完整版（放在卡片 2 的 store contract，因为那里最能证明"不是皮肤"）。卡片 4/5 不再重复 amount/1580，改为通用标签："replay checks UI **and** store diff"。
- **合法可写的 caption 主张**：强调协作效率 + spec-before-code + 业务写入验收，不碰数字。
- **不该出现**：任何 mock 字样（用 simulated 或直接说 app）、function/API/tools 混称、成功率数字、64/215。

## 4. 若张力基本成立：视觉逐项优化

（假设你只想改不重排——但强烈建议至少修下排方向）

- **下排方向**：把卡片 5 移到右、卡片 4 移到左，或把两条正向箭头方向统一为左→右。当前 4→5 右指左必须改。
- **虚线语义**：三条虚线现在同一种样式，读者分不清"回折修正"vs"正向交付"。正向流一律实心箭头，只有"corrections back to spec"用虚线，且加不同颜色（如橙色回折 vs 蓝色正向）。
- **人机 icon**：现有两个人形（capture/review）太小且信息不足。给每步左上角加一个 tag：`👤 human` / `🤖 agent` / `👤+🤖`。coding agent 必须显形。
- **配色**：卡片 2 绿、卡片 4 橙、其余灰蓝，颜色语义不一致（绿=spec？橙=failure？）。建议：正常步统一灰蓝，**只有回折/repair 相关（走查失败）用橙**做警示，spec 卡片不必单独绿。
- **截图裁切**：卡片 3 右侧手机截图和卡片 4/5 的小截图都是中文账单页，未做重点标注。若保留，用红框圈出"amount 字段"，让"业务写入"可视化；否则截图只是装饰，占版面。
- **字号层级**：五个步标题（1.Scope…）当前和卡片内标题（Capture catalog）字重接近。步标题应更大更黑，卡片内代码用等宽小号。
- **底部 artifacts 清单**：一长串圆点分隔，读起来累。可与卡片内"Per-app artifacts"合并，避免重复（spec/store/seed/checks 出现两次）。
- **留白**：右下角三卡+两截图+多虚线过密，是全图最挤处。疏解此处是最大收益。

## 5. 顶会可投稿重绘方案

**模块清单（横向单链 + 泳道）**：
1. 顶部主线 banner：`Evidence → Reviewed Spec → Executable App`
2. 两条泳道背景：Human annotator（上）/ Coding agent（下）
3. Step 1 Capture（human）：screens/flows/cases + Q&A/gaps
4. Step 2 Spec & Review（agent drafts → human approves & freezes）：**唯一**保留 store contract 代码块
5. Step 3 Build（agent）：pages/actions/state/defaults，标注 UI↔actions↔app-owned store
6. Step 4 Walk-through（human）：业务状态差分走查，失败示例
7. Step 5 Deliver（agent）：app + seed + checks
8. 单条回折虚线：Step4 → Step2（橙）
9. 底部：artifact 一行（去重）

**阅读顺序**：主线 banner → 泳道分工 → 1→2→3→4→5 左到右 → 注意到橙色回折 → artifact 落地。

**建议英文 caption**：
> Figure X: App construction pipeline. A human annotator and a coding agent collaborate to turn captured evidence into a reviewed, evidence-linked specification (object model + store contract) *before* any page is written; the built app is walked through against real business-state changes, and any failure returns to the same spec pipeline rather than being patched on the UI.

## 6. 必须删掉或改口的元素

- 删除下排右→左的阅读方向（P0）。
- 删除 bill/amount/1580 例子的两处重复，只留一处。
- 删除右下角交织的两条冗余虚线，回折只留一条。
- "Implement and self-check" 改口：区分 agent self-check 与 human walk-through，别让 self-check 暗示自动验收。
- 底部 artifacts 与卡片内 Per-app artifacts 二选一，别重复列。
- 全图确认无 mock / API / 成功率数字（现状已 OK，重绘时勿引入）。

## 7. 优先级

- **P0**：修正阅读顺序——下排（或全图）统一为左→右单向主链，杜绝"先读到 Deliver"。
- **P0**：加 Human / Coding-agent 泳道或每步 role tag，让 agent 显形、分工对齐参考图清晰度。
- **P0**：回折虚线收敛为唯一一条（Walk-through 失败 → 回 spec），用区别颜色。
- **P1**：bill 例子去重，只在 store contract 处保留一份完整伪代码。
- **P1**："self-check" 改为 agent 自查 vs human 走查两阶段措辞。
- **P2**：截图加红框圈业务字段，否则移入附录；疏解右下密度、统一配色语义。
- **P2**：底部 artifacts 与卡内清单合并去重。
