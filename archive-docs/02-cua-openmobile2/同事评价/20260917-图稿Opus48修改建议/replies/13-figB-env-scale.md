# 13-figB-env-scale

- model: `claude-opus-4-8`
- elapsed_s: 61.4
- finish_reason: stop
- usage: {"prompt_tokens": 3152, "completion_tokens": 2888, "total_tokens": 6040, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 3152, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: fig-B-env-scale.png

---

# fig-B 审稿意见

## 1. 这张图现在在说什么

三个并列的两柱对比子图，比较 "MobileGym baseline" 与 "MobileGym++ (new 35)" 在每 App 中位数上的三个规模指标：Pages/routes（9.5→36.0，×3.8）、Interactive actions（24.5→166.0，×6.8）、Nav depth（2.0→3.0，×1.5）。红色斜箭头+倍数标注强调"更大更深"。核心叙事是"我们的环境比自家 baseline 规模显著更大"。

## 2. 内容张力诊断

**弱，而且比 KPI 卡还危险——它把一个自我对照包装成了外部证据。**

- **对照对象太软**：只跟"MobileGym baseline"比。审稿人第一反应是"跟自己的旧版比当然大"，这不构成顶会级贡献。真正要回答的问题是：相对 AndroidWorld / MobileWorld / 真机 bench，你的环境提供了什么别人没有的可控性 / checker / cross-app。这张图完全没碰。
- **指标选得避重就轻**：Pages/actions/nav depth 是"页面复杂度"，不是环境论文的核心卖点。你的核心主张是：**可控可重置的 simulated 世界、业务状态差分 checker、cross-app 真实写入、GUI-first + tools 第二通道**。这些一个都没出现。规模大 ≠ 可评测性强。
- **×6.8 有过度包装嫌疑**：median actions 24.5→166 的 6.8 倍，如果 baseline 只是老版本页面少，这个倍数说明不了任务难度。actions 数多不等于任务有意义。审稿人会怀疑这是把"堆控件"当成贡献。
- **口径缺失**：new 35 与"合计可安装 64""七领域"的关系没交代；median per app 的样本 n 没写；baseline 有多少 app 也没写。
- **没有触及硬约束里的任何一等公民**：GUI-only、checker 读业务状态差分、cross-app 真实写入、reset 语义——这些才是环境论文的护城河，全缺席。
- **nav depth ×1.5（2→3）几乎没有信息量**，放进来反而稀释了另外两个，还暴露"深度其实没提升多少"。

结论：**这张图撑不住论文主张，需要重构而不是美化。** 但也不必做成三大数字 KPI 卡——KPI 卡更弱。方向是做成"能力/协议对照表 + 一张规模小图"。

## 3. 张力不够——应该改成什么

**主图改成"环境能力对照表"（capability matrix），规模柱图降为附属小图。**

对照轴（列）建议（这些是环境论文真正被 challenge 的维度）：
- Installable apps / domains
- Reset（可否程序化重置到确定初始态）
- Success checker reads（业务状态差分 vs 截图匹配 vs 路径匹配）
- Cross-app（第二 App 是否真实业务写入）
- GUI-only path（是否一等公民）
- Tools channel（同一 store 的第二通道，标注可选/plus）
- Observation（pixels / a11y tree）

行：MobileGym++ / AndroidWorld / MobileWorld / (可选 baseline)。

**必须遵守的口径**：
- AndroidWorld / MobileWorld 若只是文献占位，**该单元格标 "reported / not directly comparable"**，绝不能画成实测散点或同尺子并列的成功率。
- apps 数写清楚："new 35, 64 installable, 7 domains"；不要把训练侧 110+ apps 混进来。
- 不要出现成功率数字（那是另一张锁表图的事）。
- 用 "simulated"，不用 mock。
- checker 那一栏必须写"business-state diff"，这是你区别于截图匹配 bench 的关键。

**规模数字**如仍想保留，压成对照表下方一行 sparkline 或小柱，只留 Pages 和 Actions 两个，删掉 nav depth ×1.5。

**caption 主张**：应从"我们比旧版大"改成"我们提供可重置、按业务状态判定成败、支持真实跨 App 写入的 GUI-first simulated 环境"。

## 4. 若坚持保留规模图——视觉逐项优化

（仅当把它降为附属小图时）
- **删掉红色斜箭头**：从左低柱指向右高柱的斜箭头没有物理意义（x 轴是类别不是时间），且暗示"增长趋势"。改成柱顶上方直接标 "×3.8" 文字即可。
- **删除 nav depth 子图**：×1.5 信息量低，拉低整组说服力。
- **两柱配色**：baseline 灰 / ++蓝的对比可以，但注意灰色偏冷，弱化了 baseline，属可接受的主体强调。
- **标题去掉隐含 claim**："Environment Scale" 可保留，但副标注 median per app 后要补样本量 (n=35)。
- **y 轴**：actions 子图 200 顶格，柱子 166 顶到接近上沿，改上限到 220 留白。
- 数字标签字号已够大，保持。

## 5. 顶会可投稿重构方案（推倒重来）

**模块清单（单张 figure，左表右小图）：**
1. **主体：Capability & Protocol Comparison Table**（左 2/3 宽）
   - 行：MobileGym++ / AndroidWorld* / MobileWorld*（*= reported, not directly comparable，脚注说明）
   - 列：Apps(domains) / Reset / Checker signal / Cross-app write / GUI-only / Tools channel / Obs
   - 用 ✓ / ✗ / 文字短语填充，MobileGym++ 行整行浅蓝底强调
2. **附属：规模小图**（右 1/3 宽）
   - 两组分组柱：Pages、Actions（median per app），baseline vs ++，柱顶标 ×3.8 / ×6.8
   - 删 nav depth，删斜箭头

**阅读顺序**：先读表判断"这个环境在协议维度上有什么独特能力"→ 再瞥右图确认"规模也确实更大"。

**建议英文 caption**：
> "MobileGym++ is a controllable, resettable *simulated* mobile-app world (35 new apps, 64 installable across 7 domains). Unlike prior benchmarks, success is judged by **business-state diffs** rather than screenshot or path matching, and cross-app tasks require **real writes** in a second app. Right: per-app scale (median) vs. our earlier baseline. Numbers for AndroidWorld/MobileWorld are as reported and not directly comparable (different protocols)."

## 6. 必须删掉或改口的元素

- **删红色斜箭头**（类别轴上的伪趋势）。
- **删 nav depth 子图**（×1.5 稀释叙事）。
- **改标题**：不要让"vs baseline"成为主对照；主对照应是外部 bench 的能力矩阵。
- **补口径**：n=35、7 domains、64 installable；不得混入训练侧 110+。
- 任何 AndroidWorld/MobileWorld 的量若加入，**必须标 "not directly comparable"**。
- 全文 mock→simulated（即使本图没写，caption 要守）。

## 7. 优先级

- **P0**：把主体从"自家 baseline 双柱"改为"外部 bench 能力/协议对照表"，列含 checker=business-state diff、cross-app real write、GUI-only、tools、reset——直击论文一等公民主张。
- **P0**：外部 bench 的任何数字标注 "reported / not directly comparable"，禁止画成同尺子实测。
- **P1**：删红色斜箭头与 nav depth 子图；规模柱降为右侧附属分组柱，仅留 Pages/Actions，柱顶标倍数。
- **P1**：caption 与 apps 口径补齐（35 new / 64 installable / 7 domains / median n=35），禁混训练侧 110+。
- **P2**：actions 子图 y 轴上限抬到 220 留白；MobileGym++ 行整行浅蓝底强调，术语统一为 simulated。
