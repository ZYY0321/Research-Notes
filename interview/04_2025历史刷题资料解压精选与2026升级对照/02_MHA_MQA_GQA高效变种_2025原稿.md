# MHA,MQA,GQA （多头注意力及高效变种）

```Python
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple

class MultiHeadAttention(nn.Module):
    """
    简洁的 Multi-Head Attention 实现（batch_first: (B, T, D)）。
    返回: attn_output: (B, T, D), attn_weights: (B, num_heads, T, S)  (S = source length)
    """
    def __init__(self, embed_dim: int, num_heads: int, dropout: float = 0.0, bias: bool = True):
        super().__init__()
        assert embed_dim % num_heads == 0, "embed_dim must be divisible by num_heads"
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5

        # 线性变换：query/key/value 各自独立投影（更加直观）
        self.q_proj = nn.Linear(embed_dim, embed_dim, bias=bias)
        self.k_proj = nn.Linear(embed_dim, embed_dim, bias=bias)
        self.v_proj = nn.Linear(embed_dim, embed_dim, bias=bias)

        # 输出投影
        self.out_proj = nn.Linear(embed_dim, embed_dim, bias=bias)

        self.dropout = nn.Dropout(dropout)

    def _shape_heads(self, x: torch.Tensor) -> torch.Tensor:
        """
        把 (B, T, E) -> (B, num_heads, T, head_dim) 便于并行计算
        """
        B, T, E = x.size()
        x = x.view(B, T, self.num_heads, self.head_dim)
        # (B, T, H, d) -> (B, H, T, d)
        return x.permute(0, 2, 1, 3)

    def _unshape_heads(self, x: torch.Tensor) -> torch.Tensor:
        """
        把 (B, H, T, head_dim) -> (B, T, E)
        """
        B, H, T, d = x.size()
        x = x.permute(0, 2, 1, 3).contiguous()  # (B, T, H, d)
        return x.view(B, T, H * d)

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attn_mask: Optional[torch.Tensor] = None,
        key_padding_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        query: (B, L, E)
        key:   (B, S, E)
        value: (B, S, E)
        attn_mask: optional mask applied to attention scores before softmax.
                   shape can be (L, S) or (B, num_heads, L, S) or broadcastable to that.
                   mask values: float(-inf) or large negative where masked.
        key_padding_mask: optional tensor (B, S) with bool/0-1, True (or 1) indicates padding positions to mask out.
        """
        B, L, _ = query.size()
        _, S, _ = key.size()

        # 1) linear projections
        q = self.q_proj(query)  # (B, L, E)
        k = self.k_proj(key)    # (B, S, E)
        v = self.v_proj(value)  # (B, S, E)

        # 2) reshape 为多头： (B, H, L, d), (B, H, S, d)
        q = self._shape_heads(q)  # (B, H, L, d)
        k = self._shape_heads(k)  # (B, H, S, d)
        v = self._shape_heads(v)  # (B, H, S, d)

        # 3) 计算 attention scores: (B, H, L, S)
        # matmul: (B, H, L, d) x (B, H, d, S) -> (B, H, L, S)
        scores = torch.matmul(q, k.transpose(-2, -1)) * self.scale  # 缩放

        # 4) 应用 key_padding_mask: 把 padding 对应位置的分数设为 -inf
        if key_padding_mask is not None:
            # key_padding_mask: (B, S) 布尔型或 0/1
            if key_padding_mask.dtype != torch.bool:
                key_padding_mask_bool = key_padding_mask.to(torch.bool)
            else:
                key_padding_mask_bool = key_padding_mask
            # expand to (B, 1, 1, S) -> broadcast to scores shape
            mask = key_padding_mask_bool.view(B, 1, 1, S)
            scores = scores.masked_fill(mask, float("-inf"))

        # 5) 应用任意 attn_mask（例如 causal mask 或自定义矩阵）
        if attn_mask is not None:
            # 支持 (L, S) 或 (B, H, L, S) 等可广播形状
            scores = scores + attn_mask

        # 6) softmax -> attention probabilities
        attn_probs = F.softmax(scores, dim=-1)  # (B, H, L, S)
        attn_probs = self.dropout(attn_probs)

        # 7) 加权求和得到头输出 (B, H, L, d)
        attn_output_heads = torch.matmul(attn_probs, v)

        # 8) 合并头并输出 (B, L, E)
        attn_output = self._unshape_heads(attn_output_heads)
        attn_output = self.out_proj(attn_output)

        return attn_output, attn_probs  # 返回 output 及每个头的 attention map

```



![image\.png](图片和附件/image.png)



### Transformer 核心之力：多头注意力机制 \(MHA\) 及其高效变种

多头注意力机制（Multi\-Head Attention, MHA）是 Transformer 模型架构的基石，也是其能够出色处理序列数据、捕捉长距离依赖关系的核心原因。然而，随着模型规模的急剧增大，MHA 的计算和内存开销也变得尤为突出。为了解决这些问题，研究者们提出了一系列高效的变种，其中最著名的是多查询注意力（Multi\-Query Attention, MQA）和分组查询注意力（Grouped\-Query Attention, GQA）。

#### 一、 标准多头注意力机制 \(Multi\-Head Attention, MHA\)

标准的自注意力机制（Self\-Attention）允许模型在处理一个序列时，为序列中的每个词（Token）计算一个“注意力分数”，这个分数决定了在编码当前词时，应该对序列中其他词投入多少关注。MHA 则是对这一思想的扩展和升华。

**核心思想**：MHA 并非只让模型学习一组注意力模式，而是将注意力计算“并行化”到多个独立的“头”（Head）中。每个头都学习输入序列的不同子空间表示（aspects），从而让模型能够同时关注来自不同位置、不同维度的信息。

**工作流程**：

1. **线性投影 \(Linear Projection\)**：对于输入序列的每个 Token，其词嵌入向量会被三个独立的、可学习的线性层（权重矩阵 `Wq`, `Wk`, `Wv`）分别投影，生成三个向量：查询（Query, Q）、键（Key, K）和值（Value, V）。

2. **拆分到多头 \(Split into Heads\)**：将生成的 Q, K, V 向量在特征维度上均匀地拆分成 `h` 份（`h` 是头的数量）。例如，如果模型维度是 512，头数是 8，那么每个头的 Q, K, V 向量维度就是 64。现在，我们得到了 `h` 组独立的 Q, K, V 矩阵。

3. **并行计算注意力 \(Scaled Dot\-Product Attention\)**：对于每一个头，独立地执行缩放点积注意力计算：

    - 计算查询（Q）和键（K）的点积，得到注意力分数。

    - 将分数除以一个缩放因子（通常是 K 向量维度的平方根），以防止梯度过小。

    - 通过 Softmax 函数将分数归一化，得到权重。

    - 将权重与对应的值（V）向量相乘。

4. **拼接与最终投影 \(Concatenate \& Final Projection\)**：将所有 `h` 个头计算得到的输出向量拼接在一起，然后通过最后一个线性层（权重矩阵 `Wo`）进行投影，得到最终的输出。

**优势**：

- **捕捉多样化信息**：不同的头可以学习到不同的依赖关系，例如有的头可能关注语法结构，有的头可能关注语义关联。

- **强大的表示能力**：通过结合多个子空间的表示，模型能够更全面地理解输入序列。

**劣势**：

- **计算和内存开销大**：在解码（生成）阶段，需要为序列中的每个 Token 都缓存其对应的 K 和 V 向量（KV Cache）。随着序列长度的增加，这个缓存会变得非常庞大，消耗大量 GPU 显存，并拖慢推理速度。

#### 二、 多查询注意力 \(Multi\-Query Attention, MQA\)

为了解决 MHA 在推理过程中的显存瓶颈问题，MQA 被提了出来。

**核心思想**：所有头共享同一组键（Key）和值（Value）投影。

**工作流程**：

1. **查询（Q）**：与 MHA 相同，查询向量 Q 仍然被拆分到 `h` 个头中，每个头拥有独立的查询投影。

2. **键（K）和值（V）**：不再为每个头创建独立的 K 和 V 投影。整个模型只有 **一组** K 和 V 投影。

3. **注意力计算**：`h` 个头的查询（Q）向量，全部与这 **唯一** 的 K 和 V 向量进行注意力计算。

**优势**：

- **显著减少 KV 缓存**：由于所有头共享 K 和 V，KV 缓存的大小从 `[batch_size, num_heads, seq_len, head_dim]` 缩减为 `[batch_size, 1, seq_len, head_dim]`，内存占用大幅降低。

- **加快推理速度**：加载 K 和 V 到计算核心的内存带宽需求大大减少，从而显著提升了生成速度。

**劣势**：

- **可能导致性能下降**：由于所有头被迫共享同一套 K 和 V，这限制了它们学习不同表示的能力，可能导致模型质量出现一定程度的下降。

- **训练不稳定**：在某些情况下，MQA 可能比 MHA 更难训练。

#### 三、 分组查询注意力 \(Grouped\-Query Attention, GQA\)

GQA 是对 MHA 和 MQA 的一种折中方案，旨在平衡性能、效率和模型质量。

**核心思想**：不再是所有头共享一套 K/V，也不是每个头都有一套独立的 K/V，而是将查询头分成若干个组，**组内的查询头共享同一套 K 和 V 投影**。

**工作流程**：

1. **分组**：将 `h` 个查询头分成 `g` 个组，每个组包含 `h/g` 个查询头。

2. **投影**：创建 `g` 组独立的 K 和 V 投影。

3. **注意力计算**：每个组内的查询头共享该组的 K 和 V 向量进行注意力计算。

**与 MHA 和 MQA 的关系**：

- 当 `g=h`（组数=头数）时，GQA 就等价于 **MHA**（每个头都是一个独立的组）。

- 当 `g=1`（只有 1 个组）时，GQA 就等价于 **MQA**（所有头都在一个组内）。

**优势**：

- **灵活的权衡**：通过调整组数 `g`，可以在推理速度/内存占用和模型质量之间找到一个理想的平衡点。

- **性能优于 MQA**：实验表明，GQA 的模型质量通常优于 MQA，并且非常接近于 MHA。

- **效率高于 MHA**：相比 MHA，GQA 显著减少了 KV 缓存大小和内存带宽需求，实现了更快的推理。



