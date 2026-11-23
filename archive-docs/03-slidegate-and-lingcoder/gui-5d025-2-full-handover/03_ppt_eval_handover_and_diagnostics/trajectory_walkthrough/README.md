# 读懂一条真实 PPT 跑批轨迹

> **验收标准（也是你原来的目标）：**  
> 学完后，任意打开一道题的 `result.jsonl`，你能说明：每个顶层字段干什么、每一类 `message_records` 是什么意思、工具调用和结果如何成对、子任务何时出现、最终 HTML 从哪来、`batch_summary` 里的 `terminal_class` 和页数怎么对上。  
> 能讲清这些，面试深挖「你们 Agent 到底怎么跑的」才站得住。

## 本课用的真实样本（不是编的）

| 项 | 路径 / 值 |
|----|-----------|
| 批次 | `/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_loop2_qwen35-9B-decay-8753_tpl_20260928_190634` |
| 题目 | `prod_26016eba`（模板模式） |
| 轨迹文件 | `/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_loop2_qwen35-9B-decay-8753_tpl_20260928_190634/prod_26016eba/result.jsonl` |
| 沙盒回收目录 | `/home/gui-5d025-2/zyy/xhx_agent_v3/output/sandbox/batch_prod_26016eba_c8cea4` |
| PPT 产物目录 | `.../result/pptid_b333c0f2-4b80-4817-a592-3d49ae12c74c/` |
| 精简时间线 | `/home/gui-5d025-2/zyy/benchmark/docs/总结/_assets/trajectory_samples/prod_26016eba_timeline.json` |
| 教学包（字段摘录） | `/home/gui-5d025-2/zyy/benchmark/docs/总结/_assets/trajectory_samples/prod_26016eba_teaching_pack.json` |

本批 `batch_summary` 里该题：`terminal_class=done`，`html_pages=1`，`duration_s≈4414`。  
同批大量题是 `infra_failed`——那是另一课；先把「成功交卷」的轨迹读透。

## 阅读顺序

1. `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/11_读懂一条真实轨迹/01_打开文件你会看到什么.md`
2. `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/11_读懂一条真实轨迹/02_message_records逐类词典.md`
3. `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/11_读懂一条真实轨迹/03_prod_26016eba逐段走读.md`
4. `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/11_读懂一条真实轨迹/04_产物与分数如何接上.md`
5. `/home/gui-5d025-2/zyy/benchmark/docs/总结/10_面试友好完整版/11_读懂一条真实轨迹/05_自测题_换一条轨迹.md`
