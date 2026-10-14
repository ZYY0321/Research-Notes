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
（检索中，完成后补入）

## C. 非崩溃功能 bug oracle
见 `raw/oracle-non-crash.md`，待核实后并入本表。
