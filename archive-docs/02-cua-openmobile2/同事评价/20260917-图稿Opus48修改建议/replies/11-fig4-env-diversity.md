# 11-fig4-env-diversity

- model: `claude-opus-4-8`
- elapsed_s: 78.5
- finish_reason: stop
- usage: {"prompt_tokens": 3652, "completion_tokens": 3490, "total_tokens": 7142, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 3652, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: fig-4-env-diversity.png

---

# fig-4 审稿

## 1. 这张图现在在说什么

左面板 (a) 是七个领域的气泡带状分布：横轴 App 复杂度（pages×interactive actions，log 尺度），气泡大小编码"该 App 的 Bench 任务数"，纵轴每行一个领域并标注"N tasks · M apps"。想同时讲多样性（七领域、复杂度跨两个数量级）和任务权重分布。右面板 (b) 是横向条形，比较三套环境"每 App 中位 interactive actions"：MobileGym++ new 166、baseline 24.5、AndroidWorld 20（文献近似），配一个 ×6.8 的红色标注。合起来想说"我们的环境又广又深"。

## 2. 内容张力诊断

**结论：能撑住"深度"，撑不住干净的"多样性"，而且现在这版有几处会被审稿人一眼抓住的口径问题。**

- **任务数按领域加总会重复计数 —— 这是最致命的。** 左侧行标 105+53+47+41+41+33+30 = 350，远超 Bench 215。跨 App 任务（74 双 / 27 三 / 5 四）被每个涉及的领域各记一次。审稿人加一下就会发现总数对不上正文的 215，直接质疑数据可信度。必须显式说明这是"任务-领域出现次数"而非任务数，或改成不可加的口径。
- **纵轴 apps 加总同样越界。** 11+7+5+9+3+8+4 = 47 apps。你的 census 是环境可安装 64 / 新构造 35。47 既不是 64 也不是 35，也不是 (b) 里的"35 new apps"。三处 app 计数（左 47、右 35 new、右 28 baseline）互相打架，读者无法对齐到底在讲哪个集合。**这违反"环境 64 vs 训练侧 110+ 不得混用"的硬约束的精神**——同一张图内部就没对齐。
- **横轴"pages × interactive actions"与 AndroidWorld 的可比性问题。** (b) 里 AndroidWorld=20 标了"approx., from literature"，好。但 (a) 的横轴同样是文献口径拼装的 pages×actions，却没标不可比，且 ×6.8 这个 dramatic 倍数直接建立在一把混合尺子上（自测 166 vs 文献近似 20）。硬约束明确：跨 benchmark 协议不同不能画成同一把尺子。×6.8 现在就是把文献占位当实测在放大。
- **"complexity = pages × actions"是构造量，不是主张。** 这是环境的试验特性/描述统计，不能被读成核心贡献。图题"app complexity"容易让人以为复杂度是被验证的能力轴，其实只是规模描述。
- **气泡大小图例的 1/5/15/39** 与"某 App 39 个 Bench 任务"——若真有单 App 39 任务，需与 215 的分布自洽；读者无法从图核验。
- 优点：右图深度对比逻辑清楚，log 横轴展示两数量级跨度有说服力，领域配色区分度好。

## 3. 张力不够处 → 应该怎么改

**建议拆成 coverage 表 + 深度图，不要让一张气泡图既背多样性又背任务权重。**

- **多样性/覆盖 → 用一张紧凑表格**（不是图），列：Domain | # apps (new / installable) | # single-app tasks | # cross-app tasks it participates in。表尾给不可加的正确总计：**apps: 35 new (64 installable)；tasks: 215（109 单 / 74 双 / 27 三 / 5 四）**。表格允许"参与计数"因为读者看得到它不可加，气泡图不行。
- **深度 → 保留 (b) 这类条形**，但：
  - 只用合法自测量做主张。AndroidWorld=20 必须画成灰色、点状边框、单独一组并加"external, not directly comparable"，**不参与 ×6.8 计算**。倍数只能在 MobileGym++ vs MobileGym baseline 之间算（166 / 24.5 ≈ ×6.8 —— 确认这个 ×6.8 是对 baseline 还是对 AndroidWorld？若是对 baseline 才合法，请在图上写清 "vs baseline"）。
  - "median interactive actions per app" 是合法深度代理，保留，但去掉与文献的同尺子暗示。
- **若仍想在一张图里呈现复杂度分布 → 改成按领域的箱线/带状散点**（横轴仍 log complexity），但：
  - 气泡大小改成编码"该 App 页面数"或干脆不编码任务数，避免与 215 冲突。
  - 行标只写 "# apps"，不写 tasks（tasks 交给覆盖表）。
- 合法数字：215 / 109 / 74 / 27 / 5；new 35；installable 64；median actions 166 vs 24.5。
- 不该用：领域 tasks 加总、apps 加总 47、把 AndroidWorld 20 纳入倍数、把 pages×actions 当同尺子跨 bench。
- caption 主张改成："MobileGym++ 覆盖七领域、跨两个数量级的 app complexity，且 per-app 交互面显著深于既有 simulated baseline"——不写"比真机更真"，不写因果涨分。

## 4. 若张力基本成立 → 视觉优化（针对可保留的 (b) 与散点形态）

- **(b) 三条并列，视觉层级不对**：MobileGym++ 蓝、baseline 灰、AndroidWorld 应更弱（点线边框 + 斜纹）以示"外部/不可比"。现在三条实心度接近，读者会误当同尺。
- **×6.8 红色双箭头**：现在跨到 166 全长，暗示是相对 AndroidWorld。改为只跨 baseline→new 段，标 "×6.8 vs baseline"。红色是全图唯一强调色，保留但收窄。
- **"35 apps / 28 apps / 20 apps" 灰色小字**：good，但要与 (a) 的 app 计数对齐或说明差异，否则读者困惑。
- (a) 气泡重叠严重（Shopping、Social 右侧、Entertainment 中段），标签压线。若保留：加轻微 jitter 或缩小最大气泡；给 WeChat/RedBook/Slack 引导线。
- (a) 领域行标两行文字（"105 tasks · 11 apps"）字号偏小、与轴刻度挤，建议行标右对齐、tasks 若删则更清爽。
- log 横轴刻度 10²/10³/10⁴ 清晰，保留；灰色 band 区分行做得好。
- 双栏宽度下 (a) 气泡内标签（Notes/Calendar）仍可读，OK；(b) 数值 166/24.5/20 字号足够。

## 5. 顶会可投稿重绘方案

**推倒重来：一表 + 一图。**

模块清单：
1. **Table 1（覆盖）**：Domain × [new apps, installable apps, single-app tasks, cross-app participations]，表尾自洽总计 215 / 35 / 64。
2. **Figure 4a（复杂度分布）**：per-domain 水平 strip / box，横轴 log(pages×interactive actions)，点=单个 app，颜色=domain。行标只写 domain + #apps。不编码任务数。
3. **Figure 4b（深度对比）**：横向条形，median interactive actions per app，MobileGym++ vs MobileGym baseline（实心），AndroidWorld 单独灰色斜纹标 "external ref, approx." ×6.8 只标注 vs baseline。

阅读顺序：表（有多广/多少任务）→ 4a（每领域 app 复杂度分布）→ 4b（交互面深度 vs baseline）。

英文 caption 建议：
- Fig 4a: *"App complexity (pages × interactive actions, log scale) across seven domains; each point is one app in MobileGym++ (35 newly built)."*
- Fig 4b: *"Median interactive actions per app: MobileGym++ apps are ~6.8× deeper than the simulated baseline set; AndroidWorld (grey, approximate from literature) is shown as an external reference and is not directly comparable."*

## 6. 必须删掉或改口的元素

- **删**：左侧行标里的 "N tasks" 加总口径（重复计数）——要么改成"cross-app participations"并注明不可加，要么移到覆盖表。
- **删/改**：×6.8 若当前是相对 AndroidWorld 计算，必须改为 vs baseline。
- **改**：AndroidWorld 20 视觉降级为外部不可比参考，退出倍数计算。
- **改**：气泡大小编码任务数 → 与 215 冲突，改编码或去掉。
- **对齐**：左 47 apps 与右 35/28 apps 的关系必须在图或 caption 讲清（哪个是环境 64、哪个是 new 35）。
- **禁用词**：不出现 mock；complexity 不写成"能力/贡献"。

## 7. 优先级

- **P0** 修复领域 tasks/apps 加总重复计数：改为覆盖表或标注"participations, not additive"，总计对齐 215 / 35 / 64。
- **P0** ×6.8 只在 new vs baseline 之间计算并标 "vs baseline"，AndroidWorld 退出倍数。
- **P0** 三处 app 计数（47 / 35 / 28）在图内对齐并说明各指哪个集合。
- **P1** AndroidWorld 条与 (a) 横轴文献口径统一标 "not directly comparable / approx."。
- **P1** 气泡大小改为不编码任务数（或改编码页面数），消除与 215 的隐性冲突。
- **P2** (a) 去重叠：jitter + 引导线；行标精简；(b) 红箭头收窄到 baseline→new 段。
