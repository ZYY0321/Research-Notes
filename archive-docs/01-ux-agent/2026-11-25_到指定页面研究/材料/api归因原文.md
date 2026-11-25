# nav-high-167-1125b 失败分析（Mate X5 / qwen3.8-max / FINAL_UX=0）

> **证据缺口**：附录里所有工具调用都是 `"ok": null, "err": ""`。runtime 没有记录动作是否成功，所以"点击未生效"和"观测滞后"只能靠终态图推断。这一条本身也列为 P0 整改项（见 §3-A1）。
>
> **坐标口径**：tap 坐标是 0–1000 归一化坐标，按 1080×2504 换算后与图中控件位置吻合。例如 (115,690) 对应「驾车」图标，(761,240) 对应「最高」价格框。因此**排除坐标映射错误**。

---

## 1. 失败卡

### ① COM-amap-tablet-g01-H
| 项 | 内容 |
|---|---|
| 表面现象 | 480s 超时，9 步，未 `report_result`。终态仍在高德首页，底部 tab 高亮仍是「首页」 |
| 根因标签 | 主：`tap_no_effect_loop`。次：`blind_tap`、`no_budget_report`、`task_goal_overreach` |
| 证据 | 「驾车」点了 3 次（step 1/3/8），「共享实时位置」X 在同一坐标 (919,657) 连点 3 次（step 5–7），每次都没有可见状态变化，也没有换策略。step 2 的 reason 是"关闭**可能存在的**分享提示浮层"，属于盲点。连「探索」tab 也没切过去 |
| 可工程修 | **是**。需要动作后校验、同一动作不得重复超过 2 次、预算到点强制 report |

### ② COM-dingding-phone-g01-H
| 项 | 内容 |
|---|---|
| 表面现象 | 5 步后主动报失败，终态为钉钉登录门页 |
| 根因标签 | 主：`env_precondition_missing`（未登录）。次：`task_card_no_precondition` |
| 证据 | 终态图只有「华为账号一键登录 / 手机号码登录 / 注册 / 企业账号 / 更多选项」，没有游客入口。agent 已经查过「更多选项」，并按约束拒绝登录 |
| 可工程修 | **是，但修的是环境而不是 agent**。agent 行为正确：5 步内确认不可达并如实上报，是理想失败方式 |

### ③ DEEP-ctrip-01-H
| 项 | 内容 |
|---|---|
| 表面现象 | 480s 超时，20 步，后 7 步全在按 DEL，600 没设上 |
| 根因标签 | 主：`input_strategy_fail`。次：`deep_chain_too_long`、`obs_degraded`（dumpLayout 多次失败）、`app_screenshot_overlay`（step 1） |
| 证据 | type_text "600" 之后，框内仍显示「¥1300以上」，说明该框不是普通可编辑文本框，或者输入没有落进去。agent 没读框值，直接盲按 7 次 DEL。页面上其实有预设档（¥400-¥500 等）、双端滑杆和键盘「完成」，都没用 |
| 可工程修 | **是**。需要输入后读回校验、优先用预设档或滑杆、禁止连续盲删 |

### ④ DEEP-ctrip-02-H
| 项 | 内容 |
|---|---|
| 表面现象 | 进入火车票页后观测中断，盲试约 10 步后报环境失败 |
| 根因标签 | 主：`obs_pipeline_down`。次：`app_screenshot_overlay`、`no_early_stop` |
| 证据 | 截图目录只剩 step_1..4 和 step_7，日志为 `Input file is missing` / `unsupported image format`，坐标空间丢失。step 5–14 全是 swipe/ENTER/状态栏 tap/HOME 一类的"探活"动作 |
| 可工程修 | **是**（infra）。不是 agent 的锅，但盲试浪费了预算，而且有误操作风险 |

### ⑤ DEEP-ctrip-03-H
| 项 | 内容 |
|---|---|
| 表面现象 | 开跑即无观测，盲试 9 步后报失败 |
| 根因标签 | 主：`obs_pipeline_down`（上一任务的故障延续）。次：`no_preflight_healthcheck`、`no_early_stop` |
| 证据 | 只有 step_1.png，报 `No coordinate space is available yet`。故障时序为 01 dumpLayout 失败 → 02 缺图 → 03 全缺，设备侧在逐步劣化 |
| 可工程修 | **是**（infra）。应该由任务间健康检查拦住，这条不该被计入 agent 成绩 |

---

## 2. 原因词表

| 标签 | 定义 | 次数 | 优先级 |
|---|---|---|---|
| `obs_pipeline_down` / `obs_degraded` | 截图或 layout 文件缺失、损坏，坐标空间丢失 | 3（02、03 完全中断；01 部分） | **P0** |
| `env_precondition_missing` | 任务需要的 app 状态（如已登录）在环境里不存在 | 1（钉钉） | **P0**（直接影响短路径分数） |
| `tap_no_effect_loop` | 点击后界面无变化，仍以相同坐标或相同目标重复 ≥3 次 | 1（高德，2 组重复） | **P0** |
| `no_early_stop` | 观测失败后继续盲操作，不立即中止 | 2（02、03） | **P0** |
| `no_budget_report` | 超时前没有输出 report，丢失进度证据 | 2（高德、01） | P1 |
| `app_screenshot_overlay` | 我方截图触发 app 的「截图反馈」浮层，挡住或干扰操作 | 2（01、02） | P1 |
| `blind_tap` | 点击当前观测中未确认存在的元素 | 1（高德 step 2） | P1 |
| `input_strategy_fail` | 输入不读回、不清空，用 DEL 盲删；有预设控件却不用 | 1（01） | P1 |
| `task_card_no_precondition` | 任务卡没有声明前置状态，导致"约束"与"可达"冲突 | 1（钉钉） | P1 |
| `task_goal_overreach` | "到页"类任务卡夹带高难操作（移图到太平洋） | 1（高德） | P1 |
| `deep_chain_too_long` | 多重筛选、排序、详情的长链，480s 内放不下 | 3（deep 全部） | P2（移出本周集） |
| `no_preflight_healthcheck` | 任务间没有设备与观测自检 | 1（03，实际影响 02、03） | **P0**（与 obs 合并修） |

---

## 3. 统一整改

### A. 改 runtime

| # | 改什么 | 怎么做 | 验收 |
|---|---|---|---|
| A1 | **工具结果落盘** | 每次调用记录 `ok`、`err`、耗时、前后截图 hash、前后 layout 摘要 | 新批次 JSON 中 `ok` 不再为 null，每步都有 `pre_hash`/`post_hash` |
| A2 | **动作后校验与防重复** | tap 后比对前后截图或 layout。无变化时打 `no_effect` 标记回传给 agent。同一目标（坐标距离 <30 或 reason 同一控件）连续 2 次 `no_effect` 后，第 3 次被 runtime 拒绝，并提示改用其他方式：layout 查控件 bounds 后点中心、点文字区、等待 1.5s 再观测、先关浮层 | 重跑高德时不再出现 3 次同坐标点击；日志能看到 `no_effect` 拦截 |
| A3 | **禁止盲点** | tap 的目标必须能在当前 layout 或截图中定位到。reason 里出现"可能存在""尝试/测试是否生效"且无对应元素时拒绝执行 | 抽检 18 条，`blind_tap` 为 0 |
| A4 | **观测失败重试 + 早停** | 截图后校验 PNG 头和非零大小，失败时间隔 0.5/1/2s 重试 3 次，再退到 layout-only。**连续 2 步无有效观测**就由 runtime 中止，结果标记 `INFRA_FAIL`：不计入 agent 失败，自动排队重跑。中止期间禁止 agent 发动作 | 构造"删截图文件"故障注入，2 步内中止、标 INFRA，无盲操作 |
| A5 | **任务间健康检查（preflight）** | 每个任务开跑前：hdc 连通 → 试截一张并校验 → 试 dump layout → 清理设备临时截图目录 → 必要时重启 uitest 服务。任一失败就重置设备，仍失败则阻断后续任务 | 03 这类"开跑即瞎"的情况在 preflight 阶段被拦截，日志可见 |
| A6 | **已知浮层规则化 dismiss** | 建立浮层登记表：携程「截图反馈」、高德「共享实时位置」/分享提示。每次观测后先用 layout 精确匹配，命中则由 runtime 自动关闭，不占 agent 步数；关闭后校验浮层已消失 | 携程、高德重跑时，agent 轨迹里不再出现关浮层步骤 |
| A7 | **预算感知 + 强制收尾** | 向 agent 注入剩余时间和步数。时间用到 80%（384s）时，runtime 要求 agent 立即 `report_result`（带进度）；超时兜底时由 runtime 自动生成 report | 不再出现"timeout 且无 report" |
| A8 | **输入工具规范** | type_text 前读取字段值，有值则先清空（全选删除或清除按钮），输入后读回校验；读回不符就提示"该字段可能非文本框，改用预设项或滑杆"。连续 DEL 超过 3 次时拦截 | 01 重跑不再出现 DEL 串；价格条件通过预设档或滑杆设上 |

另