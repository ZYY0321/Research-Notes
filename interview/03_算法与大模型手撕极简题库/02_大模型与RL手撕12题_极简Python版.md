# 大模型、RL 与 Agent 手撕 12 题 · 极简背诵版（Python / PyTorch）

> **极简原则**：每题严格只留 **「标题 + 题目描述 + 一段核心思路 + 一段标准 PyTorch/Python 代码」**。全覆盖 2025–2026 阿里、月之暗面、字节、智谱等大模型与 Agentic RL 面试必考的算法组件手撕！

---

### T01. GRPO 组内归一化 Advantage 与完整 Loss（阿里 / 月之暗面最高频真题）
**题目描述**：给定 batch 内 $B$ 个 prompt、每个采样 $G$ 条变长回答的新旧对数概率 `logp_new, logp_old`（形状 `[B*G, T]`）、有效回答掩码 `mask`（Prompt/Padding/Tool 返回为 0，模型生成为 1）以及标量奖励 `rewards`（`[B, G]`），实现组内 Advantage 归一化（处理全对/全错零方差）与带 Clip + k3 KL 的 GRPO Loss。
**核心思路**：对每个 prompt 的 $G$ 个奖励算组内均值与标准差，当 `std < eps`（全对或全错）时将整组 advantage 置 0 防除零放大噪声；重要性采样比 `ratio = exp(logp_new - logp_old.detach())` 乘上 detach 后的广播优势，与裁剪项取 `min`，减去可选的 k3 低方差非负 KL 项，最后只对 `mask==1` 的有效生成 Token 聚合取负。
```python
import torch

def compute_grpo_advantages(rewards: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    # rewards: [B, G] -> returns flat advantages: [B * G]
    mean = rewards.mean(dim=-1, keepdim=True)
    std = rewards.std(dim=-1, unbiased=False, keepdim=True)
    adv = torch.where(std < eps, torch.zeros_like(rewards), (rewards - mean) / (std + eps))
    return adv.reshape(-1)

def grpo_loss(
    logp_new: torch.Tensor,   # [N, T], N = B * G, requires_grad=True
    logp_old: torch.Tensor,   # [N, T]
    rewards: torch.Tensor,    # [B, G]
    mask: torch.Tensor,       # [N, T], 1 for model action tokens, 0 for prompt/pad/tool_obs
    logp_ref: torch.Tensor = None,
    clip_eps: float = 0.2,
    beta: float = 0.01,
) -> torch.Tensor:
    adv = compute_grpo_advantages(rewards).detach().unsqueeze(-1)  # [N, 1]
    ratio = torch.exp(logp_new - logp_old.detach())
    surr1 = ratio * adv
    surr2 = torch.clamp(ratio, 1.0 - clip_eps, 1.0 + clip_eps) * adv
    obj = torch.min(surr1, surr2)
    if logp_ref is not None:
        log_r = logp_ref.detach() - logp_new
        kl_k3 = torch.exp(log_r) - log_r - 1.0
        obj = obj - beta * kl_k3
    seq_len = mask.sum(dim=-1).clamp(min=1)
    return -((obj * mask).sum(dim=-1) / seq_len).mean()
```

---

### T02. DAPO（Clip-Higher + Token-Level Loss）与 GSPO（序列级 Ratio）变体手撕（字节 / 阿里追问真题）
**题目描述**：在 T01 基础上分别写出 DAPO（解耦非对称上下裁剪 + 全局有效 Token 等权平均）与 GSPO（长度归一化序列几何平均似然比裁剪）的核心 Policy Loss 函数。
**核心思路**：DAPO 将上界放宽至 `eps_high=0.28` 保护低概率探索词不坍缩，并在分母上直接除以整个 Batch 的 `mask.sum()` 消除长序列梯度稀释；GSPO 先在序列维度对有效 Token 的对数概率差求均值再 `exp` 得到序列级比率 $s_i = (\pi_\theta/\pi_{\text{old}})^{1/|y_i|}$，整条序列统一裁剪以抹平 MoE 单 Token 路由抖动。
```python
import torch

def dapo_policy_loss(logp_new, logp_old, adv, mask, eps_low=0.2, eps_high=0.28):
    # adv: [N], mask: [N, T]
    a = adv.detach().unsqueeze(-1)
    ratio = torch.exp(logp_new - logp_old.detach())
    clipped = torch.clamp(ratio, 1.0 - eps_low, 1.0 + eps_high)
    tok_obj = torch.min(ratio * a, clipped * a) * mask
    return -tok_obj.sum() / mask.sum().clamp(min=1)

def gspo_policy_loss(logp_new, logp_old, adv, mask, clip_eps=0.1):
    # Sequence-level length-normalized importance ratio: [N]
    seq_len = mask.sum(dim=-1).clamp(min=1)
    seq_log_ratio = ((logp_new - logp_old.detach()) * mask).sum(dim=-1) / seq_len
    seq_ratio = torch.exp(seq_log_ratio)
    a = adv.detach()
    surr1 = seq_ratio * a
    surr2 = torch.clamp(seq_ratio, 1.0 - clip_eps, 1.0 + clip_eps) * a
    return -torch.min(surr1, surr2).mean()
```

---

### T03. DPO（Direct Preference Optimization）完整训练步与 Loss（阿里 Offer 场真题）
**题目描述**：给定策略模型 `policy`、冻结参考模型 `ref_model` 及成对偏好数据 `(chosen_ids, chosen_mask, rejected_ids, rejected_mask)`，实现序列有效对数概率求和与数值稳定的 DPO Loss。
**核心思路**：Causal LM 中位置 `t` 的 logits 预测 `t+1` 位置的 label（做 shift 对齐），用 `log_softmax + gather` 取出目标词 logprob 并乘 `mask`（仅回答及模型工具调用部分为 1）求和得到序列对数概率；计算策略相对参考模型在好坏轨迹上的提升差，乘 $\beta$ 后过 `-F.logsigmoid`（切忌手写 `log(sigmoid)` 防数值下溢）。
```python
import torch
import torch.nn.functional as F

def sequence_logprob(logits: torch.Tensor, input_ids: torch.Tensor, loss_mask: torch.Tensor) -> torch.Tensor:
    # Shift-by-1 alignment for Causal LM: logits[:, :-1] predicts input_ids[:, 1:]
    shift_logp = F.log_softmax(logits[:, :-1, :], dim=-1)
    shift_labels = input_ids[:, 1:].clamp(min=0).unsqueeze(-1)
    shift_mask = loss_mask[:, 1:]
    tok_logp = shift_logp.gather(dim=-1, index=shift_labels).squeeze(-1)
    return (tok_logp * shift_mask).sum(dim=-1)

def dpo_step(policy, ref_model, c_ids, c_mask, r_ids, r_mask, beta: float = 0.1) -> torch.Tensor:
    pi_logp_w = sequence_logprob(policy(c_ids), c_ids, c_mask)
    pi_logp_l = sequence_logprob(policy(r_ids), r_ids, r_mask)
    with torch.no_grad():
        ref_logp_w = sequence_logprob(ref_model(c_ids), c_ids, c_mask)
        ref_logp_l = sequence_logprob(ref_model(r_ids), r_ids, r_mask)
    logits = beta * ((pi_logp_w - pi_logp_l) - (ref_logp_w - ref_logp_l))
    return -F.logsigmoid(logits).mean()
```

---

### T04. 带 Schema 校验、错误回写与挂起恢复的 Agent Loop（阿里 Offer 场真题）
**题目描述**：手写一个生产级最小完备的 `agent_loop` 与 `resume` 函数，涵盖工具注册校验、异常结构化写回、`ask_user` 状态挂起恢复与步数上限控制。
**核心思路**：遵循“模型只提请求、Harness 负责校验与执行”原则——每轮先调 LLM，若无结构化 `tool_calls` 即正常结束；若有调用则逐一做 JSON 解析与 Schema 校验，任何解析/执行报错均封装为结构化 JSON 作为 `role="tool"` 消息带 `tool_call_id` 写回让模型下一轮自愈；遇到 `ask_user` 保存消息栈返回挂起态。
```python
import json

def execute_tool_safely(registry: dict, call: dict) -> str:
    name = call.get("name", "")
    if name not in registry:
        return json.dumps({"ok": False, "error": f"unknown_tool:{name}", "retryable": False})
    try:
        args = json.loads(call.get("arguments", "{}"))
    except Exception:
        return json.dumps({"ok": False, "error": "invalid_json_arguments", "retryable": True})
    err = registry[name]["validate"](args)
    if err:
        return json.dumps({"ok": False, "error": f"schema_error:{err}", "retryable": True})
    try:
        return json.dumps({"ok": True, "result": registry[name]["fn"](**args)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e), "retryable": False})

def agent_loop(llm, registry: dict, messages: list, max_steps: int = 20) -> dict:
    schemas = [t["schema"] for t in registry.values()]
    for _ in range(max_steps):
        resp = llm.chat(messages, tools=schemas)
        content, calls = resp.get("content") or "", resp.get("tool_calls") or []
        if not content and not calls:
            return {"status": "failed", "reason": "empty_response", "messages": messages}
        messages.append({"role": "assistant", "content": content, "tool_calls": calls})
        if not calls:
            return {"status": "done", "answer": content, "messages": messages}
        pending_ask = None
        for call in calls:
            if call["name"] == "ask_user":
                pending_ask = call
                continue
            obs = execute_tool_safely(registry, call)
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": obs})
        if pending_ask is not None:
            return {"status": "waiting_user", "pending_call_id": pending_ask["id"],
                    "question": pending_ask["arguments"], "messages": messages}
    return {"status": "max_steps_exceeded", "messages": messages}

def resume_agent(llm, registry: dict, saved_state: dict, user_reply: str, max_steps: int = 20) -> dict:
    msgs = saved_state["messages"]
    msgs.append({"role": "tool", "tool_call_id": saved_state["pending_call_id"],
                 "content": json.dumps({"ok": True, "result": user_reply}, ensure_ascii=False)})
    return agent_loop(llm, registry, msgs, max_steps=max_steps)
```

---

### T05. Grouped-Query Attention（GQA）带 Causal Mask 与 KV Cache（大模型一面高频真题）
**题目描述**：用 PyTorch 实现一个支持 GQA（查询头数 `n_heads`，KV 头数 `n_kv_heads`）及推理增量 `kv_cache` 的多头因果自注意力模块。
**核心思路**：线性投影拆出 `[B, h, S, d_h]` 的 `Q` 与 `[B, g, S, d_h]` 的 `K, V`；若有历史缓存则在序列维拼接更新缓存；利用 `repeat_interleave(h // g, dim=1)` 将每组 KV 头广播对齐到对应的查询头组，施加上三角 `-inf` 因果掩码（注意增量解码时掩码对齐总长 `T_k`）后算缩放点积注意力。
```python
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class GroupedQueryAttention(nn.Module):
    def __init__(self, dim: int, n_heads: int, n_kv_heads: int):
        super().__init__()
        assert n_heads % n_kv_heads == 0
        self.n_heads = n_heads
        self.n_kv = n_kv_heads
        self.n_rep = n_heads // n_kv_heads
        self.head_dim = dim // n_heads
        self.wq = nn.Linear(dim, n_heads * self.head_dim, bias=False)
        self.wk = nn.Linear(dim, n_kv_heads * self.head_dim, bias=False)
        self.wv = nn.Linear(dim, n_kv_heads * self.head_dim, bias=False)
        self.wo = nn.Linear(dim, dim, bias=False)

    def forward(self, x: torch.Tensor, kv_cache: tuple = None):
        B, S, _ = x.shape
        q = self.wq(x).view(B, S, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.wk(x).view(B, S, self.n_kv, self.head_dim).transpose(1, 2)
        v = self.wv(x).view(B, S, self.n_kv, self.head_dim).transpose(1, 2)
        if kv_cache is not None:
            k = torch.cat([kv_cache[0], k], dim=2)
            v = torch.cat([kv_cache[1], v], dim=2)
        new_cache = (k, v)
        if self.n_rep > 1:
            k = k.repeat_interleave(self.n_rep, dim=1)
            v = v.repeat_interleave(self.n_rep, dim=1)
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        if S > 1:
            T_k = k.size(2)
            causal = torch.triu(torch.full((S, T_k), float("-inf"), device=x.device), diagonal=T_k - S + 1)
            scores = scores + causal
        attn = F.softmax(scores, dim=-1)
        out = torch.matmul(attn, v).transpose(1, 2).contiguous().view(B, S, -1)
        return self.wo(out), new_cache
```

---

### T06. RoPE（旋转位置编码）与 RMSNorm + SwiGLU 手撕（底座结构必会）
**题目描述**：用 PyTorch 实现现代 LLM 标准三件套：`RMSNorm`、二维分块旋转的 `apply_rope` 以及 `SwiGLU` 前馈网络。
**核心思路**：`RMSNorm` 在 FP32 下计算均方根防溢出再转回原精度；`RoPE` 将最后一维拆成前后两半 `(-x2, x1)` 配合预计算的 `cos, sin` 完成复平面旋转；`SwiGLU` 用 `F.silu(w_gate(x)) * w_up(x)` 门控后过 `w_down`。
```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        norm_x = x.float() * torch.rsqrt(x.float().pow(2).mean(-1, keepdim=True) + self.eps)
        return norm_x.type_as(x) * self.weight

def apply_rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    # x: [B, H, S, D], cos/sin: [1, 1, S, D]
    x1, x2 = x[..., : x.shape[-1] // 2], x[..., x.shape[-1] // 2 :]
    rotated = torch.cat([-x2, x1], dim=-1)
    return (x * cos) + (rotated * sin)

class SwiGLUFFN(nn.Module):
    def __init__(self, dim: int, hidden_dim: int):
        super().__init__()
        self.w_gate = nn.Linear(dim, hidden_dim, bias=False)
        self.w_up = nn.Linear(dim, hidden_dim, bias=False)
        self.w_down = nn.Linear(hidden_dim, dim, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.w_down(F.silu(self.w_gate(x)) * self.w_up(x))
```

---

### T07. 多轮 Agent 轨迹 SFT Loss（精准屏蔽 System / User / Tool Observation）
**题目描述**：给定拼接好的多轮对话 `input_ids`（`[B, T]`）与每个位置的角色掩码 `assistant_mask`（仅 `role=="assistant"` 生成的推理、文本与 `tool_calls` 位置为 1，`system`/`user`/`tool_response`/padding 为 0），写出标准 SFT 交叉熵 Loss。
**核心思路**：将 `labels` 初始化为 `input_ids` 的拷贝，把 `assistant_mask == 0` 的位置全部赋值为 PyTorch `cross_entropy` 默认忽略的 `-100`；随后对 `logits[:, :-1]` 与 `labels[:, 1:]` 做错位对齐求平均损失。
```python
import torch
import torch.nn.functional as F

def agent_trajectory_sft_loss(
    logits: torch.Tensor,          # [B, T, V]
    input_ids: torch.Tensor,       # [B, T]
    assistant_mask: torch.Tensor,  # [B, T], 1 only on model-generated assistant/tool_call tokens
) -> torch.Tensor:
    labels = input_ids.clone()
    labels[assistant_mask == 0] = -100
    shift_logits = logits[:, :-1, :].contiguous()
    shift_labels = labels[:, 1:].contiguous()
    return F.cross_entropy(
        shift_logits.view(-1, shift_logits.size(-1)),
        shift_labels.view(-1),
        ignore_index=-100,
    )
```

---

### T08. 软标签知识蒸馏（带 $T^2$ 缩放）与 OPD 在策略反向 KL 蒸馏 Loss
**题目描述**：实现带温度系数 $T$ 的离线前向 KL 蒸馏损失，以及在策略蒸馏（OPD：在学生自采样序列上计算学生对教师分布的反向 KL $\mathbb{D}_{\text{KL}}(\pi_\theta \| \pi_T)$）损失。
**核心思路**：软标签蒸馏中对 logits 除以温度 $T$ 后反向梯度会缩小 $1/T^2$，故需乘回 $T^2$ 与硬标签交叉熵对齐量级；OPD 中序列由学生采样，在有效生成位置上直接最小化 $\sum_v \pi_\theta(v) (\log \pi_\theta(v) - \log \pi_T(v))$（教师侧 `no_grad`），使学生聚焦拟合教师的高概率主模态（Mode-Seeking）。
```python
import torch
import torch.nn.functional as F

def offline_kd_loss(student_logits, teacher_logits, mask, temp: float = 2.0) -> torch.Tensor:
    # Forward KL: KL(teacher || student) * T^2 over valid tokens
    s_logp = F.log_softmax(student_logits / temp, dim=-1)
    with torch.no_grad():
        t_prob = F.softmax(teacher_logits / temp, dim=-1)
    tok_kl = F.kl_div(s_logp, t_prob, reduction="none").sum(dim=-1) * (temp ** 2)
    return (tok_kl * mask).sum() / mask.sum().clamp(min=1)

def opd_reverse_kl_loss(student_logits, teacher_logits, mask) -> torch.Tensor:
    # On-Policy Distillation on student-sampled trajectories: KL(student || teacher)
    s_logp = F.log_softmax(student_logits, dim=-1)
    s_prob = s_logp.exp()
    with torch.no_grad():
        t_logp = F.log_softmax(teacher_logits, dim=-1)
    rev_kl = (s_prob * (s_logp - t_logp)).sum(dim=-1)
    return (rev_kl * mask).sum() / mask.sum().clamp(min=1)
```

---

### T09. LoRA 线性层手撕（含正确初始化与推理权重无损合并）
**题目描述**：继承 `nn.Module` 手写一个包装 `nn.Linear` 的 `LoRALinear` 层，包含标准初始化与推理期的 `merge()` 方法。
**核心思路**：冻结原线性层权重与偏置；旁路矩阵 $A \in \mathbb{R}^{r \times d_{\text{in}}}$ 用 Kaiming/高斯随机初始化，$B \in \mathbb{R}^{d_{\text{out}} \times r}$ **严格全零初始化**以保证第 0 步 $\Delta W = 0$ 且两侧梯度不死锁；合并时将 $\frac{\alpha}{r} B A$ 直接加回原权重实现零额外推理延迟。
```python
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class LoRALinear(nn.Module):
    def __init__(self, base_layer: nn.Linear, r: int = 8, alpha: float = 16.0):
        super().__init__()
        self.base = base_layer
        self.base.weight.requires_grad_(False)
        if self.base.bias is not None:
            self.base.bias.requires_grad_(False)
        self.scale = alpha / r
        self.lora_A = nn.Parameter(torch.empty(r, base_layer.in_features))
        self.lora_B = nn.Parameter(torch.zeros(base_layer.out_features, r))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        self.merged = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.base(x)
        if not self.merged:
            out = out + F.linear(F.linear(x, self.lora_A), self.lora_B) * self.scale
        return out

    @torch.no_grad()
    def merge(self):
        if not self.merged:
            self.base.weight.add_((self.lora_B @ self.lora_A) * self.scale)
            self.merged = True
```

---

### T10. Online Softmax（FlashAttention 分块安全缩放核心原语）
**题目描述**：不借助全局 `max`，仅用一次单遍分块扫描实现与 `torch.softmax(x, dim=-1)` 完全等价的 Online Softmax。
**核心思路**：沿块遍历向量，动态维护运行最大值 $m$ 与归一化分母 $\ell$；每读入新块算出新全局最大值 $m_{\text{new}} = \max(m, \max(x_{\text{block}}))$，用校正因子 $\exp(m - m_{\text{new}})$ 原地重缩放历史累加分母与分子，避免二次遍历全序列。
```python
import torch

def online_softmax_1d(x: torch.Tensor, block_size: int = 64) -> torch.Tensor:
    m = torch.tensor(float("-inf"), device=x.device, dtype=x.dtype)
    l = torch.tensor(0.0, device=x.device, dtype=x.dtype)
    for start in range(0, x.numel(), block_size):
        blk = x[start : start + block_size]
        m_blk = blk.max()
        m_new = torch.maximum(m, m_blk)
        l = l * torch.exp(m - m_new) + torch.exp(blk - m_new).sum()
        m = m_new
    return torch.exp(x - m) / l
```

---

### T11. 最小完备 BPE（Byte-Pair Encoding）Tokenizer 训练与编码（智谱一面真题）
**题目描述**：手写字符/字节级起步的 BPE 词表合并训练函数 `train_bpe` 与编码函数 `encode_bpe`。
**核心思路**：将输入初始化为单字节 ID 列表；循环 `num_merges` 轮，每轮统计当前相邻 ID 对 `(a, b)` 的最高共现频次，分配新词表 ID `256 + i` 并扫描序列原地合并该相邻对；编码时按学到的合并优先级顺序依次归约相邻对即可。
```python
from collections import Counter

def get_pair_counts(ids: list[int]) -> Counter:
    return Counter(zip(ids, ids[1:]))

def merge_pair(ids: list[int], pair: tuple[int, int], new_id: int) -> list[int]:
    out, i, n = [], 0, len(ids)
    while i < n:
        if i + 1 < n and ids[i] == pair[0] and ids[i + 1] == pair[1]:
            out.append(new_id)
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return out

def train_bpe(text: str, num_merges: int) -> dict[tuple[int, int], int]:
    ids = list(text.encode("utf-8"))
    merges = {}
    for step in range(num_merges):
        counts = get_pair_counts(ids)
        if not counts:
            break
        best_pair = counts.most_common(1)[0][0]
        new_id = 256 + step
        merges[best_pair] = new_id
        ids = merge_pair(ids, best_pair, new_id)
    return merges

def encode_bpe(text: str, merges: dict[tuple[int, int], int]) -> list[int]:
    ids = list(text.encode("utf-8"))
    while len(ids) >= 2:
        pairs = set(zip(ids, ids[1:]))
        cand = min(pairs, key=lambda p: merges.get(p, float("inf")))
        if cand not in merges:
            break
        ids = merge_pair(ids, cand, merges[cand])
    return ids
```

---

### T12. PPO GAE（广义优势估计 Generalized Advantage Estimation）逆序递推手撕
**题目描述**：给定一条或多条轨迹的逐时间步奖励 `rewards`、价值估计 `values`、终止掩码 `dones`（形状均为 `[B, T]`），用 $O(T)$ 逆序循环实现 GAE 优势 `advantages` 与目标回报 `returns`。
**核心思路**：定义 TD 残差 $\delta_t = r_t + \gamma (1 - d_t) V_{t+1} - V_t$，从最后一步 $t = T-1$ 向前逆推 $A_t = \delta_t + \gamma \lambda (1 - d_t) A_{t+1}$，最后令 Critic 拟合目标 `returns = advantages + values`。
```python
import torch

def compute_gae(
    rewards: torch.Tensor,     # [B, T]
    values: torch.Tensor,      # [B, T]
    next_value: torch.Tensor,  # [B]
    dones: torch.Tensor,       # [B, T], 1.0 if terminal else 0.0
    gamma: float = 0.99,
    lam: float = 0.95,
) -> tuple[torch.Tensor, torch.Tensor]:
    B, T = rewards.shape
    advantages = torch.zeros_like(rewards)
    last_gae = torch.zeros(B, device=rewards.device, dtype=rewards.dtype)
    for t in reversed(range(T)):
        v_next = next_value if t == T - 1 else values[:, t + 1]
        non_terminal = 1.0 - dones[:, t]
        delta = rewards[:, t] + gamma * v_next * non_terminal - values[:, t]
        last_gae = delta + gamma * lam * non_terminal * last_gae
        advantages[:, t] = last_gae
    returns = advantages + values
    return advantages, returns
```
