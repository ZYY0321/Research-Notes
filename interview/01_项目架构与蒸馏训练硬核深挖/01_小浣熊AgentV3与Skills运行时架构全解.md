# 小浣熊 AgentV3 与 Skills 运行时架构全解（源码级透视）

> **定位**：彻底讲清我们的办公 Agent 到底怎么写、怎么跑、状态怎么存、Skill 怎么驱动、子任务怎么委派、长上下文与记忆怎么管、沙盒怎么交互与去服务化。对应源码归档在 `archive-docs/03-slidegate-and-lingcoder/gui-5d025-2-full-handover/01_agentv3_architecture_and_runtime/`。

---

## 一、全链路分层架构总图

核心编排没有采用黑盒第三方框架（如 LangChain / LangGraph），而是自研了一套边界清晰、状态可回放的四层架构：

```text
Browser / 批测 CLI (run_batch_and_export.py / ppt_testset_runner)
  └─► FastAPI 服务层 (backend/server.py + database.py)：SSE 流式推送、会话持久化与恢复
        └─► 会话装配层 (session_setup.py + runtime_components.py + context_pipeline.py)
              ├─ 初始化 LLM / VLM / AudioLLM、按 locale 加载工具注册表、探活并绑定 Sandbox
              └─ 组装初始 State V3（注入 System Prompt、用户请求、附件解析上下文、Memory）
                    └─► [顶层调度器] AgentV3 (agents/agentv3/agent_v3.py)
                          ├─ MainAgent（主流程推进、全局预算管控、上下文被动摘要卸载）
                          ├─ SubtaskAgent（独立上下文局部闭环执行器，输出 <subtask_result>）
                          └─ ReflectionAgent（局部反思修正器，输出 <reflection>）
                                └─► [循环控制层] BaseAgent (src/base_agent.py)：while 步进、stop / finalize 路由
                                      └─► [单轮执行层] BaseNode (src/base_node.py)：编译消息 → 调 LLM → Schema 校验 → 沙盒/工具分发 → 写回记录
                                            └─► [模型适配层] BaseLLM (src/base_llm.py)：Provider 归一化、reasoning_content 与 thought signature 保留
```

### 一句话背诵四层职责边界
- **`BaseLLM`**：只管模型通信——清洗输入消息、适配 OpenAI / Anthropic / Cloudsway 协议、归一化响应并原样保留思考签名（`thought signature`），绝不碰工具执行与循环。
- **`BaseNode`**：只管**一轮**（1 个 assistant turn）——把结构化记录编译成 `messages`、调 `BaseLLM`、校验结构化 `tool_calls` 参数 Schema、分发执行工具并将成功或错误结果写回状态，绝不管“整个任务何时结束”。
- **`BaseAgent`**：只管**节点循环**——控制 `while` 循环是否继续、何时因步数耗尽切入 `FinalizeNode`、何时因 `waiting_user_input` 暂停挂起。
- **`AgentV3`**：只管**多智能体/委派调度**——在 `MainAgent`、`SubtaskAgent` 与 `ReflectionAgent` 之间切换执行权，维护待执行队列并完成结果的**原位回填**。

---

## 二、State V3：为什么抛弃“纯 `messages` 数组”，改用结构化事件状态？

早期 Agent 直接往一个 `messages: list[dict]` 里不断 append，一旦遇到前端文件列表渲染、上下文裁剪、用户确认后中断恢复、或者子任务隔离，就会出现“给模型看的临时视图”与“真实发生过的历史事实”互相污染。

`State V3` 将会话状态严格拆分为五块（见 `empty_conversation_state()`）：

```python
{
    "state_version": 3,
    "conversation_id": "...",
    "message_records": [...],    # 1. 事实层（Append-only 结构化事件日志，唯一真源）
    "asset_index": {...},        # 2. 资产层（上传原文件 files + 解析产物 parsed_artifacts）
    "runtime_control": {...},    # 3. 控制层（active_agent, global_loops, pending_subtasks, waiting_user_input）
    "todolist": [...],           # 4. 顶层任务进度表
    "projections": {...},        # 5. 视图投影层（按需编译出的 LLM messages 视图 / 前端展示视图）
}
```

### 核心机制：记录与视图分离（Record-Backed Compilation）
1. `message_records` 记录 8 类标准事件：`system_context`、`user_input`、`assistant_output`、`tool_call`、`tool_result`、`summary`、`subtask_summary`、`audit_event`，每条带唯一 `id`、`parent_id`、`subtask_id`、`refs`。
2. `MainAgent` 运行在 **record-backed 模式**：每轮 `BaseNode` 调模型前，调用 `rebuild_compiled_messages()` 从 `message_records` 动态编译出当前轮发给 LLM 的 `messages`；当发生上下文被动裁剪（`compact_conversation_context()`）时，只生成 `summary` 记录替换编译视图中的旧长文，**磁盘上的原始 `message_records` 毫发无损**，保证离线评测与 SFT 轨迹审计 100% 可回放。
3. `SubtaskAgent` 运行在轻量 **message-only 模式**：拥有独立局部 `messages`，避免污染主状态树。

---

## 三、主子任务委派闭环与 Skills 工程化机制

### 1. Skills 在系统里到底是什么？和 Prompt / Tool / Subagent 有什么区别？
- **Skill = 模块化业务 SOP + 阶段参考文档 + 专用脚本资产**：例如 `skills/ppt-maker/SKILL.md`（总入口）、`skills/ppt-no-template-mode/SKILL.md`（无模板模式）、`skills/ppt-template-mode/SKILL.md`（模板模式）。
- **按需渐进加载（Progressive Disclosure）**：System Prompt 里只注入极短的**技能目录索引**（名称 + 一句话触发场景 + 路径），避免几十个 Skill 一次性塞爆上下文并稀释注意力。当 `MainAgent` 判定用户要做 PPT 时，主动调用 `read_file` 读取 `ppt-maker/SKILL.md`，再按用户需求分流读取模板或无模板子 Skill。
- **中间产物落盘契约**：Skill 强制每个阶段在沙盒落盘标准结构化文件——`task_pack.json`（受众/页数/语言参数）→ `info_pack.json`（附件抽取事实与数据表）→ `style_spec.json` 或 `template_map.json`（版式映射）→ `outline.json`（逐页大纲，触发 `ask_user` 确认）→ `asset_map.json`（配图资产）→ 子任务并发调用 `html_page_generate_batch.py` 逐页生成 `page_*.html`。

### 2. `create_subtask` 完整控制流与「原位回填」设计
1. **交出控制权**：`MainAgent` 在某轮发出 `create_subtask`（或 `reflection`）工具调用后，`MainAgent._next_node()` 立即返回 `None`，将执行权交回顶层 `AgentV3`。
2. **预算门禁与入队**：`AgentV3._post_process()` 将子任务入队 `pending_subtasks`；派发前检查剩余 `global_loops_limit - global_loops` 是否充足，不足则直接拒绝执行并将拒绝原因写回主流程，防止死循环耗光配额。
3. **工具权限收窄（防无限递归与交互错乱）**：`SubtaskAgent` 自动过滤掉 `create_subtask`、`reflection`、`todolist`、`ask_user`，确保子任务不能再套娃建孙任务，也不能越过主 Agent 直接向人类提问。
4. **双上限收敛与 `<subtask_result>` 原位回填**：当子任务完成、达到 `subtask_max_loops` 或触发局部上下文上限（`_should_stop_for_context_limit`）时，自动进入 `FinalizeNode` 输出 `<subtask_result>...</subtask_result>`。`AgentV3` 提取该摘要，调用 `_write_tool_result_back_to_main()` **精准写回到主流程当初发出 `create_subtask` 那条 `tool_call_id` 对应的 `tool_result` 位置**，随后 `rebuild_compiled_messages()` 唤醒 `MainAgent`。
   - **为什么必须原位回填而不是 append 到末尾？** 因为原位回填符合 OpenAI/Anthropic 原生 Tool Use 的因果配对语义（`assistant.tool_calls[id=X] → tool[tool_call_id=X]`），主模型醒来看到的是一条干净连续的推理链，且子任务内部几十轮读写报错的几十 KB 噪声被完全隔离在子上下文之外。

---

## 四、三个关键工程细节：思考签名透传、文件型长期记忆、沙盒去服务化

### 1. 推理模型 `Thought Signature` 跨轮透传（`src/base_llm.py`）
在接入 Gemini 3 / Claude Thinking（经 Cloudsway / Anthropic 网关）做多轮工具调用与蒸馏时，部分模型要求下一轮回传上一轮工具决策时的加密推理签名（位于 `provider_specific_fields.reasoning_details[*].signature`），否则网关报错或推理退化。
- **实现细节**：并不是把明文 thought 塞进 `content` 污染正文，而是在 `_clean_messages()` 中检测 `has_google_thought_signature(msg)`，若命中则在重建 `assistant` 消息时深拷贝保留 `provider_specific_fields`，并将紧随其后的工具返回按协议归一化，同时在 `export_trace_to_openai.py` 中完整导出 `reasoning_content` 供 SFT/DPO 训练使用。

### 2. 文件型 Memory 系统（`memory_system.md` & `memory_update.py`）
淘汰了臃肿不稳定的早期 `mem0` + SQLite 向量库方案，收敛为轻量可审计的 **`memory://` 文件型记忆服务**：
- **三层存储**：`memory://user.md`（用户画像，上限 2000 tokens）、`memory://memory.md`（跨会话长期记忆，上限 2000 tokens）、`memory://date-memory/YYYY-MM-DD.md`（最近 3 天近期记忆）。
- **读写闭环**：开局由 `system_prompt_utils.py` 渲染进 System Prompt；运行中按需通过 `resource_search` 检索、通过 `read/write/edit_tool` 操作 `<p>...</p>` 标签包裹的记忆块（`p_tag_format.py` 校验防破坏受保护条目）；会话结束、触发上下文压缩或每日收口时异步执行 `memory_update.py` 沉淀新记忆。

### 3. 沙盒执行架构、FD 雪崩排障与新一代 Box-Agent（ACP 容器化运行时 + 离线轨迹效率分析）
- **独立 HTTP 沙盒形态与 FD 雪崩根因**：AgentV3 早期通过 `SandboxClient`（HTTP 调用）操作远端隔离容器；128 并发跑批时，每道题高频从远端沙盒下载 `SKILL.md` 到客户端 `/tmp` 临时文件，叠加长连接耗尽单机文件描述符（`[Errno 24] Too many open files`），引发连接重置与沙盒 500 连锁雪崩；工程上通过 `SANDBOX_CREATE_WAVE_SIZE=16` 波次限流、调大 `ulimit -n` 与进程内去服务化缓解。
- **架构升级：基于 ACP（Agent Client Protocol）的容器化 Box-Agent 蒸馏与 AgentCompass 四维解耦评测**：
  1. **Model × Benchmark × Harness × Environment 正交解耦**：在新一代评测与蒸馏管线中，采用版本化 Docker 镜像封装纯净的 Agent 运行时内核（Box-Agent），通过标准 ACP 协议对接无人值守批量蒸馏器与评测桥接层——自动注入 `autoApprovePlan` 计划审批、单次权限放行，以及遇到 `waiting_for_user` 边界时触发有上限的中立默认续写（`MAX_CONTINUATIONS`），每道题产出独立的不可变 Attempt 证据包（`protocol.jsonl` 完整协议流、`artifacts.json`、`completeness.json`），容器销毁时连带进程树完整回收，彻底根治宿主机状态泄漏与僵尸进程。
  2. **零 LLM 成本的确定性轨迹效率指标（`TraceEfficiencyAnalyzer`）**：除了结果正确率，通过固定分词器（`o200k_base`）离线审计轨迹的两个核心过程效率指标：
     - **Outcome Efficiency（$\text{OE} = C_{\text{first}}^{\text{out}} / C_{\text{full}}^{\text{out}}$）与可交付后冗余率（$R_{\text{post}} = 1 - \text{OE}$）**：衡量最终正确答案首次形成后，模型还在继续空转输出多少比例的冗余推理 Token；
     - **工具重复调用率（Repetition Rate, $\text{RR} = \frac{T - |\mathcal{A}_T|}{T - 1}$）**：基于同名工具 + 规范化参数 Sørensen–Dice 相似度 $\ge 90\%$ 识别近似重复调用，精准量化模型在沙盒中的原地打转与路径震荡。
