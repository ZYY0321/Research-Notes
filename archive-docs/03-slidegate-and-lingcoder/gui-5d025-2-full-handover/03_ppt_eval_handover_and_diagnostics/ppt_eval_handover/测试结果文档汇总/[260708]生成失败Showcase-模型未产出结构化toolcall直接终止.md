# 生成失败 Showcase（模型侧）：按模型分开的完整错误模式分析

> 本次评测自家模型的生成失败共 **119 例**，绝大多数是同一大类根因：模型某一轮没有产出「框架能识别的结构化 tool call」→ agent 循环判定「本轮无调用、已说完」→ 直接终止 → 最终无 HTML 产物。`error` 全为 null（非超时、非管线 bug）。§2 列全 4 种错误模式；§3 起按模型分开逐条 showcase。

---

## 0. 各模型失败量总览

终态取自 `batch_summary.json` 的 `terminal_class`，非 `done` 即失败。

| 模型 | done | render_suspect | done_no_html | **失败合计** |
|---|---:|---:|---:|---:|
| Flash v1.1（flashv1_1） | 35 | 6 | 6 | **12** |
| Flash-lite v36 step4k（flash4k） | 43 | 4 | 0 | **4** |
| Flash-lite v36 DPO v1 无模板（step3kdpo） | 45 | 2 | 0 | **2** |
| Flash-lite v36 DPO v1 模板（step3kdpo_tpl） | 45 | 2 | 0 | **2** |
| Flash-lite v36 DPO v2 无模板（step3kdpov2_notpl） | 44 | 3 | 0 | **3** |
| Flash-lite v36 DPO v2 模板（step3kdpov2_tpl） | 45 | 0 | 2 | **2** |
| Flash-lite v36 CSFT 无模板（step3kcsft_notpl） | 44 | 1 | 2 | **3** |
| Flash-lite v36 CSFT 模板（step3kcsft_tpl） | 46 | 0 | 1 | **1** |
| **Flash-lite v36 CSFT+DPO 无模板（step3kcsftdpo_notpl）** | **47** | **0** | **0** | **0** ✅ |
| **Flash-lite v36 CSFT+DPO 模板（step3kcsftdpo_tpl）** | 46 | 1 | 0 | **1** |
| **Flash-lite v36 DPO+CSFT v2 无模板（step3kdpocsftv2_notpl）** | **47** | **0** | **0** | **0** ✅ |
| **Flash-lite v36 DPO+CSFT v2 模板（step3kdpocsftv2_tpl）** | 46 | 1* | 0 | **1*** |
| **Louis_9B_datacheck_v3 无模板（louis9b_dc_v3_notpl）** | **47** | **0** | **0** | **0** ✅ |
| **Louis_9B_datacheck_v3 模板（louis9b_dc_v3_tpl）** | **47** | **0** | **0** | **0** ✅ |
| **Flash-lite v39 step3k 无模板（flashv39_step3k_notpl）** | **47** | **0** | **0** | **0** ✅ |
| **Flash-lite v39 step3k 模板（flashv39_step3k_tpl）** | **47** | **0** | **0** | **0** ✅ |
| **Flash-lite v39 DPO-v1 无模板（flashv39_dpov1_notpl）** | **47** | **0** | **0** | **0** ✅ |
| **Flash-lite v39 DPO-v1 模板（flashv39_dpov1_tpl）** | **47** | **0** | **0** | **0** ✅ |
| **OTTO agent v1.1 step5700 · 无模板（otto_step5700_notpl）** | **3** | **19** | **25** | **44** ⚠️ |
| **OTTO agent v1.1 step5700 · 模板（otto_step5700_tpl）** | **3** | **27** | **17** | **44** ⚠️ |
| **SenseNova-Flash-Lite-…-step4k-dpov2 无模板（flashv39_step4k_dpov2_notpl）** | **~29** | **—** | **—** | **~18 未齐 ⚠️套数不全** |
| **SenseNova-Flash-Lite-…-step4k-dpov2 模板（flashv39_step4k_dpov2_tpl）** | **47** | **0** | **0** | **0** ✅ |
| **Claude Opus 5 无模板（claudeopus5_notpl）** | **45** | **0** | **2** | **2** |
| **Claude Opus 5 模板（claudeopus5_tpl）** | **47** | **0** | **0** | **0** ✅ |
| **284B opd-step80 无模板（flash284b_opd_notpl）** | **44** | **1** | **0** | **1**（另 seq_2016 卡住未终态） |
| **284B opd-step80 模板（flash284b_opd_tpl）** | **47** | **0** | **0** | **0** ✅ |
| **284B v1.2-ep1 无模板（网页首启）** | **0** | **25** | **22** | **47** ⚠️ 见 `0812_v1-2_ep1失败分析_复现.md` |
| **284B v1.2-ep1 模板（网页首启）** | **0** | **23** | **24** | **47** ⚠️ 同上 |
| **Flash-Lite v40 step2k5 无模板** | **47** | **0** | **0** | **0** ✅ |
| **Flash-Lite v40 step2k5 模板** | **47** | **0** | **0** | **0** ✅ |
| **284B step160 无模板（进行中）** | **13** | **1** | **0** | **1 / 当前14终态** ⚠️ |
| **284B step160 模板（进行中）** | **22** | **0** | **0** | **0 / 当前22终态** |
| **合计** | | | | **120+** |

> `*` = dpocsftv2_tpl 的 1 例（prod_912af214）真根因是 litellm 端点 API bug（非模型侧），严格算模型侧失败为 **0/47**。

**变更日志**：
- 2026-08-14：新增 Flash-Lite v40 step2k5（notpl/tpl 均 **47/47 done**，0 失败）。新增 284B step160 进行中口径：模板前 22 条均 done；无模板 13 done + seq_1157 render_suspect。seq_1157 的医疗 PPT 长上下文收到完全无关的英文故事改名回复，直接 0 HTML，属于新的**疑似跨请求/上下文串线**形态，详见 §14。另 4 次 `finalize + tool_choice=none` 输出 DSML，但所属 case 后续均成功，仅记协议异常，不计失败。
- 2026-08-12：新增 284B opd-step80（notpl：**44 done + 1 render_suspect**，seq_2016 卡住；tpl：**47/47 done**）——无新错误模式。另网页首启 **v1.2-ep1** 两批 **47×2 全失败**（主因 DSML 伪 tool call + `tool_choice=none` 400），见 `0806_284b问题反馈_模型侧/0812_v1-2_ep1失败分析_复现.md`（属 0810 DSML 同族加重，不新开 § 编号）。
- 2026-07-31：新增 Claude Opus 5 两批（notpl keep：**45 done + 2 done_no_html**；tpl：**47/47 done**）。机评 notpl 0.817（n=41）/ tpl 0.767（n=46）；无新生成失败根因节。
- 2026-07-31：新增 step4k-dpov2 两批——**模板 47/47 done**；**无模板约 29/47（套数不全）**，机评 notpl n=27 / tpl n=46。无新生成失败根因节（未齐部分多为长跑/挂起，非整批新模式）。
- 2026-07-09：新增 DPO v2 两批（+5 例）。
- 2026-07-13：新增 CSFT 两批（+4 例失败）。
- 2026-07-14：新增 CSFT+DPO 两批（+1 例失败，**csftdpo_notpl 47/47 全 done**，是自家版本里成功率首次达到 100%）；**新增 OTTO 两批（+88 例失败）**——OTTO 是外部模型接入尝试，**failure rate 44/47 ≈ 94%**，模型侧问题严重，见 §9。
- 2026-07-16：新增 DPO+CSFT v2 两批（+1 例失败，**dpocsftv2_notpl 47/47 全 done**——第二个自家版本达到 100% 生成成功率）。**dpocsftv2_tpl 的 1 例（prod_912af214）真根因是 litellm/端点 API 兼容性 bug**（`Incompatible tool choice param submitted - {'type': 'none'}`，subtask Finalize 挂 → 8 个 subtask 全 fail → 主 agent 1h 超时 → render_suspect 0 页）——**非模型侧问题、非 file_action 畸形**。之前分析误判为 `<file_action>` 老根因，已在下方 §7.3 更正。
- 2026-07-17：追加 `<file_action>` 播报协议 feature 频率专项分析——见 §10（新数据加此 feature 是否起效的定量证据）。
- 2026-07-24：新增 Louis_9B_datacheck_v3 两批（**notpl/tpl 均为 47/47 done，零失败**；无新错误模式，不单开节）。机评 overall notpl 0.720（n=46）/ tpl 0.632，见 `0708_模型特点与缺陷分析.md` §6 新卡。
- 2026-07-27：新增 Flash-lite v39 step3k（`SenseNova-Flash-Lite-20260727-v39-fp-step3k`）两批（**notpl/tpl 均为 47/47 done，零失败**；无新错误模式，不单开节）。机评/人眼见 `0708_模型特点与缺陷分析.md` §6 与 `0727_flashv39_肉眼对比工作笔记.md`。
- 2026-07-28：新增 Flash-lite v39 DPO-v1（`:164`）两批（**notpl/tpl 均为 47/47 done，零失败**；无新错误模式）。机评见 `0708_模型特点与缺陷分析.md` §6 与 [飞书总表](https://sensetime.feishu.cn/wiki/ClrZwaCQTiMYIykKtrmcKwnZnFg?from=from_copylink)。

---

## 1. 正确形态（参照基准）

框架识别的是**结构化 function call**（OpenAI tool-calls 协议），**不是**文本标签。以下均取自本批次成功轮次的**原始 payload**：

```json
// read_file
{"id":"call_7e6e60e9...","type":"function",
 "function":{"name":"read_file","arguments":"{\"file_path\": \"local://mnt/data/skill/ppt-maker/SKILL.md\"}"}}

// execute_shell_command
{"id":"call_d7b4aafe...","type":"function",
 "function":{"name":"execute_shell_command","arguments":"{\"command\": \"ls /mnt/data/skill/ppt-maker/scripts/\"}"}}

// write_file
{"id":"call_daf7cbd9...","type":"function",
 "function":{"name":"write_file","arguments":"{\"content\": \"{...json...}\", \"file_path\": \"...\"}"}}
```

要点：`type:"function"` + `function.name`（**精确**工具名）+ `function.arguments`（**合法 JSON 字符串**）。**没有任何 `<invoke>`/`<tool_calls>`/`<function=>`/`<file_action>`/`<report>` 文本标签，没有特殊 token，不用自然语言宣告代替动作。**

---

## 2. 错误模式全景（4 种，本次全部列全）

19/20 都是「本轮没有有效结构化调用 → 循环终止」，区别只在**那一轮吐了什么**。据此分 4 种；第 1 种又分 4 个畸形子形态。第 20 个是长表不收敛。

| # | 错误模式 | 数量 | 一句话 | 命中模型 |
|---|---|---:|---|---|
| ① | **`textform_toolcall`** 工具调用吐成纯文本/畸形 | 12 | 知道要调什么、参数也基本对，但没按结构化协议发，被当成「说完了」 | flashv1_1(9)、flash4k(3) |
| ② | **`premature_report_stop`** 用报告代替动作 | 4 | 末轮用 `<report>`/`<response>` 写一大段自然语言（大纲/分镜/目录）就停，没发起真实调用 | step3kdpo v1(2)、step3kdpo_tpl v1(1)、flash4k(1) |
| ③ | **`narrate_then_stop`** 宣告下一步却没做 | 3 | 末轮"我现在开始做X"或反问用户要参数，然后 turn 结束、无调用 | flashv1_1(2)、step3kdpo_tpl v1(1) |
| ④ | **`verbose_no_converge`** 大表话痨不收敛 | 1 | 超大 xlsx，202 次调用 1507s 反复读/演算仍产不出结构化产物 | flashv1_1(1) |

① 的 4 个畸形子形态（同一模型会混用）：

| 子形态 | 长啥样 | 是谁 |
|---|---|---|
| a. 标准 `<invoke>` 纯文本 | `<tool_calls><invoke name="read_file">…</invoke></tool_calls>` 整段打印成文本 | flashv1_1 |
| b. 特殊 token 泄漏 `<｜DSML｜>` | `<｜DSML｜tool_calls><｜DSML｜invoke …>`（训练对话标记全角 `｜` 漏进输出） | flashv1_1 |
| c. `<function=xxx>` 畸形 + **工具名拼错** | `<tool_call><function=execute_shell_ommand>`、`<function=todtolist_update>`、`<function=executeshell>` | flash4k、部分 flashv1_1 |
| d. 杜撰伪协议 `<file_action>` | 自造 `<file_action><target>…</target><action>CREATE</action>` 来"写文件"，框架无此工具 | flashv1_1、CSFT_notpl(seq_0216/seq_1380)、CSFT_tpl(seq_1495)、CSFT+DPO_tpl(seq_1190) |

> **2026-07-17 更正**：dpocsftv2_tpl 的 prod_912af214 曾被误列入本表，实际根因是 litellm 端点 `tool_choice:{type:"none"}` 兼容性 bug（subtask Finalize 挂）→ 主 agent 1h 超时；`<file_action>` 已在 csftv2/csftdpo 两版训练数据加入 → 见 §10 频率分析（**csftv2 侧 file_action 畸形率 0%**）。

**关键观察（对训练侧最有信息量的一点）**：①③④ 的失败**很多发生在长轨迹后期**——前面几十次结构化调用都成功了，越往后越退化。前置成功调用数：seq_1025=27、prod_18bf8df6=22、prod_c40ab9ac(flash4k)=22、seq_1006=20。即**「能调对，但不稳定」**，不是「完全不会调」。

---

## 3. Flash v1.1（`flashv1_1` / checkpoint-2200）——最严重，12/20

> 失败量最大（12）、畸形语法最杂。三种错误模式都出现，其中**文本形式 tool call 占 9 个**，且 4 个畸形子形态全见过。是本次最需要训练侧关注的模型。

**失败清单（9 textform + 2 narrate + 1 verbose）**：

| case | 终态 | 时长 | 前置成功调用 | 子形态 |
|---|---|---:|---:|---|
| seq_1408 | done_no_html | 17s | 0 | ①a `<invoke>` 纯文本 |
| seq_1006 | render_suspect | 460s | 20 | ①b DSML + 工具名 `executeshell` |
| prod_e4794450 | render_suspect | 458s | 20 | ①b DSML |
| seq_1784 | render_suspect | 82s | 11 | ①b DSML |
| prod_18bf8df6 | render_suspect | 1870s | 22 | ①d `<file_action>` |
| seq_1025 | render_suspect | 326s | 27 | ①d `<file_action>` |
| seq_1081 | done_no_html | 406s | 8 | ①d `<file_action>` |
| seq_1190 | done_no_html | 127s | 14 | ①d `<file_action>` |
| seq_1293 | done_no_html | 388s | 12 | ①d `<file_action>` |
| prod_5a2ddcda | render_suspect | 38s | 12 | ③ narrate_then_stop |
| seq_1559 | done_no_html | 1425s | 28 | ③ narrate_then_stop |
| seq_1495 | done_no_html | 1507s | 202 | ④ verbose_no_converge |

### 3.1 ①a 标准 `<invoke>` 纯文本 — seq_1408（17s 即停，一次结构化调用都没成过）
> 无模板模式做教学 PPT。3 条记录、17 秒、前置成功调用 0。

```
</think>
根据现有的材料分析，我已经掌握了制作第二课教学PPT的方向和规范。现在开始工作。

<response>
我已经确认了课件制作规范和既有第二课内容的结构，现在开始制作符合规范的完整课件。
</response>

<tool_calls>
<invoke name="read_file">
<parameter name="file_path" string="true">local://mnt/data/skill/ppt-maker/SKILL.md</parameter>
</invoke>
</tool_calls>

<tool_calls>
<invoke name="execute_shell_command">
<parameter name="command" string="true">ls -la /mnt/data/ && ls -la /mnt/data/result/ 2>/dev/null; ...</parameter>
</invoke>
</tool_calls>
```
**✅ 正确应为**（两个调用各发一次结构化 function call，而非打印成文本）：
```json
{"type":"function","function":{"name":"read_file","arguments":"{\"file_path\": \"local://mnt/data/skill/ppt-maker/SKILL.md\"}"}}
{"type":"function","function":{"name":"execute_shell_command","arguments":"{\"command\": \"ls -la /mnt/data/ && ls -la /mnt/data/result/\"}"}}
```

### 3.2 ①b 特殊 token 泄漏 `<｜DSML｜>` — seq_1006（前 20 次正常，出图这一步崩）
> 无模板模式做工作汇报。已跑到 `html_page_generate_batch.py` 出图，最后一次调用崩掉；工具名也异常成 `executeshell`。

```
<｜DSML｜tool_calls>
<｜DSML｜invoke name="executeshell">
<｜DSML｜parameter name="command" string="true">cd /mnt/data/skill/ppt-no-template-mode && python scripts/html_page_generate_batch.py --deck /mnt/data/result/pptid_2d2d430a-... --prompt prompts/html_gen_no_template.md --concurrency 4 2>&1 | tail -30</｜DSML｜parameter>
</｜DSML｜invoke>
</｜DSML｜tool_calls>
```
> 训练用的对话标记（DSML 全角 `｜`）漏进输出；工具名亦异常成 `executeshell`。另 seq_1784 / prod_e4794450 同一子形态。

**✅ 正确应为**（结构化调用，工具名精确、无特殊 token）：
```json
{"type":"function","function":{"name":"execute_shell_command","arguments":"{\"command\": \"cd /mnt/data/skill/ppt-no-template-mode && python scripts/html_page_generate_batch.py --deck ... --concurrency 4\"}"}}
```

### 3.3 ①d 杜撰伪协议 `<file_action>` — seq_1025（前 27 次正常，写文件这步自造标签）
> 奢侈品业绩 xlsx → 商业提案 PPT。schema 都读懂了，写文件时**自造 `<file_action>` 标签**，框架无此工具（应为 `write_file`）。

```
好的，schema 清楚了。现在直接写两个文件到 deck 工作目录。

<file_action>
<action>CREATE</action>
<target>/mnt/data/result/pptid_208a44e1-.../style_spec.json</target>
写入商务提案深蓝商务风格说明</summary>
</file_action>

<file_action>
<action>CREATE</action>
<target>/mnt/data/result/pptid_208a44e1-.../outline.json</target>
写入商务提案7页页面大纲</summary>
</file_action>
```
> 同子形态还有 prod_18bf8df6 / seq_1081 / seq_1190 / seq_1293（共 5 个，是 flashv1_1 里最高发的畸形）。注意 seq_1190 甚至先吐了一整段 `<previous_reasoning>` 英文推理再接 `<file_action>`。

**✅ 正确应为**（写文件用 `write_file` 结构化调用，内容放进 `arguments`，一个文件一次调用）：
```json
{"type":"function","function":{"name":"write_file","arguments":"{\"file_path\": \"/mnt/data/result/pptid_208a44e1-.../style_spec.json\", \"content\": \"{...json...}\"}"}}
```

### 3.4 ③ narrate_then_stop — seq_1559（85 轮 1425s 干了很多活，最后一句话收尾没落地）
> HR 员工调研 → 管理层洞察 PPT。前置 28 次成功调用、写过文件，末轮只剩一句宣告，没有任何调用，turn 结束即停。

```
两个产物已产出。现在先补建立必要的入口材料，再继续分发后续流程。
```
> prod_5a2ddcda（垃圾分类演讲，38s）同类：`用户明确指定了无模板模式…我将以合理默认直接推进。`——说要推进，然后就没有然后了。

**✅ 正确应为**：末轮不是自然语言宣告，而是**真的发起**下一个 `execute_shell_command` / `create_subtask` 结构化调用，把"继续分发后续流程"落成动作。

### 3.5 ④ verbose_no_converge — seq_1495（考勤大表，202 调用 1507s 不收敛）
> 15 人考勤 xlsx（源材料 2 万+字）+ 逐人 1 页。202 次调用、607 条记录、25 分钟，反复 `read_file`/`document_parser`/`execute_code`（198 次！）读文件演算，就是产不出结构化 deck。末轮还停在读 `task_pack.md` 说明。

```
{"success": true, "file_path": "local://.../task_pack.md", "actual_lines_read": 190, "total_lines": 190,
 "content": "# task_pack.json 生成要求\n\n`task_pack.json` 是本 Skill…（190 行说明全文读进来）"}
```
> 与判分侧 q1495 同源（三值忠实度也话痨到抛错）。**超大表格附件是自家弱模型的公认死穴**：不做减法、反复全量重读、execute_code 空转。

**✅ 正确应为**：读一次表 → 抽关键字段 → 写 `outline.json` / 分页出图；而非 198 次 `execute_code` 在原始大表里反复演算不落盘。

---

## 4. Flash-lite v36 step4k（`flash4k`）——4/47，全是 `<function=>` 畸形 + 工具名拼错

> 与 flashv1_1 不同：flash4k 的文本形式 tool call **只出 ①c 一种子形态**——`<tool_call><function=xxx>`，且**工具名几乎都拼错**（`ommand` 少字母、`shellcommand` 漏下划线、`todtolist` 打错）。这是**工具名 token 级不稳定**的直接证据，比 flashv1_1 的"整段吐文本"更细粒度。另有 1 个 `<report>` 提前收尾。

**失败清单（3 textform ①c + 1 premature）**：

| case | 终态 | 时长 | 前置成功调用 | 子形态 / 拼错的工具名 |
|---|---|---:|---:|---|
| prod_c40ab9ac | render_suspect | 334s | 22 | ①c `<function=execute_shellcommand>`（漏下划线） |
| prod_5a2ddcda | render_suspect | 73s | 13 | ①c `<function=execute_shell_ommand>`（少 c） |
| seq_1690 | render_suspect | 58s | 9 | ①c `<function=todtolist_update>`（应 todolist_update） |
| prod_603992e9 | render_suspect | 87s | 15 | ② `<report>` 提前收尾 |

### 4.1 ①c `<function=>` 畸形 + 工具名拼错 — prod_c40ab9ac（前 22 次正常，末轮崩）
> 修 asset_map.json 缺 `pages` 字段。逻辑对，但工具名 `execute_shellcommand` 漏了下划线。

```
发现问题：asset_map.json 缺少 `pages` 字段。脚本需要它和 outline 的 page_number 一致。让我修复。

<tool_call>
<function=execute_shellcommand>
<parameter=command>
python3 -c "
import json
with open('/mnt/data/result/pptid_751eae52-.../asset_map.json') as f:
    asset_map = json.load(f)
...
"
</parameter>
</function>
</tool_call>
```
> 另两个同子形态更露骨：prod_5a2ddcda 工具名 `execute_shell_ommand`（execute_shell_c**o**mmand 少一个 c）；seq_1690 工具名 `todtolist_update`（todolist_update 里多打了个 t）。**同一批次里这些工具它前面都调对过**，只是末轮 token 级拼错。

**✅ 正确应为**（`<function=>` → 结构化 function call，工具名 `execute_shell_command` 精确无拼错）：
```json
{"type":"function","function":{"name":"execute_shell_command","arguments":"{\"command\": \"python3 -c \\\"import json; ...\\\"\"}"}}
```

### 4.2 ② premature_report_stop — prod_603992e9（刀剑神域动漫 PPT，参数已确认却只宣告）
> 前置 15 次成功、连 ask_user 确认了页数风格，末轮却用 `<report>` 写了段"现在开始…一口气做完"就停，没进入风格-大纲子任务。

```
<report>
好的，参数已确认：12-15页、均衡型风格、角色向内容侧重。

现在开始进入「风格-大纲」子任务，正在为刀剑神域定制动漫感设计风格并生成12页逐页大纲。完成后会继续进入资产规划和逐页HTML生成，一口气做完。
</report>
```
**✅ 正确应为**：`<report>` 只用于最终汇报；此处应直接 `create_subtask`（风格-大纲子任务）结构化调用，而非宣告。

---

## 5. Flash-lite v36 step3k **DPO v1**（无模板 `step3kdpo`）——2/47，全是「用报告代替动作」

> **DPO v1 模型的典型缺陷：更爱输出文字、有更强的"早交付感"。** 2 个失败**全是 ② premature_report_stop**，一个都不是文本形式 tool call——即 DPO v1 版本工具调用格式反而更稳，但**收尾纪律更差**：把"输出内容"误当成"完成任务"。（v2 见 §7）

**失败清单（2 premature）**：

| case | 终态 | 时长 | 前置成功调用 | 表现 |
|---|---|---:|---:|---|
| prod_c40ab9ac | render_suspect | 88s | 3 | `<report>` 写了整篇**分镜脚本大纲**就停 |
| seq_1006 | render_suspect | 71s | 14 | `<response>` 一句"现在开始执行…"就停 |

### 5.1 ② 把分镜脚本当交付物 — prod_c40ab9ac（百利德生日广告）
> 才 3 次调用（88s），就在 `<report>` 里写了一整篇**广告分镜脚本**（开场独白→幻想片段→推脱众生相→转折→高潮举杯→品牌升华），洋洋洒洒但**没写任何 deck 文件、没出一页 HTML**。它以为"把脚本写出来"= 完成了 PPT。

```
<report>
# 百利德生日反转故事脚本大纲
## 整体风格
- **叙事风格**：青春校园喜剧 + 温情反转…
## 分镜脚本
### 【开场】主角独白
**[画面]** 昏暗的宿舍，主角（林浩）一个人坐在桌前…
### 【幻想片段·穿插现实】…
### 【转折·社团教室】…
### 【高潮·举杯时刻】…
### 【结尾·品牌升华】…
</report>
```

### 5.2 ② 一句宣告就停 — seq_1006（美锦华宇新能源工作汇报）
> 前置 14 次成功、已建 task_pack/info_pack，末轮用 `<response>` 一句话宣告要进入风格/大纲阶段，然后停——**注意 query 里明确写了「禁止用 `<response>` 停下」，模型仍这么干**。

```
<response>
好的，已创建任务约束和信息素材文件，现在开始执行无模板模式的风格定义与大纲生成阶段。
</response>
```
**✅ 正确应为**（5.1/5.2 共同）：不写自然语言交付/宣告，直接发起 `write_file`（outline/style_spec）或 `create_subtask`（风格-大纲）结构化调用，把内容落成 deck 产物。

---

## 6. Flash-lite v36 step3k **DPO v1**（模板 `step3kdpo_tpl`）——2/47，报告代替动作 + 反问用户

> 同一个 DPO v1 模型跑模板模式。2 个失败：1 个仍是 ② 用 `<report>` 写 markdown 目录代替动作；1 个是 ③ **反问用户要参数**——在无人值守批测里等于卡死。（v2 见 §7）

**失败清单（1 premature + 1 narrate）**：

| case | 终态 | 时长 | 前置成功调用 | 表现 |
|---|---|---:|---:|---|
| seq_1472 | render_suspect | 177s | 13 | `<report>` 写了整份**跨境支付行业 markdown 大纲+表格**就停 |
| seq_0154 | render_suspect | 16s | 1 | ③ 反问用户要 role/scene/audience 等参数 |

### 6.1 ② 把 markdown 目录当交付物 — seq_1472（跨境支付面试汇报，模板 wps-dark）
> 前置 13 次成功，末轮在 `<report>` 里把 7 章内容连数据表格都写成 markdown（行业认知/市场规模/产业链/竞争格局…），**但一页模板 HTML 都没套**。模板模式要求套 wps-dark 版式出 HTML，模型却停在纯文本大纲。

```
<report>
# 跨境支付行业：市场洞察与战略机遇
## 目录 / Contents
- 01 · 行业认知  - 02 · 市场规模  - 03 · 产业链分析 …
## 02 市场规模
| 指标 | 2024 | 2025E | 2026E | … |
| 全球（万亿美元） | 2.4 | 2.7 | 3.0 | … |
…（7 章全文 + 多张表格）
</report>
```

### 6.2 ③ 反问用户要参数 — seq_0154（教师培训方案，16s 就停）
> query 已给足信息（14 页、面向校内教师、风格要求都写了），模型仍只调了 1 次 read_file 就**列出一串参数问用户**，然后停。批量无人值守下没有真人回复 = 直接卡死。

```
我已理解任务需求。不过当前请求中缺少 PPT 核心配置参数，需要先确认关键信息。
请提供以下配置参数：
- **演讲者身份**（role）：如"培训组织者"…
- **使用场景**（scene）…
- **目标受众**（audience）…
或者直接告诉我，您希望我按以下合理默认值执行：…
```
**✅ 正确应为**：批量模式下所有可自决项（role/scene/audience/页数）一律取合理默认**直接推进**；确需用户拍板才用 `ask_user` 工具（结构化），绝不用普通文本反问后停住。

---

## 7. Flash-lite v36 step3k **DPO v2**（`step3kdpov2_notpl` + `_tpl`）——5/91，含 3 种新形态

> DPO v2 相对 v1（各 2/47）失败量并未收敛（**5/91**）。5 例都是 turns=1（batch_summary 视角），但 last-turn 内容看细节比 v1 更杂：**3 种新形态、2 例落回 v1 熟悉的 ②/③**。以下逐 case（`main.json.messages` 末轮）：

### notpl 3 例

| case | 终态 | 时长 | 形态 | 一句话 |
|---|---|---:|---|---|
| prod_48c32afc | render_suspect | 437s | ⑤ **premature_finish_wrong_path** | 模型自报 `<ppt_task_finished>success`，但只做出 1 页 HTML（脚本 `verify_pages --expected 1`），dashboard `html_pages=0`——**产物落盘路径与 batch 检测的默认目录错位**，非模型口头认输 |
| seq_0902 | render_suspect | 1007s | ⑥ **empty_llm_response** | 末轮系统消息 `"LLM 返回空响应，已达到最大重试次数"`——**模型端返回真空响应**，被框架重试上限截断；不是文本形式 tool call、不是早交付，是**端点/推理层现象**，需查 vLLM 侧 |
| seq_1559 | render_suspect | 757s | ③' **narrate_then_stop 变种** | 末轮 `<response>任务包与信息素材文件已就绪，现在进入风格设计与大纲生成阶段。</response>` ——延续 v1 step3kdpo seq_1006 完全同款文案（"已...，现在进入..."），且明知 query 禁用 `<response>` 停下仍这么干 |

### tpl 2 例

| case | 终态 | 时长 | 形态 | 一句话 |
|---|---|---:|---|---|
| seq_0206 | done_no_html | 762s | ⑤ **premature_finish_wrong_path** | 模型 `<ppt_task_finished>success`，`ls` 显示 5 页 HTML 全在 `/mnt/data/skill/templates/dark-green/deck/htmls/`——**产物写到模板资源目录，不在 batch 扫描的 deck 输出根**，看板归 done_no_html |
| seq_1293 | done_no_html | 1087s | ②' **premature_report_wrong_path** | 末轮说"全部8页HTML文件均已生成"+ `<report>` 里写了 8 页完整 markdown 大纲，`ls` 也确实 8 页存在；但落盘在 `ppt-template-mode/decks/pptid_.../htmls/`——**同 seq_0206 的落盘目录错位** + 兼有"report 写成交付物"的 v1 老毛病 |

**新形态归纳**：

- **⑤ `premature_finish_wrong_path`（2 例，v2 首见）**：模型自认为完成、也确实产出了 HTML，**但落盘路径不在 batch 侧默认扫描的 deck 输出根**，导致看板判 render_suspect / done_no_html。这既是模型侧问题（skill 里默认 deck 路径应固定），也**可能是评测管线路径约定与 skill 变更不同步**——**需生成侧和评测侧一起核查**，不完全是模型的锅。
- **⑥ `empty_llm_response`（1 例，v2 首见）**：模型端直接返回空 body，触发框架重试上限。查 vLLM 端点日志（`10.210.9.14:114`）与该 case 时段（seq_0902 生成时约 25:00–41:47）的推理侧错误。
- **③'/②' 变种（2 例）**：与 v1 完全同款——"话代替动作"和"用 `<report>` 交付大纲代替产物"。这条毛病 v2 没修。

**训练/管线建议**：
1. **管线核查（优先，可能不是模型问题）**：seq_0206/seq_1293/prod_48c32afc 三例都有真实 HTML 产物但看板判失败，**先确认 skill 的默认落盘目录与 batch 扫描根是否一致**（尤其模板模式下的 `templates/dark-green/deck/htmls/`）。若是路径约定问题，修 skill 即可，无需怪罪模型。
2. **端点排查**：seq_0902 空响应查 vLLM 侧。
3. **训练侧**：③'/②' 复现 v1 短板，收尾纪律信号仍不足。

---

## 8. Flash-lite v36 step3k **CSFT**（`step3kcsft_notpl` + `_tpl`）——4/94，逐 case 原始 payload

> 4 例失败都是**末轮把结构化 function call 写成了自造的伪 XML 标签**（框架识别不到 `type:"function"`，判定"本轮无调用、说完了"，直接终止）。逐 case 展开：写成了什么、正确应该是什么、对应什么问题。

---

### 8.1 seq_0216（无模板 · render_suspect · 63s · 9 次成功调用后崩）
> 商业提案 xlsx → PPT。前 9 轮结构化 tool_calls 正常（`read_file`/`execute_shell_command`），到写 `info_pack.json` 这一步破格。

**写成啥（末轮 assistant.content 原样）**：
```
<file_action>
<target>/mnt/data/result/pptid_fd4d13af-6a25-4f78-a322-2f59450d9269/info_pack.json</target>
<action>CREATE</action>
生成本次PPT的内容素材汇总</summary>
</invoke>
```
问题点：
1. `<file_action>` 是**模型自造的标签**，框架里根本没有这个工具（写文件真名叫 `write_file`）。
2. 用了 `<target>`/`<action>` 描述参数，但**没有实际写入内容**——只有一句注释 `生成本次PPT的内容素材汇总`。
3. **闭合标签乱套**：起手 `<file_action>` 却用 `</summary></invoke>` 收尾，混了三种标签的关闭符。
4. 不是 `tool_calls` 字段里的结构化 JSON，是普通 assistant.content 文本 → 框架看到"无 tool_calls"→ 终止循环。

**✅ 正确应为**（用真实工具名 `write_file`，参数是合法 JSON，内容放进 `arguments.content`）：
```json
{
  "type": "function",
  "function": {
    "name": "write_file",
    "arguments": "{\"file_path\": \"/mnt/data/result/pptid_fd4d13af.../info_pack.json\", \"content\": \"{\\\"title\\\": ..., \\\"sections\\\": [...] }\"}"
  }
}
```

**对应啥问题**：**杜撰工具名 + 伪 XML 标签**。SFT 训练里没约束住"输出必须是结构化 function call"这一硬要求，模型学会了把 tool call 描述得"像 XML"（`<file_action><target><action>` 语义都对），但**这套语法是模型自己发明的，框架接不到**。属于 §2 表①c "杜撰 `<file_action>` 伪协议" 子形态。

---

### 8.2 seq_1081（无模板 · done_no_html · 323s · 1 次成功调用后崩）
> 公司介绍（联匠信息）。刚读完 SKILL.md + 参考素材（第 1 轮 tool_calls 正常），第 2 轮就用**伪 `<ask_user>` 标签反问用户**并停下。

**写成啥（末轮 assistant.content 原样）**：
```
我已了解附件内容和制作流程。本次为批量无人值守模式，我先确认几个制作参数（无人值守下会自动确认），随后直接进入无模板模式生成。

<ask_user>
questions=[{"option":[{"desc":"演讲者：联匠商务代表；场景：外部客户商业提案；受众：外部潜在客户/合作伙伴；页数：20页以上；模式：无模板","label":"按建议默认配置（推荐）"},{"desc":"页数更多、章节更细","label":"更详尽版本"}],"question":"请确认本次公司介绍PPT的制作配置（无人值守将自动按推荐项继续）"}]
</parameter>
</function>
</tool_call>
```
问题点：
1. **模型自己都说"本次为批量无人值守"**，却仍然反问用户——**违反了 query 明写的 "禁止把问题写进普通回复"**。
2. `<ask_user>` 是真实工具名（框架有这个 tool），但**里面用的是 `questions=[...]` 赋值语法**，不是合法 JSON 参数；这不是 `tool_calls` 结构化调用，只是 assistant.content 里的一段 XML 状文本。
3. **闭合标签是错的三层混搭**：`</parameter></function></tool_call>` ——三个都不是 `<ask_user>` 的对应闭合。
4. 无人值守 batch 里等于卡死：即便框架识别到了，也没有真人会回复。

**✅ 正确应为**（无人值守 batch 应**直接取默认配置继续**，不要发起 `ask_user`；确需拍板的字段用结构化 tool_calls，且 arguments 是合法 JSON 字符串）：
```json
// 场景 A：直接继续（推荐，无人值守下最合规）
{"type":"function","function":{"name":"execute_shell_command","arguments":"{\"command\": \"mkdir -p /mnt/data/result/pptid_XXX && ...\"}"}}

// 场景 B：真的必须问用户（本 case 不该走这条）
{"type":"function","function":{"name":"ask_user","arguments":"{\"questions\": [{\"question\": \"...\", \"options\": [...]}]}"}}
```

**对应啥问题**：**双重问题** —— (a) **收尾纪律：无人值守下反问用户**，跟 DPO v1_tpl 的 seq_18 是同一类"批测环境认知缺失"；(b) **格式退化：伪标签 `</parameter></function></tool_call>` 混杂**，与 seq_0216 同源。属于 §2 表①（textform_toolcall）+ 无人值守禁反问的复合错误。

---

### 8.3 seq_1380（无模板 · done_no_html · 100s · 16 次成功调用后崩）
> 物理课件（"第 6 章 第四节 熵 熵增加原理"，17 页参考 PDF → 新 PPT）。前 16 轮结构化 `execute_code` 全部正常（提取 PDF 图/文），到写 `task_pack.json` 破格。

**写成啥（末轮 assistant.content 原样）**：
```
I have all 17 reference slide images and the full text. Now let me write the task_pack.json and info_pack.json.

<file_action>
<target>/mnt/data/result/pptid_559b50b6-e600-4da3-8ee0-111277c352a5/task_pack.json</target>
<action>CREATE</action>
创建任务约束文件，固定本次课件的任务边界与模式</summary>
</invoke>
```
问题点：
1. **同 seq_0216 的模板**：`<file_action><target><action>...</summary></invoke>`——同一畸形。
2. **英文思路陈述夹在中间**（"I have all 17 reference slide images..."），SFT 训练数据的英文 CoT 泄漏。
3. 前 16 轮都是标准 `execute_code` 结构化调用（读 PDF 全部正常），偏偏到"写第一个策划文件"这一步就退化——**跟 seq_0216 精准一致的行为触发点：`write_file` 相关操作最容易破格**。
4. 计划里说要写"task_pack.json + info_pack.json"两个文件，末轮只吐出一个伪调用（连"计划中的两个"都没都写），再无下文。

**✅ 正确应为**（每个文件一次 `write_file` 结构化调用；内容直接放 `arguments.content`；两个文件用两次调用而非一段文本描述）：
```json
{"type":"function","function":{"name":"write_file","arguments":"{\"file_path\": \"/mnt/data/result/pptid_559b50b6.../task_pack.json\", \"content\": \"{\\\"role\\\": ..., \\\"scene\\\": \\\"教学\\\", ... }\"}"}}
{"type":"function","function":{"name":"write_file","arguments":"{\"file_path\": \"/mnt/data/result/pptid_559b50b6.../info_pack.json\", \"content\": \"{...}\"}"}}
```

**对应啥问题**：**在"从读到写"的切换点上格式退化 + 英文 CoT 泄漏**。前 16 轮都对（说明结构化 API 会用），偏偏在 `write_file` 这一类"要生成新文件内容"的 tool call 上退化到伪 XML——**具体触发点是"要在 arguments 里嵌一大段 JSON 内容"**，模型改用 `<target>/<action>` 描述参数是想"绕开 JSON escape"，但代价是标签自造 + 内容没落。属于 §2 表①c 子形态。

---

### 8.4 seq_1495（**模板模式** · done_no_html · 63s · 9 次成功调用后崩）
> 15 人考勤 xlsx → blue-table 模板 PPT。前 9 轮 `execute_code` 正常：读 xlsx → 抽员工名单 → 按部门聚合（中途一次 KeyError 自恢复），到写 `task_pack.json` 破格。**模板模式下第一例 CSFT 失败**。

**写成啥（末轮 assistant.content 原样）**：
```
The per-employee and department aggregation look reasonable (e.g. 综合部 lead 李程成 accounts for most of its overtime). Now let me write the task_pack.json.

<file_action>
  <target>/mnt/data/result/pptid_af9cdcbf-ccb5-4039-944d-894c020058f0/task_pack.json</target>
  <action>CREATE</action>
生成任务约束文件</summary>
</invoke>
```
问题点：
1. **和 seq_0216 / seq_1380 是精准同款**：`<file_action><target><action>...</summary></invoke>` 一模一样，只是缩进多了两格。
2. **触发点也一样**：前 9 轮 `execute_code` 全对，一到 `write_file` 就退化——与 notpl 两例的行为轨迹重合。
3. **英文 CoT 泄漏也一样**（"The per-employee...look reasonable"）。
4. **关键对照价值**：这是**模板模式**下的失败，**形态与无模板一模一样**——说明**这条短板与模板任务链路无关**，是模型层 `write_file` 输出格式的问题。
5. task_pack 是 5 阶段流程的**第一步产物**，第一步就崩→整条链停摆→0 页 HTML。

**✅ 正确应为**（同 seq_1380，模板模式下 task_pack.json 的字段还需包含 `template_id: "blue-table"`）：
```json
{"type":"function","function":{"name":"write_file","arguments":"{\"file_path\": \"/mnt/data/result/pptid_af9cdcbf.../task_pack.json\", \"content\": \"{\\\"template_id\\\": \\\"blue-table\\\", \\\"role\\\": ..., \\\"scene\\\": \\\"考勤汇报\\\", ...}\"}"}}
```

**对应啥问题**：**"跨模板/无模板复现的同款 `write_file` 格式退化"**——足以说明**这不是模板任务链路问题，而是模型在 `write_file`（尤其是要嵌 JSON 内容的场景）上的稳定性缺陷**。给训练/评测组的关键结论就在这一 case：**不用去查模板管线，改 SFT 数据里的 write_file 样例即可**。

---

### 归纳（4 例的共同规律，不是靠"跟 xxx 模型一样"总结的）

| 观察点 | 4 例的实际数据 | 结论 |
|---|---|---|
| **触发点** | seq_0216/1380/1495 都是"前几轮 execute_code/read_file 正常 → 到 write_file 崩"；seq_1081 是"第一轮读完素材 → 第二轮反问用户崩" | **`write_file`（要嵌 JSON 内容的场景）是主触发**；反问用户是次触发 |
| **畸形模板** | 3/4 都是 `<file_action><target>...</action>...</summary></invoke>` 一字不差；1/4 是 `<ask_user>...</parameter></function></tool_call>` | **模型在 SFT 训练里学到了这两套自造的伪 XML 模板**，不是随机 token 错乱 |
| **英文 CoT 泄漏** | 3/4（seq_1081 中文除外）末轮开头有一句英文思路陈述 | SFT 数据里混入了英文推理样本，长轨迹后期尤其容易漏出来 |
| **闭合标签错乱** | 4/4 都是"起手一个标签 + 收尾用另外 1–3 个标签的闭合"（`<file_action>...</summary></invoke>` / `<ask_user>...</parameter></function></tool_call>`） | 说明模型知道要"闭合"，但**闭合的对象记错了**——是训练时把不同轨迹的关闭符混在一起学的痕迹 |
| **模板/无模板差异** | notpl 3/47、tpl 1/47（全批完成），tpl 的 seq_1495 与 notpl 两例形态完全一致 | **模板/无模板对失败率和形态都无差异**，与模板任务链路无关 |
| **失败位置** | 全部发生在**前几次成功调用之后**（9/1/16/9）——不是从头就废 | 说明**基本工具调用能力是有的**，问题在"长轨迹里的稳定性 + `write_file` 特殊场景"，训练侧的重点应该放在这两个位置 |

**训练侧改法（对应上表逐条）**：
1. **优先补 `write_file` 样例**（尤其是 arguments 要嵌一段 JSON 内容的 case）——4 例里 3 例的触发点。
2. **删掉 SFT 数据里的 `<file_action>`/`<ask_user>...</parameter></function>` 这两套伪 XML 模板**——不是"抑制随机 token"，是模型真的从数据里学到了这套自造语法。
3. **英文 CoT 数据清洗**（或做双语一致约束）——3/4 都泄漏了英文思路。
4. **收尾闭合标签一致性约束**——训练时 `<X>...</X>` 必须成对，避免"起 A 关 B" 的教学。
5. **无人值守 batch 场景**在 system prompt / SFT 数据里明确"禁反问用户"——seq_1081 一例。

---

## 9. NEW · Flash-lite v36 step3k CSFT+DPO（`step3kcsftdpo_notpl` + `_tpl`）——1/94

> 2026-07-14 新接入。CSFT_notpl 3/47 挂（全是 `<file_action>` 伪协议）→ **csftdpo_notpl 47/47 全 done**（自家版本首次 100%）。DPO 阶段完全修掉了 CSFT 的畸形 tool_call，只剩 tpl 侧 1 例失败。

**失败清单**（仅 tpl 1 例）：

| case | 终态 | 时长 | LLM 轮次 | 形态 | 一句话 |
|---|---|---:|---:|---|---|
| seq_1190（tpl） | render_suspect | 571s | 15 assistant / 18 tool_call | ⑤ 交付摘要写全、但 HTML 没写完 | 与 CSFT 的 `<file_action>` 畸形无关，是"以为写完了/其实没写"的新形态 |

**seq_1190 复核（跟原推测不同）**：完整走完 18 次 tool_call（`execute_shell_command` 9 / `read_file` 6 / `write_file` 2 / `create_subtask` 1）+ 15 次 `assistant_output`；末轮 assistant 用 `<response>...</response>` 给了一份 24 页的完整交付摘要，说"PPT 已完成"。但沙盒 deck 目录里 `html_pages=0` —— **只调了 2 次 write_file，中间大量页没落盘就宣告完成**。这不是 CSFT 那种 `<file_action>` 畸形残余，而是"结构化调用一切正常、只是没写全就以为写完了"的**假 done**，成因跟其他模型的 `② premature_report_stop` 更接近。

**训练侧观察**：
- **DPO 对畸形 tool_call 的修复是可迁移收益**：CSFT_notpl 3 例 `<file_action>` 全在 CSFT+DPO_notpl 消失（notpl 侧 0/47），tpl 侧也从 CSFT_tpl 的 1 例畸形变成 CSFT+DPO_tpl 的 1 例假 done——**畸形语法这类"格式错"的问题 DPO 能训掉**。
- 但 DPO 没给 overall 加分（notpl 0.773 vs CSFT 0.789，差 0.016 落在噪声内）：**它换来的是可靠性，不是质量**。
- 生产环境的取舍：如果宁可牺牲 0.016 overall 换 100% 生成成功率，就选 CSFT+DPO；如果分数最大化优先，就选 CSFT。

---

## 10. OTTO agent v1.1 step5700（`otto_step5700_notpl` + `_tpl`）——88/94，failure rate ≈ 94% ⚠️ 重点说明

> 2026-07-14 接入。**44/47 case 生成失败（无模板 + 模板都是）**，情况比历史最差的 flashv1_1（12/47）还严重 3.7 倍。判分侧看到的 3 例分数没有代表性，**otto 这条路线目前不可用**。

### 10.1 关键前提：我方按厂商要求正确开启了 thinking 参数

**厂商指示**（模型作者 @张荧滢 明确说明）：
> "otto-agentv1_1_step5700 这个开 thinking 要加参数，之前测的没加是有问题的。"
> ```python
> extra_body={
>     "chat_template_kwargs": {
>         "thinking": True,
>         "reasoning_effort": "high",
>     }
> }
> ```

**我方配置**（`conf_v3_zh_otto_step5700_20260713.yaml`）：
```yaml
llm:
  base_url: http://10.210.9.14:126/v1
  model: otto-agentv1_1_step5700
  provider: openai              # ← 必须 openai，anthropic 路径会丢 extra_body
  api_key: <REDACTED_API_KEY>
  max_tokens: 128000
  temperature: 1
  extra_body:
    chat_template_kwargs:
      thinking: true
      reasoning_effort: high
```

**Smoke test 验证 thinking 已激活**：接入前独立跑了一次 "What is 2+3?"，回复里 `provider_specific_fields.reasoning` 字段有完整 CoT（"Thinking Process: 1. Analyze the Request..."），**证明 extra_body 已透传到模型侧、thinking + reasoning_effort=high 已生效**。

**结论**：厂商指示已 100% 落实。下面的失败**不是我方配置问题**，是模型侧行为。

### 10.2 失败形态分类

**notpl 44 例失败**：

| 形态 | 数量 | 说明 |
|---|---:|---|
| `<file_action>` 伪协议 | **23** | 与 CSFT 完全同款——写文件时把 tool call 吐成自造 XML |
| 其他伪 XML（自造 `<create_file>` / `<action>` 等） | 13 | 各种非框架识别的标签 |
| `<response>` 违规反问用户 | 7 | query 明确要求"无人值守、禁反问"，仍照发不误 |
| `<report>` 用报告代替动作 | 2 | 把 markdown 大纲当交付物 |
| **`AuthenticationError: Invalid token`** | 2 | litellm anthropic 路径偶发失效——**这 2 例是唯一可能与"接入方式"沾边的**，但我方 provider 明确设为 openai，仍偶发被 litellm 内部 routing 走 anthropic 分支导致；即便这 2 例全部修好、仍是 42/47 失败，与"格式退化"根因无关 |

**tpl 44 例失败**：分布几乎相同（`file_action_xml` 18 / `other_xml` 15 / `response_xml` 7 / `report_xml` 3 / `other` 4，占比一致）。

### 10.3 典型失败 payload（三例，全部是末轮 assistant.content）

**样例 A · prod_1eaed984 · 宝马 M4 生成任务**（无模板）：
```
<file_action>
  <target>/mnt/data/result/pptid_b75cbc16-.../task_pack.json</target>
  <action>CREATE</action>
写入任务边界文件</summary>
</file_action>

<file_action>
  <target>/mnt/data/result/pptid_b75cbc16-.../info_pack.json</target>
  <action>CREATE</action>
写入内容素材文件</summary>
</file_action>
```
（起 `<file_action>` 关 `</summary></file_action>`，混两种标签；框架无 file_action 工具→循环终止）

**样例 B · prod_26016eba · 商业案件 PPT**：
```
<file_action>
<target>/mnt/data/result/pptid_ea218601-.../task_pack.json</target>
<action>CREATE</action>
写入本次任务约束</summary>
</file_action>
```
（与样例 A 一字不差，说明是模型在 write_file 场景下的稳定"畸形模板"，不是偶发抖动）

**样例 C · prod_8145d493 · Anthropic auth error**（无模板）：
```
LLM 调用失败，已达到最大重试次数: litellm.AuthenticationError:
AnthropicException - {"error":{"code":"","message":"Invalid token
(request id: 202607140635481357325758268d9d6cKwWQ1fz)","type":"new_api_error"}}
```
（litellm 内部走 anthropic 路径带上的 key 触发 lightllm 端点 401；仅 2/47 例出现，与主流失败链路无关）

### 10.4 正确应为

```json
{"type":"function","function":{"name":"write_file","arguments":"{\"file_path\":\"/mnt/data/result/pptid_.../task_pack.json\",\"content\":\"{...json...}\"}"}}
```

### 10.5 责任划分（给 mentor / 汇报用）

| 问题 | 是否我方问题 |
|---|---|
| **`<file_action>` 伪协议 23+18 例** | ❌ **模型侧**——SFT 数据里学到了自造的伪 XML 语法，thinking 打开也没改善 |
| **其他伪 XML 13+15 例** | ❌ **模型侧**——同上 |
| **`<response>` 违规反问 7+7 例** | ❌ **模型侧**——违反 query 明写的批测 instruction，是收尾纪律问题 |
| **`<report>` 代替动作 2+3 例** | ❌ **模型侧**——把内容输出误当成任务完成 |
| **Anthropic auth error 2 例** | ⚠️ **litellm/lightllm 双向兼容层小问题**，与主流失败无关 |
| **thinking + reasoning_effort=high 是否正确开启** | ✅ **已正确按厂商指示开启并 smoke test 验证**（reasoning 字段有 CoT 输出） |

**训练/接入侧建议**：
1. **模型侧修 `<file_action>`/`<create_file>` 等伪标签**（同 CSFT 的旧问题，DPO 阶段已证明能修）——**这是本次跑不出结果的根本原因**
2. **训练数据里补足"结构化 function call 的强样例"**——现在模型完全没学会 OpenAI tool-calls 协议
3. **重跑前置条件**：需要一个已经在 SFT / DPO 中约束好 tool call 格式的新 checkpoint；当前 step5700 版本上重跑没意义

---

## 11. 跨模型对照小结（这是"早停"不是"超时"）

- flashv1_1 正常 done 的**中位时长 1218s**。失败 case 一半在 **16–460s** 就停（远早于正常完成）→ 是模型主动"说完就停"，不是跑不完。少数长的（1425/1507/1870s）是**干了很多活后在收尾一步崩掉**，前功尽弃。
- **两个家族失败形态不同，训练侧重点也不同**：

| 模型家族 | 主要失败形态 | 训练侧建议 |
|---|---|---|
| **Flash v1.1**（flashv1_1） | 文本形式 tool call（9），4 种畸形全见（含 DSML 泄漏、杜撰 `<file_action>`） | ①长轨迹后期工具调用格式稳定性 ②清理 DSML 特殊 token 泄漏 ③抑制杜撰工具名/伪协议 |
| **Flash-lite v36 step4k**（flash4k） | 文本形式 tool call，但集中在 `<function=>` + **工具名 token 级拼错** | 工具名 token 级正确性（`execute_shell_command` 别少字母/漏下划线） |
| **Flash-lite v36 DPO v1**（step3kdpo / _tpl） | **收尾纪律差**：`<report>`/`<response>` 代替动作、反问用户 | 强化"动作而非叙述"，抑制过早"交付感"；无人值守下禁反问 |
| **Flash-lite v36 DPO v2**（step3kdpov2_notpl / _tpl） | **3 种新形态**：⑤ premature_finish_wrong_path（2 例，落盘路径与 batch 扫描根错位）、⑥ empty_llm_response（1 例，端点空响应）、③'/②' 变种（2 例，延续 v1 短板） | ①**先查评测管线**：落盘目录错位可能是 skill 路径约定与 batch 扫描不同步（不完全是模型锅）②查 vLLM 端点空响应 ③训练侧仍需强化收尾纪律 |
| **Flash-lite v36 CSFT**（step3kcsft_notpl + tpl 全批） | **① 畸形语法回归**（notpl 3/3 + tpl 1/1 全中）：3 例 `<file_action>...</invoke>` 伪协议、1 例 `<ask_user>...</parameter></function>` 混杂伪标签；模板/无模板同款 | ①强化工具调用格式稳定性（DPO 的一个正向增益 CSFT 未继承）②清理 `<file_action>`/伪标签 token ③无人值守 batch 禁反问用户 |

> DPO 版本（v1/v2 一致）工具调用格式反而更稳（DPO 系 9 例失败没有一个是畸形语法），代价是"话多、早交付"更明显——这与内容维度分析里"DPO content 分最高、但高层美观/一致略降"的观察一致。**而 CSFT 走了相反的取舍**：单页观感/字体/间距更好（aes_high 自家第一），但**工具调用格式稳定性回退到 DPO 之前的水平**（notpl 3/3 + tpl 1/1 全畸形），失败形态与 flashv1_1/flash4k 同源，且**模板/无模板无差异**——是 SFT 层格式退化，不是模板任务链路问题。

---

## 12. 复现与明细

```bash
cd /home/gui-5d025-2/zyy/xhx_agent_v3
python3 scripts/analyze_failures.py     # 打印分布表 + 写 benchmark_failures_analysis.jsonl
```
- 机器可读明细（每条含 model / id / classify / dur_s / struct_toolcalls / last_marker / last_assistant / evidence）：`benchmark_failures_analysis.jsonl`
- 完整根因报告：`benchmark/docs/0708_生成失败根因分析_自家模型.md`
- 各批次原始轨迹：`output/<batch>/<case>/result.jsonl` 的 `message_records`

---

## 13. `<file_action>` 播报协议 feature 频率分析（2026-07-17 王博）

> **背景**：`<file_action>` 是 `agents/agentv3/system_prompt_parts/zh/09_output_principles.md` 定义的文件操作预播报协议——模型在调用写/改/删文件工具**前**必须先输出一段 `<file_action><target>…</target><action>CREATE|UPDATE|DELETE</action><summary>…</summary></file_action>` XML 摘要，作为"我即将写这个文件"的透明化播报，然后紧跟真实结构化 tool_call。**csftv2 (v2 训练数据) 的一个主打目标就是让模型学到这个 feature**——王博在 2026-07-17 明确指示要对新模型该 feature 的出现频率做定量对比。

### 13.0 术语与判定规则（给 mentor 直接粘贴用）

对 8 批 × 47 case 里**每一条 assistant 消息**（主 agent `message_records` 里的 `type=assistant_output` + 每个 `subtask_*.json.messages` 里的 `role=assistant`）逐条判定。三组指标各自独立、互补：

**A. 正向：一次 file_action → 是否落地写文件**
- **一次 file_action**：该 assistant 消息文本中包含子串 `<file_action>`。子串命中即算一次，无论标签闭合是否完整、`<target>/<action>/<summary>` 字段是否齐全（宽口径，尽量把模型的所有"尝试使用"都算进来，不因格式细节漏计）。
- **正确使用（ok）**：这条 assistant 消息**紧跟一个真实的结构化工具调用**——判据是"下一条消息是 tool（tool_call 事件、或 role=tool 的 tool_result），或这条 assistant 消息自己的 content 里就带 `type=tool_use` block"。即：**播报之后真的把文件写了**。
- **畸形使用（bad）**：这条 assistant 消息含 `<file_action>` 但**没跟真实工具调用**。可能是"末轮吐 fa 后 case 结束"（模型把播报当成了动作载体，实际没写文件）、"fa 后又输出另一条 assistant 消息"（自言自语）、或"fa XML 写在 `<subtask_result>` 汇报里当结构性总结"。这些都会被计入 bad。
- **畸形率 = bad / (ok + bad)**（在所有出现 file_action 的消息里，多少比例没落地写文件）。

**B. 反向：一次写/改文件的 tool_call → 前面是否有 file_action 播报**
- **一次 write**：出现一次 `write_file` tool_call（主 agent `tool_name==write_file` 或 subtask 内 tool_use block `name==write_file`）。（本项目暂无 edit_file 类工具；如未来出现 `edit_file/delete_file`，需要加进 `WRITE_TOOLS` 集合。）
- **有 fa 播报（w/fa）**：该 write_file 之前**最近一条** assistant 消息里含 `<file_action>`；或该 write_file 与 fa 位于同一 assistant 消息的 content 里（fa text block + tool_use block 同处）。
- **漏播报（w/o fa）**：write_file 前的最近 assistant 消息里没有 `<file_action>`——**训练目标违反项**（协议要求"写文件前必须播报"）。
- **漏播报率 = (w/o fa) / write_total**。

**C. 结构：`<file_action>` 消息里的 `<summary>` 标签成对情况**
- 对每条 fa 消息统计 `<summary>` 开标签数 opens、`</summary>` 闭标签数 closes。
- **成对 s_ok**：opens = closes 时的成对总数（即 min(opens,closes) 且 opens==closes 的 opens 值累加）。opens>closes 时 min(opens,closes) 也算成对，多出的 opens 计入 s_-close；反之亦然。
- **缺开头 s_-open**：闭标签比开标签多的差额（`</summary>` 单独出现，没有 `<summary>` 开头）。**这是本次跑测里最突出的畸形形态**（见 §13.1 表）。
- **缺结尾 s_-close**：开标签比闭标签多的差额（开头有但没闭）。
- 说明：本口径只统计"开头/结尾数量是否匹配"，不校验"是否嵌在 `<file_action>` 内部/顺序是否正确"（那是更严格的结构检查，本节先给数量口径给训练侧最快对齐的观察）。

⚠️ **三个坑**：

1. **bad ≠ fatal 挂死**：bad 里包含"subtask 已正常完成，结尾拿 `<file_action>` 当结构性总结"这类**非致命**的畸形——它们不会让 case 失败（case 仍是 done），但仍是模型把 feature 用歪了。真正让 case 挂死的是"主 agent 末轮吐 fa 后没 tool_call → 循环终止 → 无 HTML" 的 fatal 型（见 §2 ①d 表格里点名的 seq_0216 / seq_1495 / seq_1190 等）。**本节的畸形率是"所有使用中格式不规范的占比"，比 §2 ①d 的 fatal 挂死更宽，是训练侧看"格式稳定性"的合适口径**。
2. **必须扫 subtask**：主 agent `message_records` 只覆盖主循环产出；**大部分 file_action 使用和 write_file 调用都发生在 subtask 里**（PPT 生成的多阶段 subtask 结构）。漏扫会把 dpov2 的使用漏成 0、write_file 都算不到反向。
3. **正向 A / 反向 B 不对称**：A 关心"用了 fa 是不是真写了"，B 关心"写了文件是不是先播报了"。一次 write_file 前若无 fa，A 完全统计不到（因为 A 只看 fa 消息），必须靠 B。用户 mentor 强调"写/改 tool_call 前必须有 fa"就是 B 的口径。

### 13.1 跨版本对比表（8 批 × 47 case，全扫主 agent + subtask）

**A · 正向（fa → 落地）**：

| 版本 | fa 消息数 | 覆盖 case | 消息占比* | ok | 畸形 | 畸形率 |
|---|---:|---:|---:|---:|---:|---:|
| DPO v2 无模板 | 1 | 1/47 | 0.03% | 0 | 1 | 100.0% |
| DPO v2 模板 | 0 | 0/47 | 0.00% | 0 | 0 | — |
| CSFT 无模板 | 60 | 34/47 | 3.50% | 50 | 10 | 16.7% |
| CSFT 模板 | 70 | 31/47 | 3.02% | 60 | 10 | 14.3% |
| CSFT+DPO 无模板 | 65 | 37/47 | 3.71% | 57 | 8 | 12.3% |
| CSFT+DPO 模板 | 53 | 29/47 | 2.66% | 49 | 4 | 7.5% |
| **DPO+CSFT v2 无模板** | **124** | **47/47** ⭐ | **6.52%** ⭐ | **123** | **1** | **0.8%** |
| **DPO+CSFT v2 模板** | **164** | **47/47** ⭐ | **7.63%** ⭐ | **164** | **0** | **0.0%** ⭐ |

`*` 消息占比 = fa 消息数 ÷ 该批全部 assistant 消息数（主 agent assistant_output + 全部 subtask 里的 role=assistant）

**B · 反向（write_file → 是否先播报）**：

| 版本 | write_file 总数 | 之前有 fa | **漏播报** | **漏播报率** |
|---|---:|---:|---:|---:|
| DPO v2 无模板 | 105 | 0 | 105 | **100.0%** |
| DPO v2 模板 | 54 | 0 | 54 | **100.0%** |
| CSFT 无模板 | 70 | 25 | 45 | 64.3% |
| CSFT 模板 | 70 | 17 | 53 | 75.7% |
| CSFT+DPO 无模板 | 76 | 27 | 49 | 64.5% |
| CSFT+DPO 模板 | 81 | 22 | 59 | 72.8% |
| **DPO+CSFT v2 无模板** | **96** | **96** | **0** | **0.0%** ⭐ |
| **DPO+CSFT v2 模板** | **95** | **95** | **0** | **0.0%** ⭐ |

**csftv2 侧 write_file 前 100% 都有 fa 播报**（191 次写文件全部提前播报）。dpov2 100% 漏播报、CSFT 系 65~76% 漏播报。这是训练目标"写文件前必须播报"的直接达成度指标。

**C · 结构（`<summary>` 标签成对）**：

| 版本 | fa 消息数 | 成对 ✓ | **缺开头** ⚠️ | 缺结尾 | 缺开头率 |
|---|---:|---:|---:|---:|---:|
| DPO v2 无模板 | 1 | 0 | 0 | 0 | — |
| CSFT 无模板 | 60 | 28 | **32** | 0 | **53.3%** |
| CSFT 模板 | 70 | 43 | **27** | 0 | **38.6%** |
| CSFT+DPO 无模板 | 65 | 35 | **30** | 0 | **46.2%** |
| CSFT+DPO 模板 | 53 | 27 | **26** | 0 | **49.1%** |
| **DPO+CSFT v2 无模板** | 124 | 21 | **103** | 0 | **83.1%** ⚠️ |
| **DPO+CSFT v2 模板** | 164 | 65 | **100** | 0 | **61.0%** ⚠️ |

**csftv2 的 `<summary>` 缺开头率反而是家族最高**（notpl 83.1% / tpl 61.0%）——模型学会了"用 fa 播报"但生成时把开头 `<summary>` 漏掉，直接跳到内容再补 `</summary>`。**缺结尾 0 例**（所有版本），说明模型知道 fa 块要有 `</summary>` 收尾但不知道要先开 `<summary>`。

**典型样例**（csftv2_notpl / prod_1289b84a 主 agent msg 36）：
```
<file_action>
  <target>/mnt/data/result/pptid_.../task_pack.json</target>
  <action>CREATE</action>
写入任务约束文件，固化边界与模式</summary>
</file_action>
```
`<action>CREATE</action>` 后直接进入 summary 文本，缺 `<summary>` 开头。csft/csftdpo 也普遍这样，但比例更低（38~53%）。

**格式解读**：这不影响 A（ok）判定（用了 fa + 后接 tool_call 就是 ok），也不影响 B（write 前有 fa 就算播报）；但**格式检查工具/正则解析器会把这类当成 malformed XML**。若下游依赖严格 XML 解析（如生成侧要抽取 summary 文本入库），需要单独修。训练数据里 fa 样本的 `<summary>` 完整闭合率不够是根因——**建议 v3 数据补 fa 完整格式正例**。


### 13.2 结论

1. **v2 训练数据让 `<file_action>` feature 完全学到并放大**（A 正向 + B 反向双向验证）：
   - **A 正向 · 覆盖率**：从 DPO v2 的 0~1/47（**完全没学到**——那 1 条还是把 tool_call XML 拿来用 file_action 名字的畸形）→ CSFT 系的 65~79%（29~37/47）→ csftv2 的 **100%（47/47）**——每个 case 都在用
   - **A 正向 · 调用密度**：DPO v2 ~0% → CSFT 系 2.7~3.7% → csftv2 **6.5~7.6%**（2× 密度）
   - **A 正向 · 落地率（ok/畸形）**：CSFT 16.7%/14.3% 畸形 → CSFT+DPO 12.3%/7.5%（DPO 阶段先修一半）→ **csftv2 0.8%/0.0%**（v2 数据几乎把畸形清光）
   - **B 反向 · write_file 漏播报率**：dpov2 **100%** → CSFT 系 64~76% → **csftv2 0%**（191/191 次 write_file 全部提前播报）——这是训练目标"写文件前必须播报"的直接达成度。**这是本次跑测最亮的一项**。
2. **DPO 阶段的贡献**（A + B 都验证）：CSFT 的 10~10 例 A 畸形通过 DPO 阶段（csftdpo/csftv2 均含 DPO）显著清理；B 反向漏播报率 CSFT 64.3% → CSFT+DPO 64.5%（notpl 未改善）/ CSFT 75.7% → CSFT+DPO 72.8%（tpl 微改善）；csftv2 直接归 0——**A 畸形 DPO 就能修，B 漏播报要靠 v2 数据补正例**。
3. **为什么 DPO v2 几乎没有 file_action**：提示词 `agents/agentv3/system_prompt_parts/zh/09_output_principles.md` 从 2026-06-17 (commit 55afc28) 就已加入 file_action 段，DPO v2 跑批时（7-8）已经在提示词里被规定——**但 DPO v2 训练数据的 assistant 侧几乎没有 `<file_action>` 出现**，所以模型即便看到提示词也不会用。这直接证明**提示词规定 ≠ 模型执行；必须训练数据里有正例才能真正学到**。CSFT 数据加了 feature 后模型开始按规则播报（3~4%），csftv2 数据密度显著提升后模型全用起来（6~8% + 100% 覆盖 + 反向 100% 播报）。
4. **⚠️ 但 csftv2 有格式副作用：`<summary>` 缺开头率家族最高**（notpl 83.1% / tpl 61.0%，见 C 表）。模型学会了"用 fa 播报"但没学会"完整闭合 XML"，`<action>CREATE</action>` 后直接跳到 summary 文本再补 `</summary>`。**不影响功能（A ok / B 播报），但严格 XML 解析器会挂**。建议 v3 数据补 fa 完整格式正例。
5. **csftv2_tpl 唯一失败 prod_912af214 与 file_action 无关**：真根因是 litellm 端点 `tool_choice:{type:"none"}` API 兼容性 bug（subtask Finalize 挂 → 8 个 subtask 全 fail → 主 agent 1h 超时 → render_suspect 0 页）。即"file_action feature 在 csftv2 侧模型侧 0 挂案"。

### 13.3 训练侧含义

- v2 数据加入 `<file_action>` 相关样本的目标**已达成且量化验证**——不仅习得、还高频使用、还格式基本无畸形
- 副产物是 content_checklist 覆盖率上升（0.701 无模板 / 0.606 模板，家族首次破 0.7/0.6）；参见 `0708_模型特点与缺陷分析.md` §6
- 但也带来 deck 结构分小幅回退（-0.03 notpl）和 faithfulness 微降（-0.06 tpl，见分析文档 §6 用户复核段）——**未来 v3 数据可以考虑在保持 file_action 高频使用的同时补跨页结构/忠实度信号**

### 13.4 复现命令（正确扫主 agent + subtask）
```bash
python3 -c "
import json, os, glob
BATCHES = {
    'dpov2_notpl':   'output/testset_v2_step3kdpov2_notpl_20260708_182527',
    'dpov2_tpl':     'output/testset_v2_step3kdpov2_tpl_20260708_182645',
    'csft_notpl':    'output/testset_v2_step3kcsft_notpl_20260713_095138',
    'csft_tpl':      'output/testset_v2_step3kcsft_tpl_20260713_101403',
    'csftdpo_notpl': 'output/testset_v2_step3kcsftdpo_notpl_20260713_215002',
    'csftdpo_tpl':   'output/testset_v2_step3kcsftdpo_tpl_20260714_013217',
    'csftv2_notpl':  'output/testset_v2_step3kdpocsftv2_notpl_20260716_184121',
    'csftv2_tpl':    'output/testset_v2_step3kdpocsftv2_tpl_20260716_184126',
}
def scan(d):
    n=asst=fa=ok=bad=0; cases=set()
    for cd in sorted(glob.glob(f'{d}/*/')):
        n += 1; cid = os.path.basename(cd.rstrip('/'))
        # 主 agent
        rj = os.path.join(cd,'result.jsonl')
        if os.path.isfile(rj):
            try: rec = json.loads(open(rj).read())
            except: rec = None
            if rec:
                msgs = ((rec.get('result') or {}).get('state') or {}).get('message_records') or []
                for i,m in enumerate(msgs):
                    if m.get('type')!='assistant_output': continue
                    asst += 1
                    if '<file_action>' in (m.get('text') or ''):
                        fa += 1; cases.add(cid)
                        nxt = msgs[i+1] if i+1<len(msgs) else None
                        (ok := ok+1) if nxt and nxt.get('type')=='tool_call' else (bad := bad+1)
        # subtask
        for sf in sorted(glob.glob(f'{cd}subtask_*.json')):
            try: dj = json.load(open(sf))
            except: continue
            sm = dj.get('messages') or []
            for i,m in enumerate(sm):
                if m.get('role')!='assistant': continue
                asst += 1
                c = m.get('content')
                text = c if isinstance(c,str) else json.dumps(c)
                if '<file_action>' not in text: continue
                fa += 1; cases.add(cid)
                has_tool = isinstance(c,list) and any(b.get('type')=='tool_use' for b in c)
                if has_tool or (i+1<len(sm) and sm[i+1].get('role')=='tool'):
                    ok += 1
                else:
                    bad += 1
    return n, asst, fa, ok, bad, len(cases)
for L, d in BATCHES.items():
    if not os.path.isdir(d): continue
    n,asst,fa,ok,bad,cvr = scan(d)
    print(f'{L:<18} cases={n} asst={asst} fa={fa} ok={ok} bad={bad} bad%={bad/max(1,fa)*100:.1f}% pct={fa/max(1,asst)*100:.2f}% cvr={cvr}/{n}')
"
```

---

## 14. NEW · 疑似跨请求/上下文串线（284B step160 · seq_1157）

### 14.1 现象与直接后果

| 模式 | case | request_id | 请求上下文 | 实际末轮回复 | 后果 |
|---|---|---|---|---|---|
| 无模板 | seq_1157 | `16cf87374968` | 143 条医疗/HIT/PPT/HTML 制作上下文 | 突然回复“把故事名字更新为 Zihao Wang”及完全无关的英文星星故事；`structured_tool_calls=0`、`finish_reason=stop` | agent 直接结束，0 HTML，`render_suspect` |

这条不能归到原有 4 类“知道任务但工具调用格式错/提前报告/只宣告/不收敛”：回复内容与当前任务语义完全无关，且不是当前上下文里已有内容。更像 serving 侧拿到了别的请求结果或上下文发生串线，需模型/推理服务侧按 request id 查路由和 KV/cache 隔离。

### 14.2 直接证据

- 请求：`logs/run_batch_and_export/agentv3_concurrent_20260813_161223.log:123331`
- 响应及诊断字段：同文件 `:123359-123364`
- case 落盘轨迹：`output/testset_v2_step160_1105_0813_full_notpl_20260813_160352/seq_1157/main.json:1692`
- 同时点隧道仍 active、`NRestarts=0`、`/v1/models=200`；主评测进程未重启，因此现有证据不支持“本地隧道切断后串了旧回复”。

### 14.3 正确应为

模型应继续当前医疗 PPT 的下一步结构化工具调用（如生成/写入 HTML），或在确需结束时返回与医疗 PPT 当前任务一致的最终说明；不应出现任何 Zihao Wang/英文星星故事内容。

### 14.4 给模型/serving 侧的短结论

step160 的 `request_id=16cf87374968` 在 143 条医疗 PPT/HTML 上下文后返回完全无关的 Zihao Wang 英文故事改名内容，且无 tool call、`finish_reason=stop`，直接造成该 case 0 HTML。请按 request id 核查跨请求响应路由、连续批处理/KV-cache 隔离和日志中的实际入参/出参映射；这不是普通超时，也不是评测框架未识别工具协议。

<!-- BEGIN ppt_outline_merge_v39_dpov2_mtp_20260911 -->
## SenseNova-Flash-Lite-20260727-v39-fp8-step4k-dpov2-mtp：本轮终态盘点

任务 `ppt_outline_merge_v39_dpov2_mtp_20260911`；此表区分生成终态与分数，不把非空页面等同于质量通过。

| 模式 | 有效HTML/47 | 最新终态 | 缺分case |
|---|---:|---|---|
| 无模板 | 47/47 | {"done": 47} |  |
| 模板 | 47/47 | {"done": 47} |  |

本分支 smoke 已观察到风格规划深度耗尽后的伪工具文本、review 超时检查点被缓存、字小/越界等问题；详细原始证据见 `[260911]outline合并分支评测记录.md`。smoke 未并入本表正式分数。
<!-- END ppt_outline_merge_v39_dpov2_mtp_20260911 -->
<!-- BEGIN ppt_outline_md_only_v39_20260914 -->
## SenseNova-Flash-Lite-20260727-v39-fp8-step4k-dpov2-mtp：本轮终态盘点

任务 `ppt_outline_md_only_v39_20260914`；此表区分生成终态与分数，不把非空页面等同于质量通过。

| 模式 | 有效HTML/47 | 最新终态 | 缺分case |
|---|---:|---|---|
| 无模板 | 47/47 | {"done": 47} |  |
| 模板 | 47/47 | {"done": 47} |  |
<!-- END ppt_outline_md_only_v39_20260914 -->
<!-- BEGIN sensenova-flash-284b-vision-v16-20260908-sft-step400 -->
## sensenova-flash-284b-vision-v16-20260908-sft-step400：本轮终态盘点

任务 `sensenova-flash-284b-vision-v16-20260908-sft-step400`；此表区分生成终态与分数，不把非空页面等同于质量通过。

| 模式 | 有效HTML/47 | 最新终态 | 缺分case |
|---|---:|---|---|
| 无模板 | 13/47 | {"done": 13, "other_error": 4} |  |
| 模板 | 46/47 | {"done": 46, "render_suspect": 1} |  |

本批异常与原始证据：automation/tasks/sensenova-flash-284b-vision-v16-20260908-sft-step400/0916_takeover.md。smoke 未并入正式分数。
<!-- END sensenova-flash-284b-vision-v16-20260908-sft-step400 -->
