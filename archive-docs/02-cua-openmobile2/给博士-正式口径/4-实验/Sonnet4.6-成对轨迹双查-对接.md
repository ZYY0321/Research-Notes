# Sonnet 4.6 成对轨迹双查 · 对接

脚本和产物都在本机 `0823论文写作-Sonnet咨询/`，**没有推远端**。别的窗口按下面这段话接即可。

---

## 可转发

正式 215 的 GUI / Hybrid 成对轨迹，我们是用 **Claude Sonnet 4.6 当分类器、人在看台上拍板**，不是让模型替我们锁表。

做法：同一道题只喂一对——Gemini GUI-only 和 Hybrid 各一条。包进同一条 user 消息的是：正式题面、候选工具、设计时要验的字段、两边 `success/步数/stop`、每步压缩后的 `trace`（app、调用名、参数、thought 截断、工具返回摘要）、以及判定的 expected/actual。**不喂截图。** 模型固定输出三栏：【任务】像不像正式题、【模型】两条轨迹实际做成什么样、【验证】判定靠不靠得住。看不出就写看不出，不准列环境检修清单，不准替我们做去留。

人工只把 Sonnet 当预审：对了就用，驳过的以人工为准（例如 Case09 日期、Case14 小红书纯文字）。看台按钮才是合同：保留 / 改题 / 修判定 / 拿掉。旧 Gemini 37.7% / 68.4% 冻结，不因改判定重跑翻分。

215 道已经全量跑过；产物在本机 `artifacts/bench215-official-insight/`。看台：

```bash
python3 docs/不要上传-修bug/0823论文写作-Sonnet咨询/scripts/serve_bench215_lock.py
# http://127.0.0.1:4192/
```

要复跑分析（需 `TOKENHUB_API_KEY`）：

```bash
python3 docs/不要上传-修bug/0823论文写作-Sonnet咨询/scripts/run_bench215_official_insight.py
# --build-only 只打 packets；--force 覆盖已有 para.md
```

轨迹本身在 worktree `trial_apps/mobilegym/runs/`：9/3 的 207 reinst + 9/4 recover（timewall / pack8 / secretary / pack2 / pack3），看台脚本按题 stitch 成一对，不是远端仓库里的一份总表。

更早还有 63 条候选的「一段话」版（`run_bench200_paired_insight.py`）和 Qwen 207 成对版；**现行锁表以正式 215 三栏版为准。**

---

## 本地入口（给接着做的人）

| 要什么 | 在哪 |
|---|---|
| 本方法脚本 | `scripts/run_bench215_official_insight.py`（system prompt 写在文件头） |
| 看台 + 成对 stitch | `scripts/serve_bench215_lock.py`（`OFFICIAL_GEMINI` 那张表就是对哪几包 runs） |
| 215 全量分析 | `artifacts/bench215-official-insight/items/*/para.md`，总表 `all.md` |
| 人工批注 | `artifacts/bench215-lock/comments.json` |
| 人怎么用 Sonnet | `bench215-锁表口径-20260908.md` 第 6 条 |
| 看过的论文点 | `bench215-已看55-论文点.md`、`bench215-今晚对齐-Sonnet与人工.md` |

**不要做的事：** 把 Sonnet 原文当分数解释；Hybrid `tools: []` 仍当「工具救回来了」；GUI/Hybrid 断言集不一致却当 rescue。
