# 架构与生命周期

Mac-CUA 每题克隆独立 macOS 环境，让 agent 自主组合 CLI、GUI、文件系统、API 和 MCP。应用包声明复用能力与生命周期，任务包声明业务初始化和评分；新增应用不修改核心编排。

## 模块边界

平台只编排任务、固定环境、尝试状态、停止门禁、评分、证据和清理。任务包保存目标、输入、初始化与评分；应用包复用能力、账号和云端状态约束；Agent 适配器是宿主侧调度已安装在固定镜像内的程序。可信内部 Python 包可通过 `mac_cua.agents` 扩展入口提供适配器；当前只有 Codex 生产实现。GUI 策略由各 Agent 适配器持有，不由平台核心按工具名分支。

Codex 每批固定 `repl`（默认）或 `direct` GUI 策略。`repl` 链路为 `Codex → cua_repl MCP → 持久 Node REPL → Python 适配器 → cua-driver MCP`；`direct` 沿用直连 `cua-driver` MCP。同批只暴露一种 GUI 接口，切换需要新批次。REPL 的 adapter、JS 和 skill 随任务部署，Node 22.22.1 与 Codex/cua-driver 程序预装于固定镜像。接口和能力限制见 [Codex GUI REPL](../reference/cua-adapter.md)。

```mermaid
flowchart LR
    P[团队公共镜像] --> W[个人准备 VM]
    W -->|登录与设置后保存| G[固定环境版本]
    G -->|每题新克隆| V[临时任务 VM]
    V --> A[Agent 执行]
    A --> S[确认 Agent 与控制组件停止，独立请求停录]
    S --> R[评分后回收轨迹和录像]
    R --> D[删除 VM 与封存]
```

| 模块 | 职责 |
|---|---|
| `foundation/contracts.py` | 公开 JSON Schema、严格声明与参数校验 |
| `tasks/packages.py`、`tasks/applications.py` | TaskSpec、ApplicationSpec、依赖解析、字节快照与内容身份 |
| `foundation/environment.py`、`evaluation/environments.py` | 每题环境解析、固定镜像与安装准入 |
| `foundation/interfaces.py`、`evaluation/adapters.py` | provider、agent、observer 接口与默认组合入口；Agent 发现仅选可信已安装适配包 |
| `foundation/resources.py` | 创建意图、对象身份、资源保留与跨批次账号租约 |
| `foundation/preparation.py`、`foundation/assessment.py` | 初始化预算和失败分类；统一推导恢复资格、完成情况及材料质量 |
| `tasks/execution.py` | 客体阶段、事件确认、宿主状态和评分 |
| `infrastructure/orchard.py` | Orchard 请求、重试、UID 核对、客体通道和控制器删除回执 |
| `runtime`、`artifacts` | Codex 适配与 GUI 策略、凭据格式、原始轨迹、通用证据索引、录制与成果采集 |
| `images`、`images/profiles` | 镜像事务、独立库存扫描、基础和 MacArena 检查策略 |
| `evaluation/runner.py`、`scheduling.py`、`attempt.py` | 批次调度、持久派发队列与单次尝试执行 |
| `evaluation/results.py`、`campaign.py`、`viewer` | 分层结果、每题实际环境和保留资源展示 |

`suite.json` 只维护题目列表和题集内应用目录；task/app 的应用引用只包含 ID、版本和参数。suite 映射优先于配置的外部应用目录回退，冻结后由 `application-lock.json` 单独固定。完整公开契约见[任务清单关系](../evaluation/task-packages.md)。

依赖测试检查函数内导入和模块循环。应用业务代码仅通过客体阶段执行，不由宿主动态导入。`ExecutionServices` 可以替换 provider、agent、observer 和阶段执行器；编排不解释 Codex OAuth、原生轨迹或 supervisor 命令。通用绑定准备与 Codex 专用配置/OAuth 投影分开。

## 运行时就绪由使用方验证

`EnvironmentProvider.wait_ready()` 只确认 VM 身份和 SSH 通道可用。SSH 成功、程序
`--version` 成功和 REPL 自检成功，都不能代替桌面服务就绪。Codex 的
`AgentBackend.prepare(vm, *, budget=None)` 在业务开始前验证其 Cua 运行时；其他
Agent 适配器接受同一初始化预算，并自行检查所需运行时。准备期间的版本和自检
RPC 可安全重试，整个 `prepare` 不再由编排层重新执行。

`infrastructure.cua` 提供共享的 Cua 身份校验和默认端点等待。就绪要求目标用户的
GUI 会话、固定版本 app daemon 的元数据／进程／套接字身份，以及非交互的辅助
功能和屏幕录制权限检查同时成立。权限检查前后再次观察身份，拒绝把其他进程或
替换后的端点当作已验证服务。每次调用都重新观察，已就绪时立即返回；缺席或已知
连接暂态才在剩余预算内轮询。身份错误、协议错误、明确权限缺失和未知权限分别
失败，不触发授权、启动服务或重放 GUI 动作。

任务初始化的 VM 通道、网络和 Agent 运行时共用 `PreparationBudget` 的绝对截止
时间；内层 RPC、轮询和安全重试不重置预算。镜像冷克隆的启动与首个 GUI 检查也
传递同一启动预算。独立应用／采集验收有各自的启动边界；业务 GUI 检查耗时不计为
另一轮 VM 初始化。失败分类保留就绪检查的最后观察和权限结果，沿现有诊断回执存储。
私有录像端点的启动请求返回后，握手阶段另有 15 秒上限；每次观察取握手剩余时间、
总预算剩余时间与 RPC 上限中的最小值。发起观察前和接收结果后均检查截止时间，
逾期成功也不能通过就绪门禁。

默认控制端点与私有录像端点各自持有生命周期。镜像 GUI、文件访问、LibreOffice
检查和采集隔离验收在开始时验证默认端点；私有录像端点只在首次启动时等待其默认
端点前置条件。评分前停止控制端点后，普通成果回收、录像收尾、恢复和停止确认
继续使用 SSH、既有私有端点或单次事实观察，不等待或重新拉起默认 daemon。

## 统一资源池

单机是一个 worker 的 Orchard 池。任务执行不读取 host 配置或启动服务；deployment 模块负责宿主启动、注册与维护，运行客户端只接收连接及已解析请求。宿主配置独立声明总容量；每题从任务完整资源或环境默认资源解析并冻结 CPU、内存，与镜像、标签、网络和绑定一起提交。Orchard 选择 worker 并计量容量。`jobs` 只限制客户端在途任务数。

环境选择依次使用显式环境、满足要求的默认环境、唯一匹配候选；候选不唯一或没有匹配时，在派发前报错。安装回执与 worker 标签必须对应固定镜像，未知应用库存不被当作兼容证据。续跑直接使用冻结环境，不重新选择当前默认版本。

## 尝试顺序

冻结任务及应用字节 → 获取账号租约 → Orchard 创建克隆 → 运行资源 → 应用 ready/prepare → 任务 setup → Agent 与 observer → 确认 Agent／控制组件停止、最终快照及录像停止 → 应用 settle → 评分与证据回收 → 应用 cleanup 与资源登记 → Orchard 删除 → 释放租约 → 封存。

`attempt_id` 在任何外部动作前持久化。资源名称带任务 ID、UTC 时间和随机后缀。客体使用 `resource_events.intent/created`，每条事件都等待宿主原子写入后的确认。创建结果未知、诊断对象和成果分别记录；本轮外部对象全部保留，VM 删除不代表云端对象已删除。

账号以绑定的非敏感 `principal` 独占，同一池的所有批次必须共用协调状态目录。租约不按时间自动失效，Orchard 对象删除后释放；未完成操作由原尝试自动恢复，`cleanup-run` 也复用同一机制。它不是跨控制器分布式锁，也不是账号权限隔离。应用包 v3 可进一步声明本地状态、每次尝试独立云端作用域或专用身份；ready/prepare 回执必须证明声明的隔离条件。旧 v2 包的云端隔离状态标记为未验证。资源账本只确认通过标准阶段事件登记的对象，不能保证发现 Agent 以 GUI、CLI 或 MCP 创建的所有云对象。

任何恢复都不重放可能已经启动的 Agent。框架创建／就绪／网络／运行时检查的暂态失败，在业务开始前、旧资源清理与租约释放后可有界自动创建新尝试；进入业务准备后，新尝试需要显式 retry。settle 只能观察或等待已发起的操作，不补做任务。schema 9 在 Agent 和控制会话停止后运行 settle 与评分；必需成果和原生轨迹优先回收，录像及额外截图失败独立记录告警。评分异常为未评分，不能折算成零分。

创建超时先按唯一 VM 名查找并核对原请求；删除核对 UID，删除后查询控制器对象消失。暂态故障有界重试，未知结果保留原身份意图并自动核对，不阻止无关任务派发。`restart_policy=Never`。回执明确 `controller_object_absent`、`host_verified=false`；不声称独立核验宿主实体删除。

## 版本、镜像与历史

公开任务清单为 `task-package-v4`，新增应用包为 `app-package-v3`（v2 继续按未验证云端隔离读取），执行协议为 `task-package-v21`，新结果为 schema 9。应用和依赖字节参与任务哈希，路径仅用于定位，实际执行使用冻结副本。任意业务参数必须通过应用的闭合参数 schema；说明字段放在 metadata。

schema 3/4/5/6/7/8 只读查看和验证，支持独立清理回执及有关联的新批次，不支持按新协议直接续跑。MacArena 原始任务、oracle、评分语义和 provenance 保留；生成适配器迁移新任务契约。

通用镜像事务保留准备、关机、保存、哈希、注册、冷克隆检查和恢复。交付包格式 2 通过独立元数据策略支持 base/macarena，格式 1 保持读取兼容；worker 安装登记完整校验镜像字节。`image.profile=base` 检查运行组件、GUI、录制与采集；显式 `macarena` profile 承载原环境和历史应用要求。仓库只分发五题样例，因此需要完整 49 题的应用门禁会拒绝当前题集。应用兼容性、授权与业务就绪由应用探针单独报告。所有私有存储通过 `Config.paths`，不提交镜像、账号或真实运行材料。

## 执行端口与状态所有权

批次清单、尝试事实和调度意图分别维护，结果判定器从事实推导状态，不保存另一份评分或材料结果：

| 记录或组件 | 权威职责 |
|---|---|
| `run.json` | 冻结任务、输入、环境、模型及执行策略 |
| 每次尝试的 `result.json` | 实际阶段、启动边界、失败、停止、材料和清理事实 |
| `run-state.json` | 派发预留、待执行与初始化恢复队列、退避时间 |
| `evaluation.results.AttemptView` | 分开提供原始尝试、当前资源交接及档案完整性，统一读取恢复记录 |
| `foundation.assessment` | 从统一视图推导完成情况、初始化重试资格和必需材料质量 |

父调度器持有操作系统自动释放的批次写入互斥，先写入预留，再创建尝试记录，最后记录派发并启动子进程。每次尝试持有独占写入锁；父进程退出但子进程仍存活时，新调用拒绝接管。预留阶段中断恢复同一尝试身份；可能派发后缺失尝试记录则停止核对，不能从旧预留推断没有启动 Agent。

恢复按原尝试处理资源，再判断该题的初始化补跑资格。单个未完成恢复不阻止无关题目预留或派发；同一题的新尝试仍要求原资源交接完成，实际共享 principal 继续互斥。尝试封存与资源交接分别判断。独立清理持有批次与尝试独占锁，父进程退出后仍不能接管活跃子进程。串行和并行共用持久队列，原资源恢复完成后，普通待执行任务优先于退避到期的补跑任务。启动和恢复约束见[尝试协议](../reference/protocol.md#初始化与启动边界)，操作入口见[运行说明](../evaluation/running.md)。

`ExecutionServices` 的工厂实际引用公共 Protocol，组合时固定 provider/agent/control/observer/executor ID 和契约版本。正常注册与显式注入共用 `AgentRegistration`，由描述对象提供工厂、凭据读取、身份、客体要求、证据契约和离线审计；`AgentFactory` 仍是普通可调用对象，不要求额外属性。新执行只接受组合契约 5，缺失声明或旧组合在创建批次前明确拒绝；旧记录清理仅核对 provider 身份。当前组合契约为 5：`AgentBackend.confirm_agent_stop` 仅确认 Agent；`ControlFactory.for_attempt/recover` 返回具有 `prepare/confirm_stop` 的控制会话。适配器须显式提供动作控制实现，不再通过检测旧 `confirm_stop` 方法选择停止合同。一个批次只使用一个 Agent；Agent 适配器版本、客体载荷摘要、GUI 策略和模型配置属于执行身份。正常执行和恢复使用冻结组合；只清理 VM 不依赖原 Agent 包仍在宿主安装。恢复不匹配时拒绝，历史 schema 3/4/5/6/7/8 走只读或明确的清理兼容入口。

环境生命周期与 `GuestTransport` 分离。阶段执行器和通用成果采集只接收命令、RPC、上传和下载能力。Codex 适配器持有凭据读取、原生配置、停止解释、usage 推导和证据目录收尾；`StopReceipt` 确认 Agent 与控制组件停止，observer 独立给出 `recording_stop` 回执。Agent 与控制会话停止且应用 settle 成立才允许评分；Observer 的录像停止证明独立报告。辅助采集失败记录告警。

`ConfigSnapshot`、`ResolvedEnvironment`、`ResolvedRuntime` 和 `RunContext` 使用不可变递归存储，公开字典均为副本，支持多进程 spawn。维护入口解析默认客体条件，执行入口不从当前 guest.json 补字段。运行绑定冻结引用，秘密仍在适配器边界即时读取。共享 runtime 合并、阶段结果、评分和清理完成各有一个权威规则。

控制停止策略集中在 `artifacts.control_stop.ControllerStop`；`CuaControlSession` 建立任务控制端，镜像检查复用同一策略。进入停止阶段时持久保存目标进程及端点身份；准备阶段的观察只作参考，重试不能把新观察到的替换进程变成授权目标。套接字消失后仍核对同一目标进程，失败后的重新观察保留此前回执。

资源恢复只核对原资源、删除控制器对象并释放实际租约，不推断或覆盖 Agent 状态、评分与停止边界。原始记录定稿后哈希固定，封存只新增清单。恢复操作在临时目录内保存回执与清单，经目录原子重命名后独立提交；没有不断增长的权威总清单。读取时忽略未提交临时目录，损坏或身份不符的已提交证明不被采信，原资源仍可按有效归属再次核对。材料完整性校验独立于资源归属校验，录像损坏不会阻止清理。

当前执行协议为 `task-package-v21`；历史执行条件不自动迁移。schema 9 的证据索引声明带 kind/path/size/sha256 的引用、Agent／会话身份、工具与 GUI 事件及完整性状态；原生 Codex trace 原样保留，官方 reducer 只作为按需离线诊断。通用校验不依赖 Codex 专属目录或 state.json；`codex-native-v2` 只核验原生证据覆盖与引用，已记录的失败、取消和部分响应保留为执行事实；训练格式转换是另行版本化的离线步骤，不能反向改变材料或补跑结论。历史证据解释集中在 legacy_records，不把旧尝试重新封存。镜像准入兼容版本为 `pool-basic-14`，仍需在实际固定镜像上重新检查；实机和任务验收以对应批次的原始结果及独立校验记录为准。


任务阶段采用 task-package-v4 类接口：setup.entry / evaluation.entry 指向共享 Python
文件，args 对象传给 run(context, **args)。未声明 entry 时查找相邻 initial_setup.py /
evaluation.py，缺失则调用 BaseSetup / BaseEvaluation。默认初始化无操作，默认评分
为 not_evaluated、score=null；它不计入有效评分，也不因缺少评分而触发重跑。
入口分别导出 Setup(BaseSetup) / Evaluation(BaseEvaluation)，基类由框架部署的
task_api 提供。框架在 VM 子进程中导入类并负责参数与结果文件、超时和日志；
宿主发现仅检查清单、路径和语法。旧脚本接口须迁移，新执行协议禁止不兼容续跑；
历史结果保持只读兼容。完整示例与迁移见[任务包教程](../evaluation/file-tasks.md)。

## 统一 REPL 下的浏览器路径

[编号 DOM 与差量观察](browser-harness/dom-observation-design.md)由 browser-harness 采集 DOM／AX 并持有元素引用，BrowserBackend 按 target 管理模型输出 diff。仅编号 click/fill 扩展动作入口；iframe 只显示边界，主文档及 open Shadow DOM 内部编号。客体部署见[浏览器示例](../examples/browser-task-suite/README.md)。

`Codex → cua_repl → cua_browser.BrowserBackend → stdio MCP → browser-harness managed → CDP → 任务 Chrome`。同一个 Python McpClient 也用于原生 cua-driver，Node 只提供持久变量和薄 JS API，不引入第二套调度器。浏览器连接、目标身份和观察参照由 BrowserBackend 持有；supervisor 负责同组控制进程清理及评分前停止核验。Chrome 属于业务应用，控制停止时保留页面。应用包负责 Chrome/profile/下载目录，通用 runner 不增加 Chrome 分支。

成果捕获通过声明的严格/尽力模式隔离失败，先提交严格成果与回执，再处理补充内容和原生材料；清理仍有界，不隐式恢复业务。统一 assessment 解释已有评分、捕获与证据政策，原因跟随回执，不另建成功判定。模型提示不承担墙钟调度职责，后台 supervisor 继续控制资源上限。

## 材料政策的单一来源

`AgentRegistration.evidence_contract(config)` 声明 `policy` 与非空、唯一的 `required_kinds`，在批次 `identity.execution.agent_backend.evidence_contract` 冻结；`audit_evidence(output, record)` 对已保存材料进行只读复核。采集结果必须提供 `required_refs`，这些路径引用同一结果的 evidence，不重复保存哈希。Codex 的事件与会话用于独立覆盖及 GUI 行为核对；其他 Agent 自行声明原生证据，平台不按 Agent 名称分支。

尝试的 `material_requirements` 合并冻结契约和任务成果声明。统一材料判定解释实际捕获状态及缺口；报告读取已保存事实，verify 核验全部封存引用，补跑复核当前必需引用并单独保存政策与来源哈希。历史格式在读取边界适配，历史验收与当前行动可以采用不同政策，均不覆盖原始字节。

Orchard 的 `resource_admission` 在创建互斥内提供当前资源清单和阻塞原因。维护、停止和切换消费同一准入规则；已观察缺席的原请求继续核对但不因记录存在永久阻塞。接口不提供迟到请求取消证明，因此始终保留原名称、请求及已知 UID，不使用时间租约推断删除完成。缺席的未知请求不阻断业务或维护，极端迟到风险由后续尽力核对及人工运维承担。

遗留请求核对在创建互斥内消费顶层逻辑操作持有的辅助上下文：共享 5 秒截止时间与 32 条探测额度，跨 provider 及嵌套检查不重新领取，辅助锁非阻塞，按最近处理时间公平推进并退避。预算耗尽及预期基础设施失败返回结构化摘要，不扩散为当前创建失败；当前任务本身的截止时间、取消和程序错误仍有效。已有缺席记录只有在发现对象并需要删除后才进入删除状态，失败查询不能撤销此前的政策内交接。一轮复用原身份快照，只把可选调度字段在收尾时与最新账本合并一次，不形成恢复事件流；无变化的缺席事实不重复写入，新 UID、删除意图和首次交接仍及时持久化。摘要保留准确计数与每类最多 10 条明细，耗尽额度后不逐条遍历填充剩余明细。

`infrastructure/orchard_state.py` 定义操作辅助额度，并统一解释请求匹配、探测调度和只读疑似孤儿视图；提示不承担删除授权。`status()` 只读 controller 与本地归属，报告检查范围、未知请求、疑似迟到对象和冲突，不调用带清理副作用的准入入口。创建结果未知通过既有初始化重试条件判定：未开始业务、未启动 Agent 且清理和账号交接完成后，同一任务建立下一次尝试，不因原请求留存卡在原 VM 上。


### 账号等待不产生恢复事件流

`AccountLeases` 以本地租约判断账号是否可用；同一持有者的多个 principal 合并核对，跨进程持有者锁避免重复远程工作。私有 `pool/account-recovery/` 内的可覆盖提示采用 1、2、4、8、16、30 秒封顶退避，时钟变化或提示损坏不构成释放证明。提示仅调度探测，不是租约 TTL。

每次自动探测最多使用等待期限内的 5 秒，provider 的 `recover(..., budget=...)` 使用剩余 RPC 预算并非阻塞取得修改锁。它验证原批次、尝试 ID、结果归属与实时 UID，不扫描历史恢复目录；暂态失败返回结构化结果，不追加清理收据。成功交接独立原子发布；显式清理保留失败诊断，已知交接不重复发布。报告、完整校验、补跑和批量清理在各自操作内复用一次已核验的恢复快照，不设置跨操作的权威缓存。等待结束或身份阻塞由等待者记录一次错误，原账号仍保持占用。
