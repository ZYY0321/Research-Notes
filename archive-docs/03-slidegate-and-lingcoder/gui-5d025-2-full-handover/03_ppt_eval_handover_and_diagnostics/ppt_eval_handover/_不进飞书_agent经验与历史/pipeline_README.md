# 新模型 PPT 自动评测流水线

把一个新的大模型接入后，这套流水线会让它批量制作 PPT，并自动完成评分、模型对比和结果上板。

## 真正的交接入口

沿用项目原来的工作方式：新开一个 AI 窗口，把下面两份文件和新模型端点交给它。

1. [`0708_评测复现完整手册.md`](../评测任务文档/0708_评测复现完整手册.md)：权威的完整执行手册。
2. [`0709_跑完模型的后置产出清单.md`](../评测任务文档/0709_跑完模型的后置产出清单.md)：分数出来后的完整收尾清单。

[`AI_RUNBOOK.md`](AI_RUNBOOK.md) 只负责把一键入口接到这两份手册上，不替代它们；发生冲突时以上述两份文件为准。

你最终得到的不只是一批 PPT，而是一套可以回答这些问题的评测结果：

- 47 道不同行业任务完成了多少，哪些失败，为什么失败？
- 模板模式和无模板模式分别表现如何？
- 单页美观、整套结构、内容完整性和附件忠实度各是多少分？
- 新模型相对 Opus、GPT、Flash 等基准强在哪里、弱在哪里？
- 每道题实际生成了什么页面，能否直接在线逐页查看？

![多模型评分与模式对比](../docs/images/dashboard-overview.jpg)

看板还会展示自动整理的模型结论、典型缺陷和训练建议：

![模型分析与训练建议](../docs/images/dashboard-analysis.jpg)

## 它会自动做什么

```text
行业测试题
   ↓
新模型批量生成 PPT（支持断点续跑）
   ↓
收集 HTML/PPT 页面并建立生成看板
   ↓
xhx-ppt-eval 自动评分
   ↓
登记到对比看板
   ↓
分数、页面、跨模型对比、模型分析
```

评分器使用独立维护的
[`SenseTime-FVG/xhx-ppt-eval`](https://github.com/SenseTime-FVG/xhx-ppt-eval)，首次运行时自动下载并固定版本。

## 三步上手

### 1. 克隆并切换分支

```bash
git clone -b feat/portable-ppt-eval-pipeline \
  https://github.com/SenseTime-FVG/xhx_agent_v3.git
cd xhx_agent_v3
```

### 2. 把以下信息告诉 AI

直接复制这段话，把尖括号内容替换掉：

```text
请依次完整阅读：
1. 评测任务文档/0708_评测复现完整手册.md
2. 评测任务文档/0709_跑完模型的后置产出清单.md
3. pipeline/AI_RUNBOOK.md

然后接入并评测以下模型：

模型标识：<例如 my_model_v1，只用英文、数字和下划线>
模型名称：<API 使用的 model 名称>
协议：<openai 或 anthropic>
API Base：<模型端点>
API Key：<密钥；只放环境变量，不写入 Git>

裁判模型 API Base：<评分端点>
裁判模型 API Key：<评分密钥>

先执行 doctor 和 smoke；通过后执行全量生成、评分、上板。
遇到可恢复错误请断点续跑，不要重新跑已成功任务。
```

仓库已经提供最小可运行配置 `pipeline/conf_v3_ppt_eval_base.yaml`。脚本会自动复制原始
`skills/`，把新模型端点写入本次私有副本，并让沙箱使用该副本；不需要接手人另找基础 YAML。

### 3. 查看结果

AI 完成后会返回输出目录、评分文件和看板地址。默认可这样启动看板：

```bash
python results_dashboard/server.py --host 127.0.0.1 --port 8770
```

打开 <http://127.0.0.1:8770/>。

## 给熟悉命令行的人

环境变量准备好以后，全链路入口是：

```bash
bash pipeline/run_both.sh
```

它会按原手册分别生成 `<VERSION>_notpl` 和 `<VERSION>_tpl`，两批各自评分并上板。单独补跑某一模式时才使用 `pipeline/run_all.sh`。详细变量、验收标准、恢复策略和 AI 必须遵循的步骤见
[`AI_RUNBOOK.md`](AI_RUNBOOK.md)。

## 运行产物

| 位置 | 内容 | 是否提交 Git |
|---|---|---|
| `output/<版本>_<时间>/` | 生成结果、trace、生成看板 | 否 |
| `results_dashboard/scores/` | 每题评分 JSONL | 否 |
| `results_dashboard/runs.json` | 本机看板登记 | 否 |
| `.pipeline/` | 临时配置、评分输入、checklist 缓存 | 否 |
| `.deps/` | 自动下载的评分器及其虚拟环境 | 否 |

运行时生成的模型配置和 `skills_<model>` 副本放在 `.pipeline/`，不会污染原始 skills；运行结果不进入 Git。

## 当前边界

默认最小配置使用当前 PPT 评测沙箱，并按既有评测口径禁用非必要联网工具。若沙箱地址变化，直接更新仓库内的最小配置；AI 必须先按完整手册探活，再开始全量。
