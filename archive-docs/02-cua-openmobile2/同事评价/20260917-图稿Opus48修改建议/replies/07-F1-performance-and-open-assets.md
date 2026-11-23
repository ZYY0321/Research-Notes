# 07-F1-performance-and-open-assets

- model: `claude-opus-4-8`
- elapsed_s: 63.0
- finish_reason: stop
- usage: {"prompt_tokens": 3679, "completion_tokens": 3014, "total_tokens": 6693, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 3679, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: F1-performance-and-open-assets.png

---

# 审稿意见：OpenMobile-2 开源资产 + 跨 benchmark 成绩图

## 1. 这张图现在在说什么

左半页展示"开放训练栈"：110+ apps、12K SFT traces、2K RL tasks，配三张 App 截图（Jingdong / Kapi / Calendar）、四类开放资产（spec.json / task.json / trajectory / checker.py），底部一段任务伪代码。右半页是"跨 benchmark 成绩"：AndroidWorld 79.2、MobileWorld 48.3、MobileGym++ 60.8 三条横条，副标题写"One training stack, three benchmarks"。整张图想传达的合并主张是：一套开放训练栈，在三个外部 benchmark 上都跑出成绩。

## 2. 内容张力诊断

**这张图有两个致命结构问题，直接违反硬约束，不能进环境章。**

- **数字口径混装。** 左边 110+ 是训练环境口径，右边三条是外部 benchmark 成绩，而环境章的 census 是 64 可安装 / 35 新构造。这张图把训练侧数字放到"环境章资产图"的位置，读者会默认 110+ 就是环境规模，与 census 直接打架。**110+ 不能出现在环境章。**
- **右图是一把假尺子。** 79.2 / 48.3 / 60.8 来自摘要稿、三个 benchmark 协议各不相同，横条并排且共用 0–100 同一 x 轴，视觉上强烈暗示"同一把尺子、同一评测协议下的三个成绩"。这正是硬约束禁止的：不能暗示我们在三套 bench 上用同一把尺子赢或输。副标题"One training stack, three benchmarks"进一步固化了这个错误因果。
- **说满/说错。** "One training stack, three benchmarks" 把三套不可比的成绩包装成"同源可比"，是过度声称。而且右图完全没有出现 Bench 215 的锁表数字（GUI 58.6 / Hybrid 68.4），读者会误以为这三条就是本文的主战场成绩。
- **伪代码越界。** 底部伪代码写 "find largest expense in **Alipay** ... write into Notes"，但截图标的是 Kapi（记账），出现 App 名不一致；且这是跨 App 任务示例，放在"开放资产"块里语义混乱——它既不是资产也不是 census。
- **缺的东西：** 没有说明这三个 benchmark 各自的评测协议不同、不可比；没有区分训练环境（110+）与评测环境（64/35）；没有 GUI-only 一等公民的任何体现。

**结论：这张图不该以现在的形态进环境章。** 它是"训练资产 + 外部迁移成绩"的混合海报，更适合放在实验/附录，且右图必须彻底改。

## 3. 张力不够 → 应该改成什么

**先做定位切分：这张图承担了两件不该合并的事，拆开。**

**左半（可保留，但归属到"训练栈/开放资产"章，不是环境章）：**
- 保留 110+ apps / 12K SFT / 2K RL，但**必须加限定词**："Training environments (110+ apps) — distinct from the 64 installable / 35 newly-built benchmark apps"。一行小字把两套口径钉死，防止读者混算。
- 四类开放资产（spec.json / task.json / trajectory / checker.py）是真的开源亮点，保留。
- 伪代码统一 App 名：截图是 Kapi 就写 Kapi，别混 Alipay；或直接换成与截图一致的示例。

**右半（必须重画，禁用同轴并排条）：**
- **不该用的数字方式：** 三条同 x 轴（0–100）横条并排 —— 删。这是暗示可比的元凶。
- **该用的做法（三选一）：**
  1. **三个独立小卡片（分面），每个卡片自带一句协议说明**，卡片之间用明显间隔/分隔线，明确标注 "protocols differ, not directly comparable"。x 轴不共享。
  2. 若要进正文主结果，**换成本文合法锁表数字**：Gemini 3.1 GUI 58.6% (126/215) / Hybrid 68.4% (147/215)，gpt-5.6-sol 68.8 / 79.1，且明确写 Bench 215 口径。外部三 benchmark 移到"cross-benchmark transfer (non-comparable protocols)"的附录表。
  3. 保留三个外部成绩但**改成表格 + 显式协议列**（benchmark / metric / protocol / #tasks / score），彻底放弃条形图的"同尺"暗示。
- **caption 必须改口**，去掉"one ruler wins"含义，见第 5 节。

## 4. 视觉元素优化（仅对可保留部分）

- 左侧三个大数字 110+/12K/2K 层级好，但下方限定小字目前完全缺失，必须补，字号约主数字的 22%。
- 三张截图裁切偏满，手机边框占用过多，可统一裁到内容区，宽度对齐。截图下方 App 名（Jingdong/Kapi/Calendar）加粗合理，保留。
- 开放资产四行图标+文字对齐良好，spec.json/task.json 蓝、checker.py 绿的配色一致性可以，保留。
- 伪代码块字号偏大且占三行，可压到两行；`</> Task example` 标题与代码正文层级清楚，保留。
- 右图目前的浅色"剩余槽"背景条（灰）会让人误读为满分参照系，一旦改成分面卡片就应去掉这种共用背景。

## 5. 顶会可投稿的重绘方案

**方案：一图两栏，但语义彻底切开（推荐推倒右半）。**

**模块清单（阅读顺序）：**
1. 左栏标题 "Open training stack (110+ training apps ≠ 64 benchmark apps)" → 三大数字带限定小字 → 三截图 → 四类开放资产 → 一段与截图一致的伪代码。
2. 右栏改为 **"Cross-benchmark transfer"**，三个**独立分面小卡**，每卡：benchmark 名 + 单条 bar + 卡内小字 protocol/#tasks + 显著的 "protocols differ — not on one scale" 灰底提示条横跨三卡上方。
3. （可选）右栏底部加一行指针："Main results on OpenMobile Bench-215 (GUI 58.6 / Hybrid 68.4) in Table X" —— 把主战场引回本文锁表。

**建议英文 caption：**
> **Figure X.** OpenMobile-2 open training stack (110+ training environments, distinct from the 64 installable / 35 newly-built benchmark apps) with released spec/task/trajectory/checker artifacts. Right: transfer scores on three external benchmarks whose evaluation protocols differ and are **not directly comparable**; they are not measured on OpenMobile Bench-215.

## 6. 必须删掉或改口的元素

- **删** 副标题 "One training stack, three benchmarks"（暗示同源可比）→ 改为 "Transfer across three external benchmarks (non-comparable protocols)"。
- **删** 右图三条共用 0–100 同 x 轴的并排布局 → 改分面。
- **删/改** 伪代码里的 "Alipay"，与截图 App 名统一。
- **改** 110+ apps 旁必须加 "≠ 64/35 benchmark census" 限定。
- **禁止** 这张图以现形态进环境章；若进环境章，右半整块删除，只留训练资产。
- **禁止** 出现"用同一把尺子赢/输"或 Hybrid 胜利的任何暗示（当前无 Hybrid 字样，保持）。

## 7. 优先级

- **P0** 右图去掉同轴并排条，改三个独立分面卡并加"协议不同、不可比"横幅——消除假尺子。
- **P0** 110+ apps 旁加限定小字，明确 ≠ 64/35 census；把此图移出环境章（或环境章版本删掉右半）。
- **P0** 删改副标题 "One training stack, three benchmarks" 为非可比表述。
- **P1** 伪代码 App 名与截图统一（Alipay→Kapi 或对应）。
- **P1** 右栏加一行指针把主结果引回 Bench-215 锁表（GUI 58.6 / Hybrid 68.4）。
- **P2** 截图统一裁切与宽度对齐；伪代码压两行；限定小字字号定为主数字约 22%。
