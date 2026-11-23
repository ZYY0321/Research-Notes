# MobileGym GUI + Tools 项目交接

## 1. 当前做到哪里

本项目在 MobileGym mock 环境上增加了 GUI + App Tools 混合交互能力，目标是让 Agent
既能使用通用 GUI，也能按当前前台 App 调用稀疏的业务原子工具。

当前可交付状态：

- 环境侧共有 **19 个 App、203 个 App Tools**；
- Python 侧已有独立的 Hybrid Agent Runtime；
- Runtime 每轮只暴露当前前台 App 的工具，Launcher 只暴露基础 GUI 动作；
- 支持 `hybrid` 和 `gui_only` 两种可控实验设置；
- 当前固定评测集为 **Hybrid Tools V6，共 75 条任务**；
- V6 使用统一 setup、环境状态和 verifier，可公平比较 Hybrid 与 GUI-only；
- 已完成 7 个模型的双设置基线，最终结果见
  [MOBILEGYM_HYBRID_GUIDELINE.md](MOBILEGYM_HYBRID_GUIDELINE.md#76-v6-最终评测结果)。

## 2. 系统结构

```text
模型
  -> Hybrid Agent Runtime（Python）
     -> mobile_use：MobileGymEnv.step() 执行 GUI 动作
     -> App Tool：浏览器 window.__MOBILE_GYM_TOOLS__.callTool(...)
  -> MobileGym App、Store 和结构化状态
  -> Task Verifier 统一检查最终状态
```

四个主要代码入口：

| 模块 | 路径 | 职责 |
| --- | --- | --- |
| 环境侧 App Tools | `trial_apps/mobilegym/app_tools/` | TypeScript 工具定义、注册、执行和浏览器 API |
| Agent Runtime | `trial_apps/mobilegym/bench_env/hybrid_agent/` | Prompt、工具发现、XML/Kimi 协议、动作执行和轨迹记录 |
| Benchmark Runner | `trial_apps/mobilegym/bench_env/hybrid_benchmark/` | Task setup、并行运行、verifier、结果汇总 |
| V6 Suite | `trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/` | 75 条任务及 V6 局部契约修订 |

App Tool 的 schema 和业务实现以 TypeScript 为事实来源。Python Runtime 负责发现和
调用，不在 Agent 侧重复实现 App 业务逻辑。

## 3. 重要文档

建议按以下顺序阅读：

1. [MOBILEGYM_CHANGE_AUDIT.md](MOBILEGYM_CHANGE_AUDIT.md)  
   从最初 clone 基线到当前工作区的完整变更范围、共享环境改动、验证状态和交接风险。
2. [MOBILEGYM_HYBRID_DESIGN.md](MOBILEGYM_HYBRID_DESIGN.md)  
   项目动机、整体架构，以及 V1-V4 的探索过程。
3. [app_tools/TOOLS_DESIGN.md](trial_apps/mobilegym/app_tools/TOOLS_DESIGN.md)  
   如何选择、实现和验证一个 App 的 Tools，是新增工具时的主要规范。
4. [app_tools/TOOL_CATALOG.md](trial_apps/mobilegym/app_tools/TOOL_CATALOG.md)  
   当前 203 个工具的完整目录，以及各 App 刻意不开放的能力。
5. [app_tools/VALIDATION.md](trial_apps/mobilegym/app_tools/VALIDATION.md)  
   工具的状态副作用、GUI 可继续操作性和真实浏览器验证结果。
6. [hybrid_agent/README.md](trial_apps/mobilegym/bench_env/hybrid_agent/README.md)  
   Agent Runtime 的输入输出、动态工具暴露、轨迹产物和模型协议。
7. [hybrid_benchmark/README.md](trial_apps/mobilegym/bench_env/hybrid_benchmark/README.md)  
   Benchmark Runner、Hybrid/GUI-only 设置和输出文件说明。
8. [MOBILEGYM_HYBRID_GUIDELINE.md](MOBILEGYM_HYBRID_GUIDELINE.md)  
   instruction、setup、environment、tool、verifier 五层契约的构建和审查指南。
9. [V6 README](trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/README.md) 和
   [V6 TASK_CATALOG](trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/TASK_CATALOG.md)  
   当前正式 suite 的运行方式和全部任务。

V1-V6 的典型问题轨迹已整理到：

```text
trial_apps/mobilegym/benchmark_evidence/hybrid_guideline_cases/
```

## 4. 快速运行

### 4.1 启动模拟器

```bash
cd /Users/chengkanzhi/Desktop/mobilegym-mock/trial_apps/mobilegym
npm run preview -- --host 127.0.0.1 --port 4181
```

Python 环境使用已有的 `mobilegym-bench`：

```bash
conda activate mobilegym-bench
cd /Users/chengkanzhi/Desktop/mobilegym-mock/trial_apps/mobilegym
```

模型接口配置可参考 `tools/test_api.py`，但不要把 API Key 写入文档或提交到仓库。

### 4.2 列出 V6 任务

```bash
python -m bench_env.hybrid_benchmark \
  --suite hybrid_tools_v6 --list
```

### 4.3 执行 Hybrid

```bash
python -m bench_env.hybrid_benchmark \
  --suite hybrid_tools_v6 \
  --interaction-mode hybrid \
  --env-url http://127.0.0.1:4181 \
  --model-base-url "$MODEL_BASE_URL" \
  --model-api-key "$MODEL_API_KEY" \
  --model-name "$MODEL_NAME" \
  --parallel 8 --headless \
  --max-tokens 8192 \
  --output-dir "runs/$RUN_NAME"
```

GUI-only 对照只修改：

```bash
--interaction-mode gui_only
```

具体的 Gemini、Kimi 和其他协议参数，以
[V6 README](trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/README.md) 和
[Hybrid Benchmark README](trial_apps/mobilegym/bench_env/hybrid_benchmark/README.md)
为准。

## 5. 如何查看结果

每次正式运行会产生：

```text
<run>/meta.json
<run>/tasks.json
<run>/results.jsonl
<run>/summary.json
<run>/episodes/<task-id>/index.html
<run>/episodes/<task-id>/trace.json
<run>/episodes/<task-id>/step_*_{before,after}.jpg
```

优先查看：

- `summary.json`：SR、停止原因、工具调用次数和覆盖；
- `results.jsonl`：每条任务的 verifier diagnostics；
- `episodes/.../index.html`：逐步截图、模型动作、App Tool 参数和返回结果。

当前实际保留的实验目录见
[MOBILEGYM_HYBRID_RUNS.md](MOBILEGYM_HYBRID_RUNS.md)。

正式结论不能只看 SR。强模型失败任务应逐条检查是 Agent failure，还是
instruction/setup/environment/tool/verifier 契约缺陷。

## 6. 新增 App Tools

新增工具时不要从 task 答案反推接口，也不要把所有业务能力都开放。标准流程是：

1. 阅读 App 的页面、store、业务 action 和现有 benchmark 任务；
2. 选择稀疏的 query、navigation、draft 和有限 write 工具；
3. 在 `app_tools/apps/<app>/definitions.ts` 定义 schema；
4. 在 `index.ts` 复用 GUI 已使用的业务 action 或正常页面 route；
5. 增加 schema、状态 diff、GUI/Tool 等价和真实浏览器测试；
6. 更新 `TOOL_CATALOG.md` 与 `VALIDATION.md`。

完整要求见
[TOOLS_DESIGN.md](trial_apps/mobilegym/app_tools/TOOLS_DESIGN.md)。关键红线：

- 不使用 `__SIM__.setState()` 执行业务操作；
- 不读取 verifier 或 task ground truth；
- query 工具不能产生业务副作用；
- navigation/draft 声明的 `uiEffect` 必须真实发生；
- 敏感最终动作应优先留给 GUI。

## 7. 新增 Benchmark 任务

任务不是只有 instruction 和 verifier，而是以下五层共同组成的契约：

```text
instruction -> setup -> environment/tool observations -> agent actions -> verifier
```

新增或扩展 suite 时，直接按照
[MOBILEGYM_HYBRID_GUIDELINE.md](MOBILEGYM_HYBRID_GUIDELINE.md)
第 6 章的十步流程和第 10 章发布门禁执行。特别注意：

- 指令描述高层目标，不提供 step-by-step 解法；
- setup 固定模拟时间并生成唯一、可观察的 ground truth；
- verifier 判断最终业务状态，不绑定 Agent 使用 GUI 还是 Tools；
- 自由文本接受合理等价表达，但关键实体、金额、集合和收件人仍须严格；
- 每条正式对比任务必须存在可在预算内完成的纯 GUI 路径；
- Hybrid/GUI-only 配对运行后，要重点审查 `Hybrid PASS / GUI-only FAIL`。

当前 V6 的修订历史和失败审查位于：

```text
trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/V6_REPAIRS.md
trial_apps/mobilegym/bench_env/task/hybrid_tools_v6/*AUDIT*.md
```

## 8. 推荐演示轨迹

以下成功轨迹适合展示 GUI 和 Tools 都参与关键业务流程：

| Case | 关键混合能力 |
| --- | --- |
| V6 Case13 | Tool 定位 B 站榜单视频，GUI 一键三连和发布朋友圈 |
| V6 Case32 | Tool 查询天气、日历和车次，GUI 选择乘客、座席并提交订单 |
| V6 Case38 | GUI 创建歌单，Tools 搜索并添加歌曲，GUI 启动播放 |
| V6 Case57 | GUI 阅读老板消息，Tools 定位文件，GUI 移动文件并回复 |
| V6 Case75 | GUI 获取纪念日，Tool 准备日历草稿，GUI 设置提醒并保存 |

轨迹位于相应 V6 run 的 `episodes/hybrid_tools_v6.HTV6CaseXX/index.html`。正式演示前
应确认对应 run 未被清理。

## 9. 接手时的注意事项

1. **当前正式版本是 V6。** 旧 README 中的 V1/V4/V5 命令主要是历史示例，实际运行
   以 V6 README 为准。
2. **V6 复用了 V5 未修改任务的代码。** 这是静态代码复用，不是评分失败后回退旧
   verifier；修改 V5 公共 spec、setup 或 contract 时仍需回归 V6。
3. **不要直接把工具覆盖率当成任务质量。** 当前跨模型并集是 99/203，仍需结合实际
   任务价值和 GUI 参与程度判断。
4. **不要把 Hybrid 与 GUI-only 的单次 SR 差值直接称为因果增益。** 需要轨迹审查，
   正式论文结果还应增加多 seed。
5. **原始 MobileGym 隔离是发布要求。** App Tools 使用被动注册和按需加载，独立
   Runtime/Runner 不应修改官方 agent、split 和指标；共享 App 修复后要运行 isolation
   regression。
6. `trial_apps/mobilegym/runs/` 已清理为正式 V6 基线、官方复现和日历 demo。保留
   清单见 `MOBILEGYM_HYBRID_RUNS.md`；重要问题案例另有独立归档。
7. 当前工作区包含尚未提交的相关实现和文档。交给其他同事开发前，建议先建立明确的
   checkpoint commit 或分支，避免工具、runtime、suite 和文档版本错位。

## 10. 建议的接手顺序

1. 阅读总体设计、Tools 设计和五层契约指南；
2. 手动查看 3-5 条推荐轨迹；
3. 跑一个 V6 单任务 Hybrid smoke；
4. 对同一任务跑 GUI-only，比较两条轨迹；
5. 选择一个已有 App，新增一个低风险 query/navigation 工具并完成验证；
6. 选择一个 V6 task，阅读 instruction、setup、verifier 和失败审计；
7. 再开始扩展新 App Tools 或下一版 benchmark。
