# ReDeCheck：面向响应式网页的自动布局失效检测工具（工具论文，ISSTA 2017 Tool Demo）

## 开会速记

- 这是一篇 5 页的工具演示论文，提出 **ReDeCheck**：通过在浏览器中以多个视口宽度渐进渲染网页、构建"响应式布局图"（RLG），**在没有显式 oracle 的情况下**自动检测响应式网页的布局失效。
- 两种模式：①回归检测——比较同一页面改版前后的 RLG，报告布局差异；②常见失效检测——在单一页面上检测 5 类常见响应式布局失效（元素碰撞、元素/视口溢出、窄区间布局、错误换行）。
- 证据强度有限：论文本身只是**摘要性地转述**另外两篇完整实验论文（ASE、ISSTA 正刊论文）的结果数字，并补充两个案例研究（getbootstrap.com、Duolingo），不含本文独立的新实验设计细节。
- 关键结果：回归模式在 100 个人工改版页面上 Recall 90.9%（FP=0）；常见失效模式在 26 个真实网站上报告 196 TP、48 FP、83 NOI（不可见但 DOM 层面已变化的问题），33 个不同 RLF 平均只需查看 4.2 个视口宽度即可定位。
- 与我们课题关系：方法论上高度相关（都是用截图/DOM 在"滑动/缩放视口"式的主动探测中找显示缺陷），但平台（Web DOM vs 鸿蒙 ArkUI 原生控件树）、信号（DOM 坐标几何关系 vs 截图文字截断线索+布局树）完全不同，更多是思路参考而非可直接复用的组件。

## 一页读懂

| 维度 | 内容 |
|---|---|
| 旧方法不够在哪 | 人工"抽查"固定几个视口宽度（如 320/768/1024px），劳动密集且易漏检只在极窄视口区间出现的失效（原文 Sec 1, Introduction）；已有工具（WebSee、Wraith、Cornipickle、Galen）要么用图像比较、要么要求开发者**预先写好 oracle/约束**，都不是专门针对响应式布局失效、且多数仍需人工在每个分辨率下检查（Sec 4 Related Work）。 |
| 本文新增 | 提出"响应式布局图"（RLG）作为页面在不同视口宽度下元素可见性与对齐关系的动态表示；在此之上构建**两种无需显式 oracle 的检测模式**：回归检测（比较新旧版本 RLG）与常见失效检测（针对单一页面检测 5 类预定义 RLF 类型）；工具开源、文档完善、可集成多浏览器。 |
| 输入/输出 | 输入：一个（或两个版本的）网页 URL；通过 Selenium 驱动浏览器在采样的视口宽度下渲染并读取 DOM。输出：文本报告（失效类型、涉及元素、失效出现的视口宽度区间）+ 一组高亮失效元素的截图 S。 |
| 怎样验证 | 本文转述了两项已发表实验（分别见参考文献 [19] 回归检测、[18] 常见失效检测）的汇总数字，并附两个案例研究（getbootstrap.com 回归案例、Duolingo 常见失效案例）说明报告如何帮助开发者定位与修复问题。本文本身未重新做实验，是"工具+已有结果汇总+案例"。 |
| 结论边界 | 只处理静态渐进渲染的单页面布局，不支持 JavaScript 驱动的动态页面，也不做跨页面的整站检测（Sec 5 列为未来工作）；回归检测目前限于同一浏览器内比较，不支持跨浏览器回归（XBI）；报告含 DOM 引用，作者承认"可能难以解读，需要进一步工程化"（Sec 3.2）。 |

具体方向论文条目建议写入 [catalog](../catalog.md)：ReDeCheck｜web｜display(布局失效)｜无oracle(规则/差分)｜工具论文(汇总已发表实验)。

## 一段话介绍

这篇论文研究的是响应式网页（RWD）在不同视口宽度下出现的**布局失效**（如元素重叠、溢出视口、仅在极窄区间出现的异常布局）如何自动检测的问题。解决思路是：用浏览器在一系列采样的视口宽度下渲染页面、读取 DOM 坐标，构建一个随视口宽度变化的"响应式布局图"（RLG），再在图上做两类分析——把新旧版本的 RLG 做差分比较来发现"回归"式的意外布局变化，或者对单一版本的 RLG 直接套用 5 类预定义规则来发现"常见失效"模式——两种分析都不需要开发者预先写 oracle。评价证据是论文作者在另外两篇正刊/会议论文中做的实验结果：回归检测在人工构造的 100 个改版页面上达到 90.9% 的 recall；常见失效检测在 26 个真实生产网站上发现大量布局失效（包括 Duolingo、Consumer Reports 等知名网站），并被作者称为优于人工抽查方法。本文作为工具演示论文，把这些结果和工具架构做了汇总展示，并补充了两个具体案例说明报告如何辅助开发者定位与修复缺陷。

## 关键术语与阅读前提

- **RWD（Responsive Web Design，响应式网页设计）**：通过流体网格、弹性媒体、媒体查询，使页面在不同设备/视口宽度下自适应排布的设计范式（Sec 1）。
- **RLF（Responsive Layout Failure，响应式布局失效）**：页面在某些视口宽度下出现的非预期布局问题，论文定义了 5 类（element collision 元素碰撞、element protrusion 元素溢出容器、viewport protrusion 元素溢出视口、small-range layouts 极窄区间布局、incorrectly wrapping elements 错误换行）（Sec 2）。
- **RLG（Responsive Layout Graph，响应式布局图）**：工具核心数据结构，建模元素在视口宽度变化过程中可见性与相对对齐关系的变化（Sec 2）。
- **NOI（Non-Observable Issue，不可见问题）**：DOM 坐标层面存在异常（如元素重叠）但视觉上尚未表现为失效的情况，作者将其与 TP/FP 并列报告（Sec 2, Table 1b）。
- **viewport width（视口宽度）**：浏览器可视区域宽度，是本文采样与检测的自变量。
- 这些术语建议链接到 ../glossary.md 中对应的"布局/显示缺陷""oracle"条目；RWD 背景知识可链接 ../field.md 的 Web GUI 测试综述部分。

## 动机

作者指出，尽管响应式设计框架（Bootstrap、Foundation）让开发者容易构建"看起来响应式"的页面，但元素与布局规则间复杂的相互作用容易引入非预期的视觉缺陷（Sec 1, Challenges Addressed）。论文给出的例子（并非作者自编教学例子，而是论文正文案例）：Duolingo 页面在宽视口下语言选项轮播图居中显示、箭头可点击（Figure 1 (a)(c)），但在稍窄的视口宽度下轮播图溢出视口，右箭头被遮挡不可点击（Figure 1 (b)(d)）。由于 RLF 往往只在不可预测、有时很窄的视口区间内出现，人工"抽查"少数固定宽度（如 320/768/1024px）容易漏检（Sec 1）。已有研究原型（X-PERT 检测跨浏览器不一致、GWALI 检测国际化呈现失效、WebSee/Wraith 用图像比较、Cornipickle 需要用户预先定义布局约束）均未专门解决"无需显式 oracle 的响应式布局自动检查"问题（Sec 4）。

教学例子（本笔记自编，非论文原文）：假设一个导航栏在宽屏下横排显示，窄屏下变成下拉竖排列表；如果开发者只在 768px 和 1024px 两个常见断点检查，可能漏掉 766–767px 这个仅两像素宽的区间内导航栏"既不是横排也不是竖排"的中间异常状态——这正是论文 Figure 3 案例所展示的真实情形（见下文方法部分）。

## 贡献

原文未按编号列出贡献清单，本节为我们的归纳：

1. **方法/工具贡献**：提出 RLG 作为响应式页面在视口宽度维度上的动态布局表示，并在此基础上实现两种无需显式 oracle 的检测模式（回归检测、常见失效检测）（Sec 2）。
2. **工具实现贡献（harness）**：用 Java 实现、基于 Selenium 驱动多浏览器（Chrome、Firefox、Safari、PhantomJS）、开源发布在 GitHub，附文档与 JUnit 测试，可扩展新的失效检测器（Sec 2, Sec 5）。
3. **工具论文层面的汇总性贡献**：汇总并展示了作者此前两篇独立论文（[18] ISSTA、[19] ASE）的实验结果，并补充两个案例研究说明工具产出的报告如何辅助开发者诊断与修复问题（Sec 3）。

需要注意：本文**没有**提供独立于 [18][19] 的新实验设计或新数据集，不构成严格意义上的新 empirical study；它的"benchmark"性质也仅限于转述他人已发表的评测语料（100 个改版页面、26 个真实网站），本文自身未重新采集或筛选数据。

## 方法

整体思路：先把一个（或两个版本的）网页在一系列视口宽度下渲染出来，提取 DOM 坐标，构造出随宽度变化的布局模型（RLG）；再根据任务模式（回归 vs 常见失效）在模型上做差分比较或规则匹配，产出带截图与文字描述的失效报告。

1. **输入与表示**：输入是网页 URL（回归模式下是同一页面的两个版本 W 与 W′）。工具不使用源码或需求文本，而是通过 Selenium 驱动真实浏览器渲染页面，并通过 DOM 读取元素坐标与可见性，在一系列采样的视口宽度下重复渲染-读取过程（Sec 2，Figure 2）。

2. **中间模块处理**：
   - **Model Extractor（模型提取器）**：负责提取 RLG。采样策略为"均匀采样"（例如每 60 像素一个宽度点）加"边界采样"（在页面样式表中搜索 media query 断点宽度），两者结合以获得具有代表性的采样集合（Sec 2）。
   - 对相邻采样宽度的布局做比较，若发现差异，则用**二分搜索**定位布局变化发生的精确视口宽度，重复直至所有布局分析完毕（Sec 2）。
   - 回归模式下，**Model Comparator（模型比较器）**用成对匹配（pairwise matching）比较 RLG 与 RLG′，产出潜在回归差异集合 F_reg；常见失效模式下，**Common Failure Detector**直接在单一 RLG 上检测 5 类预定义 RLF，产出 F_com（Sec 2，Figure 2）。

3. **动作/流程控制**：整个过程是全自动的脚本化渲染-提取-比较流程，没有"agent 式"动作选择或失败重试机制描述；论文未提及人工干预或失败反馈环节（原文未给出相关细节）。

4. **判定依据**：判定失效的依据来自 DOM 坐标层面的几何关系变化（对齐、碰撞、溢出边界等），不依赖像素级图像比较，也不要求开发者预先编写 oracle（Sec 4 强调这是与 X-PERT/Cornipickle/Galen 等工具的区别）。报告生成模块（Report Generator）进一步分析 F_reg 或 F_com，判断失效性质与可见的视口宽度区间，并生成带高亮框的截图集合 S（Sec 2）。开发者需要人工判读报告中的 TP（真实可见失效）、FP（无实际视觉问题）、NOI（DOM 层面异常但尚不可见）三类结果（Sec 2, Sec 3.1）。

5. **终止与产物**：当所有采样宽度（及二分搜索细化后的边界宽度）分析完毕后流程终止，最终产物是一份文本报告（失效类型、涉及元素、视口宽度区间）加一组高亮截图，供开发者人工复核、诊断与修复（Sec 2，Figure 1(e)）。

**完整例子**（来源：论文 Figure 3 案例研究，Sec 3.2）：getbootstrap.com 页面在原始版本中，导航链接在窄视口下以竖直下拉列表显示，在 768px 及以上宽度变为横向导航条。某次样式表小改动后，工具检测到 766–767px 这一窄区间内导航链接被错误地渲染为"一行"而非下拉列表。ReDeCheck 的回归检测报告给出："NAV/UL/LI[1] - NAV/UL/LI[2] 的对齐约束（leftOf, topAlign, bottomAlign）：原版本 768→1300，修改版本 766→1300"，从而提示开发者该区间的布局行为已发生意外变化（Figure 3 底部报告片段）。

## 核心技术 / 综述主题详解

本文是方法/工具论文而非综述，核心设计点如下：

- **RLG 的设计动机**：传统做法逐个视口宽度独立检查，而响应式布局的本质是元素对齐关系随宽度**连续变化**，因此需要一个能表示"在哪个宽度区间内，元素 A 和元素 B 保持什么相对关系"的结构。RLG 正是为此设计，采样+二分搜索的组合保证了既不需要穷举所有像素宽度（成本太高），又不会因为采样过粗而漏掉窄区间失效（Sec 2）。
- **两种模式服务不同场景**：回归检测服务于"代码改动后是否引入意外布局变化"的持续集成/CI场景，不需要预先知道失效的具体模式，只需比较前后版本差异；常见失效检测服务于"首次/定期扫描一个页面是否存在已知模式的布局缺陷"，依赖研究者事先总结的 5 类 RLF 规则（这 5 类规则来自作者在参考文献 [18] 中对 RWD 实践的分析，本文未重复展开其具体判定公式，原文未给出规则的数学表达式细节）。
- **TP/FP/NOI 的三分类设计**：这是本文在 oracle 问题上的核心取舍——由于布局"是否算失效"最终依赖人类视觉判断，工具只能基于 DOM 几何关系产出候选，因此报告中专门保留 NOI 类别，承认某些 DOM 层面的异常当前不可见，但可能是未来回归的前兆（Sec 2，Table 1b 讨论）。这与"无需显式 oracle 但也无法完全自动判定真假"的设计哲学是一致的。
- **消融/实验对应关系**：本文没有做消融实验（这是工具演示论文，不含控制变量研究）；Table 1a/1b 的数字分别对应回归检测与常见失效检测两个独立评测研究，用以支持"工具能检测大多数布局变化/常见失效类型"这一主张，但不能回答"哪个模块贡献更大""采样策略是否最优"等机制性问题（这些留给参考文献 [18][19]）。

交付前检验自评：合作者可以据此说明——论文做了什么（渐进渲染+RLG+两种无 oracle 检测模式的工具）、研究价值（首个专门针对响应式布局、无需显式 oracle 的自动检查工具）、证据支持到哪里（转述的两组实验数字 + 两个案例研究，但本文未独立设计实验）。

## 实验

本文所述实验均为**转述**自参考文献 [18]（ISSTA 正刊）与 [19]（ASE），本文（工具演示论文）本身未重新开展实验设计，只汇总结果数字并做解读。

**(a) 回归检测评测**（对应 [19]）
- 数据：用一个代码变异工具，对 5 个响应式页面各生成 20 个"渐进式修改版本"（改变元素的 width/margin/padding 等），共 100 个改版页面（Sec 3.1）。
- 真值构造方式：原文未给出具体的人工标注流程细节，只说明这些是通过简单代码修改算子人工构造的变异版本。
- 指标：TP/TN/FP/FN 及 Recall（召回率，即工具检测出的真实布局差异占全部真实差异的比例）。
- 结果（Table 1a）：TP=80，TN=12，FP=0，FN=8，Recall=90.9%。作者解释 15 个假阴性（原文此处数字与 FN=8 不完全对应，原文写"15 false negatives were observed"而 Table 1a 给出 FN=8，**此处保留原文两处数字的不一致，不代替作者修正**，见 Sec 3.1 正文与 Table 1a）中的变化被认为"极小、不太可能构成真实失效"，用以说明工具的不足有限。
- 结论边界：该实验只能说明工具在**人工构造的小幅代码变异**场景下的回归检测召回率较高，不能说明工具在真实世界复杂改版场景下的表现。

**(b) 常见失效检测评测**（对应 [18]）
- 数据：26 个随机收集的、复杂度和领域各异的真实生产网站（Sec 3.1）。
- 指标：TP/FP/NOI 三分类计数；以及"视口宽度（viewports）数量"与"不同 RLF 数量"的比值，用来说明开发者平均需要查看多少个视口宽度才能找到一个独立失效。
- 结果（Table 1b）：TP=196，FP=48，NOI=83，报告涉及的不同视口宽度总数=137，对应 33 个不同的 RLF。作者据此计算平均每个 RLF 需要查看 137/33 ≈ 4.2 个视口宽度。
- 结果解读：论文称"well over half of the web pages ... contained RLFs"（Sec 3.1），包括 Duolingo、Consumer Reports 等知名网站，并称工具优于若干"spotchecking"式人工检查方法（如漏检 Duolingo 失效的案例，Figure 1）。
- 结论边界：该实验证明了真实生产页面中 RLF 的**普遍存在性**和工具的**检出能力**，但 FP=48、NOI=83 也说明工具存在误报与"不可见但 DOM 异常"的灰色地带，需要开发者人工复核；原文未给出该评测中具体的人工复核标准或多人标注一致性数据。

**运行效率**：原文称工具在大多数研究页面上运行时间少于两分钟（Sec 1, Evaluation Results），具体运行环境、重复次数、硬件配置原文未给出。

**新缺陷报告/确认/修复**：论文称在 Duolingo、Consumer Reports 等真实网站上检测到失效，但未说明是否向相关网站开发者报告、是否被确认或修复（原文未给出）。

## 局限

**论文承认的**：
- 报告含 DOM 元素引用，"可能难以解读，需要进一步工程化"（Sec 3.2, Case Studies 部分明确写道 "further engineering is required to make them more useful for developers"）。
- 当前不支持使用 JavaScript 的动态页面，也不支持整站级别检测，只能处理单个静态渲染页面（Sec 5, Future Work）。
- 回归检测目前只能在同一浏览器内比较前后版本，尚不能检测跨浏览器的响应式不一致（responsive XBI），这是未来工作（Sec 5）。
- 存在误报（FP）与不可见问题（NOI），例如工具曾将 3 个元素误判为"同一行"，从而误报对齐变化为换行失效（Sec 3.1）。

**我们的观察**：
- 本文作为工具演示论文（ISSTA Tool Demo track），其证据链条依赖另外两篇完整论文 [18][19]，本篇自身未提供原始数据集、标注协议或统计检验细节，读者若需要严谨评估准确率应查阅原始论文，仅凭本文无法独立核验结果可靠性。
- 判定逻辑完全基于 DOM 几何坐标关系（对齐、碰撞、溢出），不涉及任何视觉语义理解（如文字是否被截断、图标是否被遮挡的"内容层面"判断），这与我们课题中依赖截图视觉线索（如文字截断）的判定方式在信号来源上是互补而非替代关系。

## 和我们课题的关系

### 与 UX testing 的关系

ReDeCheck 检测的是**Web DOM 层面的几何布局失效**（碰撞、溢出、窄区间异常、错误换行），这与我们 UX-Agent 关注的"文字截断、遮挡、重叠、溢出"等显示缺陷在**问题类型上高度重合**（尤其是元素碰撞/溢出与我们的遮挡/重叠/溢出候选是同类问题的 Web 版本）。但平台完全不同：ReDeCheck 依赖 Web 标准化的 DOM 坐标系统和 CSS media query 断点，可以精确读取每个元素的几何边界并做规则化判定；而鸿蒙 ArkUI 原生应用没有等价的、可直接遍历的"响应式断点"概念，我们的 UX-Agent 必须先靠截图视觉线索（文字截断候选）发现问题，再用布局树复核、用主动滑动模拟"视口变化"去验证。可以说 ReDeCheck 的"多宽度采样+二分搜索定位边界"思路，对我们"主动滑动探测"这一步有**方法论参考价值**——即如何系统化地在一个连续变化的交互维度（视口宽度 vs 滚动位置）上定位缺陷出现的精确区间，而不是依赖人工抽查固定状态点。但 ReDeCheck 本身不检测文字截断、图标遮挡等内容语义类问题，也不是为移动端原生应用设计，因此不能直接迁移到我们的候选生成或布局树复核环节，只能作为"主动探测定位边界"思路的旁证。

### 与 GUI testing 的关系

ReDeCheck 为 GUI 测试中的**oracle 问题**提供了一个具体解法范例：它说明在没有显式 oracle（开发者无需预先写断言或约束）的前提下，仍可通过**对比同一软件在不同配置下的结构化表示**（这里是不同视口宽度下的 DOM 几何关系）来自动发现潜在缺陷，这是一种"差分式/基于规则的隐式 oracle"思路（原文 Sec 4 明确将自己与需要显式 oracle 的 Cornipickle、Galen 对比）。它也为**探索（exploration）**问题提供了"系统化采样+二分搜索收窄边界"的具体策略，而非随机或穷举。在**评测（eval）**层面，它给出了 TP/FP/NOI 三分类和"平均需查看视口数"等指标设计，对我们设计 UX-Agent 的评估指标（如"平均需要人工复核的候选数"）有参考价值。需要明确的是，论文未来方向提到的"动态 JS 页面支持""整站检测""跨浏览器回归检测"仅是作者提出的**待验证的问题假设**，并非本文已验证的创新点，不应在后续引用中当作已解决的问题处理。

## 原文摘要关键句（节选）

"Since the quality assurance process for responsively designed websites is often manual, time-consuming, and error-prone, this paper presents ReDeCheck, an automated layout checking tool that alerts developers to both potential unintended regressions in responsive layout and common types of layout failure."
—— Abstract，所读版本（White Rose PDF）第 1 页。

中文解释：这句话限定了论文的问题范围——不是通用的 Web 功能测试，而是专门针对**响应式布局**的质量保证自动化，且明确区分了两类检测目标（意外回归 vs 常见失效类型），这是理解后文两种模式设计的前提。

## 原文摘录

> "This two-part combined approach thereby obtains as representative a sample as possible. The layouts at the chosen widths are then analyzed sequentially to model the responsive layout. If difference(s) are found between two consecutive layouts, the tool conducts a binary search to find the exact viewport width at which the layout change, repeating the process until all layouts are analyzed."
> — Sec 2 (The ReDeCheck Tool)，所读版本第 2 页。

> "Unlike ReDeCheck's failure checking mode, they also require an oracle."
> — Sec 4 (Related Work)，所读版本第 4 页。

> "Since Table 1b shows that the tool reported 137 different viewport ranges for the 33 distinct RLFs, a developer would only have to study, on average, 4.2 viewport widths to find each distinct RLF."
> — Sec 3.1 (Experimental Studies)，所读版本第 4 页。

## 所读版本与核对范围

所读版本为 White Rose Research Online 存档的 Accepted Version PDF（https://eprints.whiterose.ac.uk/id/eprint/116991/1/c49.pdf），对应 ISSTA 2017 会议论文正式出版版（pp. 360-363，DOI: 10.1145/3092703.3098221）。本次通读覆盖全文正文（Abstract、Sec 1 Introduction、Sec 2 The ReDeCheck Tool、Sec 3 Applying the Tool 含 3.1 实验研究与 3.2 案例研究、Sec 4 Related Work、Sec 5 Conclusions and Future Work）及参考文献列表；论文本身篇幅仅 5 页，无独立附录。视觉核对了 Table 1a（回归检测结果）与 Table 1b（常见失效检测结果）两张表格数字，以及 Figure 1（Duolingo 案例）、Figure 2（工具架构图）、Figure 3（getbootstrap.com 回归案例）中的文字性描述。未对照 ACM 正式排版版本逐字核验页码与版式差异；未复现工具或重新运行实验；Table 1a 正文叙述的"15 false negatives"与表格中 FN=8 的数值不一致之处已在"实验"节中如实保留，未做主观修正。

## 书目与分类（记录用）

<details>
<summary>展开标题、作者、版本和标签</summary>

- title: ReDeCheck: An Automatic Layout Failure Checking Tool for Responsively Designed Web Pages
- authors: Thomas A. Walsh, Gregory M. Kapfhammer, Phil McMinn
- year: 2017
- era: classic
- venue: ISSTA 2017 (International Symposium on Software Testing and Analysis)
- venue_type: conference
- url: https://eprints.whiterose.ac.uk/id/eprint/116991/
- pdf_url: https://eprints.whiterose.ac.uk/id/eprint/116991/1/c49.pdf
- version: Accepted Version (White Rose Research Online)
- code_url: https://github.com/redecheck/redecheck/
- institution: University of Sheffield; Allegheny College
- aka: ReDeCheck
- door: gui
- question: eval（工具同时服务于 generate 候选发现与 eval 报告，但核心贡献是“自动检测+报告”，更偏 oracle/eval 性质，无独立 generate/execute 环节）
- contribution_type: method, harness
- platform: web
- method: hybrid（规则化差分比较 + 结构化采样算法，非 LLM/RL）
- oracle_type: differential（回归模式，基于 RLG 差分）/ spec（常见失效模式，基于预定义 5 类规则）
- bug_type: display
- benchmark: 原文未给出标准化公开 benchmark 名称；评测语料为 5 个页面×20 变异版本（共100个，来自[19]）与 26 个真实网站语料（来自[18]），均为作者自建
- baselines: 人工 spotchecking（抽查固定视口宽度）
- headline_result: 回归检测 Recall 90.9%（TP=80,TN=12,FP=0,FN=8，原文Table 1a）；常见失效检测 TP=196,FP=48,NOI=83，33个RLF对应137个视口宽度（原文Table 1b）
- one_liner: 基于响应式布局图（RLG）的多视口采样+差分/规则检测，无需显式oracle自动发现响应式网页布局失效
- use_in_survey: 可作为“Web GUI 显示缺陷检测”“无oracle布局检查”代表工作之一
- concepts: RLG, RLF, viewport sampling, binary search boundary detection, regression checking, common failure detection, NOI
- priority: should
- read_depth: full
- owner: ZYY0321(AI辅助)
- status: extracted

</details>