# WebHarbor：把 153 个真实网站做成离线 Docker 镜像，拿来评测，也拿来训 4B 网页 agent

## 一页读懂
| 项 | 内容 |
|---|---|
| 来源 | arXiv 2611.03634（2026-11-02 提交）/ venue：arXiv 预印本（正文标 "Preprint"）/ 作者署名 "WebHarbor Team and Contributors"（首页注明 Appendix A 有完整作者表，我没读）/ 代码 https://github.com/aiming-lab/WebHarbor（HTTP 200）；摘要称代码和数据公开 |
| 读深度 | 主文全读，附录 E（RL 配置、评测协议）读；环境构造细节（附录 C–D）未读 |
| 问题 | 真网站评测不可复现（内容变、被机器人检测拦、登录后的流程测不到）；已有合成环境视觉和功能深度不够 |
| 它检查了什么默认假设 | 「在线评测的分数代表能力」——作者实测 Online-Mind2Web 约 38% 任务被机器人检测挡住，WebVoyager 约 22% 任务过时（§1，p1） |
| 发现问题的方式 | 失败统计：自己跑一遍，数出多少任务因环境原因失败 |
| 解决方式 | 资源 + 训练：153 个可 Docker 运行的网站镜像、3,518 个任务；4B 模型在其中做 RL |
| 最强证据 | WebHarbor-4B 在 WebVoyager 81.2、Online-Mind2Web 70.4、均值 75.8，OpenWebRL-4B（在真网站上训的）为 74.1/67.0/70.6（表 6，p8） |
| 品味 | B：资源规模大、控制变量清楚（同一 SFT 起点、同一 GRPO 配方、只换环境），但奖励用的是 GPT-4.1 判官，和评测判官同族 |

## 一段话介绍
作者从 WebVoyager 和 Online-Mind2Web 覆盖的网站空间出发，用「任务驱动」的方式让编码 agent 复刻前端、后端、数据库和图片，人再逐站检查视觉保真、功能正确、数据真实、任务有效，直到通过。产物是 153 个离线网站和 3,518 个任务（含登录后、改状态、订票交易类）。他们拿同一个 SFT 检查点（OpenWebRL-4B-SFT），用同一套多模态 GRPO，只把训练环境从「704 个真实网站上的 2,102 个 WebGym 任务」换成 WebHarbor 的镜像，比较结果。

## 动机
原文（§1，p1）：

> "Even apparently functional environments may expose shortcuts, omit plausible alternative actions, or leak answers through their interfaces, undermining task validity."

## 方法（资源构成）
- 构造：任务先指定环境要支持的页面、数据、流程 → 编码 agent 用标准化「环境构造技能」实现 → 人类逐站审计并让 agent 修（Figure 2）。
- 规模：153 个环境、3,518 个任务；448 个交易/预订类，31.8% 需要登录，35.6% 修改持久状态，53.7% 需跨页推理（表 2，p6）。
- 泄漏检查（p6）：任务相似度——WebHarbor 到 Online-Mind2Web 的最近邻中位相似度只有 0.39。
- 训练（附录 E.3，表 22，p31）：2,288 个任务取自 123 个站点，**留出 15 个 WebVoyager 站点和另外 15 个站点**；每任务 5 条轨迹；100 次迭代；奖励是 OpenWebRL 的格式门 + **二值 GPT-4.1 成功判断**；WebHarbor 自己的验证器**只作诊断指标，不进策略目标**。

## 实验
- **表 6**：Qwen3-VL-4B-Thinking 基座 52.6 / 32.0 / 均值 42.3；OpenWebRL-4B-SFT 60.2/47.0/53.6；OpenWebRL-4B(RL) 74.1/67.0/70.6；WebHarbor-4B 81.2/70.4/75.8。表内开源模型最高 MolmoWeb-8B 均值 56.8；闭源最高 GPT-5 74.2（星号数字来自 OpenWebRL 论文，非本文复现）。
- **WebArena 子集（表 9）**：Overall 28.8 vs OpenWebRL-4B 20.4；去掉自动登录（WebArena-NL）后降 2.7 点（OpenWebRL SFT/RL 分别降 4.9/3.6）。Reddit 站所有模型都低于 12%，WebHarbor-4B 26 题只做对 1 题（p9）。
- **WebHarbor 测试集（表 8，306 题）**：WebHarbor-4B 验证器通过 30.0、Agent-Judge 41.5、两者一致率 87.0；GPT-6-Astra 的 GUI 模式两项都过 95%（饱和）。
- **按能力分组（图 5）**：登录 +13.3、多页导航 +12.6、状态操作 +10.8（对 OpenWebRL-4B），配对检验 p<0.01。
- 能支持：在离线镜像里训，可以不输给在真网站上训。支持不了：增益来自「环境更好」而不是「任务更多/更对口」——训练任务数量和 OpenWebRL 的 2,102 个并不相同（2,288 对 2,102），没有等量对照。

## 局限
- 作者承认（Limitations，p10）：(1) 镜像是模仿而非等同，主张受限于所提任务和人工保真审计，交互地图、实时行情等用静态替代；(2) 脚本验证器和模型判官可能漏掉合理的替代解法和细微失败；以及真实网站的多样性不可完全复现。
- 我看到的：
  1. **钻空子**：策略训练用 GPT-4.1 判官，看的是最终回答 + 完整动作历史 + 三张最近截图（附录 E.3）；评测时 WebVoyager、DeepShop 也用 GPT-4.1 判官（§4.1）。同一个判官既出奖励又出分，若策略学会让判官容易点头（答案措辞、截图排布），这个增益会被同时放大。迹象：表 8 里 WebHarbor-4B 的 Agent-Judge 通过率（41.5）比确定性验证器（30.0）高 11.5 点，是表中 4B 模型里差距最大的；一致率 87.0 在 4B 里最低。这是我的读法，作者没这么解释。
  2. **数据泄漏**：站点层面，WebVoyager 的 15 站被剔除，但 Online-Mind2Web 只说「原任务不在任务集里」（p9），站点并未剔除；环境是从两个榜单覆盖的网站空间出发造的，所以 Online-Mind2Web 70.4 的增益里有多少来自站点熟悉度，论文没有拆开。0.39 的任务相似度只说明任务文本不同。
  3. 训练奖励不使用确定性验证器，等于放弃了环境最大的优势（可验证），我读到的部分没看到原因解释，也没看到「用验证器当奖励」的对照结果。
  4. 4B 模型的 WebHarbor 测试集成绩仅 30.0，低于 Qwen3.6-35B 的 36.8（GUI 模式）。

## 品味判断
1. **问题怎么发现的？** 自己把在线榜单跑一遍，数出 38% 被拦、22% 过时。任何团队都能做；贵的是 153 站点的人审。
2. **最能说服审稿人的**：表 6 的对比设计：同一 SFT 起点、同一 MM-GRPO 配方、同一 harness，只换环境。
3. **可模仿**：写「环境」类论文时，先量化现有评测里有多少比例是环境噪声（被拦/过时/无效），把它当动机，而不是只说「不稳定」。
4. **没比的**：没有和同样做「真站点复刻」的 GUI-Genesis、VeriEnv（§2 提及）做同基座的训练对比，表 1 只比特性。

## 和 CUA 评测 / 换路鲁棒性的关系（公开层面）
它的 Reddit 站几乎全军覆没，且去掉自动登录后分数下降，说明「同一任务、不同入口路径」会明显改变成功率。

## 原文摘录
- "Even apparently functional environments may expose shortcuts, omit plausible alternative actions, or leak answers through their interfaces, undermining task validity."（§1，p1）
- "The task-specific WebHarbor verifier ... Logged as a diagnostic metric only and excluded from the policy objective"（表 22，p31）
- "(1) WebHarbor imitates target website rather than equaling it ..."（Limitations，p10）

## 核对说明
读的是 v1 PDF。表 6、表 8、表 9、表 22 数字对过。「Agent-Judge 比验证器高 11.5」是我用表 8 的 41.5−30.0 算出来的。环境构造的详细流程（附录 C–D）和 Table 2–4 没逐项核。GitHub 返回 200，权重和数据（HuggingFace）没核。
