# CUA / MobileGym 核心代码摘录（2026-11-18 同步）

> 目的：面试与复盘时能对照「论文附录训练配方」和「环境/Verifier/桌面运行时」关键实现。  
> **不是**完整可运行仓库；完整工程仍在仓外。

## 目录

| 子目录 | 来源 | 内容 |
|---|---|---|
| `mobilegym_verifier/` | `mobilegym-mock-tooluse/trial_apps/mobilegym/bench_env/task/` | Store Verifier、变异审计、noop 审计 |
| `mobilegym_env_snippets/` | 同仓 `system/Notes`、`apps/Taobao` | `navigation.declaration.ts` + `state.ts`（可重置业务状态契约样例） |
| `mac_cua/` | `/Users/zhangyingying/CUA/mac-cua` | Brain–Driver 相关：`runtime/agent.py`、`gui_strategy.py`、任务执行与 `architecture.md` |

## 刻意未拷

- `.env` / `credentials.py` / 含 key 的 client toml
- 完整 63 App 前端、node_modules、数据集、DAPO/verl 训练 launcher（本机未落入可同步的独立训练仓）
- MobileGym 全量源码树

## 对照论文

训练超参见同级目录：`../论文终稿_OpenMobile2/chapters/A_appendix.tex`
