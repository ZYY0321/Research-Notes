# OpenMobile 论文详细解读

## 基本信息

| 项目 | 内容 |
|------|------|
| **论文标题** | OpenMobile: Building Open Mobile Agents with Task and Trajectory Synthesis |
| **arXiv** | [2604.15093](https://arxiv.org/abs/2604.15093) |
| **提交日期** | 2026年4月16日（work in progress） |
| **作者** | Kanzhi Cheng, Zehao Li, Zheng Ma, Nuo Chen, Jialin Cao, Qiushi Sun, Zichen Ding, Fangzhi Xu, Hang Yan, Jiajun Chen, Luu Anh Tuan, Jianbing Zhang, Lewei Lu, Dahua Lin |
| **机构** | 南京大学、商汤科技、南洋理工大学、上海AI实验室、香港大学、西安交通大学 |
| **开源** | [GitHub](https://github.com/njucckevin/OpenMobile-Code)、[HuggingFace模型](https://huggingface.co/cckevinn/OpenMobile-8B)、[数据集](https://huggingface.co/cckevinn/OpenMobile-Data) |

---

## 核心问题

闭源移动端agent（GPT-4o/Gemini）在AndroidWorld上达~70%成功率，而开源方案仅~30%。**瓶颈在于缺乏高质量训练数据**——包括多样化任务指令和包含错误恢复模式的轨迹数据。

---

## 技术方法

### 阶段一：可扩展的任务合成（Scalable Task Synthesis）

核心创新：**将探索与指令生成解耦**

1. **环境探索（Random Walk Exploration）**
   - 每次session随机探索10步，生成屏幕-动作转换序列
   - 重点不在探索效率，而在数据的组织与使用方式

2. **全局环境记忆构建（Global Environment Memory）**
   - 使用感知哈希（pHash）聚类视觉相似屏幕（阈值τ=0.95）
   - VLM提取每个UI元素的功能描述
   - 建立邻接关系图（直接可达的屏幕）
   - 构建语义embedding索引支持跨屏幕功能检索

3. **记忆增强的任务合成（Memory-Augmented Task Synthesis）**
   - 焦点屏幕及其功能标注
   - 短期记忆：转换图中的相邻屏幕
   - 长期记忆：语义相关但距离较远的功能（最多30项，带多样性过滤）
   - 这种检索机制鼓励**跨功能组合**，是单轨迹方法所缺乏的

### 阶段二：策略切换的轨迹采集（Policy-Switching Rollout）

交替使用学习者模型（πl）和专家模型（πe）：

- **错误干预切换（Error-Intervention Switching）**：监控器（Gemini-3.1-Pro-Preview）观察动作历史，检测学习者偏离时专家介入纠正
- 捕获标准模仿学习中缺失的**错误恢复信号**
- 消融实验：error-intervention switching每条轨迹平均1.56次错误恢复 vs 纯专家蒸馏0.42次

---

## 数据集规模

| 指标 | 数值 |
|------|------|
| 合成任务指令 | 2,800条 |
| 动作步骤 | 34,000个 |
| 覆盖应用 | 20个Android应用 |
| 平均轨迹长度 | 12.2步 |
| 每步平均推理 | 129词 |

---

## 主要实验结果

| 模型 | AndroidWorld | AndroidLab | MobileWorld |
|------|-------------|------------|-------------|
| Qwen2.5-VL-7B + OpenMobile | **51.7%** | - | - |
| Qwen3-VL-8B + OpenMobile | **64.7%** | **51.5%** | **17.7%** |
| ScaleCUA (开源baseline) | 27.2% | - | - |

在三个benchmark上均大幅超越现有开源方法，AndroidWorld上接近闭源商用系统。

---

## 污染分析

- 仅3.5%合成指令与AndroidWorld测试集语义相似度>0.7
- 移除最相似的10%指令后性能仅边际下降
- 功能覆盖度分析证实提升来自广泛的原子功能覆盖，非测试集过拟合

---

## 局限性

1. 监控器依赖Gemini-3.1-Pro-Preview闭源模型（完全开源pipeline的妥协）
2. 仅覆盖20个Android应用，更广泛应用生态的泛化未充分验证
3. 2,800条指令规模相对较小
4. Random walk探索可能无法覆盖深层或需特定前置条件的功能
5. 论文标注"work in progress"，trajectory synthesis和training code标注"Coming soon"

---

## 同一作者的研究脉络

| 时间 | 工作 | 贡献 |
|------|------|------|
| 2024 | **SeeClick** | 纯视觉GUI grounding预训练，提出ScreenSpot benchmark |
| 2024 | **OS-Atlas** | 最大开源跨平台GUI grounding语料库（1300万+元素） |
| 2024 | **OS-Genesis** (ACL 2025) | 逆向轨迹收集：先交互后回溯生成任务 |
| 2025 | **OS-Sentinel** | Mobile GUI agent安全性，混合验证方法 |
| 2026 | **OpenMobile** | 全流程开源数据合成框架（本论文） |

OpenMobile是OS-Genesis的进化版——OS-Genesis提出"先交互后生成任务"的逆向思路，OpenMobile进一步引入全局环境记忆和策略切换机制提升数据质量。
