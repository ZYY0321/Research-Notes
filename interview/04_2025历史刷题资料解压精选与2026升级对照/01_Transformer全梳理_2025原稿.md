# Transformer 全梳理

## RNN 循环神经网络 

![image\.png](图片和附件/image%201.png)

循环神经网络（Recurrent Neural Network, RNN）是一类专门用于处理序列数据的人工神经网络。\[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQG6uBgMFq-YJfN-wZjbtkSuEdHfnqzMMmvqoLnd3Ik1SW9SqiNSB4qGfX29lhmuvOjRX2_TBXoSPOZ_h8zvmQpxEC5W23wWundKoScWpYvZAPu788qAUj2x4io95zaB-cYJ)\]\[[2](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQGXu9tSHsoYq8VBtzPjMyEJaE6XMtmzja7CPdj_l3M1gGcxflRy0KST2DrIdnmO7qaTTyBhxtQD9heIgDRgF4Uq0t0z1HkImyClwys6--4fVH0pveLfW7KOIZPkjVEFVFvz3lM-CT4TCsZMxsDkBT8NoUv958XY)\] 与一次性处理所有输入的前馈神经网络不同，RNN 的设计使其能够识别数据中的时间动态行为和模式，例如文本、语音或时间序列数据。\[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQG6uBgMFq-YJfN-wZjbtkSuEdHfnqzMMmvqoLnd3Ik1SW9SqiNSB4qGfX29lhmuvOjRX2_TBXoSPOZ_h8zvmQpxEC5W23wWundKoScWpYvZAPu788qAUj2x4io95zaB-cYJ)\]\[[3](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQGSDFbFiPQE9Iuy3maTkSoGaOah9S2E_mLnafjuTknxVelWWvd7JJLyqEBEdfqlxjAnMsyST4B3MOYV44sht-nD7Ipys56Fb5V1m8sg6RF_8LBkVYUOCFyG99MN3b5ZryjlP8DLs3POzdTG418_AtcoDQ%3D%3D)\]

#### 核心思想：循环与记忆

RNN 的核心在于其内部的循环（或称为“反馈环”）。在处理一个序列时（例如一个句子中的单词），RNN 会按顺序对每个元素进行操作。在处理当前元素时，它不仅会考虑当前的输入，还会利用从上一步处理中获得的信息。\[[4](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQGXg8__lw7qm12-b8ojuvG9yi4olHc2ERxRH1TUrAKBRlzuDYjRmRb5M6GzSNa5wD180yWpZOo4Mu7dPoA4AS3xfzbncOUmarWCQwcuje9px54mi3d4AmjcbkH-Ij3FMmAVAo4t08g%3D)\]

这个被传递的信息称为**隐藏状态（Hidden State）**，可以看作是网络的“记忆”。\[[4](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQGXg8__lw7qm12-b8ojuvG9yi4olHc2ERxRH1TUrAKBRlzuDYjRmRb5M6GzSNa5wD180yWpZOo4Mu7dPoA4AS3xfzbncOUmarWCQwcuje9px54mi3d4AmjcbkH-Ij3FMmAVAo4t08g%3D)\]\[[5](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQHvpT0w1WGU3J7QKpkDMR9gmVwaZ89s107E5paaN3Ka4mLC9dobgQ7fx0dMkPGkas1829QE4iU8_uAncy9tL9d11EYaj3lWmFSGfzo1vsoJ4nXcldlLeFyQi1bXlAtTNLGBzs3BaOLxVbD7c8NxAsIzOokUkjY%3D)\] 隐藏状态会捕捉截至目前为止的序列信息，并将其传递给下一步，从而影响后续的输出。\[[6](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQExZ5L7BhgRW4FjSWAZkifU0oRFRyIl1KNAKhOSwQ0dqp4H4kaySuYUJcxl4SL2yyDeLfKrkqeANh8-TH81TxzrK2wPvgn0yLV2455d_VuedHKRDzsInd9hwe1oACJjQxj4XmDLhls7f13rdBN4HSLHKifb)\] 这种结构使得 RNN 能够将先前的信息内容与当前任务联系起来，这对于理解上下文至关重要，比如理解一个句子的含义需要记住前面出现的词。\[[7](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQHutgblX9BIlJp16vqWkJM0OU0CVvPyHrLTPydtgvewH8kJRziiCW0IOiBXrb1Isal7GD8vctQA7KibH-5ln20aydVjxykd4DJhZU3N2m3exxUdq-y6dE_Q0Ig-M4flnxrNO2qkJe3E9P3B5XPyPXRjmbldWNKDg92jtYeo-N_ju3144SM%3D)\]

#### 工作方式简述：

1. **输入**: RNN 接收序列中的第一个元素（例如，句子的第一个词）。

2. **处理与更新**: 网络处理该输入，并生成一个输出和一个隐藏状态。

3. **循环**: 在处理序列的下一个元素时，RNN 会将上一步产生的隐藏状态与新的输入结合起来，再次生成输出和更新后的隐藏状态。

4. **重复**: 这个过程会一直持续到序列的所有元素都被处理完毕。

一个关键特征是，RNN 在序列的每个时间步都使用**相同的权重参数集，这极大地减少了模型的参数数量**。\[[4](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQGXg8__lw7qm12-b8ojuvG9yi4olHc2ERxRH1TUrAKBRlzuDYjRmRb5M6GzSNa5wD180yWpZOo4Mu7dPoA4AS3xfzbncOUmarWCQwcuje9px54mi3d4AmjcbkH-Ij3FMmAVAo4t08g%3D)\]\[[5](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQHvpT0w1WGU3J7QKpkDMR9gmVwaZ89s107E5paaN3Ka4mLC9dobgQ7fx0dMkPGkas1829QE4iU8_uAncy9tL9d11EYaj3lWmFSGfzo1vsoJ4nXcldlLeFyQi1bXlAtTNLGBzs3BaOLxVbD7c8NxAsIzOokUkjY%3D)\]

#### 应用领域

由于其处理序列数据的能力，RNN 在许多领域都取得了成功，尤其是在自然语言处理（NLP）方面，包括：

- **语言翻译**\[[5](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQHvpT0w1WGU3J7QKpkDMR9gmVwaZ89s107E5paaN3Ka4mLC9dobgQ7fx0dMkPGkas1829QE4iU8_uAncy9tL9d11EYaj3lWmFSGfzo1vsoJ4nXcldlLeFyQi1bXlAtTNLGBzs3BaOLxVbD7c8NxAsIzOokUkjY%3D)\]\[[8](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQEc42EvtKM2qsf8JfSKSbdWWsNiEZHF-i0VV03ipO9VbcAPRR2Q2PCxi1M8eK4W1piYGaHODVgA6qMN1TlI9fGeQ4yNMgnOmFU4zg5B6NZmOcuK9GCMJhS1PtDnd2nF4bHppIEyuEKBAf6MAoCZ1KdsEC_3N9oFxTGGZtQ%3D)\]

- **语音识别**\[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQG6uBgMFq-YJfN-wZjbtkSuEdHfnqzMMmvqoLnd3Ik1SW9SqiNSB4qGfX29lhmuvOjRX2_TBXoSPOZ_h8zvmQpxEC5W23wWundKoScWpYvZAPu788qAUj2x4io95zaB-cYJ)\]\[[3](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQGSDFbFiPQE9Iuy3maTkSoGaOah9S2E_mLnafjuTknxVelWWvd7JJLyqEBEdfqlxjAnMsyST4B3MOYV44sht-nD7Ipys56Fb5V1m8sg6RF_8LBkVYUOCFyG99MN3b5ZryjlP8DLs3POzdTG418_AtcoDQ%3D%3D)\]

- **情感分析**\[[5](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQHvpT0w1WGU3J7QKpkDMR9gmVwaZ89s107E5paaN3Ka4mLC9dobgQ7fx0dMkPGkas1829QE4iU8_uAncy9tL9d11EYaj3lWmFSGfzo1vsoJ4nXcldlLeFyQi1bXlAtTNLGBzs3BaOLxVbD7c8NxAsIzOokUkjY%3D)\]\[[8](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQEc42EvtKM2qsf8JfSKSbdWWsNiEZHF-i0VV03ipO9VbcAPRR2Q2PCxi1M8eK4W1piYGaHODVgA6qMN1TlI9fGeQ4yNMgnOmFU4zg5B6NZmOcuK9GCMJhS1PtDnd2nF4bHppIEyuEKBAf6MAoCZ1KdsEC_3N9oFxTGGZtQ%3D)\]

- **文本生成**

#### 主要局限：短期记忆问题

尽管 RNN 在理论上可以处理任意长度的序列，但标准的 RNN 在实践中难以捕捉长距离的依赖关系。\[[9](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQFq7RInUhYFQep-M5qknoZrTqXpbgOMeq5Q-pAdZYJsCHR-7Umb19_O5elS3ythDEJUI4ewaVz6aoEOcHBUlSOZJmYNPFGFgbq1Pv6G4jdpYR9suRUWOOag6TCq191VtNc9nt4ju6cB7cymv_q9IWiGuw188sD5EWGBW3nehqlriW4_uEQy1Fo_-jQCPPlxp0A%3D)\] 这是由于在训练过程中（使用一种称为“沿时间反向传播”的算法），梯度可能会随着序列变长而变得非常小（**梯度消失**）或非常大（**梯度爆炸**）。\[[7](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQHutgblX9BIlJp16vqWkJM0OU0CVvPyHrLTPydtgvewH8kJRziiCW0IOiBXrb1Isal7GD8vctQA7KibH-5ln20aydVjxykd4DJhZU3N2m3exxUdq-y6dE_Q0Ig-M4flnxrNO2qkJe3E9P3B5XPyPXRjmbldWNKDg92jtYeo-N_ju3144SM%3D)\]\[[9](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQFq7RInUhYFQep-M5qknoZrTqXpbgOMeq5Q-pAdZYJsCHR-7Umb19_O5elS3ythDEJUI4ewaVz6aoEOcHBUlSOZJmYNPFGFgbq1Pv6G4jdpYR9suRUWOOag6TCq191VtNc9nt4ju6cB7cymv_q9IWiGuw188sD5EWGBW3nehqlriW4_uEQy1Fo_-jQCPPlxp0A%3D)\]

- **梯度消失**：导致网络难以学习到序列中相距较远的元素之间的关联，从而限制了其“记忆”的长度。

- **梯度爆炸**：会导致训练过程不稳定。

为了解决这个问题，研究人员开发了更复杂的 RNN 变体，最著名的是**长短期记忆网络（LSTM）和门控循环单元（GRU）**。这些模型引入了“门”机制，可以更有选择性地保留、遗忘或传递信息，从而更有效地处理长期依赖问题。此外，还有**双向RNN（BRNN）**，它能同时从前向和后向两个方向处理序列，从而更好地捕捉上下文信息。



## Transformer



![image\.png](图片和附件/image.png)



Transformer 是一个完全基于注意力机制的深度学习模型，最初在论文《Attention Is All You Need》中被提出，用于机器翻译任务。它摒弃了传统的循环（RNN）和卷积（CNN）结构，在处理序列数据方面取得了革命性的突破。其核心优势在于强大的并行计算能力和捕捉长距离依赖关系的能力。

Transformer 的整体架构可以分为两个主要部分：**编码器（Encoder）和解码器（Decoder）**。

## 整体输入与输出

- **输入**: 原始输入序列（例如，一个句子）首先会经过\*\*词嵌入（Embedding）\*\*层，将每个词转换成一个固定维度的向量。

- **位置编码（Positional Encoding）**: 由于 Transformer 没有循环结构，无法天然地感知序列中词的顺序。因此，它引入了位置编码，将每个词的位置信息注入到词嵌入向量中，让模型能够区分同一个词在不同位置的含义。

- **输出**: 模型最终会输出一个目标序列（例如，翻译后的句子）。

## 编码器（Encoder）

编码器的作用是处理输入序列，并将其转换成一系列富含上下文信息的连续表示（即一组向量）。一个完整的编码器由 N 个相同的层堆叠而成（在原论文中 N=6）。

每个编码器层包含两个核心子层：

#### a\. 多头自注意力机制 \(Multi\-Head Self\-Attention\)

这是 Transformer 最核心的部分。

- **自注意力 \(Self\-Attention\)**: 允许模型在处理一个词时，能够关注到输入序列中的所有其他词，并计算它们对于当前词的重要性（即“注意力权重”）。这使得模型能够理解一个词在具体语境下的含义。例如，在句子 "The animal didn't cross the street because **it** was too tired" 中，自注意力机制可以帮助模型理解 "it" 指代的是 "The animal"。

- **多头 \(Multi\-Head\)**: 与其只进行一次自注意力计算，多头机制是将输入向量拆分成多个子空间，在每个子空间中独立地进行自注意力计算。这允许模型从不同的“角度”关注输入序列的不同部分，捕捉到更丰富的特征。最后，将所有头的输出拼接并线性变换，得到最终的输出。

#### b\. 前馈神经网络 \(Feed\-Forward Network\)

在多头注意力层之后，每个位置的输出都会经过一个简单但完全连接的前馈神经网络。这个网络包含两个线性层和一个 ReLU 激活函数，用于对注意力层的输出进行非线性变换，增加模型的表达能力。

**此外，每个子层（注意力层和前馈网络）都包含：**

- **残差连接 \(Residual Connection\)**: 将子层的输入直接加到其输出上。这有助于防止在深度网络中出现梯度消失问题，使得模型更容易训练。

- **层归一化 \(Layer Normalization\)**: 对每个子层的输出进行归一化，稳定训练过程。

## 解码器 \(Decoder\)

解码器的作用是接收编码器的输出，并结合已经生成的部分目标序列，来预测下一个词。与编码器类似，一个完整的解码器也是由 N 个相同的层堆叠而成。

每个解码器层包含三个核心子层：

#### a\. 带掩码的多头自注意力机制 \(Masked Multi\-Head Self\-Attention\)

这一层与编码器中的自注意力层类似，但有一个关键区别：它在计算注意力时引入了**掩码（Masking）**。在生成目标序列的第 i 个词时，模型只能关注到前 i\-1 个已经生成的词，而不能“看到”未来的词。这是为了防止模型在训练时作弊，确保其预测行为与实际推理时一致。

#### b\. 编码器\-解码器注意力机制 \(Encoder\-Decoder Attention\)

这一层是连接编码器和解码器的桥梁。它允许解码器中的每个位置都能够关注到编码器输出的所有位置。这使得解码器在生成当前词时，能够有效地利用输入序列的全部信息。例如，在翻译时，这一层帮助模型决定当前要翻译的词与源句中的哪个词最相关。

#### c\. 前馈神经网络 \(Feed\-Forward Network\)

这一层与编码器中的前馈网络完全相同，用于进一步处理信息。

与编码器一样，解码器的每个子层也都包含了残差连接和层归一化。

1. 最后的输出层

解码器栈的最终输出会经过一个\*\*线性层（Linear Layer）\*\*和一个 **Softmax 层**。

- **线性层**: 将解码器的输出向量映射到整个词汇表的大小。

- **Softmax 层**: 将线性层的输出转换成一个概率分布，表示下一个词可能是词汇表中每个词的概率。概率最高的那个词就是最终的预测结果。

### 总结

Transformer 的结构通过以下创新实现了性能的飞跃：

- **完全基于注意力机制**：高效捕捉全局依赖关系。

- **并行化计算**：相比 RNN，训练速度大大提升。

- **位置编码**：弥补了没有循环结构所带来的顺序信息缺失。

- **编码器\-解码器架构**：使其成为处理序列到序列（Seq2Seq）任务的强大框架。

### 注意力机制的核心计算公式

Transformer 中使用的注意力机制被称为 **“缩放点积注意力”（Scaled Dot\-Product Attention）**。其计算可以分解为以下几个步骤，输入是三个向量：**查询（Query, Q）**、**键（Key, K）** 和 **值（Value, V）**。

可以把这个过程类比于在图书馆（信息库）中查找信息：

- **Query \(Q\)**: 你脑中的问题或想要查询的主题。

- **Key \(K\)**: 图书馆里每本书的书名或索引标签，你可以用你的问题去和这些标签匹配。

- **Value \(V\)**: 书籍的实际内容。

计算过程如下：

**公式：**
`Attention(Q, K, V) = softmax( (Q * K^T) / sqrt(d_k) ) * V`

**分解步骤：**

1. **计算相似度分数（Score）**: 将你的查询向量 `Q` 与所有键向量 `K` 进行点积运算 \(`Q * K^T`\)。这个点积的结果衡量了查询 `Q` 与每个键 `K` 的相似度或相关性。分数越高，代表相关性越强。

2. **缩放（Scaling）**: 将得到的分数除以一个缩放因子 `sqrt(d_k)`，其中 `d_k` 是键向量 `K` 的维度。这一步非常重要，可以防止在维度很高时点积结果过大，导致 softmax 函数进入梯度极小的区域，从而稳定训练过程。

3. **计算注意力权重（Weights）**: 将缩放后的分数输入到一个 **Softmax** 函数中。Softmax 会将分数转换成一个概率分布，所有权重的和为 1。每个权重值表示在当前查询 `Q` 下，应该对相应的值 `V` 投入多少“注意力”。

4. **加权求和（Weighted Sum）**: 将上一步得到的注意力权重与对应的值向量 `V` 相乘，然后将所有结果相加。权重越高的 `V` 向量在最终的输出结果中占的比重就越大。

最终的输出是一个加权后的向量，它融合了所有 `V` 的信息，但侧重于那些与 `Q` 最相关的部分。

### Self\-Attention \(自注意力\)

自注意力，有时也叫内部注意力（intra\-attention），是 **在单个序列内部** 计算注意力的一种机制。它的目的是捕捉序列中不同单词之间的相互关系，从而为每个单词生成一个富含上下文信息的表示。

- **Q, K, V 的来源**: 在自注意力中，**查询（Q）、键（K）和值（V）均来自同一个输入序列**。具体来说，输入序列的每个词向量会分别通过三个不同的线性变换（乘以三个独立的权重矩阵 `W_Q`, `W_K`, `W_V`）来生成自己对应的 Q, K, V 向量。

- **作用**: 它回答的问题是：“当处理这个序列中的某个词时，我应该关注这个序列中的哪些其他词？”

- **例子**: 在句子 "The animal didn't cross the street because **it** was too tired" 中，自注意力机制在处理单词 "it" 时，能够计算出 "it" 与 "The animal" 的相关性得分最高，从而将更多的注意力放在 "The animal" 上，理解 "it" 指代的是 "animal"。

- **使用位置**:

    - **编码器（Encoder）** 的每一层都使用自注意力。

    - **解码器（Decoder）** 的第一个注意力子层使用**带掩码的自注意力（Masked Self\-Attention）**。

### Cross\-Attention \(交叉注意力\)

交叉注意力是 **在两个不同的序列之间** 计算注意力的机制。它连接了编码器和解码器，让解码器在生成输出时能够“关注”输入序列的信息。

- **Q, K, V 的来源**: 在交叉注意力中，Q, K, V 来自不同的源头：

    - **查询（Q）**: 来自 **解码器** 的序列（即解码器前一层的输出）。它代表解码器在生成下一个词时，“想要查询”的信息。

    - **键（K）和值（V）**: 来自 **编码器** 的输出序列。它们代表了可供查询的原始输入信息库。

- **作用**: 它回答的问题是：“为了生成目标序列的下一个词，我应该关注源序列中的哪些词？”

- **例子**: 在机器翻译任务中，将 "Je suis étudiant"（法语）翻译成 "I am a student"（英语）。当解码器准备生成 "student" 这个词时，交叉注意力机制会帮助它将注意力集中在编码器输出中与 "étudiant" 对应的向量上。

- **使用位置**:

    - **解码器（Decoder）** 的第二个注意力子层（位于带掩码的自注意力和前馈网络之间）。

### 总结对比

理解这两种注意力机制的差异是掌握 Transformer 工作原理的关键。自注意力负责理解上下文，而交叉注意力负责在不同上下文之间建立联系。



## Transformer 相较于RNN 类模型的好处 

与循环神经网络（RNN）和卷积神经网络（CNN）等早期模型相比，Transformer 模型在多个方面展现出显著优势，彻底改变了自然语言处理（NLP）领域，并对计算机视觉等其他领域产生了深远影响。其核心优势在于创新的架构设计，有效解决了先前模型的一些根本性局限。

### Transformer 模型的主要优势：

1. 更高效的并行计算能力

传统上，RNN 及其变体（如 LSTM 和 GRU）按顺序处理序列数据，这意味着模型必须处理完前一个词元才能处理下一个，这种固有的顺序性阻碍了并行计算，导致在处理长序列时训练速度缓慢。\[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQH-LHt-vYRgUow8QYPnEnYgwm3OA2zG3UVIUFcPX8J0UFFspO9u8QVC6R6DQhcetWtJd-4Ze-v_WYoJ4rnr3uy_6o3Yw1WslDDTNQ0Kp-GnX_78lwjpgXXB4nsWUdjA1fSFkC6aZZwi)\]\[[2](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQHtUJX7APU9p_GHGuCWEYQ9pjC4kojeHulgH-Qt5xHZhh9Gyr7eFrRQxTbdvve0xOjp1pvDQutcKQx8E9FQSFu4b2r1JE4Dv6Mx28qisdkC07jwivxAUCVyhU06qurfnL1lD5WBGVrCLcsz4k88TA%3D%3D)\]

相比之下，Transformer 模型完全摒弃了循环结构。\[[3](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQFNvMpUdjGZPFSxXS_aHK_4-o5gV8DacV-gXkZeZDyfOlHe-aEBmifFuOGO9DcG4VQWflE8XbKDDLEpKqnnsC8pfhgF0kOXh47HhedNnICkhGYl_ZW0TPXMaepa1T4sMv-5se1pNqODyxU943XNEidk876GKsgbj86yPAjVCBg2I68%3D)\] 其核心的自注意力机制（Self\-Attention）能够同时处理输入序列中的所有词元，独立计算它们之间的关系。\[[4](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQG2FFNojUUCw9mLusLwxvvhBwAd23zCW3kfhIxPxJ8eaqzWy-p7Pfd2Su2anMxxjn_8A_oKSA5qVttLEpnSOINtOloEK3XFRxoXcM2KwDK2wcpxm-fhaeD2m3w6tNY1_Tkhf1o%3D)\] 这种设计使得计算可以在现代硬件（如 GPU 和 TPU）上大规模并行化，从而显著缩短了训练时间。\[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQH-LHt-vYRgUow8QYPnEnYgwm3OA2zG3UVIUFcPX8J0UFFspO9u8QVC6R6DQhcetWtJd-4Ze-v_WYoJ4rnr3uy_6o3Yw1WslDDTNQ0Kp-GnX_78lwjpgXXB4nsWUdjA1fSFkC6aZZwi)\]\[[5](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQGrzaDCYQif1SQQSn3su9jH8ySUNBpTE8iH9ZhL_hXVmybuK16GqwMK5yrfMBJ86-z6NbRF8_38zzEs9zYuFdEKu9FpVwhngSNqRevL1VnLVEmXaeeMvZbOl6D4uUm93X-socjcQENJI16t4ejqB1EXyPxtdyambA%3D%3D)\]

2. 更强大的长距离依赖关系捕捉能力

在处理长文本时，RNN 模型常常会遇到梯度消失或梯度爆炸的问题，难以有效捕捉序列中相距较远的词元之间的依赖关系。\[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQH-LHt-vYRgUow8QYPnEnYgwm3OA2zG3UVIUFcPX8J0UFFspO9u8QVC6R6DQhcetWtJd-4Ze-v_WYoJ4rnr3uy_6o3Yw1WslDDTNQ0Kp-GnX_78lwjpgXXB4nsWUdjA1fSFkC6aZZwi)\]\[[6](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQE61hWo23Ow3laODNUIhDYH0bY2OhHHm-vfexp7l2a4PUUWHOt1M0_5DTUb69RL8l8j6yr-m-AVbbvstcumvpdFtZJbJgwC_Xt9_kT3Ft-T6jo3UOdWw8pe1CTSZyYFn4aODG0Ed6MGJvafOsIBmPiz-WKbmvaPn3t7WOctTAfuxybkIa3CXm4ucjnqBmc96NL9YzmKaLb9x1UOgc9Qkd7gUR7Hw5jVlG7kDcdxtrJhqqRUyyxB-6lkCtfj1dx60IvR3TmgIJ4kMjE8mUylbbeciYBLg9BPhJQ2xZklW1WletaTcyI1wCPIPn6_hbvVShf7z23FaLHqKg0yBJs9840mEhj7OAw%3D)\]\[[7](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQFhT8FKPYo0L2jzUe5QXFnM3brx6tqQsGZwB_WaXbcEF2A5OWfRJQjd0aH1LLYL5HdyWzMJuQmpZJvD0_j5vb66e1ClgX2nPmCCVrWAta9lNBTFdEcBNadh4Oej2nK-0TdMAQ%3D%3D)\]

Transformer 通过自注意力机制解决了这一难题。\[[8](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQE29o3gwK8lQuGAKmvRA2ejqmlH0qmPoEymGSPev-_IldhPejKgkRlYVJbhW36Qya3NrRePve2xxHBtZA85DvMcK-Hmyt0hAM4zc0zc271bOQCVC0ZQiItq43EGrd8OsdqDamzK-G5oqkXKIu3e0_vh7Ax4qSjE2lDaPw%3D%3D)\] 该机制允许模型在处理每个词元时，直接衡量序列中所有其他词元的重要性，并建立直接联系，而不考虑它们之间的距离。\[[9](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQFRv_Tjw4mWmtoP370zY-1CiH4DNoBcxCg8snRyR-DURkHBR0O7CqcsYO7hRzZAZGalNCvaF9uXNIwwHwVDOe2NbRmwJVBOw84_DzHFz5icHv6InylHpPqb9_6op1ck3QKla-wP3JjAXa_ByG-Bfm0p7vbIbFM5yA%3D%3D)\] 这使得 Transformer 能够非常有效地捕捉全局上下文信息和长距离依赖关系。\[[10](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQFDS_V5DXTYXPBvLIxFjEM9YZuczjDI5GZ9LroKo47RsoUB75BVrjlTjrGwfOcNMmdVXf0PZhXhfUlTrhCfJ29b68PgPvEA2sJuySpfo2wXH4Ozgfn_SbBVRiu7DHt1HjeBbuxluF_4eKOTYGYQ1mQr1I7ApMGTLtawFZ3StKqHFlW-5KAmz8ZI)\]\[[11](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQGoxCTlAPSm2AO4IwakepddHyxaUtOU3B9WTNeLIpY_r7lwpO9wdgc7TZivdv2RgV8NiyYc4VwVtrFQGCgM-MWl1mjr5TlbrzZG5fv776eHsl36GphpWOJNJdz_GOhrb1LRQDRvrS8am2iTvUVGnyd0nX4yHUdDeqw%3D)\]

3. 更出色的可扩展性和对大规模预训练的支持

Transformer 架构的并行计算优势和高效的长距离依赖建模能力，使其非常适合在海量数据集上进行训练。\[[12](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQH0JmIjwHNguEnHCA5BeOMKdIKD6hiHDEpbRxi3iYi9nC4zg7HnvvbXZny5lJAbDWt_TK3SY8iYVScuXp3mSxHwWQdLT3PM7AkjLPEqzvr3Acfx60K_vQeWy2PzKJqFdS8bnJ1NAJ5oAfnMmXo0YkmimBNn6WxC2gcBpsyeaWPRBMuEkkvx79ci2fQ%3D)\] 这催生了像 BERT 和 GPT 这样的大型语言模型（LLMs）。\[[3](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQFNvMpUdjGZPFSxXS_aHK_4-o5gV8DacV-gXkZeZDyfOlHe-aEBmifFuOGO9DcG4VQWflE8XbKDDLEpKqnnsC8pfhgF0kOXh47HhedNnICkhGYl_ZW0TPXMaepa1T4sMv-5se1pNqODyxU943XNEidk876GKsgbj86yPAjVCBg2I68%3D)\]\[[13](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQG_pAe9Oe-6doPTHrB4JOYb-wPWVq4UdxulwuA8apg5yfqSDRiuyP7yZe5J4BWbte4kcElNNoa1E68yz64tu-2Zs_6E6OGJ28rmvM7Oj49F7y4z8j1yIBzG_bs8Yls-J9iDY9_pe7xfhSrLoA%3D%3D)\] 这些模型可以通过在庞大的文本语料库上进行预训练，学习到丰富的语言知识，然后通过微调（fine\-tuning）快速适应各种下游任务，并取得最先进的性能。\[[14](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQGlyH5mqGlxN_l-SJu9xEi3HPALFjS_ZDR4Xtlrk49G2bDXfcU1W1i3sewF4J4BaSG01JDJUgavRz1N_aQhvHw-bdPOMtv6ed_xOLCDUenBzoy4hlW2auVsq08JTt1GAQxHHflgZ33c4jxMtwoqsdZXpCiAueM0c97VyC5P_EfncjAThg%3D%3D)\]

4. 更强的灵活性和广泛的应用领域

最初为机器翻译任务设计的 Transformer 模型，其强大的特征提取能力已经超越了自然语言处理的范畴。\[[3](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQFNvMpUdjGZPFSxXS_aHK_4-o5gV8DacV-gXkZeZDyfOlHe-aEBmifFuOGO9DcG4VQWflE8XbKDDLEpKqnnsC8pfhgF0kOXh47HhedNnICkhGYl_ZW0TPXMaepa1T4sMv-5se1pNqODyxU943XNEidk876GKsgbj86yPAjVCBg2I68%3D)\] 视觉 Transformer（Vision Transformers, ViT）等模型已成功应用于图像识别等计算机视觉任务。\[[15](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQEMhAPUNFY7r7E-5FzZ9SNA6KZdw1LgLU5b975_Z9IYegMMKqdxDejTBX39f92HMqCkfxGOr3vwnTZu9PGiV-5QcX5i5lsxCSrTGH3CXrfQQCk5aVPpNCiL-VvCPAv3Og82oZsMlpq3dNjJgbr4oDzMuUCmAHga2XnYswqZ5PoPk9Ga)\] 此外，它还在音频处理、强化学习和多模态学习等多个领域展现出巨大潜力。\[[3](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQFNvMpUdjGZPFSxXS_aHK_4-o5gV8DacV-gXkZeZDyfOlHe-aEBmifFuOGO9DcG4VQWflE8XbKDDLEpKqnnsC8pfhgF0kOXh47HhedNnICkhGYl_ZW0TPXMaepa1T4sMv-5se1pNqODyxU943XNEidk876GKsgbj86yPAjVCBg2I68%3D)\]

5. 更好的可解释性

Transformer 中的注意力机制为模型的决策过程提供了一定的透明度。\[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQH-LHt-vYRgUow8QYPnEnYgwm3OA2zG3UVIUFcPX8J0UFFspO9u8QVC6R6DQhcetWtJd-4Ze-v_WYoJ4rnr3uy_6o3Yw1WslDDTNQ0Kp-GnX_78lwjpgXXB4nsWUdjA1fSFkC6aZZwi)\] 通过可视化注意力权重，研究人员可以观察模型在生成输出时关注了输入序列的哪些部分，从而更好地理解模型的行为。\[[12](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQH0JmIjwHNguEnHCA5BeOMKdIKD6hiHDEpbRxi3iYi9nC4zg7HnvvbXZny5lJAbDWt_TK3SY8iYVScuXp3mSxHwWQdLT3PM7AkjLPEqzvr3Acfx60K_vQeWy2PzKJqFdS8bnJ1NAJ5oAfnMmXo0YkmimBNn6WxC2gcBpsyeaWPRBMuEkkvx79ci2fQ%3D)\]

总而言之，Transformer 模型通过其创新的自注意力机制和并行化架构，克服了以往模型的关键瓶颈，在计算效率、捕捉长距离依赖关系和模型可扩展性方面实现了重大突破。\[[6](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQE61hWo23Ow3laODNUIhDYH0bY2OhHHm-vfexp7l2a4PUUWHOt1M0_5DTUb69RL8l8j6yr-m-AVbbvstcumvpdFtZJbJgwC_Xt9_kT3Ft-T6jo3UOdWw8pe1CTSZyYFn4aODG0Ed6MGJvafOsIBmPiz-WKbmvaPn3t7WOctTAfuxybkIa3CXm4ucjnqBmc96NL9YzmKaLb9x1UOgc9Qkd7gUR7Hw5jVlG7kDcdxtrJhqqRUyyxB-6lkCtfj1dx60IvR3TmgIJ4kMjE8mUylbbeciYBLg9BPhJQ2xZklW1WletaTcyI1wCPIPn6_hbvVShf7z23FaLHqKg0yBJs9840mEhj7OAw%3D)\]\[[13](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAUZIYQG_pAe9Oe-6doPTHrB4JOYb-wPWVq4UdxulwuA8apg5yfqSDRiuyP7yZe5J4BWbte4kcElNNoa1E68yz64tu-2Zs_6E6OGJ28rmvM7Oj49F7y4z8j1yIBzG_bs8Yls-J9iDY9_pe7xfhSrLoA%3D%3D)\] 这些优势使其成为当前深度学习领域，尤其是大规模模型时代的核心构建模块。



## Transformer 时间复杂度计算

[Transformer 时间复杂度计算](https://fcnisnh9uh54.feishu.cn/wiki/XP00wxbvciWP1vk0qsicOESpnCg)



## 注意力机制

[MHA,MQA,GQA （多头注意力及高效变种）](https://fcnisnh9uh54.feishu.cn/wiki/WTIzwufVIiJeFYk2P1dc4J1jnEb)



