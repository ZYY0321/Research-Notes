# 分册五：Transformer 底座、MLA、MoE、推理优化与 RAG 真题详解（`Q73`–`Q85`）

> 覆盖淘天、阿里国际、华为、智谱、百度等大模型算法岗必考的 **全局核心底座八股（Attention 数学、GQA/MLA、FlashAttention/vLLM、MoE/FP8/MTP、LoRA、分布式并行与工业级 RAG）**，彻底补齐全局硬核基础！

---

### Q73：写出 Scaled Dot-Product Attention 公式：为什么要除以 $\sqrt{d_k}$？在长程多轮 Agent 场景下标准 Self-Attention 有哪些本质局限？
- **公式**：
  $$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}} + M\right)V$$
  其中 $Q \in \mathbb{R}^{n \times d_k}, K \in \mathbb{R}^{m \times d_k}, V \in \mathbb{R}^{m \times d_v}$，因果掩码 $M_{ij} = 0\ (j \le i)$ 否则 $-\infty$。
- **为什么要除以 $\sqrt{d_k}$（方差推导必背）**：假设 $q, k$ 各分量独立同分布，均值为 $0$、方差为 $1$，则点积 $q \cdot k = \sum_{i=1}^{d_k} q_i k_i$ 的均值为 $0$、**方差为 $d_k$**（标准差为 $\sqrt{d_k}$）。当 $d_k$ 较大（如 64 或 128）时，点积数值量级很大，送入 $\text{softmax}$ 后最大值趋近 $1$、其余趋近 $0$（进入饱和区），导致 $\text{softmax}$ 雅可比矩阵梯度 $\text{diag}(s) - ss^\top \approx 0$ **梯度消失**！除以 $\sqrt{d_k}$ 将点积方差重新拉回 $1$，保证训练梯度平滑。
- **在多轮长程 Agent 下的四大本质局限（淘天高频原题）**：
  1. **Prefill 计算复杂度 $O(L^2 d)$ 与 KV Cache 显存随轮次线性累加**：Agent 跑 30 轮，每轮拼接大段工具返回与截图 Token，长序列下延迟与成本急剧恶化；
  2. **注意力稀释与 Lost-in-the-Middle（中间迷失）**：$\sum_{j=1}^L \alpha_{ij} = 1$，当中间塞满几十 KB 无关工具日志时，分配给开局 System Prompt 硬约束和用户初始要求的注意力权重被严重摊薄，导致后半程忘掉页数/格式要求；
  3. **Attention Sink 与位置外推衰减**：过长序列超出训练长度时 RoPE 远程衰减产生相位失真；
  4. **工程对策**：所以必须配 **Harness 层上下文摘要卸载、子任务上下文隔离、工具按需加载与 GQA/MLA/FlashAttention**。

---

### Q74：从张量形状和显存公式对比 MHA、MQA、GQA：为什么现代基座（Qwen3 / Llama3）标配 GQA + QK-Norm？
- **设批次 $B$、序列长 $L$、总查询头数 $h$、每头维度 $d_h$（隐藏维 $D = h \cdot d_h$）**：
  - **MHA（多头注意力）**：$Q, K, V$ 均有 $h$ 个独立头，形状均为 $[B, h, L, d_h]$；单层每 Token KV Cache 元素数为 **$2 \cdot h \cdot d_h$**；Decode 阶段每次生成 1 个 Token 都要从 HBM 搬运全部 $h$ 头历史 KV，严重卡在**显存带宽瓶颈（Memory-bound）**；
  - **MQA（多查询注意力）**：保留 $h$ 个 $Q$ 头，所有 $Q$ 头共享 **1 组** $K, V$（形状 $[B, 1, L, d_h]$），KV Cache 直接缩减为 **$1/h$**，推理极快，但容量压缩过猛在大模型上会有一定质量退化；
  - **GQA（分组查询注意力）**：折中方案，将 $h$ 个 $Q$ 头均分为 $g$ 组（通常 $g=4$ 或 $8$），每组 $h/g$ 个 $Q$ 头共享 1 套 $K, V$（形状 $[B, g, L, d_h]$），KV Cache 与访存带宽压缩为原来的 **$g/h$**（例如 $h=64, g=8$ 时直降 **8 倍**），而模型精度几乎与 MHA 无损！
- **为什么 Qwen3 等现代模型还要加 QK-Norm**：在进入点积前分别对每个头的 $Q$ 和 $K$ 做 **RMSNorm**，从根源锁死 $Q, K$ 向量模长上限，彻底防止深层大尺寸模型、BF16/FP8 混合精度以及超长上下文下 Attention Logits 数值爆炸引起的训练 Loss 尖峰（Loss Spike）。

---

### Q75：深入拆解 DeepSeek MLA（多头潜在注意力）：低秩压缩公式是什么？为什么必须做“解耦 RoPE（Decoupled RoPE）”？什么是推理期矩阵吸收？
- **核心思想**：GQA 通过砍头数省显存会损失多头多样性；**MLA（Multi-head Latent Attention，DeepSeek-V2/V3 核心架构）**则将所有头的 $K, V$ 联合下投影压缩成一个低维潜在向量 $c_t^{KV}$（如 $d_c = 512 \ll 2 h d_h$），**KV Cache 里只存这一个压缩潜向量**，兼顾比 GQA 更小的缓存体积与比 MHA 更强的多头表达力！
- **核心压缩与矩阵吸收（Matrix Absorption）**：
  - 内容分支：$c_t^{KV} = W^{DKV} h_t \in \mathbb{R}^{d_c}$，$k_t^C = W^{UK} c_t^{KV}$，$v_t^C = W^{UV} c_t^{KV}$。
  - **推理期为什么不用把巨大的 $k_t^C, v_t^C$ 还原出来占显存？** 利用矩阵乘法结合律：
    $$q_{t,i}^\top k_{j,i}^C = q_{t,i}^\top \left(W_i^{UK} c_j^{KV}\right) = \left({W_i^{UK}}^\top q_{t,i}\right)^\top c_j^{KV}$$
    推理时直接把上投影矩阵 $W_i^{UK}$ **吸收进 Query 侧投影**（变成每个头一个 $d_c$ 维查询向量直接和缓存里的 $c_j^{KV}$ 做点积），同理把 $W_i^{UV}$ **吸收进输出投影矩阵 $W^O$**，全程无需显式展开完整 $K, V$！
- **为什么必须做“解耦 RoPE（Decoupled RoPE）”（必考追问！）**：
  - 如果直接对压缩还原后的 $k_j^C$ 施加依赖相对位置 $(t-j)$ 的旋转矩阵 $\mathcal{R}_{t-j}$，式子变成 $q_t^\top \mathcal{R}_{t-j} W^{UK} c_j^{KV}$——中间插了一个随位置动态变化的非线性旋转矩阵 $\mathcal{R}_{t-j}$，**$W^{UK}$ 就没法跨过 $\mathcal{R}_{t-j}$ 吸收到 $q_t$ 一侧了**！如果硬算就必须在每步把所有历史潜向量全解压成完整 $K$，彻底丧失加速意义。
  - **解法**：额外单开一个极轻量的**共享位置分支** $k_t^R = \mathcal{R}_t(W^{KR} h_t)$（如仅 $d_R = 64$ 维，所有头共享），与不加 RoPE 的压缩内容分支拼接计算点积。这样单层单 Token 只需缓存 $d_c + d_R = 512 + 64 = 576$ 个 BF16 元素（1,152 字节），既保住了相对位置信息，又完美实现了矩阵吸收！

---

### Q76：Prefill 与 Decode 两阶段的计算/访存瓶颈（Compute-bound vs Memory-bound）分别是什么？KV Cache 显存占用怎么手算？
- **两阶段本质差异**：
  1. **Prefill（预填充阶段）**：一次性并行输入整段长 Prompt（长度 $S$），算子是**矩阵乘矩阵（GEMM）**，算术强度（FLOPs / 访存字节数）极高，GPU Tensor Core 满载，属于 **计算受限（Compute-bound）**，核心看 TTFT（首字延迟）；
  2. **Decode（自回归逐词生成阶段）**：每次只生成 1 个新 Token（序列维度为 1），算子退化为**向量乘矩阵（GEMV）**——每生成一个词都要把几十 GB 的模型权重和全部历史 KV Cache 从慢速 HBM 显存搬到 SRAM 一遍，算力大量闲置等显存带宽，属于典型的 **访存带宽受限（Memory-bound）**，核心看 TPOT / ITL（每词间隔延迟）。
- **KV Cache 显存手算公式（当场写出来稳得分）**：
  $$\text{Bytes}_{\text{KV}} = 2_{(\text{K和V})} \times B \times S \times L_{\text{layers}} \times n_{\text{kv\_heads}} \times d_{\text{head}} \times \text{sizeof(dtype)}$$
  - **心算举例**（以 7B/8B GQA 模型为例：$L=32$ 层，$n_{\text{kv}}=8$，$d_h=128$，BF16 占 2 字节，单并发 $B=1$，上下文 $S=32\text{k}$）：
    单 Token 全层缓存 $= 2 \times 32 \times 8 \times 128 \times 2 = 131,072\text{ B} = 128\text{ KB}$；乘 $32,768$ 长度 $= \mathbf{4\text{ GB}}$（若是传统 MHA $n_{\text{kv}}=32$ 则高达 $16\text{ GB}$！）。

---

### Q77：详解 FlashAttention（Tiling + Online Softmax）与 vLLM PagedAttention（分页虚拟内存 + Prefix Caching）的核心原理。
- **FlashAttention（解决训练与长 Prefill 的 $O(N^2)$ 显存读写瓶颈）**：
  - **痛点**：标准 Attention 先算 $S = QK^\top \in \mathbb{R}^{N \times N}$ 写回慢速 HBM，读出来算 $P = \text{softmax}(S)$ 写回 HBM，再读出来乘 $V$——中间 $N \times N$ 矩阵既爆显存又反复读写慢速 HBM；
  - **两大核心技术**：① **分块计算（Tiling）**：将 $Q, K, V$ 切成小块加载进高速片上 SRAM，在 SRAM 内一气呵成算完直接写出最终输出 $O$，全程不实例化完整 $N \times N$ 矩阵，空间复杂度从 $O(N^2)$ 降为 **$O(N)$**；② **Online Softmax（在线安全重缩放）**：Softmax 需要全行最大值 $m$ 和指数和 $\ell$，分块遍历 $K_j$ 时动态维护局部运行最大值 $m^{\text{new}} = \max(m^{\text{old}}, m^{(j)})$，用缩放因子 $e^{m^{\text{old}} - m^{\text{new}}}$ 实时修正累加分子与分母，在数学上**零近似、比特级等价于标准 Attention**（反向传播不存中间矩阵而采用重计算 Recomputation 换高速）。
- **vLLM PagedAttention（解决推理并发的 KV Cache 显存碎片瓶颈）**：
  - **痛点**：生成前不知模型会吐多少个词，传统框架按 `max_seq_len` 预分配连续显存，产生严重的内部碎片与外部碎片（显存浪费高达 60%–80%，并发 Batch 上不去）；
  - **核心机制**：借鉴操作系统虚拟内存分页思想，把每个请求的逻辑 KV Cache 切成固定大小的物理 **KV Block（如每块 16 个 Token）**，通过一张页表（Block Table）映射到非连续物理显存块，按需逐块动态分配，显存浪费率压至 **<4%**，吞吐量提升 2–4 倍；
  - **对 Agent 极关键的 Prefix Caching（RadixAttention）**：多轮 Agent 每轮请求的前缀（System Prompt + 工具定义 + 前 $t-1$ 轮历史）完全相同，哈希命中物理 KV Block 直接零拷贝共享复用，省掉 80%+ 重复 Prefill 计算！

---

### Q78：现代 Decoder-only 架构细节：Pre-LN vs Post-LN、RMSNorm vs LayerNorm、SwiGLU 激活函数、RoPE 旋转位置编码与 YaRN 长外推。
- **四点速答清单**：
  1. **Pre-LN vs Post-LN**：原始 Transformer 用 Post-LN（$x_{l+1} = \text{LN}(x_l + F(x_l))$），深层主干残差被反复归一化阻断导致底层梯度消失、必须强依赖长 Warmup；现代 LLM 全用 **Pre-LN（$x_{l+1} = x_l + F(\text{RMSNorm}(x_l))$）**，恒等残差高速公路直通到底，百层深网训练极稳；
  2. **RMSNorm vs LayerNorm**：去掉减均值（Centering）和偏置项 $\beta$，只做均方根缩放 $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{d}\sum x_i^2 + \epsilon}} \odot \gamma$，少算一次规约均值，提速 10%–15% 且效果持平；
  3. **SwiGLU FFN**：$\text{FFN}_{\text{SwiGLU}}(x) = (\text{Swish}(x W_{\text{gate}}) \odot x W_{\text{up}}) W_{\text{down}}$（$\text{Swish}(z) = z \cdot \sigma(z)$）；由 2 个矩阵变成 3 个矩阵，为保持总参数量 $8d^2$ 不变，中间隐层维度从 $4d$ 缩为 **$\frac{2}{3} \times 4d = \frac{8}{3}d$**（向上对齐 128 倍数）；门控逐元素乘带来更强非线性特征选择能力；
  4. **RoPE（旋转位置编码）与 YaRN 长外推**：通过对 $q_m, k_n$ 在二维分组子空间乘绝对位置旋转矩阵 $\mathcal{R}_m, \mathcal{R}_n$，使得内积 $\langle \mathcal{R}_m q, \mathcal{R}_n k \rangle = \text{Re}(q^\top \mathcal{R}_{n-m} k)$ **只依赖相对距离 $(n-m)$**，且天然兼容线性/分块注意力；长上下文外推（NTK-aware / **YaRN**）核心是区分高频分量（局部相对位置，不做线性拉伸以防局部语义模糊）与低频分量（长程全局位置，做基底 $\theta_{\text{base}}$ 放大/插值）并配注意力温度修正。

---

### Q79：MoE（混合专家）架构核心考点：Router Top-K、负载均衡辅助损失（Aux Loss vs Loss-free Bias 调节）、DeepEP 通信，以及 MTP（多 Token 预测）+ 投机解码。
- **MoE 核心机制（结合你的 Qwen3-30B-A3B & SenseNova Flash 经验）**：
  - 将稠密 FFN 替换为 $N$ 个路由专家（细粒度拆分 + 若干常驻共享专家 Shared Experts 承载通用共性知识），每个 Token 经线性门控 $s = \text{Softmax}/\text{Sigmoid}(W_g h)$ 只激活 Top-$K$ 个专家，实现**总参数量扩容知识上限、单 Token 激活计算量保持轻量**；
  - **防专家坍缩（Load Balancing）两代方案**：若不加干预，马太效应会让所有 Token 全挤向少数几个专家（其余专家饿死，并在 Expert Parallel 跨卡 All-to-All 通信中形成严重单卡木桶卡死）。第一代加 **可微负载均衡辅助损失（Aux Loss）**，但系数大了会反向干扰主语言建模精度；第二代（DeepSeek-V3 **Aux-Loss-Free**）改为给每个专家维护一个不参与主梯度的动态偏置项 $b_i$（仅在选 Top-$K$ 时判断 $s_i + b_i$，过载专家减 $b_i$、欠载加 $b_i$，前向加权仍用原始纯净 $s_i$），既均衡负载又不伤主干精度；
  - **DeepEP**：针对 MoE 跨节点/跨卡 Token 分发（Dispatch）与聚合（Combine）的高性能低延迟 All-to-All 通信库（支持 NVLink 与 RDMA 混合重叠）。
- **MTP（Multi-Token Prediction，多词预测）与投机解码（Speculative Decoding）**：
  - **训练期**：在主头预测 $t+1$ 之外，串联轻量因果变换模块依次预测 $t+2, \dots, t+D$ 位置的 Token，使训练信号密度翻倍、迫使模型提前规划后续词句表征；
  - **推理期（自投机解码）**：直接复用自带的轻量 MTP 头一口气猜出后面 $k$ 个候选草稿词，再由主模型**一次并行前向（像 Prefill 一样高算力利用率）同时验证这 $k$ 个词**，结合拒绝采样保证输出分布**数学上 100% 无损等价于逐词解码**，吞吐提速 **1.5–1.8 倍**！

---

### Q80：模型量化（FP16 / BF16 / FP8 / INT8 SmoothQuant / INT4 AWQ & GPTQ）原理对比，以及 LoRA 参数量计算与 $A$ 高斯、$B$ 全零初始化原因。
- **精度与量化速记**：
  - **FP16 vs BF16**：FP16（1符号+5指数+10尾数）动态范围窄极易梯度上溢变 NaN（需 Loss Scaling）；**BF16（1符号+8指数+7尾数）**指数位与 FP32 完全一致，训练极稳不溢出；
  - **FP8（E4M3 / E5M2）**：Hopper/Blackwell 架构原生 Tensor Core 支持（如 SenseNova Flash FP8 / DeepSeek-V3），采用细粒度 Tile/Block 级动态缩放因子克服激活离群值（Outliers），显存减半、计算吞吐翻倍且精度近乎无损；
  - **INT8 SmoothQuant vs INT4 AWQ / GPTQ**：大模型激活值在固定几个通道有高达百倍的离群峰值（Activation Outliers）导致激活难量化——**SmoothQuant** 通过数学等价变换 $Y = (X \text{diag}(s)^{-1}) \cdot (\text{diag}(s) W)$ 把激活的量化难度平滑转移一部分给容易量化的权重；**GPTQ**（W4A16）基于近似二阶海森矩阵逐列量化并用未量化列补偿误差；**AWQ**（W4A16）发现仅 1% 对应大激活通道的显著权重最关键，对其做等价放大保护而不直接裁剪。
- **LoRA（Low-Rank Adaptation）必考细节**：
  - 公式：$h = W_0 x + \frac{\alpha}{r} B A x$，冻结 $W_0 \in \mathbb{R}^{d_{\text{out}} \times d_{\text{in}}}$，只训 $A \in \mathbb{R}^{r \times d_{\text{in}}}$ 与 $B \in \mathbb{R}^{d_{\text{out}} \times r}$（$r \ll d$），新增参数量 $r(d_{\text{in}} + d_{\text{out}})$，**推理时可直接合并进 $W' = W_0 + \frac{\alpha}{r}BA$ 实现零额外推理延迟**；
  - **为什么必须 $A \sim \mathcal{N}(0, \sigma^2)$ 高斯初始化、$B = 0$ 全零初始化？（反过来或全零/全随机行不行？）**
    1. 保证训练第 0 步时 $\Delta W = BA = 0$，模型初始输出与预训练基座**严格 100% 一致**，不破坏已学好的表征；
    2. **若 $A, B$ 全初始化为 0**：反向传播 $\frac{\partial L}{\partial A} = B^\top \frac{\partial L}{\partial (\Delta W x)} = 0$，$\frac{\partial L}{\partial B} = \frac{\partial L}{\partial (\Delta W x)} (Ax)^\top = 0$，**两边梯度全死锁为 0 永远训不动（鞍点）**！
    3. **若 $A, B$ 全随机非零**：第 0 步就往每层注入大块随机噪声改变原分布，初期梯度剧烈震荡破坏预训练知识；而“一零一随机”第 0 步 $\Delta W=0$，同时 $\frac{\partial L}{\partial B} \propto (Ax)^\top \neq 0$ 先把 $B$ 更新为非零，第 1 步起 $A, B$ 双双正常迭代（缩放因子 $\alpha / r$ 则保证调整秩 $r$ 时无需重新大改学习率）。

---

### Q81：分布式训练基础：DP / DDP、ZeRO-1/2/3（FSDP）、TP（张量并行）、PP（流水线并行）、SP/CP（序列/上下文并行）各自切什么、怎么组合？
- **显存大账本先立住**（以混合精度 Adam 训练 $\Psi$ 参数量模型为例：权重 BF16 $2\Psi$ + 梯度 BF16 $2\Psi$ + 优化器状态 FP32 主权重/一阶动量/二阶方差 $4+4+4=12\Psi$，光静态模型状态就占 **$16\Psi$ 字节**，外加随序列长和 Batch 增长的激活值 Activations！）：
  1. **DDP（数据并行）**：每卡存完整 $16\Psi$，切分数据 Batch，反向传播同步 All-Reduce 梯度；单卡塞不下大模型即失效；
  2. **ZeRO-1 / 2 / 3（DeepSpeed / PyTorch FSDP）**：本质仍是数据并行切法，但消除冗余副本——**ZeRO-1** 分片优化器状态（$12\Psi/N$）；**ZeRO-2** 再分片梯度（$(12+2)\Psi/N$）；**ZeRO-3 / FSDP** 连模型参数也分片（$16\Psi/N$，前反向按层临时 All-Gather 用完即释）；
  3. **TP（Tensor Parallelism，张量并行，Megatron）**：在层内把单个大矩阵按列切接按行切（如 MLP $W_1$ 按列切免通信过激活函数，$W_2$ 按行切做一次 All-Reduce），通信极频繁，**通常严格限制在单节点 8 卡高速 NVLink 内**；
  4. **PP（Pipeline Parallelism，流水线并行）**：按层切分到不同机器节点（跨机慢网友好，只传层间激活），配合 1F1B / DualPipe 微批次调度压小流水线气泡（Bubble）；
  5. **SP / CP（序列并行 / Ring Attention 上下文并行）**：针对超长序列（如 128K Agent 轨迹）单卡存不下激活值，沿序列长度维度切分 LayerNorm/Dropout（SP）及 $Q, K, V$ 块（CP 环状通信），与 MoE 的 **EP（专家并行）** 共同组成现代 5D 并行栈。

---

### Q82：现代工业级 RAG 全链路架构：文档解析与分块策略（Chunking）、Query 改写（HyDE/Multi-Query）、多路混合召回（Dense + BM25 + RRF）与 Cross-Encoder Rerank。
- **全链路五步标准答法**：
  1. **高保真文档解析与父子层级分块（Parsing & Hierarchical Chunking）**：PDF/表格若被硬按 500 字暴力截断，表头与数据行分离直接报废！工业界采用结构感知解析（保留 Markdown 标题树与完整表格块）+ **小块检索、大块喂入（Small-to-Big / Parent-Child Chunking，子块 256 tokens 保证向量语义聚焦，命中后取回 1024 tokens 父段落或相邻滑窗补齐上下文）**；
  2. **检索前 Query 理解与改写**：多轮对话先做指代消解补全主语；复杂模糊问题做 **Sub-query 拆解**，或用 **HyDE** 生成假设答案文档去搜相似真实文档；
  3. **多路混合召回（Hybrid Retrieval：Dense Embedding + Sparse BM25/SPLADE）**：稠密向量擅长跨表述语义泛化，但在**精确型号、SKU 编码、报错码、专有名词**上远不如词频匹配 BM25；双路并行召回 Top-50 后，用无需调参量纲对齐的 **RRF（倒数秩融合，$\text{score}(d) = \sum_m \frac{1}{k + \text{rank}_m(d)}, k=60$）** 合并；
  4. **精排重排（Cross-Encoder Reranker）**：双塔 Embedding 无法做 Query 与文档的逐词深度交互；用 Cross-Encoder（如 BGE-Reranker）对合并后的 Top-50 做联合精细打分，截出高纯度 Top-5～8 送入大模型；
  5. **带引用溯源约束生成**：强制模型标注引用块编号 `[1][2]`，无依据明确拒答。

---

### Q83：RAG 与传统搜索、以及与长上下文（Long-Context LLM）的区别与取舍边界是什么？重排模型蒸馏怎么做？
- **RAG vs 长上下文（128K–1M Context）为什么长窗口消灭不了 RAG？**
  1. **企业知识库体量是 GB～TB 级（亿级 Token）**，远超任何单次窗口；
  2. **延迟与金钱成本差百倍**：每句问答都塞 50 万字即使有缓存也极慢极贵，RAG 只精准喂 4k 相关片段；
  3. **时效权限与注意力信噪比**：RAG 支持毫秒级增删改文档与行级租户权限隔离，且消除了大海捞针中间迷失。**只有当待分析材料本身就是单次上传的一份完整财报/代码仓（几万 Token）且需要全局跨章汇总统计时（如 SlideGate 解析整份输入附件提取 `info_pack`），直接走长上下文才优于切片 RAG**（因为局部 Top-5 切片做不了“统计全表总和”这类全局聚合题！）。
- **Reranker 蒸馏怎么做（淘天二面真题）**：线上大尺寸 Cross-Encoder（或 LLM Listwise 重排）太慢，离线用大模型对 `(query, candidate_docs)` 打细粒度相关性软标签并挖掘高相似度但实际不答所问的**困难负样本（Hard Negatives）**，用 KL 散度 / MarginMSE / ListNet 损失蒸馏给轻量级 0.5B–1.5B Reranker，配合量化实现 20ms 内完成精排。

---

### Q84：如何系统量化评估一套 RAG 系统（Ragas 四大核心指标：Context Recall / Context Precision / Faithfulness / Answer Relevancy）？
- **必须把「检索侧锅」与「生成侧锅」拆开评（两阶段四象限评估）**：
  - **检索层指标**：
    1. **Context Recall（上下文召回率）**：标准答案所需的事实要点里，有多少比例成功出现在召回的 Top-$K$ 片段中？（低 → 分块碎了、Embedding 漏搜了）；
    2. **Context Precision（上下文精确率 / MRR / NDCG）**：真正有用的金标片段是不是排在 Top-$K$ 最靠前的位置，没被一堆无关噪音块淹没？（低 → Reranker 没排准或 $K$ 开太大）；
  - **生成层指标**：
    3. **Faithfulness（忠实度，与我们 SlideGate 三值忠实度完全同构！）**：把模型生成的回复拆成原子陈述（Claims），逐条核对是否完全由召回的 Context 支撑（低 → 模型无视检索结果自由发挥编造幻觉）；
    4. **Answer Relevancy（回答相关性 / 完备度）**：生成的答案是否正面、完整回应了用户的原始问题，没有答非所问或漏掉子问题。

---

### Q85：【淘天/国际高频排障】如果「检索明明命中了正确文档块，模型生成依然出现幻觉或答错」，怎么分层定位根因并解决？
- **这道题直接体现你的系统排障功力，按 5 大典型死因逐条击破**：
  1. **噪音淹没与位置迷失（Lost in the Middle）**：虽然第 7 个块命中了真答案，但前面排了 6 个字面极像（如别的型号 SKU 参数）的**强干扰块（Hard Distractors）**，模型把张冠李戴的参数拼到了一起 → **治法**：上调 Reranker 阈值砍掉低分尾巴、把高置信度块放首尾（首尾效应）、在每个 Chunk 头部显式拼接所属文档标题与商品全称元数据（Contextual Header Injection，防脱离语境张冠李戴！）；
  2. **分块截断了前提条件（Broken Context）**：命中的块写了“优惠价 99 元”，但上一块末尾写的“仅限 2024 年已截止”被切丢了 → **治法**：改用父子层级回溯或前后重叠滑窗补齐完整语义段；
  3. **新旧知识冲突（或模型内部预训练参数记忆太顽固）**：召回里既有 2025 旧规又有 2026 新规，或者事实违背模型预训练常识导致模型固执己见 → **治法**：检索侧按时间戳过滤/提权最新文档，Prompt 与 DPO 对齐侧强化“严格以所给参考资料为准，并显式输出证据块编号再作答”；
  4. **多跳推理或数值计算失误**：两块材料都齐了（A 块有单价、B 块有折扣），模型口算乘错了 → **治法**：开启 `<think>` 逐步演算或挂载代码解释器工具算账；
  5. **生成采样温度过高或后置无核查**：问答导购类将 `temperature` 压低至 $0 \sim 0.2$，对高风险价格/政策数字加轻量三值忠实度后置拦截。
