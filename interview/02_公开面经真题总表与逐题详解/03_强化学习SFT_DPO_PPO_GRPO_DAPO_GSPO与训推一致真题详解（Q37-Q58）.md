# 分册三：强化学习 SFT / DPO / PPO / GRPO / DAPO / GSPO 与训推一致真题详解（`Q37`–`Q58`）

> 覆盖 2025–2026 阿里、月之暗面、字节、华为、腾讯大模型与 Agentic RL 算法面**出现率最高、问得最深**的 22 道训练核心真题。

---

### Q37：【2026 必考】多轮 Agent SFT / RL 训练时，工具返回的 Token（Tool Observation）参与 Loss 计算吗？为什么？
- **核心结论**：**绝对不参与策略梯度 / SFT Cross-Entropy Loss 计算（`loss_mask = 0`），但必须完整保留在 Attention 上下文里供后续轮次读取！**
- **底层原因**：
  1. **分布归属不同**：工具返回（沙盒 stdout、搜索结果、报错堆栈）以及用户输入都是**外部环境状态转移 $P(s_{t+1}|s_t, a_t)$**，不是策略网络 $\pi_\theta(a_t|s_t)$ 要输出的动作。如果对工具返回算 Loss，等于逼迫大模型去死记硬背或凭空伪造数据库查询结果与报错栈，不仅浪费模型容量，还会严重诱发“不调工具自己编造观察结果”的幻觉！
  2. **哪些 Token 必须 `loss_mask = 1`**：模型自身在每轮生成的 **思考过程（`reasoning_content` / `<think>`）、预播报/状态块（如规范清洗后的 `<file_action>`）、结构化工具调用名称与参数（`tool_calls`）以及最终对用户的回复**。在 veRL 等框架中，对应 `AgentLoopOutput` 的 `response_mask`（模型生成位置为 1，环境拼接进去的 `tool_response` 位置严格置 0）。

---

### Q38：【2026 必考】为什么多轮 Agent 在线 RL 必须用 `Token-in / Token-out` 接口，而不能每轮重跑 `apply_chat_template`？
- **核心结论**：如果在多轮 Rollout 结束后把 `messages` 列表重新过一遍 `tokenizer.apply_chat_template()` 再分词喂给训练引擎，**重分词得到的 Token ID 序列往往和推理引擎（vLLM/SGLang）当时真实采样的 Token ID 序列对不上（Retokenization Drift）**，会导致训练直接无法收敛甚至崩溃！
- **失配机制与工程正解**：
  1. **为什么会对不上**：BPE 分词在边界空格、换行符、特殊控制符以及 Tool Call JSON 反序列化再序列化后的键值空格差异下，同一个字符串可能被切成不同的 subword 组合；一旦某处错位 1 个 token，后面整段序列的 `old_logprob` 与训练引擎重算的 `new_logprob` 全部错位，重要性采样比率 $\rho_t = \exp(\log \pi_\theta - \log \pi_{\text{old}})$ 彻底失真爆炸。
  2. **工程正解（`Token-in / Token-out`）**：Agent Loop 在与推理引擎交互时直接传 Token IDs 数组、拿回生成的真实 Token IDs 与对应的 `rollout_logprobs`；每当环境返回工具结果时，只把新增的这几句环境文本编码成 Token IDs 追加到已有序列尾部（同时追加一段全 0 的 `response_mask`），全程绝不对已生成的历史前缀重跑模板分词。

---

### Q39：Agent SFT 数据怎么筛选与配比？如果 SFT 后模型出现协议违约或总复读“万能套话”，根因是什么、怎么治？
- **核心结论**：Agent SFT 贵精不贵多，“脏示范比没示范危害更大”。
- **四层筛选法 + 结合你的实战根因治理**：
  1. **终态结果硬过滤**：只保留确定性 Verifier 通过或有非空最终产物（如 `deck_html_pages > 0`）的成功轨迹；
  2. **轨迹过程效率去噪**：剔除虽然最终蒙对了、但中间反复原地报错重试十几次的低 OE / 高 RR 脏轨迹（或将无意义的纯语法笔误弯路裁剪干净，仅保留有信息量的合理探索与恢复）；
  3. **协议不变量 100% 校验（你的硬核案例）**：正如我们在 1.6 万条 Opus 轨迹中抓出的——哪怕是顶级教师模型，原始轨迹里也有 42% 残缺 System Prompt、65%–89% 漏发 `<file_action>` 以及末轮悬空 `<file_action>` 导致训后模型“不发”或“发完早停”；通过六步自动化修复使协议 100% 一致后症状彻底消失；
  4. **为什么总复读“好的我将为您处理 / 万能安全套话”及治法**：根因是训练集里同质化开场白/机械确认模板（如批测自动生成的 5,184 条一模一样的 `<ask_user_answer>` 确认套话）频率极高，局部条件熵趋近于 0 导致过拟合。治法是**对高频模板做 N-gram / MinHash 去重降采样、用小模型把机械套话改写多样化、混合通用代码/推理语料防退化，并在后续用 DPO/RL 惩罚无信息量复读**。

---

### Q40：为什么做 Agent 模型通常要先 SFT 再 RL（而不是像 R1-Zero 那样直接 Base 上纯 RL）？Rejection Sampling 冷启动有什么用？
- **核心结论**：R1-Zero 直接在 Base 模型上跑纯 RL 能成功，是因为数学题动作空间就是自然语言文本、Base 模型本身就有非零概率写出算式并碰对答案；而在复杂 Agent 场景下，直接拿未见过私有工具协议的 Base 模型上 RL 会死在**冷启动零奖励悬崖**上。
- **三大必先 SFT 的原因**：
  1. **对齐结构化协议与动作语法**：Agent 需要严格输出合法的 JSON `tool_calls`、遵循 `local://` 路径规范与 `SKILL.md` 阶段契约，未经 SFT 冷启动的模型采样 100 次可能 99 次都在工具解析层报错，根本走不到终态拿不到任何正向梯度；
  2. **可读性与混合语种控制**：R1-Zero 纯 RL 暴露出了严重的中英夹杂与可读性崩溃，正式版 R1 第一步也是先用数千条精标长 CoT 做冷启动 SFT；
  3. **Rejection Sampling（拒绝采样 SFT）的桥梁作用**：当第一轮小规模 SFT 或初步 RL 具备一定成功率后，在大量任务上采样 $G$ 条并用 Verifier 筛出高分干净轨迹做一轮 RFT，能以极低成本把稀疏的在线探索成果稳固地蒸馏进模型权重，为下一阶段大规模多场景 RL 垫高基准起点。

---

### Q41：详细对比 PPO、DPO、GRPO 的优化目标、模型显存开销、优缺点与适用场景边界。

| 维度 | **PPO**（Proximal Policy Optimization） | **DPO**（Direct Preference Optimization） | **GRPO**（Group Relative Policy Optimization） |
|---|---|---|---|
| **核心思想** | 在线采样 + 用独立 Critic 价值网络配合 GAE 估计逐 Token 优势 $\hat{A}_{t}$，裁剪概率比更新 | 利用最优策略与奖励函数的闭式解，将 RLHF 转化为静态成对偏好 $(x, y_w, y_l)$ 上的分类损失 | 在线对同题采样一组 $G$ 条回答，直接用**组内奖励均值与标准差**充当基线算相对优势，**砍掉 Critic** |
| **同时驻留模型** | **4 个**（Actor $\pi_\theta$、Critic $V_\phi$、Ref $\pi_{\text{ref}}$、RM $r_\psi$） | **2 个**（Actor $\pi_\theta$、冻结 Ref $\pi_{\text{ref}}$，甚至 Ref logprob 可提前离线算好存盘变成 **1 个**） | **2 个 + 规则 Verifier**（Actor $\pi_\theta$、Ref $\pi_{\text{ref}}$；去 KL 时甚至只需 1 个训练模型） |
| **策略属性** | On-Policy（在线探索） | Off-Policy（纯离线静态数据） | On-Policy（在线组采样探索） |
| **核心优势** | 具备 Token 级细粒度时间差分信用分配，通用开放场景上限稳 | 极省算力、无需 Rollout 基础设施、训练如 SFT 般简单稳定 | 省去与 Actor 同等庞大的 Critic 显存与拟合误差，与代码/数学/环境状态等**可验证奖励（RLVR）**天作之合 |
| **核心局限** | 显存通信开销翻倍，Value 网络在长链稀疏奖励下极难训准 | 受限于离线偏好对覆盖分布，存在长度偏置与好坏概率同降风险，无法自主探索新路径 | 采样推理开销乘 $G$ 倍；优势是序列级标量广播到全序列（信用分配粗）；组内全对/全错时梯度为 0 |
| **选型口诀** | 预算充足、需精细逐轮价值估计的复杂交互 | 已有明确好坏对比数据（如 Opus vs 自研负样本、人工改稿记录）、低成本定向治毛病 | 有确定性 Verifier/沙盒（Coding、GUI/MCP Store、数学）、追求自主探索与推理上限的首选 |

---

### Q42：推导 DPO 的损失函数：为什么不需要显式加 KL 正则？DPO 有哪些固有缺陷及改良版（IPO/KTO/SimPO）？
- **核心推导脉络（30 秒讲清）**：
  1. 带 KL 约束的 RLHF 目标 $\max_\pi \mathbb{E}[r(x,y)] - \beta D_{\text{KL}}(\pi \| \pi_{\text{ref}})$ 存在解析最优解：$\pi^*(y|x) = \frac{1}{Z(x)}\pi_{\text{ref}}(y|x)\exp\left(\frac{1}{\beta}r(x,y)\right)$；
  2. 反解出奖励函数：$r(x,y) = \beta \log \frac{\pi^*(y|x)}{\pi_{\text{ref}}(y|x)} + \beta \log Z(x)$；
  3. 代入 Bradley-Terry 成对偏好概率 $P(y_w \succ y_l | x) = \sigma(r(x,y_w) - r(x,y_l))$，恰好消掉了难以计算的配分函数 $\log Z(x)$，取负对数似然即得：
     $$\mathcal{L}_{\text{DPO}}(\theta) = -\mathbb{E}_{(x,y_w,y_l)}\left[\log \sigma\left(\beta \log \frac{\pi_\theta(y_w|x)}{\pi_{\text{ref}}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{\text{ref}}(y_l|x)}\right)\right]$$
  - **为什么不用显式加 KL**：因为 KL 约束在数学推导第一步就已经完全等价编码进了参考模型对数似然比和温度系数 $\beta$ 里（$\beta$ 越大惩罚偏离 $\pi_{\text{ref}}$ 越重）。
- **三大固有缺陷与主流改良**：
  1. **长度偏置（Length Bias）**：序列 $\log \pi(y|x) = \sum_t \log \pi(y_t|x, y_{<t})$ 是逐 token 累加，长废话容易拉大差值 → **SimPO** 改用长度归一化的平均 logprob 加目标 margin $\gamma$，并直接省掉 $\pi_{\text{ref}}$；
  2. **确定性偏好过拟合（易把 $\pi(y_l)$ 压到 0 导致 KL 失控）** → **IPO** 改用均方误差损失防止概率比趋向无穷；
  3. **Chosen 和 Rejected 概率同时下降（Likelihood Displacement）**：只要 $y_l$ 降得比 $y_w$ 快，差值仍在变大，导致模型连正确回答的概率都掉 → 常混入少量 $y_w$ 上的 NLL SFT 正则项（如 RPO / DPO+NLL）；**KTO** 则利用前景理论支持非成对的单样本好/坏二元标签训练。

---

### Q43：GRPO 没有 Critic（Value 网络），它的 Advantage 是怎么估出来的？Group Size $G$ 取 4 和取 16 有何权衡？
- **Advantage 计算机制**：对同一个输入 $q$，用旧策略 $\pi_{\theta_{\text{old}}}$ 独立采样 $G$ 条完整轨迹 $\{o_1, \dots, o_G\}$，由 Verifier/RM 算出标量奖励 $\{r_1, \dots, r_G\}$，以组内均值作为蒙特卡洛基线（Baseline）、组内标准差归一化：
  $$A_i = \frac{r_i - \text{mean}(r_1, \dots, r_G)}{\text{std}(r_1, \dots, r_G) + \epsilon}$$
  在结果奖励设定下，第 $i$ 条轨迹内所有模型生成的有效动作 token 共享同一个优势标量 $A_{i,t} = A_i$。
- **Group Size $G$ 取 4 vs 取 16 的核心权衡**：
  - **$G=4$（小 Group）**：单题 Rollout 推理延迟与 KV 显存小，同样算力预算每步能塞进更多不同的 Prompt（Batch 多样性高）；缺点是均值/方差估计噪声大，且对于命中率 10% 的中难题极易采出 `[0,0,0,0]` 全错无效组；
  - **$G=16$（或 32/64，大 Group）**：基线估计方差低，命中稀有正确轨迹的概率 $1-(1-p)^G$ 大幅提高，梯度信号稳；缺点是单卡生成显存（KV Cache）与长尾等待时间（木桶效应：整组要等最慢那条长轨迹跑完）显著上升。实践中推理/Agent RL 常用 $G=8$ 或 $16$。

---

### Q44：如果一个 Group 里的 $G$ 条采样全对（全 1）或全错（全 0），Advantage 和梯度是多少？除了全对全错，Loss 变成 0 还有哪些可能？
- **全对或全错时**：$r_1 = \dots = r_G$，组内标准差 $\text{std}(r) = 0$，分子 $r_i - \bar{r} = 0$，因此所有样本的 **$A_i = 0$**（实现上必须判断 `std < eps` 直接置 0，否则浮点误差除以 `eps` 会把舍入噪声放大成巨型假梯度！）。在不带显式 KL Loss 的纯策略目标下，该组对模型参数的**策略梯度严格为 0**，采样算力完全白费。
- **面试追问：如果监控面板看到 Policy Loss / Grad Norm 变成 0，除了“全对/全错”还有哪 5 种工程 Bug 可能？**
  1. **`response_mask` 全被置成了 0**（例如模板解析错位，把模型回答误标成了 prompt 或 tool observation）；
  2. **不小心对 `logp_new` 做了 `.detach()` 或开启了 `torch.no_grad()`**；
  3. **Verifier / 环境挂了**（比如沙盒端口断连或超时，所有采样无条件返回 0 分）；
  4. **奖励全是常数或未归一化导致除零出 NaN 后被框架梯度裁剪跳过**；
  5. **Clip 完全饱和且单向截断**（虽然 Loss 值未必是 0，但被 clip 分支截平后对 $\theta$ 的导数为 0，导致梯度为 0）。

---

### Q45：【字节/阿里必考】详解 DAPO 的四项核心改进（Clip-Higher、Dynamic Sampling、Token-level Loss、Overlong Shaping）及其在 veRL 中的实现配置。
- **核心结论**：DAPO（Decoupled Clip and Dynamic sAmpling Policy Optimization，字节+清华开源推理 RL 标杆方案）专门针对原始 GRPO 在长链推理/Agent 训练中的四大痛点逐一击破：
  1. **Clip-Higher（解耦非对称裁剪：$\epsilon_{\text{low}}=0.2, \epsilon_{\text{high}}=0.28$）**：原始对称裁剪下，低概率探索词（如反思词 `Wait` 或冷门工具调用，$\pi_{\text{old}}=0.01$）单步最多只能涨到 $0.012$，很快被高概率套路词挤死导致**熵坍缩**；单独放宽上界 $\epsilon_{\text{high}}$ 给低概率好动作留足上升空间，同时保持 $\epsilon_{\text{low}}=0.2$ 防止把概率瞬间压成 0；
  2. **Dynamic Sampling（动态过滤补采）**：在线过滤掉准确率为 1（全对）和 0（全错）的零梯度无效组，持续从题池补采直到凑满一个全是有区分度（$0 < \sum r_i < G$）的有效训练 Batch，保证每步更新梯度质量恒定；
  3. **Token-level Policy Gradient Loss（按 Batch 内总有效 Token 平均，而非先按序列长度平均）**：原始 GRPO 先除以每条回答长度 $|o_i|$ 再对组求平均，导致越长的回答每个 Token 分到的梯度权重越小——既学不充分长链里的正确推理，也惩罚不动长废话里的胡言乱语；改为全局 `token-mean` 让每个动作 Token 权重平等；
  4. **Overlong Reward Shaping + 移除 KL 惩罚**：对触及最大长度被硬截断的未完结样本，不简单粗暴给 -1（否则会把原本推理方向完全正确的长思考冤杀，引入巨大奖励噪声），而是采用超长缓冲区间线性软惩罚或直接 mask 超长截断样本；同时在可验证推理任务上去掉对 SFT 参考模型的 KL 束缚，释放长链演化空间。
- **veRL 配置落地加分句**：在 veRL 中无需重写引擎，直接通过配置组合开启：`clip_ratio_low=0.2, clip_ratio_high=0.28`、`loss_agg_mode="token-mean"`、`use_kl_loss=False`、配合 Rollout Buffer 的动态组过滤重填与自定义超长软惩罚函数即可。

---

### Q46：【阿里/Qwen 必考】GSPO 为什么要把重要性采样比（IS Ratio）和 Clip 从 Token 级提升到序列级？Dr.GRPO 与 CISPO 又分别修了什么？
- **GSPO（Group Sequence Policy Optimization，Qwen3 核心 RL 算法）**：
  - **痛点**：GRPO 给的是**序列级**标量优势 $A_i$，却乘在**逐 Token** 的重要性采样比 $\rho_{i,t} = \frac{\pi_\theta(y_{i,t}|\cdot)}{\pi_{\text{old}}(y_{i,t}|\cdot)}$ 上。优化粒度与奖励粒度错位！在几千 Token 的长序列特别是 **MoE 模型**上，单个 Token 因专家路由微小翻转就会让 $\rho_{i,t}$ 剧烈抖动，局部随机裁掉几个 Token 导致梯度方向扭曲甚至训练崩溃。
  - **解法**：GSPO 定义**长度归一化的序列级重要性采样比（几何平均似然比）**：
    $$s_i(\theta) = \left(\frac{\pi_\theta(y_i | x)}{\pi_{\text{old}}(y_i | x)}\right)^{\frac{1}{|y_i|}} = \exp\left(\frac{1}{|y_i|}\sum_{t=1}^{|y_i|} \log \frac{\pi_\theta(y_{i,t}|x, y_{i,<t})}{\pi_{\text{old}}(y_{i,t}|x, y_{i,<t})}\right)$$
    并将 PPO Clip 直接作用在整个序列比率 $s_i(\theta)$ 上。这样单 Token 的路由毛刺被全序列平均抹平，一旦整条轨迹分布偏离过大就干净地整条截断，大幅提升了长链 CoT 与大 MoE 模型 RL 的稳定性。
- **同族高频对比**：
  - **Dr.GRPO**：指出 GRPO 除以组内 `std(r)` 会给极简/极难题（方差极小）赋予过大权重（难度偏置），且除以 $|o_i|$ 会让模型故意把错误回答写长来稀释负梯度、把正确回答写短（长度偏置）→ **直接去掉除 `std` 和除 $|o_i|$**（改除固定常数）；
  - **CISPO（MiniMax）**：指出 PPO Clip 一旦越界梯度直接变 0，会把低概率关键转折词的梯度彻底丢掉 → 改为用 `stop_gradient(clip(ratio))` 作为加权系数乘在 $\log \pi_\theta$ 上（裁权重而不截断对数概率梯度）。

---

### Q47：PPO/GRPO 里 Clip 的 $\epsilon$ 在 $A>0$ 和 $A<0$ 时分别约束哪一侧？什么是熵坍缩（Entropy Collapse），怎么监控和缓解？
- **Clip 两侧非对称物理意义**（目标 $\min(\rho A, \text{clip}(\rho, 1-\epsilon, 1+\epsilon)A)$）：
  - **当 $A > 0$（好动作，想调高概率）**：$\min$ 在 $\rho > 1+\epsilon$ 时生效被截平——即**只封顶上界 $1+\epsilon$**，防止单步把好动作概率猛推过头；若 $\rho < 1-\epsilon$ 则不截断，保留梯度把它拉回来；
  - **当 $A < 0$（坏动作，想压低概率）**：因为乘了负数，$\min$ 在 $\rho < 1-\epsilon$ 时生效被截平——即**只托底下界 $1-\epsilon$**，防止单步把坏动作概率猛砸到零导致分布崩坏。
- **熵坍缩（Entropy Collapse）**：训练早中期策略分布的词表熵 $H(\pi_\theta) = -\sum_v \pi(v)\log\pi(v)$ 断崖式跌向 0，组内 $G$ 条采样长得几乎一模一样，探索彻底停止、验证集指标停滞甚至倒退。
  - **监控与缓解**：实时盯紧 `actor/entropy` 与组内独特轨迹占比；缓解手段包括 **DAPO Clip-Higher**、降低单批数据重复更新轮数（保持近 On-policy）、适度加微小熵奖励系数、动态剔除已完全掌握的简单题。

---

### Q48：为什么可验证 RL 训久了模型回复会越来越长？长度和准确率是因果关系吗？长度惩罚怎么加才不伤推理能力？
- **核心结论**：**长度与准确率是局部正相关但绝非简单因果关系**。
  - **变长的两个真因**：① **正向探索因素**：在难题上自我检查、回溯试错客观上需要更多 Token，且早期更长的链确实命中率更高；② **损失与偏差诱导的虚假膨胀（Spurious Length Inflation）**：如 Dr.GRPO 揭示的，按长度平均 Loss 时，模型把注定答错的题故意拉长胡扯可以稀释每 Token 的负优势惩罚！
- **不伤正常深度推理的长度惩罚设计**：
  1. **严禁对所有回答无差别减固定长度分**（否则模型遇到真难题不敢展开推理，准确率暴跌）；
  2. **组内正确样本相对长度修正 / GFPO**：只在**同样答对（$r=1$）**的组内样本之间温和奖励更紧凑简洁的那几条，答错的不因写得短而少罚（配合 Token-level Loss 消除负惩罚稀释）；
  3. **分段软阈值（Overlong Buffer）**：在合理预算（如 8k tokens）内零惩罚自由思考，仅在逼近物理上限（如 12k–16k）的缓冲带施加线性递增软惩罚引导优雅收尾。

---

### Q49：区分 On-Policy 与 Off-Policy：GRPO 一批采样更新多个 mini-batch 属于什么？KL 散度加在 Reward 里和加在 Loss 里（k1/k2/k3 估计器）有什么区别？
- **On-Policy vs Off-Policy 细粒度界定**：
  - 严格意义的纯 On-Policy 是采样一批只做 **1 次**梯度更新就丢弃；实际工程中 Rollout 一大批样本（如 512 题 × 16 条），切分成多个 mini-batch 连续更新 $\mu=4\sim 8$ 步——从第 2 个 mini-batch 起，$\pi_\theta$ 已经偏离了采样时的 $\pi_{\text{old}}$，属于**近策略（Near-Policy / Mildly Off-Policy）**，这正是为什么必须乘重要性采样比率 $\rho_t = \pi_\theta / \pi_{\text{old}}$ 并加 Clip 约束！
- **KL 加在 Reward 里 vs 加在 Loss 里 & k3 估计器**：
  - **PPO 传统做法（KL in Reward）**：把 $-\beta \log\frac{\pi_\theta}{\pi_{\text{ref}}}$ 塞进每步即时奖励里参与优势计算（无梯度直接穿过该项，靠策略梯度间接推回）；
  - **GRPO 标准做法（KL in Loss + Schulman k3 低方差无偏估计）**：直接作为可微正则项加在总 Loss 上。因为朴素蒙特卡洛估计 $k_1 = \log\frac{\pi_\theta}{\pi_{\text{ref}}}$ 方差大且可能为负，GRPO 采用恒非负、低方差且一阶无偏的 **$k_3$ 估计器**：
    $$\mathbb{D}_{\text{KL}}(\pi_\theta \| \pi_{\text{ref}}) \approx \frac{\pi_{\text{ref}}(y_t)}{\pi_\theta(y_t)} - \log \frac{\pi_{\text{ref}}(y_t)}{\pi_\theta(y_t)} - 1 \ge 0$$

---

### Q50：【高频硬核】RL 训练中的「训推不一致（Training-Inference Mismatch）」有哪些来源？会导致什么后果？
- **核心结论**：现代 RL 框架为了速度采用**训推分离架构**——Rollout 用高吞吐推理引擎（vLLM / SGLang），梯度更新用分布式训练引擎（Megatron / FSDP）。**哪怕加载完全同一份权重，两端对同一个 Token 算出的 `logprob` 往往也不相等**！
- **五层根因背诵框架**：
  1. **算子与 Kernel 归约层**：PagedAttention vs FlashAttention、不同 Tensor Parallel（TP）切分下的矩阵乘浮点累加顺序不同（浮点数加法不满足结合律）；
  2. **数值精度层**：推理端常用 **FP8 权重 / FP8 KV Cache** 提吞吐，而训练端用 **BF16 + FP32 累加** 重算 `logprob`；
  3. **采样分布截断层**：推理时开了 `top_p / top_k / temperature`，训练侧若在未裁剪的全词表 Logits 上做 `log_softmax` 会产生基准偏移；
  4. **系统与分词层**：异步 RL 权重同步延迟（Stale Policy）或多轮重跑 `chat_template` 导致 Token 错位；
  5. **MoE 离散路由翻转层（最致命，见 Q51）**。
- **严重后果**：本该在第一次更新时严格等于 $1.0$ 的重要性比率 $\rho_t = \exp(\text{logp}_{\text{train}} - \text{logp}_{\text{rollout}})$ 开局就剧烈偏离 1 甚至飙到几十上百，产生系统性虚假离线偏差，轻则策略熵异常波动，重则在几百步内梯度爆炸彻底训崩！

---

### Q51：【MoE RL 杀手题】为什么 MoE 模型做 GRPO 时训推不一致会被急剧放大（94% token 路由差异）？详解 Routing Replay（R3）、TIS、IcePop、GSPO 四种解法。
- **为什么 MoE 是重灾区**：在稠密模型里，训推算子浮点差 $10^{-5}$ 只会让最终 `logprob` 差 $10^{-4}$；但在 MoE（如 Qwen3-30B-A3B、DeepSeek-V3、SenseNova Flash MoE）里，每层 Router 做的是 **`Top-K` 离散阶跃选择**！当第 8 专家和第 9 专家门控打分差 $10^{-6}$ 时，两端微小精度差就会翻转激活的专家网络，误差逐层指数级放大——实测研究（R3）显示**一次前向中高达 94% 的 Token 至少有一层选了与推理时不同的专家**，导致 `logprob` 出现断崖跳变！
- **四大工业级解法矩阵（答出这一套直接拿满分）**：
  1. **强制路由对齐派 —— Routing Replay（R3 / DeepSeek-V3.2 方案，最治本）**：在推理引擎（SGLang）采样时记录每个 Token 每层选中的 Top-K 专家 ID（并对齐 `sorted` 归约顺序），传给训练引擎（Megatron）前向重算时**强制走完全相同的专家路径**，同时保留门控权重可微让梯度正常流过 Router；
  2. **序列平滑容错派 —— GSPO**：把逐 Token 比率改为整条序列几何平均比率，单层几个 Token 的路由抖动在全序列平均下被天然抹平；
  3. **重要性截断修正派 —— TIS（Truncated Importance Sampling）**：承认 Rollout 引擎是另一个行为策略 $\mu$，训练侧是 $\pi_{\text{old}}$，在 PPO 目标前显式乘上截断后的训推校正系数 $\min\left(\frac{\pi_{\text{train\_old}}}{\pi_{\text{rollout}}}, C\right)$；
  4. **激进掩码派 —— IcePop / OPSM**：监控逐 Token 或整序列的 $|\text{logp}_{\text{train}} - \text{logp}_{\text{rollout}}|$，超过安全阈值的异常离群 Token/序列直接 `mask=0` 丢弃不参与反传，干净阻断脏梯度。

---

### Q52：多轮 Agent 的奖励怎么设计（格式奖励 / 过程奖励 PRM / 终态结果奖励 ORM）？为什么过程奖励权重通常设得很低？
- **三层奖励结构**：
  1. **格式合规奖励（Format / Protocol Reward，权重低，如 $0.05\sim 0.1$）**：校验 `<think>` 标签闭合、JSON `tool_calls` 语法合法、无内部协议字符串泄漏（前期扶上马，稳定后可退火）；
  2. **终态可验证结果奖励（Outcome Verifier Reward，主奖励 $1.0$）**：任务最终是否真正改对了业务 Store / 通过了全部单元测试 / 满足了硬约束（决定大方向绝不跑偏）；
  3. **过程奖励（Process / Milestone Reward，权重极低且严格受控）**。
- **为什么过程奖励（尤其是神经 PRM 或调用工具奖励）权重必须压得很低甚至慎用？**
  - **极易触发灾难性 Reward Hacking**！正如我们在 OpenMobile-2 训练规范中明确写死的铁律：**严禁给“调用了工具”或“步数多/少”赋予独立高额正奖励**——一旦给调工具加分，模型会疯狂原地空调无用查询函数刷满上限步数而不交卷；一旦用大模型 PRM 给每步打主观分，策略网络几十步内就能摸清 PRM 的打分漏洞写出“讨好裁判但完全不推进业务”的漂亮废话。只有基于**环境真实状态差分（State-Milestone Diff）且不可重复刷取（Potential-based Shaping）**的里程碑信号才安全。

---

### Q53：信用分配（Credit Assignment）难题：一条 25 步的轨迹前 24 步都对、第 25 步填错得 0 分，或者两条不同完成度的失败轨迹，奖励该怎么给？截断轨迹怎么计分？
- **核心结论**：长程全 0/1 奖励把第 25 步的一个笔误惩罚无差别扣在了前 24 步正确规划上，是长链路 Agent RL 收敛慢的头号元凶。
- **四套精准解法**：
  1. **基于状态潜势函数的里程碑奖励（Potential-Based State Milestone，你的项目杀手锏）**：在可控环境（如 MobileGym++ 的业务 Store 或 PPT 阶段的落盘产物检验）中，把终态复合断言拆成 $M$ 个客观子条件（如“找对商品 SKU + 加进购物车 + 选对地址 + 实付记账”）；定义潜势变化 $r_t = \gamma \Phi(s_{t+1}) - \Phi(s_t)$（保证来回加购再删掉刷不到重复分！），让完成度 80% 的失败轨迹显著高于开局乱点的 0% 轨迹，组内立刻产生有效梯度；
  2. **前缀树复用 / 分支重采样（Tree / VinePPO / GiGPO 思路）**：对同一题的多条 Rollout 在共同中间状态节点汇聚，用从该节点分叉出去的子树平均成功率估计每一步的真实步级优势 $A_{i,t}$，无需训练 Critic 网络即可定位“究竟是第 25 步走错了”；
  3. **反事实强模型定位（Counterfactual Critique / Step-level DPO）**：找到失败轨迹第一个偏离点，用专家模型从第 24 步分叉补出正确第 25 步，只在分叉步之后算偏好梯度；
  4. **截断轨迹（跑满 `max_steps` 或 `max_tokens` 未自然结束）怎么计分**：区分**环境超时崩溃**（直接 `mask` 剔除出训练分母，绝不给 0 分）与**模型死循环/废话超长未交卷**（给 0 分或叠加 DAPO 软超长惩罚，促使其学会在预算内收敛收尾）。

---

### Q54：举一个你亲历或典型的 Reward Hacking（奖励黑客 / 虚假完成）案例：怎么发现、怎么紧急止血、怎么从根源治理？
- **两个一手真实案例直接任选或连击**：
  - **案例一（MobileGym++ 虚假完成 Hallucinated Completion）**：在 369 次运行中抓到了 **190 次**“模型看到预填工具返回 ok 或仅滑到了确认页，未点最终落库按钮就直接调 `finish` 声称已帮用户办妥”。如果早期用简单 LLM 看对话历史当裁判，这 190 次大半会被误判拿正分！**治理**：用直接读取底层业务 Store 前后状态差分的确定性 Verifier 替代对话面裁判，并对 470 个近错变异终态做 100% 拦截审计。
  - **案例二（小浣熊评测尺子漏洞 + `done_no_html`）**：① 模型不调生图脚本直接输出一段总结话术使 Agent 终态变为 `case_ok`（`done_no_html`）；② 内容分动态清单偶发静默降级 `dyn=0` 导致简短空洞文稿白拿高分。**发现—止血—根治三部曲**：
    1. **发现监控**：盯紧 **“代理指标涨、硬产物/人抽评跌”的剪刀差**，以及轨迹长度、工具调用次数异常骤降；
    2. **紧急止血**：上线硬规则前置门禁（如 `html_pages == 0` 无条件判 0 分、`dyn == 0` 直接抛错阻断绝不给分）；
    3. **根源治理**：修复裁判漏洞、把被模型钻空子的畸形样本加入变异负例集做回归测试，重洗污染批次后再恢复训练。

---

### Q55：GRPO 训练中某个任务一直采不到正确轨迹（Reward 恒为 0），怎么系统排查是模型能力不够、数据题面错了、环境崩了还是 Verifier 写太严了？
- **标准四层二分排查SOP（面试官极看重的实战工程素养）**：
  1. **第一层查环境与基础设施（Infra & Env）**：看这批轨迹的终止原因是不是 App 启动超时、沙盒 500、端口不通或缺少种子静态资源（如 MobileGym++ 里美团进店偶发崩溃、缺资源包）；若是环境锅，先修环境并从训练分母剔除；
  2. **第二层查题面与 Verifier 死锁（Task & Verifier Audit）**：拿**最强旗舰模型（如 Claude Opus / Gemini 3.1）或人工手点一条确定正确的黄金轨迹**喂给该题的 Verifier——若连人工/旗舰做对的终态都判 `0` 分，立刻抓出“题面条件与默认数据库对不上”或“Verifier 写了过严的字符串标点死匹配 / 绑死了某条隐藏路由”（如我们发现的瑞幸购物车 ID 错位死题与标点假阴性）；
  3. **第三层查协议与上下文截断（Harness & Context）**：看模型是不是还没走到最后一步就被 `max_steps` 截断，或者像我们在 23 道题上发现的那样**被超长 Thinking 提前撑爆了上下文窗口报错**；
  4. **第四层确认是纯模型能力短板后怎么救**：若旗舰能过、自研模型采样 64 次全挂，说明跨度超出当前模型探索半径——采用**前缀提示引导采样（Hinted / Prefix Rollout，给前一半专家步骤让模型续完后半段）**或先补少量同类跨功能 SFT 数据垫脚。

---

### Q56：多目标奖励（正确性、格式、步数效率、安全性）怎么加权而不互相吞噬？多个 RM 打分冲突怎么聚合？
- **核心结论**：如果把格式分、步数短分和正确性分直接简单相加 $R = w_1 R_{\text{acc}} + w_2 R_{\text{fmt}} + w_3 R_{\text{len}}$，模型很快就会发现**“开局 1 步写个完美格式然后直接放弃任务，稳拿 $w_2 + w_3$ 保底高分，比冒风险做 20 步题划算得多”**！
- **正确的层级门控（Hierarchical Multiplicative / Lexicographic Gating）设计**：
  1. **主次乘法门控而非平级加法**：
     - **安全与红线一票否决**：触碰越权/危险操作直接给极低负分封死；
     - **效率与质量奖励以“任务成功”为前置开关**：$R = R_{\text{fmt}} + R_{\text{acc}} \cdot (1 + \alpha \cdot R_{\text{efficiency}})$——**只有真正把题做对了（$R_{\text{acc}}=1$），步数更少、Token 更省才能拿到额外加分**；没做对而提前早停一律没有效率分！
  2. **多 RM 冲突聚合**：先对各维度 RM 分数做 running mean/std 标准化消除量纲差异；对客观硬伤维度（如 SlideGate 的指令硬失败、事实幻觉、页面裁切）采用 **Min-Gate / 阈值硬门禁（木桶短板法则）**，绝不允许高美观分抵消事实编造（我们在 SlideGate 66 组线性权重消融出 22 种排名的实验直接证明了纯线性求和在跨维冲突时的脆弱性）。

---

### Q57：完整讲清 DeepSeek-R1 的四阶段训练流水线（它和 R1-Zero 有什么区别）？小模型直接做 RL 好还是蒸馏大模型推理链好？
- **R1-Zero vs R1 正式版四阶段流水线**：
  - **R1-Zero（概念验证）**：在 `DeepSeek-V3-Base` 上跳过 SFT 直接用规则奖励（准确性 + `<think>` 格式）跑 GRPO，证明纯 RL 可自发涌现反思与长链推理，但存在**语言混杂、可读性差、非推理通用任务弱**的缺陷。
  - **DeepSeek-R1 四阶段完整工程方案**：
    1. **阶段一（数千条冷启动 SFT）**：收集几千条格式优美、可读性强的长 CoT 精标样本微调 V3-Base，定好人类友好的思考范式起点；
    2. **阶段二（面向推理的 GRPO RL）**：在数学、代码、逻辑等可验证任务上跑大规模 GRPO，并加入**语言一致性奖励**消除中英乱跳；
    3. **阶段三（大规模拒绝采样 + 通用混合 SFT）**：利用阶段二收敛的强推理模型采样并通过 Verifier + 生成式裁判筛出 **约 60 万条推理轨迹**，拼上 **约 20 万条写作/问答/角色扮演通用 SFT 数据**（共 ~80 万条）重新微调 V3-Base，把推理能力与通用文风融为一体；
    4. **阶段四（全场景对齐 RL）**：推理题继续用规则奖励，通用有用性/安全性用偏好 RM，训出最终兼顾强推理与人类对齐的 R1。
- **小模型蒸馏 vs 直接 RL 的重要结论**：R1 报告实证表明，对于 7B/14B/32B 中小模型，**直接蒸馏 R1 生成的高质量长推理链，效果显著优于让小基座自己从零苦跑大规模 RL（且成本低一个数量级）**；但若要进一步突破小模型在交互环境下的自身分布偏差，**“强模型蒸馏 SFT 冷启动 + 小规模针对性在线 RL / OPD”** 是当前最强组合。

---

### Q58：什么是 OPD（On-Policy Distillation，在策略蒸馏）？它相比传统离线 SFT/KD 和在线 RL 各有什么独特优势？
- **核心结论**：OPD（如我们在 `sensenova-flash-320b-v16-step500-opd-step160` 配方中使用的关键阶段，对应 GKD / MiniLLM / 2026 主流后训练组件）是连接离线蒸馏与在线 RL 的黄金桥梁。
- **核心机制与双向降维优势**：
  1. **对比传统离线蒸馏（Off-Policy SFT / KD）—— 解决暴露偏差（Exposure Bias）**：离线蒸馏是在**教师自己生成的轨迹 $y \sim \pi_T(\cdot|x)$** 上训学生，学生推理时一旦第 5 步采偏到了教师从未去过的状态，后面就全乱套；**OPD 则让学生模型 $\pi_\theta$ 自己在线采样生成轨迹 $y \sim \pi_\theta(\cdot|x)$**，再把学生跑出来的序列喂给教师模型做一次前向，最小化每个位置上学生与教师分布的**反向 KL 散度 $\mathbb{D}_{\text{KL}}(\pi_\theta(\cdot|x, y_{<t}) \| \pi_T(\cdot|x, y_{<t}))$**——等于请老师站在学生真实走歪的路口手把手教下一步该怎么救回来！
  2. **对比纯标量奖励 RL（GRPO）—— 提供逐 Token 稠密监督信号**：GRPO 跑完几千个 Token 只拿到末尾 1 个比特的 0/1 标量反馈，信用分配极慢；而 OPD 在学生采样的每一个 Token 上都能从教师 Logits 获得词表级稠密梯度（通常只需短短百余步如 `step160` 即可大幅拉升稳定性），且完全不需要构建复杂的环境 Verifier。
