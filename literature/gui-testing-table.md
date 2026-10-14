# GUI 测试文献大表（demo）

列说明：动机/贡献尽量保留原文措辞；gap 分"作者自认"和"我们看到"。UNVERIFIED = 未在全文核对。
来源：子代理逐篇打开全文/PDF 抽取，venue 与数字以全文为准（会议摘要页与全文不一致处已注明）。

## A. 显示/布局类缺陷（display / layout）

| 论文 | 年份·venue | 第一作者机构 | 动机（原文） | 贡献（原文要点） | 方法 | 实验/关键数字 | gap（作者自认 / 我们看到） | 一段话叙事 |
|---|---|---|---|---|---|---|---|---|
| **OwlEye** Owl Eyes: Spotting UI Display Issues via Visual Understanding | 2020 ASE | 中科院软件所（Zhe Liu；Monash Chunyang Chen 合作） | "display issues such as text overlap, blurred screen, missing image always occur during GUI rendering on different devices"；现有测试 "can only spot critical crash bugs"；众测截图 43.2% 有显示问题 | first systematical investigation + 首个大规模数据集；CNN 检测 + Grad-CAM 定位；启发式数据增强 | 截图 → CNN 二分类 → Grad-CAM 热力图；Rico 合成缺陷 | P 0.85 / R 0.84；329 应用报 57 新问题，26 确认/修复 | 自认：模糊屏合成不了，DroidBot 探索不全 / 我们：热力图不是紧框，合成≠真实分布 | 崩溃测试看不见"人眼一看就错"的显示问题，把它变成截图分类 |
| **Nighthawk** | 2023 TSE（OwlEye 期刊扩展） | 中科院软件所 | "the localized issue area by OwlEye is usually too large"；收集缺陷图费时；XML 静态分析 P 0.32 | Faster R-CNN 检测+定位；从无缺陷截图自动生成带框训练数据；开源 | 改 Rico JSON 合成 4 类缺陷 → Faster R-CNN | P/R 0.84；定位 AP 0.589；1,328 应用 151 新问题，75 确认 | 自认：未做根因与补丁 / 我们：定位仍约 0.6，跨平台样本小 | 不需要人工标缺陷图、框更准，能指导修复 |
| **dVermin** The Metamorphosis | 2022 ASE | 中科院软件所（Yuhui Su） | 放大字号/显示 "can easily lead to scaling issues such as text truncation, component overlap"；单看一张图"looks good"，OwlEye 抓不到 | 首个缩放问题自动检测：view 配对 + view 间/view 内不一致检测 | 默认 vs 放大两套 view tree，注入 id 配对，OpenCV 比较 | 页面级 P/R 0.97；view 级 F1 0.88；20 个 issue 确认/修复 | 自认：可滚动 view 误判为裁剪，ellipsize 当合法 / 我们：要改 XML 跑两遍；评估集=动机集 | **差分 oracle**：和"正常配置下的自己"比 |
| **ReDeCheck** | 2017 ISSTA | Univ. of Sheffield | "difficulty in providing an automated 'oracle' to validate RWD layouts" | 5 类响应式布局失败分类；4 个检测算法；26 页实证 | 320–1400px 多宽度采样 DOM → 布局图 → 找相邻宽度间不合理突变 | 26 页中 16 页有真问题，33 个失败；无 P/R 表 | 自认：FP 多 / 我们：元素整段消失抓不到（SALAD 测其 R 4%） | 没有"正确截图"时，用跨宽度一致性当**隐式 oracle** |
| **SALAD** | 2024 ICSE | USC（Halfond 组） | 缩窄后 "loss of content and functionalities"；布局工具 "do not focus on the functional and interactive aspects" | 首个 RAF（响应式无障碍失败）自动检测 | 1280 与 320px 各做键盘爬取建交互模型，比较功能集合 | 62 页 559 RAF；P 85% / R 94%；ReDeCheck 18%/4% | 自认：功能分组粗、平均约 1 小时/页 / 我们：是功能丢失不是像素缺陷 | 从"好不好看"改成"还能不能完成功能" |
| **ReFLAIR** | 2026 FSE | UC Irvine（Sam Malek 组） | WCAG 要求 reflow 后信息与功能可达；现有工具 "static analysis that fails to capture how content is actually displayed" | 动态 reflow 检测；对比 7 基线；扩展到 36 页、平板、换 LLM | DOM+截图，**滚动+LLM 指导展开菜单**，两侧比对信息/功能控件 | 24 页 P 80.49% / R 95.31%；**去掉探索 P 降 40%**；约 $1.18/站 | 自认：多步交互漏、只测 320px / 我们：样本小，等价判断交给 LLM | **交互探索是关键**——与 UX-Agent 滑动验证思路最接近 |
| **多窗口 GUI 缺陷**（arXiv 2604.19081） | 2026 arXiv（未见录用） | 武汉理工 | 现有方法 "largely passive… designed for conventional full-screen"；FAB/角标重叠 "may either indicate a true defect or reflect intentional design" | 主动触发分屏/折叠；SoM+MLLM 检测解释；首个多窗口 benchmark（50 应用） | DroidBot 改造 → SoM 标记 → Qwen2.5-VL-32B LoRA + CoT | 截断 +184%；截断 F1 73.1%（**低于 YOLO 73.4%**）；遮挡 F1 87.2% | 自认：效率、连续交互 / 我们：截断没赢；意图 vs 缺陷仍靠 VLM 猜 | 折叠/分屏放大缺陷，要主动触发 |
| **OpenHarmony UI Overlap / HCO-Eye** | 2025 ASE Industry Showcase | 北航（Li Li 组） | 重叠既是 "necessary means… rich visual hierarchies" 又是 overdraw 根源；"lack of systematic, data-driven understanding" | 100 个鸿蒙应用实证；三层分类；HCO-Eye + HCOBench | 组件树几何统计；前后帧截图+组件树 diff → VLM CoT | 99.6% 是父子重叠；静态兄弟重叠中 23.7% 是缺陷；HCOBench F1 93.12% | 自认：随机探索低估、只鸿蒙 / 我们：只抓"高成本遮挡"，不管截断 | **大多数重叠是设计，不是 bug**——直接支撑"区分意图与缺陷" |
| **UI-Lens** | 2026 CVPR | 浙江大学 | 模型 "struggle with… whether content is partially rendered or merely obscured"；现有评测靠 RICO | 4,759 页中文基准（11 商业应用、21 设备）；6 类任务；9 模型评测 | 真实采集 + 设计师合成正例；只给截图 | Text Overflow 平均 F1 22%；跨页不一致 11%；提示工程仅 +0.6~2.5 | 自认：把可滚动裁切当缺陷、分不清设计意图 / 我们：只评测不提方法 | **通用 MLLM 看单帧分不清截断**——UX-Agent 的最强外部证据 |
| **Minuku** | 2025 ASE Industry Showcase | 复旦 + 美团 | 现有工具 "rely on a vast amount of high-quality training data"；VLM "lack task-specific knowledge" | 常识模拟 + 微调 VLM（细节 UNVERIFIED） | UNVERIFIED | 美团部署发现 40 个未知问题 | 全文未获得 | 小数据也能抓显示问题 |
| **Can LLMs Detect Display Issues?** | 2025 UIST Adjunct | 全北国立大学 | 提示技术效果 "has not been systematically analyzed" | 比较 7 种提示策略 | GPT-4 看截图 | 4-shot+CoT 遮挡 F1 0.86；错位 P 0.33 | 自认：仅靠提示解决不了错位 / 我们：样本小、无定位 | 提示能补明显坏图，补不了细微问题 |
| **RotDroid** | 2026 ISSRE（arXiv 2608.25425） | 北航 | 单视图方法 "cannot capture cross-orientation inconsistencies" | 898 条旋转 issue 实证；RotBench + RotVL；状态保持序列 | 构造等价竖/横屏对 → 微调 VLM 比较 | RotVL F1 85.29%（GPT-5.2 70.84%）；72 提交 47 确认 | 自认：服务端状态、动态内容误报 / 我们：只覆盖旋转 | **构造"应等价"的两态再比较**——又一个差分 oracle |

### 从 A 表能直接读出的三点（给你和师妹讨论用）
1. **oracle 三条路线**：单帧视觉分类（OwlEye/Nighthawk/UI-Lens）→ 差分/等价比较（dVermin、ReDeCheck、RotDroid）→ 交互探索（ReFLAIR、SALAD、多窗口）。近两年明显在往后两条走。
2. **共同未解决的问题**：分不清"故意设计"和"缺陷"（HCO-Eye、UI-Lens、多窗口论文都自己承认）。
3. **UX-Agent 的位置**：布局几何证据 + 可恢复的主动滑动验证，正好落在"交互探索 + 区分意图"的交叉点；最接近的对手是 ReFLAIR（Web）和多窗口论文（Android，截断没赢 YOLO）。

## B. LLM 用于 GUI 测试

| 论文 | 年份·venue | 第一作者机构 | 动机（原文） | 贡献（原文要点） | 方法 | 实验/关键数字 | gap（作者自认 / 我们看到） | 一段话叙事 |
|---|---|---|---|---|---|---|---|---|
| **GPTDroid** Make LLM a Testing Expert | 2024 ICSE | 中科院软件所（Zhe Liu） | 学习式方法 "low testing coverage, inadequate generalization… heavy reliance on training data" | 把 GUI 测试 "formulate… to an interactive question & answering task"；functionality-aware memory | view hierarchy 转 prompt → LLM 出动作 → 功能记忆 | 93 应用；activity 覆盖 75%（+32%）；53 新崩溃，35 修复 | 自认：记不住早期探索 / 我们：不看截图，oracle 只有崩溃 | 把测试员换成会聊天的 LLM |
| **VisionDroid**（arXiv 名 Trident） | 2025 TSE（ICSE 2026 journal-first） | 中科院软件所 | 测试 "limited to detecting crash bugs"；非崩溃错误需看 "a sequence of screenshots" | 非崩溃 bug 检测变成多模态问答；explorer/monitor/detector | 截图标框 → MLLM 探索 → 功能结束时先说预期再判 | 590 bug；P 50–72% / R 42–52%；43 新 bug，31 修复 | 自认：跨平台待深入 / 我们：鸿蒙仅 10 应用，可能幻觉 | **LLM 当功能 oracle**：先说预期再判对错 |
| **DroidAgent** | 2024 ICST | KAIST | 工具 "target lower level adequacy metrics"，开发者要的是 feature 级测试 | 自主设任务并执行的 Android 测试智能体 | Planner/Actor/Observer/Reflector + 记忆 | 15 应用；activity 覆盖 61% vs 51% | 自认：只跑一次、可能数据污染 / 我们：无功能 oracle | 从"刷覆盖率"变成"测用户意图" |
| **AUITestAgent** | 2024 arXiv（未录用） | 复旦（美团实习） | 需求 "typically written in natural language"，脚本跟不上迭代 | 首个自然语言需求驱动的 GUI 测试工具；工业验证 | 需求拆成交互+校验点；从控件/页面/轨迹三维取证 | oracle 准确率 0.90；美团每轮回归省 1.5 人日，4 新 bug | 自认：交互与校验解耦做不了交叉需求 / 我们：正文有占位数字 | 一句话需求 → 自动回归 |
| **GTArena** | 2024 arXiv（未录用） | 浙江大学 | GUI 测试智能体 "lack standardized evaluation metrics" | 统一基准：意图生成、执行、缺陷检测 | POMDP 形式化；真实/注入/合成缺陷 | 任务成功 GPT-4o 16% vs 人 90%；缺陷召回约 14% | 自认：模型偏向答"无缺陷" / 我们：arXiv 与项目页版本不一致 | 现成大模型离"自主测试员"很远 |
| **LLMigrate** | 2025 ISSTA | UC Irvine | 旧迁移方法 "struggled to accommodate real-world variations" | 首个用多模态 LLM 跨应用迁移 UI 测试，无需源码 | 源测试抽象成自然语言 → 目标应用边看边生成动作与断言 | 成功率 97.5%；省 91.1% 工作量 | 自认：toast、不可逆操作 / 我们：oracle 只有出现/不可见 | 测试不该每个 app 重写 |
| **HmTest** | 2025 JCST | 南方科技大学 | 鸿蒙应用如何自动测试 "has become a crucial task" | 页面跳转图定向探索 + 强化学习 | 源码静态分析 + RL（**不是 LLM**） | 9 应用，覆盖优于 Wukong/DevEco（数字 UNVERIFIED） | 自认：大模型留作未来 / 我们：要源码 | 鸿蒙缺的是页面模型 |
| **Android→OpenHarmony 迁移实证** | 2026 arXiv 2607.11245 | 哈工大（深圳） | "neither proposes solutions tailored for OpenHarmony nor provides a systematic evaluation" | 首个迁移实证；36 应用 108 用例基准；ITeM-HM | 改提示 + ArkUI 功能控件组 + 鸿蒙手势 | 现有方法 15%/26% → ITeM-HM 81%；失败 46% 来自架构差异 | 自认：只测核心功能 / 我们：匿名仓库 | **ArkUI 与 Android 结构不同**——鸿蒙专属证据 |
| **LLMDroid** | 2025 FSE | 华中科技大学 | LLM 测试 "time inefficiency and high costs due to constant LLM querying" | 覆盖停滞时才叫 LLM 的增强框架 | 原工具探索 + 低增长时 LLM 导航 | 代码覆盖 +26%；GPT-4o mini $0.03/小时 | 自认：插桩崩溃 / 我们：依附宿主工具 | LLM 从驾驶员变导航员，省钱 |
| **BugHunter** | 2025 FSE | 中科院软件所 | "similar apps often encounter similar bugs"，现有方法只追覆盖 | 用 13 万份历史缺陷报告做 RAG 引导探索 | 报告挂到页面转移图 → 检索 → MLLM 改写步骤 | 已知 bug 召回 64%（GPTDroid 40%）；49 新崩溃 | 自认：数据泄漏 / 我们：只针对崩溃 | 去别人摔过跤的地方 |
| **GUIPilot** | 2025 ISSTA | 上海交大 / NUS | 工业要查与设计稿的 "deviations in screen layout, widget position, or GUI transition" | 首个面向设计稿的端到端 GUI 测试 | 控件编辑距离对齐 + VLM 按稿执行转移 | 80 应用；工业 9 个偏差全确认（摘要与引言 P/R 数字矛盾） | 自认：依赖 OpenAI / 我们：需要设计稿 | **设计稿就是 oracle** |
| **AndroB2O** | 2025 ASE | Univ. of Minnesota | 功能失败的 oracle "creation… remains" 缺自动化 | 从 bug 报告生成断言式 oracle；首个数据集 | 报告 + 出错屏 → 相关控件 → 断言 | 152 失败，61.2% 可识别（仅摘要） | 全文未打开 | 从"点出 bug"挪到"写成断言" |
| **ScenGen** | 2026 TOSEM（ASE 2026 journal-first） | TUM Heilbronn / 南京大学 | 测试与 "underlying app business logic" 有缺口 | 场景驱动多智能体；CV+MLLM 控件定位 | 五角色闭环，Supervisor 核对并回滚 | 99 任务完成率 84.85%；定位 97.76% | 自认：场景有限、不稳定 / 我们：场景人给，bug 数未确认 | 覆盖率高 ≠ 业务做完 |
| **TUSR** | 2026 FSE | 南京大学 | 界面与交互改变 "render scripts… obsolete" | 首个按测试单元修复脚本的框架 | MLLM+规则切分 → 按单元 CoT 修复 + 反思 | 262 脚本；动作 95% / 脚本 89% | 自认：切分难 / 我们：无成本报告 | 一个意图由一串动作完成，不能逐步修 |

### 从 B 表能读出的
1. 主流叙事从"LLM 探索提覆盖"（GPTDroid、LLMDroid）转向"**LLM 当 oracle**"（VisionDroid、AUITestAgent、AndroB2O、GUIPilot）。
2. 中科院软件所 Zhe Liu / Qing Wang 组一条线贯穿 OwlEye→Nighthawk→GPTDroid→VisionDroid→BugHunter，是这个方向最该先读的组。
3. 鸿蒙相关的工作很少，且都是测试生成或迁移（HmTest、2607.11245）；**鸿蒙上的显示缺陷检测几乎空白**，只有 HCO-Eye 做重叠。

## C. 非崩溃功能 bug oracle
见 `raw/oracle-non-crash.md`。B 表已核实其中两篇：VisionDroid（TSE 2025）、AndroB2O（ASE 2025）。

---

## D. 对 Testing-Survey 的评价（和师妹语音时可以照着说）

**现状**：catalog 只有 6 列（编号、标题、年份、venue、对应问题、笔记链接），4 篇里 3 篇是综述，最新的实证论文缺失；notes 每篇 235–371 行，`field.md` 1,393 行概念教程。

**问题**：
1. 读综述多、读原始论文少，看不出"别人具体怎么做、差在哪"；
2. 单篇笔记太长，没人会回头读，也没法横向比较；
3. 没有机构、动机原文、gap、叙事这些列，没法用来找选题。

**建议**（说的时候用商量语气）：
1. 以本表为模板，主表放在 `catalog.md`，每篇一行；单篇笔记变成可选，限 50 行以内；
2. 只收 2024–2026 的原始论文，综述只留 1–2 篇当入口；
3. 分工：她负责按模板填 B、C 两类新论文，每周 3–5 篇；动机和贡献必须贴原文，venue 必须在 DBLP 或会议页核实；
4. 每两周一起看一次表，只讨论 gap 列。
