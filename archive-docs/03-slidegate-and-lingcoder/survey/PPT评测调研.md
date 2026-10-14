# 论文/系统：PPTAgent (EMNLP 2025)
- 发表渠道与来源：EMNLP 2025，arXiv (2501.03936)
- 评估维度：Content、Design、Coherence
- 具体计算方式 / 评分细节：采用 PPTEval 框架。
  1. Content（内容）：评估文本信息是否具影响力且是否得到图像的支持。
  2. Design（设计）：评估设计是否连贯，是否存在视觉重叠（Overlap）或越界（Out-of-Bounds）的问题。
  3. Coherence（连贯性）：评估逻辑结构是否存在瑕疵。
  评分方式：使用微调后的多语言大模型（MLLM，如 GPT-4o）对每个维度进行 1-5 分量表打分，并计算平均值。
  计算流程：① 使用 MLLM 提取幻灯片的内容和逻辑结构；② 对提取结果基于预设的评分 Rubric（评分准则）进行打分。
- 代码仓库资源：包含完整的评估框架（提示词）
- 备注：基于 LLM 的主观评分，易受 Prompt 影响。

# 论文/系统：SlidesGen-Bench (Arxiv 2025)
- 发表渠道与来源：arXiv (2601.09487)
- 评估维度：Content、Aesthetics、Editability
- 具体计算方式 / 评分细节：
  1. Content（内容）：将生成的幻灯片解析为结构化的 Markdown 文档，然后使用 LLM 评估器仅基于幻灯片内容回答 QuizBank 中的问题，准确率直接作为内容质量的代理指标。
  2. Aesthetics（美学）：包含四个客观指标：
     ① 和谐度 (Harmony)：检测文本、图像等元素之间的相互遮挡或越界（Overlap/Out-of-Bounds），使用 PP-DocLayout_plus-L 模型进行检测；
     ② 可用性 (Usability)：评估元素的可交互性（如图表是否可点击、动画是否易于操作）；
     ③ 吸引力 (Attractiveness)：基于视觉层次和配色方案进行打分；
     ④ 视觉节奏 (Visual Rhythm)：评估页面间视觉元素的节奏感（如动画过渡、留白分配）。
  3. Editability（可编辑性）：引入“演示文稿可编辑性智能 (PEI)”框架，验证复杂元素是否被正确分组（Group），以避免编辑时碎片化。
- 代码仓库资源：采用了 PP-DocLayout_plus-L 进行客观检测。
- 备注：无

# 论文/系统：SlideAudit (UIST 2025)
- 发表渠道与来源：UIST 2025，arXiv (2508.03630)
- 评估维度：Composition & Layout、Typography、Color 等
- 具体计算方式 / 评分细节：采用 Taxonomy（分类法）+ LLM 判断。
  1. 分类法：共包含 27 个详细缺陷类别，组织在 5 大维度下（Composition & Layout、Typography、Color 等）。
  2. 评估方式：基于 Prompt 使用 LLM 判断幻灯片是否存在这些缺陷，返回 Yes/No 判断。
  3. 维度示例：
     ① Composition & Layout：检测布局是否混乱、对齐是否错误；
     ② Typography：检测字号不一致、字距过大/过小、层级结构缺失；
     ③ Color：检测配色冲突、对比度不足、颜色过多等。
- 代码仓库资源：无
- 备注：提供了最细粒度的设计缺陷分类，是目前最细致的检测标准；但也仅提供了分类标准，用 LLM as judge 的方法做了简单的一致性分析。

# 论文/系统：PPTC Benchmark (ACL 2024)
- 发表渠道与来源：ACL 2024 (Findings)，arXiv (2311.01767)
- 评估维度：属性内容检查、空间位置检查
- 具体计算方式 / 评分细节：Reference-Based 参考指标。
  ① Element Matching：计算生成幻灯片与参考幻灯片中匹配元素（Textbox、Image、Shape）的总大小占比。
  ② Content Similarity：
     - 文本：使用 Sentence-Transformer (MiniLM-L6-V2) 计算余弦相似度。
     - 图像：使用 CLIP Score 评估图像相似度。
  ③ Color Similarity：使用 CIEDE2000 公式量化感知颜色差异。
  ④ Position Similarity：将坐标归一化至 [0,1]，计算曼哈顿距离。
- 代码仓库资源：无
- 备注：强调了基于 Ground Truth 的客观评估，不依赖于 LLM 主观判断。

# 论文/系统：LecEval (arXiv 2025)
- 发表渠道与来源：arXiv (2505.02078)
- 评估维度：Content Relevance、Expressive Clarity、Logical Structure、Audience Engagement
- 具体计算方式 / 评分细节：基于 Rubric 的 LLM 评估。
  1. Content Relevance (CR)：评估幻灯片内容与主题的相关性。
  2. Expressive Clarity (EC)：评估表达的清晰度（如文字是否简洁、是否有冗余）。
  3. Logical Structure (LS)：评估逻辑结构是否清晰。
  4. Audience Engagement (AE)：评估内容是否能吸引受众（基于 Mayer 的多媒体学习理论）。
  评分方式：使用 LLM 进行 1-5 分评分，并计算平均分。
- 代码仓库资源：无
- 备注：专注于教育学视角的知识传递质量。

# 论文/系统：EvoPresent (Arxiv 2025)
- 发表渠道与来源：arXiv (2510.05571)
- 评估维度：内容准确性、设计合理性
- 具体计算方式 / 评分细节：
  全局指标：
  1. 困惑度 (Perplexity, PPL)：评估叙事连贯性（基于语言模型的困惑度）。
  2. ROUGE-L：评估文本内容的保真度（与参考稿件的重叠度）。
  3. 布局平衡性 (Layout Balance)：评估视觉布局的平衡度。
  4. 美学分数 (Aesthetic Scores)：基于 PresAesth 模型的评分，范围通常为 1-10 分。
  细粒度指标：
  1. 困惑度 (Perplexity)：叙事连贯性。
  2. 平衡度 (Balance)：视觉布局平衡。
  3. ROUGE-L：内容相似度。
  4. 训练模型打分：基于 Reinforcement Learning (RL) 的自我改进反馈。
- 代码仓库资源：只有美学模型训练代码（无全部已标注数据）
- 备注：引入了 PresAesth 多任务 RL 美学模型，强调自我改进 (Self-Improvement) 能力。

# 论文/系统：AutoPresent (CVPR 2025)
- 发表渠道与来源：CVPR 2025，arXiv (2501.00912)
- 评估维度：Reference-Based Metrics（参考指标）、Reference-Free Metrics（无参考指标）、Executability（可执行性）
- 具体计算方式 / 评分细节：
  Reference-Based：
  ① Element Matching：匹配元素总大小比率。
  ② Content Similarity：文本余弦相似度 / 图像 CLIP 分数。
  ③ Color Similarity：CIEDE2000 颜色差异。
  ④ Position Similarity：归一化曼哈顿距离。
  Reference-Free：
  ① 受 Slide Design Principles 启发，四个子维度均采用 0-5 分量表：
     - Text：检查标题、正文是否简洁、格式是否统一。
     - Image：检查图片是否高质量、是否与内容匹配。
     - Layout：检查元素是否在幻灯片内、是否重叠、是否对齐。
     - Color：检查颜色对比度、是否使用刺眼颜色。
  Executability：统计生成的 PPTX 程序能否成功运行，防止生成无效代码。
- 代码仓库资源：大量指令-代码训练数据
- 备注：与 PPTC 类似，但更加专注于从头设计结构化视觉元素；无参考还是用的 0-5 量表评估。

# 论文/系统：PPTArena
- 发表渠道与来源：arXiv:2512.03042v2
- 评估维度：指令遵循度（IF, Instruction Following）、视觉质量（VQ, Visual Quality）
- 具体计算方式 / 评分细节：两大核心维度均采用 0-5 分整数评分制（0 分 = 完全失败，5 分 = 完美执行）。
  指令遵循度（IF）评分标准：
  - 5 分：所有请求的修改完全准确执行，无遗漏、无错误，无额外无关修改；
  - 4 分：核心修改全部完成，仅存在不影响语义的微小偏差；
  - 3 分：大部分修改完成，但至少 1 项关键任务不完整或存在细节错误；
  - 2 分：仅完成部分核心修改，存在明显遗漏或错误应用；
  - 1 分：大部分请求未执行或执行结果严重偏离指令；
  - 0 分：完全无视指令或修改结果与指令冲突。
  视觉质量（VQ）评分标准：
  - 5 分：无意外修改，字体、尺寸、颜色、位置与目标完全一致，结构完整保留；
  - 4 分：视觉效果与目标高度接近，仅存在亚像素级对齐等可忽略差异，无样式偏移；
  - 3 分：存在轻微可见差异（如字体粗细、间距微调），但不破坏整体布局；
  - 2 分：存在明显偏差（如字体错误、位置偏移）或轻微布局问题；
  - 1 分：严重布局问题（如元素重叠、超出画布），但内容仍可辨认；
  - 0 分：幻灯片完全损坏或无法阅读。
- 代码仓库资源：无
- 备注：针对多维度编辑任务的评估体系。

# 论文/系统：DECKBench（KDD ’26）
- 发表渠道与来源：KDD 2026，arXiv:2602.13318v1，华为加拿大研究院+英属哥伦比亚大学，代码数据开源：https://github.com/morgan-heisler/DeckBench
- 评估维度：三级评估维度
  1. 幻灯片级：语言流畅性、内容保真度、文本/图表相似度、布局质量
  2. 幻灯片集级：全局语言流畅性、整体内容保真度/覆盖率、结构对齐度、叙事过渡连贯性
  3. 多轮交互级：多轮编辑的结构收敛度、叙事结构收敛度（每级均含无参考指标+有参考指标）
- 具体计算方式 / 评分细节：
  1. 预处理：将生成幻灯片与真实幻灯片对齐，解决数量/顺序不一致问题。
  2. 幻灯片级指标：
     「无参考」：①困惑度（PPL）计算文本流畅性；②保真度=幻灯片与源论文最相似片段的余弦相似度。
     「有参考」：①文本相似度=对齐后文本嵌入余弦相似度；②图表相似度=CLIP-ViT-base-patch32计算视觉相似度；③布局质量直接评估布局合理性。
  3. 幻灯片集级指标：
     「无参考」：①集级困惑度=所有幻灯片文本拼接后的PPL；②集级保真度=幻灯片-论文片段相似度平均值；③集级覆盖率=论文片段-幻灯片相似度平均值；④LLM-as-a-judge评估全局连贯性/叙事质量。
     「有参考」：①DTW（动态时间规整）软对齐序列，值越低结构越相似；②过渡相似度评估嵌入序列演进匹配度；③LLM-as-a-judge结合真实集评估内容完整度/结构对齐。
  4. 多轮交互级指标：
     「有参考」：①ΔDTW=前一轮DTW-当前轮DTW，值越高结构收敛越好；②Δ过渡相似度=前一轮过渡相似度-当前轮过渡相似度，值越高叙事收敛越好。
- 代码仓库资源：无
- 备注：没有涉及视觉评估。

# 论文/系统：PPTBench
- 发表渠道与来源：arXiv 2025‑12，中科大 “PPTBench: Towards Holistic Evaluation of Large Language Models for PowerPoint Layout and Design Understanding”
- 评估维度：1) Detection、2) Understanding、3) Modification、4) Generation
- 具体计算方式 / 评分细节：
  Detection: Accuracy – 对元素提取与分类的准确匹配率（与 JSON ground truth 一致率）。
  Understanding: 多项选择题准确率（模型回答与人工标注一致率）。
  Modification: 含元素修改、文本修改、布局优化 3 个子任务，修改后 JSON 结构与 ground truth 一致率（Exact match accuracy）。
  Generation: LLM Judge 评分机制 – 基于 rubric 的 0‑5 级评分映射为 0‑100 分（LLM 评价幻灯片评估内容清晰度、布局合理性、视觉设计等）。与人类评估 Spearman 相关系数可达 0.86-0.89。
- 代码仓库资源：无
- 备注：叙事重点在“全流程评估”以及视觉布局的评估（因此配套数据集是有 json 语义结构信息的）；任务有明确 ground truth，“结构化 JSON + 幻灯片截图”双模态输入形式。

# 论文/系统：PresentBench
- 发表渠道与来源：arXiv 2026‑03，清华“PresentBench: A Fine‑Grained Rubric‑Based Benchmark for Slide Generation”
- 评估维度：五大维度
  1) Presentation Fundamentals
  2) Visual Design & Layout
  3) Content Completeness
  4) Content Correctness
  5) Content Fidelity
- 具体计算方式 / 评分细节：Checklist Binary 项目 – 每个实例约 54 个 atomic binary 判断项，每项回答是/否；
  Aggregation Protocol: 将 binary 项目结果基于预设权重或简单求和/平均聚合成总体评分（内部采用 MLLM 执行 checklist 判断并生成解释证据）。各维度由 checklist item 细分测量，如文本逻辑流、版式规范、真实背景材料对应等。
  PresentBench 的评估结果与人类偏好的 Spearman 相关系数达 0.532，显著优于传统的“LLM-as-a-Judge”（0.258）和 PPTEval（0.303）。
- 代码仓库资源：Coming soon
- 备注：这个和我们做的挺像的；每个实例根据背景材料与任务 instruction 出发设计独立 checklist，每个模块包含原子级二进制评估项。

# 论文/系统：VLM‑SlideEval
- 发表渠道与来源：arXiv 2025‑10，微软“VLM‑SlideEval: Evaluating VLMs on Structured Comprehension and Perturbation Sensitivity in PPT”
- 评估维度：1) Element‑Level Extraction、2) Robustness to Controlled Perturbations、3) Narrative / Deck Order Understanding
- 具体计算方式 / 评分细节：
  Element Extraction: 基于元素匹配的 F1 / IoU 等指标评估预测的几何位置、文本内容与 ground truth 的一致性；
  Perturbation Sensitivity: 使用 R²、POAadj（比例的降级一致性指标）、Spearman(severity, score) 衡量评分对扰动的敏感性；
  Narrative Order: 打乱幻灯片顺序后，要求模型重新排序，采用 Kendall’s τ、Spearman’s ρ、Exact Match 评估模型对 PPT 叙事逻辑的理解能力。
- 代码仓库资源：有 zenodo PPT 数据集
- 备注：需要完整 PPTX 文件数据集；三个 GAP：一是像素级精确提取能力不足，对应第一个指标；二是对幻灯片特有的几何、样式、文本扰动的鲁棒性未知，对应第二个指标；三是缺乏对跨幻灯片叙事逻辑的评估，对应第三个指标。