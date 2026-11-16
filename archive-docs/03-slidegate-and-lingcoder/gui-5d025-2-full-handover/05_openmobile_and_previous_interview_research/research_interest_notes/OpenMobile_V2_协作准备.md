# OpenMobile V2 合作准备手册

> 用途：与OpenMobile作者会面前的知识储备 + 提问框架  
> 工期预期：四个月，每天≥3小时（约360小时总工时）

---

## 一、领域基础知识地图

### 1.1 核心概念体系

```
Mobile Agent（移动端智能体）
    ├── 输入：手机截图（screenshot）
    ├── 感知：Vision-Language Model (VLM) 看懂屏幕
    ├── 动作：click / type / scroll / swipe / long_press
    └── 目标：自动完成用户的自然语言指令（"帮我订一张机票"）

训练数据的两个核心要素：
    ├── Task Instruction（任务指令）：告诉agent要做什么
    └── Trajectory（轨迹）：一步一步的操作记录，含截图+动作+推理思维链
```

### 1.2 数据获取的三条路线（重要背景）

| 路线 | 代表工作 | 优点 | 缺点 |
|------|---------|------|------|
| **人工标注** | AndroidControl, AMEX | 质量可控 | 昂贵、耗时、规模受限 |
| **专家蒸馏** | OS-Genesis, ScaleCUA | 质量高 | 只有"理想行为"，缺错误恢复 |
| **自我进化(Self-Evolution)** | UI-TARS系列 | 分布匹配 | 收敛慢，受模型上限约束 |
| **策略切换（OpenMobile创新）** | **OpenMobile** | 兼顾质量+错误恢复 | 依赖闭源expert |

### 1.3 关键技术术语速查

| 术语 | 解释 |
|------|------|
| **SFT** | Supervised Fine-Tuning，监督微调，用标注轨迹直接训练 |
| **RL / RLHF** | 强化学习，模型自己探索并根据成功/失败更新 |
| **VLM** | Vision-Language Model，多模态大模型（Qwen3-VL, GPT-4o等） |
| **GUI Grounding** | 把文本描述映射到屏幕坐标（点哪个按钮） |
| **Pass@1 / Pass@3** | 1次/3次机会内完成任务的成功率 |
| **pHash** | 感知哈希，用于判断两张截图是否"同一屏幕" |
| **Chain-of-Thought (CoT)** | 每步操作前的文字推理过程，训练时一起学 |
| **Policy Switching** | OpenMobile核心：学习者犯错时专家介入纠正 |
| **Error Recovery** | 从错误中恢复的能力，是v1和闭源系统的最大差距点 |
| **Data Contamination** | 训练数据与测试集重叠，导致虚假高分 |

---

## 二、OpenMobile V1 深度拆解

### 2.1 解决的核心问题
- **现象**：闭源系统（GPT-4o, Gemini）在AndroidWorld约70%，开源约30%，差距巨大
- **根因**：不是模型能力不够，而是**训练数据质量**太差（无多样任务指令 + 无错误恢复轨迹）

### 2.2 两大技术贡献

**贡献1：解耦的任务指令合成**
```
传统方式：探索一条轨迹 → 从这条轨迹生成任务（多样性受限于单条路径）

OpenMobile：
  Step1: 随机游走探索（收集屏幕转移数据）
  Step2: 构建全局环境记忆 M = (S, N, F)
         - S：唯一屏幕集合（pHash去重）
         - N：屏幕邻接关系图
         - F：每屏幕上的UI功能描述（VLM提取）
         + 语义embedding索引支持跨屏检索
  Step3: 以"焦点屏幕+短期记忆邻居+长期语义相关功能"为上下文
         → 让VLM生成跨功能的复杂组合任务
```

**贡献2：策略切换轨迹采集（Error-Intervention Switching）**
```
专家蒸馏：expert全程操作 → 只有完美轨迹，无错误恢复样本（avg 0.42次恢复/轨迹）
自我进化：learner自己探索 → 训练信号稀疏，收敛慢（avg 0.10次恢复/轨迹）
随机切换：按概率切换    → 噪声大，轨迹碎片化（avg 0.64次恢复/轨迹）
✅ 错误干预切换：
   - Learner默认执行
   - Monitor（Gemini-3.1-Pro-Preview）实时监控
   - 检测到偏离 → Expert介入纠正
   - avg 1.56次恢复/轨迹，性能最佳
```

### 2.3 数据集规模（V1）
- 2,800条任务指令
- 34,000个动作步骤
- 20个Android应用
- 平均轨迹长度：12.2步
- 每步平均推理：129词CoT

### 2.4 V1的主要实验结果

| 模型 | AndroidWorld | AndroidLab | MobileWorld |
|------|-------------|------------|-------------|
| **Ours-7B** (Qwen2.5-VL) | 51.7% | 22.7% | 14.8% |
| **Ours-8B** (Qwen3-VL) | **64.7%** | **51.5%** | **17.7%** |
| ScaleCUA (开源最强baseline) | 27.2% | 30.0% | 7.7% |
| Gemini-3-Pro (闭源) | 60.3% | - | 51.3% |
| MAI-UI-8B (工业闭源数据) | 70.7% | - | 27.5% |

### 2.5 V1的消融实验（做过哪些，供参考）
1. **任务合成策略对比**：OS-Genesis vs. 耦合baseline vs. OpenMobile（人工评估50对 + 1.5K轨迹训练性能）
2. **策略切换策略对比**：4种策略（专家蒸馏/自我进化/随机切换/错误干预切换）
3. **数据扩展曲线**：指令数量 → AndroidWorld性能变化
4. **污染分析**：合成指令与测试集相似度分布 + 删除最相似10%后的性能变化
5. **功能覆盖度分析**：指令数量 → 覆盖benchmark所需原子功能的比例

---

## 三、V1的局限性（即V2的机会点）

这些是论文自己承认的弱点，也是你们可能要改进的方向：

| # | 局限性 | 潜在V2方向 |
|---|--------|-----------|
| 1 | Monitor依赖**闭源Gemini**（违背"完全开源"愿景） | 用开源VLM替代Monitor；或设计规则based检测器 |
| 2 | 只覆盖**20个Android应用**，泛化未充分验证 | 扩展到更多应用；跨平台（iOS/Web/Desktop） |
| 3 | **2,800条指令**规模相对小（工业界可能数十万级） | 数据scaling；探索自动化程度更高的pipeline |
| 4 | **随机游走**探索效率低，难到达深层/需前置条件的功能 | 结构化探索（coverage-based）；人工演示辅助 |
| 5 | **MobileWorld性能**仍大幅落后（17.7% vs 33.3%） | 专门针对长视野跨App任务设计训练数据 |
| 6 | 没有充分探索**RL训练**（step-level/trajectory-level RL结果不显著） | 更好的RL reward设计；在线RL pipeline |
| 7 | 代码"Coming soon"，**轨迹合成和训练代码未完全开源** | 补全开源工程 |

---

## 四、做这类论文需要的实验清单（V2你可能要做的工作）

### 4.1 【核心工程实现类】（最耗时）

```
□ 搭建Android模拟器环境（AndroidWorld基础设施）
  - 配置AVD (Android Virtual Device)
  - 集成AndroidWorld评估框架
  - 测试任务初始化、执行、评估的完整流程

□ 实现/改进环境探索模块
  - 随机游走 OR 结构化探索策略
  - 屏幕转移序列记录

□ 构建全局环境记忆
  - pHash去重模块
  - VLM调用：UI功能描述提取
  - 邻接图构建
  - 语义embedding索引（FAISS/ChromaDB等）

□ 任务合成pipeline
  - Prompt工程：短期+长期记忆上下文组织
  - VLM生成任务指令
  - 质量过滤（model-based）
  - 去重（embedding相似度）

□ 轨迹采集pipeline（最复杂）
  - Expert模型接入（Gemini/开源替代）
  - Learner模型接入
  - Monitor模块（V2重点：开源化）
  - 切换逻辑控制
  - 轨迹存储格式设计
```

### 4.2 【模型训练类】

```
□ SFT训练
  - 环境配置（LLaMA-Factory）
  - 数据格式转换（轨迹 → 训练样本）
  - 超参数调优（lr, batch size, epoch）
  - 多个base model实验（Qwen2.5-VL / Qwen3-VL / 其他）

□ RL训练（可选，但可能是V2亮点）
  - Step-level RL
  - Trajectory-level RL
  - Reward函数设计（任务成功 vs. 中间奖励）
  - 在线RL数据飞轮
```

### 4.3 【评估实验类】

```
□ 主实验：三个基准测试
  - AndroidWorld（116 tasks × 20 apps）
  - AndroidLab（138 tasks × 9 apps）
  - MobileWorld（201 tasks，长视野+跨App）
  - 每个需要多次运行取均值（Pass@1 ± std）

□ 消融实验（每个变量都要跑完整评估）
  - 任务合成策略对比（V2的新方法 vs. V1 vs. baseline）
  - 策略切换策略对比（V2改进的Monitor vs. 旧版）
  - 数据规模消融（scaling curve）
  - RL vs. SFT对比

□ 分析实验
  - 数据污染分析（合成指令 vs. 测试集相似度）
  - 功能覆盖度分析
  - 错误恢复能力定量分析
  - Case study / 错误分析
```

### 4.4 【人工评估类】

```
□ 指令质量人工评估
  - Complexity（复杂度）pairwise比较
  - Soundness（合理性）pairwise比较
  - 通常需要50对，2-3名标注员，计算Cohen's Kappa

□ 轨迹质量标注
  - 错误恢复次数统计（人工抽样50条轨迹）
```

---

## 五、四个月工期规划参考

| 月份 | 核心目标 | 具体任务 |
|------|---------|---------|
| **第1月** | 环境搭建+复现V1 | 跑通AndroidWorld环境；复现V1数据合成pipeline；理解代码结构 |
| **第2月** | V2创新点实现 | 实现改进的探索策略/Monitor开源化/扩展更多App |
| **第3月** | 数据生成+训练 | 跑完整数据合成；SFT训练；初步评估；快速迭代 |
| **第4月** | 完整实验+写作 | 消融实验；分析实验；论文写作；代码整理开源 |

> **注意**：AndroidWorld每次评估一个模型需要数小时（116个任务×随机种子），多GPU并行是必要的。

---

## 六、与作者交流的关键问题框架

### 6.1 关于V2定位（最重要，优先问）

- "V2的核心贡献点是什么？相比V1主要改进哪几个方向？"
- "V2是否要解决Monitor闭源的问题？用什么方案替代Gemini？"
- "数据规模目标是多少？20个App → 多少个App？"
- "是否要扩展到其他平台（iOS/Web/Desktop）？"
- "V2是否要加入RL训练？V1中RL效果不显著的原因是什么？"

### 6.2 关于我的具体分工

- "我在这个项目中主要负责哪个模块？"（探索/合成/训练/评估/写作？）
- "我需要独立完成哪些实验？哪些是团队合作？"
- "我的机器资源是什么配置？是否有GPU集群？"
- "代码基础是什么？基于V1的codebase还是重写？"

### 6.3 关于工程细节

- "评估一次全量AndroidWorld大概需要多长时间？有多少GPU可以用？"
- "V1用的是哪个版本的Qwen3-VL？训练用了多少GPU？"
- "Monitor模块的具体prompt是什么？开源计划是什么时候？"
- "是否有预处理好的Android环境快照可以直接用？"

### 6.4 关于写作和投稿

- "目标投稿期刊/会议是什么？（NeurIPS/ICLR/ACL/EMNLP？）"
- "时间线是怎么安排的？截稿日期是什么时候？"
- "我是否参与论文写作？写哪些部分？"

---

## 七、需要提前学习的技术栈

| 优先级 | 内容 | 推荐资源 |
|--------|------|---------|
| ⭐⭐⭐ | **阅读V1完整论文**（重点看Appendix的实现细节） | arxiv.org/abs/2604.15093 |
| ⭐⭐⭐ | **AndroidWorld环境搭建** | github.com/google-research/android_world |
| ⭐⭐⭐ | **LLaMA-Factory训练框架** | github.com/hiyouga/LLaMA-Factory |
| ⭐⭐ | **Qwen3-VL使用** | HuggingFace模型页面 |
| ⭐⭐ | **FAISS向量检索** | 用于构建功能embedding索引 |
| ⭐⭐ | **OS-Genesis论文**（V1前身，理解逆向轨迹思路） | arxiv |
| ⭐ | **UI-TARS论文**（了解RL训练路线） | arxiv |
| ⭐ | **ADB (Android Debug Bridge)** | 控制模拟器的底层工具 |

---

## 八、你的核心优势定位建议

根据论文局限性，以下几个切入点适合深度参与：

1. **开源Monitor的设计**：用Qwen3-VL等开源模型替换Gemini作为Monitor，这是"完全开源"愿景的关键一步，也有独立贡献价值
2. **扩展应用覆盖**：将pipeline扩展到更多App，验证泛化性
3. **数据规模实验**：做更系统的scaling law分析
4. **MobileWorld专项优化**：针对长视野/跨App任务设计专门的数据合成策略

---

*最后更新：2026年5月22日*
