# 正式样本运行状态

| 样本 | 任务路径 | 当前状态 | 证据 |
|---|---|---|---|
| SI-001 | 我的 → 内容上新 → 组件/Sample/技术文章 → 列表底部 | 数据为空，无法生成 `NewContentItem` 底部提示 | `sample_newcontent_layout.json` |
| SI-002 | 我的 → 设置 → 关于 | 已复现；模型候选、布局验证、主动滑动链路已执行 | `SI-002-full-chain-summary.json`、`ux-detect-output/20260913-111036-174/` |
| SI-003 | 我的 → 设置 | 已取得真实截图和 UI dump，待按同一模型配置重新执行 | `sample_settings2.png`、`sample_settings2_layout.json` |

统一运行入口为 `scripts/formal_samples/run_sample_chain.sh`。脚本只负责将应用恢复到约定路径；视觉模型输入仍由 `src/ux-detect-runner.ts` 生成的最终单张截图提供。每个样本的结果必须以 `runId` 单独归档。
