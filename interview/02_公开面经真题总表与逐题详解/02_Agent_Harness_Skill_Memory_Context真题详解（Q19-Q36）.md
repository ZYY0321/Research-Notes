# 分册二：Agent Harness、Skill、Memory 与 Context Engineering 真题详解（`Q19`–`Q36`）

> 覆盖阿里国际 Agent 一二三面、字节火山 Agent 面、深智/智谱等岗位最高频的 **Harness Engineering、Skill/MCP、上下文压缩、记忆治理与高并发排障** 真题。

---

### Q19：Agent Loop、Workflow、Orchestrator 和 Agent Harness 到底有什么区别？如何评价一个 Harness 的好坏？
- **核心结论**：按系统控制边界从小到大递进：
  1. **Agent Loop**：最内层的单智能体迭代循环（基于当前 Context 调模型 → 产出 Action → 环境返回 Observation → 判断继续或停止）；
  2. **Workflow**：由开发者静态硬编码的有向图/状态机分支（如固定先 OCR 再翻译再入库），确定性强但缺乏自主应变能力；
  3. **Orchestrator（编排器）**：负责任务拆解、主子智能体路由、队列调度、依赖与全局预算分配（如我们系统里的顶层 `AgentV3` 调度器）；
  4. **Agent Harness（智能体运行治理底座）**：包在模型外面的**完整工程操作系统**——除了 Loop 和 Orchestrator，还统管 **System Prompt 与动态 Skill 装配、结构化状态存储（State V3）与上下文压缩、工具 Schema 校验与权限审批、隔离沙盒（Sandbox/ACP）、断点持久化恢复（Checkpoint/Resume）、以及全链路 Trace 可观测性与离线评测**。同一个模型在不同 Harness 下真实能力可相差数倍。
- **评价好坏的五个硬指标**：① 工具接口人机工程学（Schema 清晰度、报错信息是否可自愈）；② 上下文可控性（压缩不丢硬约束且命中 KV Cache）；③ 安全与隔离边界（权限分级、沙盒进程树干净回收）；④ 状态可恢复性（支持异步挂起与重放）；⑤ 评测可归因性（能精确区分模型错、协议错还是基建错）。

---

### Q20：ReAct 一步包含什么？结构化 Tool Call 与文本解析式调用有何区别？什么叫“伪工具调用早停”？
- **核心结论**：ReAct 一步由 **Thought（推理分析当前状态与下一步计划）→ Action（选择工具名与结构化参数）→ Observation（Harness 校验执行后写回的环境结果）** 组成，直至模型不再发出工具调用（正常完成）、发出 `ask_user`（挂起待确认）或触达 `max_loops` 预算上限终止。
- **结构化 Tool Call vs 文本正则解析**：早期 ReAct 靠提示词让模型输出 `Action: search\nAction Input: ...` 再用正则硬抠，遇到代码块或嵌套引号极易解析崩溃；现代原生 Function Calling 由推理引擎结合有限状态机/语法约束解析进独立 `assistant.tool_calls` 数组，与给用户看的正文 `content` 严格物理隔离，经 `BaseNode` 做 JSON Schema 必填项与类型校验后才执行。
- **“伪工具调用早停”实战案例**：我们在评测 `SenseNova-Flash-284B`（如 `seq_1293`、`seq_2016`）时抓到典型协议退化——模型把预训练/后训练残留的内部标记 `<｜DSML｜tool_calls><｜DSML｜invoke name="execute_code">...` 当成普通字符串吐进了 `content`，而结构化 `tool_calls` 字段为空！Harness 看到 `tool_calls` 为空便判定本轮对话正常结束，导致 0 页产物提前终止。排查时需联合原始响应分清是**模型自身没对齐格式**还是 **Serving 网关的 Tool Parser 漏截获**。

---

### Q21：单 Agent 与多 Agent 架构怎么选？多 Agent 之间通信如何保证结果可验证、不传谣放大幻觉？
- **核心结论**：**能用“单主 Agent + 按需工具/Skill”解决的任务，绝不盲目拆成对等网状多 Agent 群聊**（多 Agent 群聊通信开销大、责任边界模糊、上游一个小幻觉会被下游当成事实层层放大）。只有当**子任务上下文极重（如读几十页财报或跑几十轮代码调试会撑爆主窗口）、工具权限需要严格隔离、或子任务天然可并行（如逐页并发生成 HTML / 多路独立调研）**时，才引入层级式主从架构。
- **通信可验证三大设计铁律（结合 AgentV3 + MobileGym++）**：
  1. **结构化契约交接 + 共享文件系统验真，拒绝纯自然语言传话**：在 `AgentV3` 中，子任务不仅要返回 `<subtask_result>` 结构化摘要并**原位回填**到主流程的 `tool_result`，更重要的是它产出的 `info_pack.json`、`outline.json`、`asset_map.json` 必须落盘在共享工作区并通过 Schema/脚本确定性校验（如 `slice_stage5_inputs` 发现缺文件当场报错打回，绝不听信子任务口头说“已写好”）；
  2. **严禁无限递归套娃**：`SubtaskAgent` 显式屏蔽 `create_subtask` 与 `ask_user`，控制深度为 1 层，所有对用户的交互统一收口在 `MainAgent`；
  3. **全局预算统一兜底**：子任务共享顶层 `global_loops_limit`，剩余配额不足时调度器直接拒单并回填原因。

---

### Q22：Claude Code / 小浣熊 AgentV3 本质是单 Agent 还是多 Agent？为什么要设计无递归权限的 Subagent？
- **核心结论**：它们都属于 **「单主线程编排为主（Single Master Loop）+ 受控无状态子代理委派（Scoped Subagent Delegation）」** 的混合范式，而非松散对等的多智能体框架。
- **设计精髓**：
  1. **保住主线程的全局连贯性与前缀缓存（Prefix Cache）**：主 Agent 始终持有完整的用户意图、`todolist` 进度和全局决策链，不会出现多个 Agent 互相抢方向盘；
  2. **把子代理当成“自带独立临时草稿本的高阶工具”**：比如在代码库里翻找 30 个文件定位一个函数，或在 PPT 流程里反复调试数据清洗脚本，中间会产生数万 Token 的文件内容和报错堆栈。放进无递归权限的 `SubtaskAgent` 跑完后，几万 Token 临时上下文随子代理销毁直接释放，主线程只收到几百字的 `<subtask_result>` 结论与落盘文件路径；
  3. **为什么禁递归（No Sub-subagent）**：一旦允许子代理无限派生孙代理，调用树呈指数爆炸、超时取消难以穿透、且局部代理缺乏全局视角极易偏离原始任务约束。

---

### Q23：【必考辨析】Skill、MCP、Function Calling、Tool 四者的本质区别与协作关系是什么？
- **核心结论（四句话一针见血分清层次）**：
  1. **Function Calling（模型推理层能力）**：大模型把自然语言意图转化为结构化 JSON 函数名与参数（`tool_calls`）的**原生输出机制**；
  2. **Tool（运行时原子执行单元）**：Harness 暴露给模型的一个具体可执行函数（如 `read_file`、`execute_shell`、`query_order`），含名称、参数 JSON Schema 与后端实现；
  3. **MCP（Model Context Protocol，工具连接通信标准协议）**：类似 AI 界的 USB-C 接口标准，规定了 Agent Host 如何通过标准 Client-Server 协议动态发现并调用外部数据源或应用暴露的 Tools / Resources / Prompts，解决“N 个 Agent × M 个外部服务重复写胶水代码”的问题；
  4. **Skill（领域业务知识与工作流 SOP 层）**：**Tool 解决“有什么锤子可用”，Skill 解决“盖房子先打地基还是先砌墙、验收标准是什么”**。一个 Skill 通常是一个自包含目录（含 `SKILL.md` 领域步骤规范、边缘情况避坑指南、模板资产与专用辅助脚本），指导模型按正确业务顺序编排多个 Tools / MCP 接口。

---

### Q24：复杂的商家 SOP 写成 Skill 后，模型跳步、漏步或收尾违规怎么办？如何保证 Skill 被严格逐步执行？
- **核心结论**：**纯靠在 `SKILL.md` 里写“请你千万不要跳步”的软提示词，在长上下文下一定会被违背**（例如我们实测连 Opus 4.7 在子任务收尾轮都会违背 `SKILL.md` 第 132 行禁令多吐一个悬空 `<file_action>`）。必须把软文档升级为 **「提示词引导 + 阶段产物硬门禁 + 确定性脚手架 + 后训练内化」** 四道防线。
- **四道工程与算法防线**：
  1. **阶段中间产物前置校验（Artifact Gatekeeper）**：在我们的 PPT Skill 中，每一阶段必须落盘标准 JSON（`task_pack.json` → `info_pack.json` → `outline.json` → `asset_map.json`），下游脚本（如 `preflight.py`、`slice_stage5_inputs.py`）启动时强制校验上游产物存在且 Schema 合法，跳步直接拦截报错打回；
  2. **动态工具可见性门控（State-Scoped Tool Masking）**：在不同阶段只解锁当前允许调用的工具集（如同 MobileGym++ 只暴露当前前台 App 的 MCP 函数，或在未完成安全校验前隐藏对外发送/支付工具）；
  3. **显式进度账本（`todolist` 状态同步）**：将 SOP 关键节点注册进顶层 `todolist`，`AgentV3` 在收尾时执行核对，未勾选必做项禁止直接 `done`；
  4. **轨迹合规清洗与 DPO 对齐**：扫描线上违反 SOP 的跳步轨迹作为 `rejected`、完整合规轨迹作为 `chosen` 做全轨迹 DPO 定向纠偏。

---

### Q25：【高频场景题】当系统里有几百个商家 Skills / MCP Tools 时，全塞进上下文会导致 Context 爆炸且选错工具，怎么解决？
- **核心结论**：几百个工具 Schema + Skill 全文动辄 5 万+ Token，不仅贵且慢，更会引发严重的**注意力稀释与同名相近工具误选**。解法是 **「三级渐进式披露（Progressive Disclosure）+ 语义/场景路由 + 代码执行聚合」**。
- **具体落地方案**：
  1. **Skill 两级按需加载（目录索引 → 按需 `read_file`）**：System Prompt 里只放每个 Skill 的 `name + 1句话触发条件 + 路径`（100 个 Skill 也才 ~3k tokens）；模型命中某个业务（如“外贸海运询盘报价”或“模板 PPT 生成”）后，再调 `read_file` 把对应 `SKILL.md` 读入当前会话；
  2. **Tool 动态作用域挂载与检索路由（Tool Search / Scoped Registry）**：
     - **按上下文状态自动作用域裁剪**：像我们在 MobileGym++ 面对 **333 个 MCP 工具**时，绝不把 333 个全喂给模型，而是只动态挂载当前前台激活应用对应的 5–14 个工具（立省 95% 工具 Token 并杜绝跨应用乱调）；
     - **元工具检索（`search_tools`）**：当全局工具上千时，默认只挂核心基础工具 + 一个 `search_tools(query)`，模型先用自然语言搜回 Top-5 相关工具 Schema 再注入下一轮调用；
  3. **高频碎工具下沉为脚本/复合动作**：避免暴露几十个细碎的原子 CRUD 接口，封装为内聚的领域脚本或允许在安全沙盒写几行 Python 批量组合调用。

---

### Q26：Skill 与 Harness 的「自我迭代（Self-Evolving）」本质是什么？如果让你从历史轨迹和人类反馈自动抽取并评测 Skill，怎么做？
- **核心结论**：Skill/Harness 自我迭代的本质是 **在无需重训百亿权重的前提下，把线上失败教训、专家人工接管修改与高频成功路径，结构化编译进外部符号经验库（`SKILL.md` / 工具护栏），属于非参数化的在线策略梯度更新（Symbolic Policy Optimization）**。
- **四步自动抽取与回归评测闭环设计**：
  1. **轨迹对比挖掘触发源**：收集三类高价值样本——① 多次报错试错最终成功的曲折轨迹（提炼避坑捷径）；② 人类/商家手动修改了 Agent 回复或中途接管的会话（提炼领域隐性规则，如“发往巴西报价必须询问税号 CNPJ”）；③ 同类高频重复成功轨迹（固化为标准 SOP 与脚本）；
  2. **结构化抽象与去过拟合**：用强模型对比失败段与成功段，抽象出**触发前提（Trigger）+ 执行步骤（Steps）+ 边界禁忌（Guardrails）**，注意剥离单次客户的具体姓名单号，防止把单题特例写死成全局规则；
  3. **回归基准门禁评测（防负优化）**：正如我们在小浣熊做 `outline 单一依据 Skill 优化` 时的铁律——**任何新抽或修改的 Skill 上线前，必须在冻结题集上跑同模型 A/B 对照**，同时核查目标场景成功率是否提升、历史已过回归题是否退化、以及单题平均 Token 与时延是否恶化；
  4. **生命周期淘汰与合并**：监控线上 Skill 被读取后的任务转化率与冗余度，定期合并重叠 Skill、下线低效过时规则。

---

### Q27：多轮 Agent 对话变长后，上下文压缩（Context Compaction）何时触发、怎么压才不丢关键约束、且不破坏 KV Prompt Cache？
- **核心结论**：上下文压缩如果做成“每轮滑动窗口删最老的 2 条消息”，会瞬间**击穿整条会话的 KV Prefix Cache（导致每轮全量重算 Prefill，成本与延迟暴增 5–10 倍）**，还会把开局用户的硬约束删丢！
- **工业级三层无损且缓存友好的压缩架构（对标 Claude Code & 我们的 AgentV3）**：
  1. **何时触发（水位线批量触发，绝不逐轮滑窗）**：监控 `non_system_tokens > budget_threshold`（如窗口上限的 75%–80%）时才**低频触发一次批量压缩**；未触线前保持前缀字节级完全不变，100% 吃满推理引擎 Prefix Caching；
  2. **三层分级压缩策略**：
     - **第一层（工具巨型结果卸载 Offload）**：历史轮次里几十 KB 的网页正文、大表输出或长报错日志，落盘保存为文件，编译视图里替换为百字摘要 + 文件引用路径（模型后续真需要细节可随时按路径重读）；
     - **第二层（子代理天然隔离）**：探索性脏活派给 `SubtaskAgent`，主上下文原本就不存中间废话；
     - **第三层（结构化状态摘要段替换）**：触发阈值时，将较早的多轮交互压缩成固定槽位的 `<summary>` 记录（**原始用户目标与硬性约束、已完成步骤与落盘产物路径、已确认的用户偏好、当前未决卡点**），而保留最近 $K$ 轮原始 `assistant/tool` 配对消息不拆散（绝不能把一对 `tool_call` 和 `tool_result` 从中间劈开，否则 API 直接 400 报错）；
  3. **事实层与视图层解耦（`State V3`）**：压缩只改编译出来的 `messages` 投影视图，底层 `message_records` 全量保留，审计与离线训练零损失。

---

### Q28：Context、Working State、Session、Transcript（事件日志）和 Long-term Memory 五者怎么严格区分？
- **五句话精准定义（结合 `State V3` 源码一锤定音）**：
  1. **Context（模型上下文表面）**：**下一轮调 `llm.completion()` 时真正发出去的 Token / `messages` 数组**——它是临时的、经过压缩裁剪和角色映射的“投影视图”；
  2. **Working State（工作态）**：当前任务正在读写的**结构化运行状态**（如 `AgentV3` 中的 `todolist`、`asset_index` 已解析文件表、`runtime_control` 里的剩余预算与子任务队列）；
  3. **Transcript / Event Log（事件事实日志）**：磁盘上持久化、不可篡改的全量事件流（对应我们的 `message_records` / `result.jsonl`），**磁盘有完整 Transcript 不等于当前模型 Context 里全塞得下**；
  4. **Session / Thread（会话生命周期）**：一次完整任务或一段连续交互的隔离边界与恢复句柄（含 `conversation_id`、沙盒工作目录绑定与挂起状态）；
  5. **Long-term Memory（跨会话长期记忆）**：跨越单个 Session 生命周期、经过价值筛选、冲突消解与有效期治理后沉淀下来的用户画像与经验知识（如 `memory://user.md`、`memory://memory.md`）。

---

### Q29：Personal Agent 的长期记忆（Memory）怎么做分级、抽取、检索、冲突更新与过期失效治理？
- **核心结论**：长期记忆最忌讳“把所有历史聊天切片全塞进向量库无脑 Top-K 召回”——那会导致三天前的旧报价和今天的改价同时召回打架！成熟的 Personal Agent 记忆需按 **「三级存储 + 写入门控 + 冲突覆写 + 时效戳失效」** 治理。
- **完整系统设计（结合 `AgentV3` 文件型记忆 + 外贸场景）**：
  1. **三级分层架构**：
     - **核心画像与铁律层（Profile / Policy Memory，如 `user.md`）**：商家主营品类、最低毛利红线、固定物流合作方，体量小（<2k tokens）常驻注入 System Prompt；
     - **语义事实与客户档案层（Semantic / Entity Memory，如 `memory.md` + 客户维度分片）**：某买家的历史询盘偏好、目标价区间、港口信息，按实体 ID + 语义混合检索（`resource_search`）；
     - **近期情景日志层（Episodic Date Memory，如 `date-memory/YYYY-MM-DD.md`）**：保留最近 $N$ 天会话摘要，支撑短期连续跟进；
  2. **异步抽取与写入门控**：在会话结束或触发压缩时（`memory_update.py` 异步执行，不阻塞前台响应延迟），仅抽取具有跨会话复用价值的事实，忽略寒暄与一次性噪音；
  3. **冲突更新与过期失效（Crucial!）**：每条记忆块（`<p>...</p>`）附带 `updated_at`、`source_session` 与有效期属性——当商家更新“海运费上调 10%”或“某 SKU 停产”时，走精确 `edit_tool` **原地覆写或将旧条目打标 `deprecated`**，绝不让新旧矛盾价格并存；对库存、汇率、限时促销等高时变信息设置硬 TTL，超时强制触发工具重查而非采信旧记忆。

---

### Q30：用户中途确认（`ask_user`）或买家隔天回复，异步长任务的状态持久化与断点恢复（Checkpoint & Resume）怎么设计？
- **核心结论**：绝对不能靠把整个 Python 进程 `await` 挂在内存里等三天（服务重启或容器扩缩容瞬间全丢）！必须做成 **无状态计算节点 + 结构化事件状态落盘（Event-Sourced Checkpointing）**。
- **完整挂起—恢复链路（基于 `AgentV3` 真实实现）**：
  1. **挂起（Yield & Persist）**：当模型发出 `ask_user` 工具调用请求商家确认大纲或底价时，`BaseNode` 记录该 `tool_call`（保存 `pending_call_id`），此时不生成假 `tool_result`，而是将 `runtime_control.waiting_user_input = True`、会话状态置为挂起，将整份 `State V3`（含 `message_records`、`asset_index`、沙盒产物快照路径）序列化落库，立即释放计算线程与 GPU 连接；
  2. **恢复（Hydrate & Resume）**：无论 5 分钟还是 3 天后收到用户/买家回复，任一可用 Worker 从数据库反序列化加载该 `conversation_id` 的 `State V3`，将用户回复加上运行时上下文前缀封装为对应 `pending_call_id` 的 `tool_result` 写入 `message_records`，清除挂起标志，调用 `rebuild_compiled_messages()` 重新编译上下文后无缝接续下一轮循环；若原沙盒容器已回收，则先从对象存储拉回会话 `asset_index` 工作区文件再继续执行。

---

### Q31：模型连续多次调用同一个工具报错，或者陷入 A→B→A 路径震荡死循环，Harness 层怎么拦截与自愈？
- **核心结论**：长程 Agent 失败耗时大头都在无效死循环（如我们分析 `seq_1157` 单题卡在修脚本报错上耗费 150.8 分钟）。需在 Harness 层建立 **三级递进熔断与干预机制**：
  1. **错误分类结构化回传（区分可重试 vs 不可重试）**：`BaseNode` 捕获异常后不崩进程，返回带明确原因的结构化错误（如 JSON 语法错、参数字段路径错标为 `retryable: true` 让模型自改；工具不存在、权限拒绝、无 OCR 环境标为 `retryable: false` 明确告知模型勿再重试该工具）；
  2. **在线重复度检测（Online Repetition Guard）**：实时计算滑动窗口内的工具调用相似度（同工具名 + 参数 Dice 相似度 $\ge 0.9$ 连续出现 $K=3$ 次，或页面状态哈希 `uiHash` 出现 `A→B→A→B` 二阶环），Harness 主动拦截第 3 次执行，在 `tool_result` 中注入系统强干预提示（*“检测到你已连续 3 次以相同方式调用 X 失败/无进展，请停止当前路径，切换备选方案或汇总当前已知信息”*）；
  3. **局部反思（`ReflectionAgent`）或预算兜底 `FinalizeNode`**：触发停滞时可调度独立反思节点审视错误根因重排计划；若触及 `subtask_max_loops` 或 `global_loops_limit`，强制剥夺工具调用权限切入 `FinalizeNode` 保底交付已有成果。

---

### Q32：工具调用超时或网络抖动时怎么设计重试？如何区分只读幂等工具与有副作用的写操作工具（如发报价/扣款）？
- **核心结论**：**网络超时中最危险的不是连接没建上，而是“请求已发到下游且实际执行成功了，只是回包超时（Read Timeout）”**——此时如果无脑自动重试，就会给同一个外贸买家连发三封报价单或重复下单扣款！
- **工程分级治理规范**：
  1. **超时拆分**：严格区分连接池获取/TCP 握手超时（`connect_timeout`，请求根本没发出去，任何工具都可安全重试）与读写响应超时（`read_timeout`，下游状态未知）；
  2. **工具元数据强制标注副作用等级（Side-Effect Level）**：
     - **只读幂等类**（如 `web_search`、`read_file`、`query_logistics`）：遇超时或 5xx 采用指数退避（Exponential Backoff + Jitter）自动重试；
     - **本地可覆盖幂等写**（如 `write_file` 覆写沙盒文件）：可安全重试；
     - **外部有状态非幂等写**（如 `send_message`、`create_order`、`apply_discount`）：**严禁在 `read_timeout` 后盲目自动重发**！必须携带会话级幂等键（`idempotency_key = hash(session_id + turn_id + tool_call_id)`）由下游去重，或者先调用只读查询接口核实刚才那笔状态到底落地没有，再决定补发还是继续。

---

### Q33：沙盒（Sandbox）在高并发 Agent 跑批/服务中为什么容易卡死或报 `Too many open files`？如何隔离、限流或去服务化？
- **核心结论（直接讲你亲历的 0819 深夜 128 并发雪崩与架构演进实战）**：
  1. **三大真实卡死/雪崩根因**：
     - **客户端/服务端文件句柄耗尽（`[Errno 24] Too many open files`）**：我们在 128 路并发刷全轨迹 DPO 时，每路 Agent 频繁将 `SKILL.md` 拉到客户端 `/tmp` 临时文件并保持多路 HTTP 长连接，直接打爆 Linux 进程 FD 上限引发连接重置；同时瞬时 250+ 并发 `create_session` 也会打爆远端沙盒守护进程的句柄池返回 HTTP 500；
     - **旋转门效应（Revolving Door）**：`ThreadPoolExecutor(max_workers=64)` 一次性 submit 全部几百题，前面一题因 500 秒崩，下一题立刻涌入新建会话，几分钟内把整批题全烧成 `other_error`；
     - **同步子进程阻塞事件循环与孤儿进程泄漏**：沙盒内用户脚本起后台子进程不关 stdout 管道导致 `communicate()` 死锁，或超时取消时只杀了父 shell 没杀整组子进程（需 `os.killpg` 杀进程组）。
  2. **三层根治架构**：
     - **准入波次限流与信号量背压**：引入 `SANDBOX_CREATE_WAVE_SIZE=16` 错峰建连，用有界队列按真实存活槽位逐题准入；
     - **进程内受控后端去服务化（轻量文件/脚本场景）**：砍掉不必要的宿主机↔沙盒 HTTP 序列化跳数，改为进程组级隔离直接执行，大幅消灭网络半开卡死；
     - **容器级 ACP 强隔离（重度复杂场景，如 Box-Agent）**：一任务一受控容器生命周期，支持 POSIX 全后代进程树自动清理（Descendant Cleanup）。

---

### Q34：工业界怎么做端到端的 Agent 评测？为什么不能只看最终成功率，必须拆成 Outcome、Trajectory、Latency、Cost 四维？
- **核心结论**：只看单一最终质量分或成功率会陷入两大盲区——① **分不清“做不出来（稳定性差）”和“做出来但不好（上限低）”**；② **掩盖“靠狂调 50 次工具、烧掉 10 倍 Token 暴力撞大运过关”的低效轨迹**。
- **四维全栈评测矩阵（融合小浣熊 + MobileGym++ + AgentCompass 实践）**：
  1. **完成与覆盖层（Completion & Coverage）**：强制度量并绑定报告 `生成成功数 / 评分覆盖数 n / 基础设施异常率 infra_failed`（基建挂了先剔除重跑，绝不算模型 0 分）；
  2. **终态产物可交付层（Outcome Quality）**：有状态环境用零假阳性业务 Store Verifier（MobileGym++ 拦截虚假完成）；开放生成产物用冻结实例级核查项 + 程序化硬约束 + 源材料忠实度 + 视觉硬伤计数（SlideGate）；
  3. **执行轨迹与协议效率层（Trajectory & Efficiency）**：检查结构化工具调用合规率（有无 DSML 伪调用、Schema 报错率）、步骤自我纠错率，以及确定性离线指标 **Outcome Efficiency ($\text{OE}$)** 与 **工具重复调用率 ($\text{RR}$)**；
  4. **工程延迟与经济成本层（Latency & Token Cost）**：从真实网关请求日志统计 P50/P95/P99 时延、单任务总输入输出 Token 及 Prefix Cache 命中率，画出 **成功率—成本—时延帕累托前沿**。

---

### Q35：LLM-as-a-Judge 当裁判有哪些系统性偏置（长度偏置、位置偏置、自偏好、静默降级）？你实操中是怎么校准尺子的？
- **核心结论**：大模型裁判是带噪声和偏置的测量仪器，**“未用人类金标和扰动实验校准过的 Judge，直接拿去指导训练一定会误导方向”**。
- **四大偏置与你的硬核校准实操**：
  1. **长度与排版偏置（Verbosity / Aesthetics Bias）**：整体打分模型天然偏爱字多、色彩花哨的产物，对页数违规、局部裁切与张冠李戴视而不见 → **解法**：取消笼统主观分，拆成冻结的二元/三元原子事实核查项（SlideGate 2,191 条），客观指标交由程序直接覆盖；
  2. **Pairwise 位置偏置与自偏好（Position & Self-Preference Bias）**：成对比较时偏爱排在 A 位的回答或同家族模型 → **解法**：正反交换顺序双评（Swap A/B），只有两次方向一致才采信，并用跨家族裁判交叉验证；
  3. **工程静默降级与大输入格式失控（你亲手抓出的致命真坑！）**：在 `0708` 排查中，旧网关偶发返回空串导致 `dynamic_checklist=[]` 静默退化，使老批 30%–49% 样本只考简单通用项而虚高，险些误判 DPO 退化；在 `q1495` 超大考勤表上裁判狂吐 2.5 万字演算不输出 JSON → **解法**：重试仍缺关键字段立即抛错阻断（宁可无分绝不交付假高分）+ 强制首字符 `{` 语法约束；
  4. **元验证三件套（校准尺子本身）**：重测自洽性（97.8%）、人工植入受控硬伤的检出召回率（100%）、以及与独立双盲人工标注/专家偏好的对齐度（一致率 80.7%/85.6%，Spearman 0.855）。

---

### Q36：【场景设计题】一个高频调用的导购/外贸 Agent 串行调 3 个外部工具，P95 延迟高达 15s，预算砍半时怎么把延迟和成本打下来？
- **核心结论**：P95 15s 的瓶颈等于 **「4 次串行大模型推理（3 次调工具 + 1 次总结）+ 3 次串行外部 I/O + 重复膨胀的历史前缀计算」**。优化按“砍轮次 → 改并行 → 压前缀 → 分大小模型 → 加缓存与流式”五步立竿见影：
  1. **串行改并行（Parallel / Batched Tool Calling）**：若 3 个工具无强前后依赖（如同时查商品库存、买家历史订单、海运报价表），引导或训练模型在**第 1 轮一次性发出 3 个并行 `tool_calls`**，Harness 用 `asyncio.gather` 并发执行，4 轮 LLM 调用瞬间砍成 2 轮，I/O 耗时从 $t_1+t_2+t_3$ 降为 $\max(t_1,t_2,t_3)$；若有固定先后依赖（先查买家 ID 再查订单），直接在后端封装成一个聚合复合工具，省去中间一次模型往返；
  2. **榨干 KV Prefix Cache + 工具精简**：固定 System Prompt 与热门工具定义前缀不动，动态变化的时间戳/会话状态后置；按当前意图动态裁剪候选工具与输出无用冗余字段，输入成本直降 50%+；
  3. **大小模型分级路由 + MTP 投机解码**：意图路由与参数提取轮切到 `Qwen3-30B-A3B`（FP8 + MTP）或 `8B` 蒸馏小模型（单轮 <400ms），只有复杂异议谈判才升级旗舰大模型；
  4. **P95 长尾止血与流式体验**：给每个外部工具设严格超时（如 2s）与热点数据本地 Redis 短缓存（汇率/热门 SKU），次要工具超时优雅降级不卡主链路；前台首轮边跑工具边流式输出过渡确认话术，把用户体感首响（TTFT）压进 1 秒内。
