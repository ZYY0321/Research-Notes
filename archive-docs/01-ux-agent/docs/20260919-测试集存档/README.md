# 2026-09-19 测试集存档

**评测只用最新带 Labelme 的一版：`测试集/整理`。**  
`整理 2`、`整理_older` 是更早的只有图、没有 json 的版本，不要混用。

| 文件 | 用途 |
|---|---|
| [有XML才端到端.md](../有XML才端到端.md) | **2026-09-21：没 XML 不跑端到端** |
| [失败要写清问题和证据.md](../失败要写清问题和证据.md) | **挂了要写哪一段、情况、改进方向、证据** |
| [catalog.md](catalog.md) | 规模和用法 |
| [catalog.json](catalog.json) | 299 条全量 case |
| [quality-issues.json](quality-issues.json) | 45 条冲突明细 |
| [给数据同学的反馈.md](给数据同学的反馈.md) | 可转发；已去掉「请补到达路径」 |
| [给测试团队的问题.md](给测试团队的问题.md) | 验收页是否必须跟 GT 截图同一环境；10 秒从哪计 |
| [bundles.json](bundles.json) | 从 XML 抽出的包名，仅参考 |
| [给人看.md](../给人看.md) | 给人看的说明：人做什么、五屏怎么连、校园网模型、什么叫过 |
| [给AI.md](../给AI.md) | 交给合作同学 Agent 的说明 |
| [合作与测试队列.md](../合作与测试队列.md) | 谁测哪条、怎么避免抢设备 |
| [检测工作约定.md](检测工作约定.md) | 跳转到上面三份 |
| [case-run-log.md](case-run-log.md) | 真机逐 case 记录 |
| `HarmonyArena-fdu_agent/scripts/testset/build_catalog.py` | 重新生成 catalog |

`测试集/sample_in_harmonyos 2.zip` 是代码工坊全量包（6.1G，含 oh_modules）。工作区已有解压目录 `测试集/sample_in_harmonyos`，先用这个，不必再解 6G。包名 `com.huawei.hmos.sample`。这是构造缺陷 App，和 TOP App 测试集分开跑。

页级 GT 以 json 的 `flags.正常图` 和 `shapes` 为准。XML 只参考。到达页面由我们对着图点，不找数据同学要路径。
