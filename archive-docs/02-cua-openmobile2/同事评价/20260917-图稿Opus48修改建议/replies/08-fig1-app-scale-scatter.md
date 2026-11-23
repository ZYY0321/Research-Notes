# 08-fig1-app-scale-scatter

- model: `claude-opus-4-8`
- elapsed_s: 73.0
- finish_reason: stop
- usage: {"prompt_tokens": 4344, "completion_tokens": 3228, "total_tokens": 7572, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 4344, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: fig-1-app-scale-scatter.png

---

# fig-1 审稿意见

## 1. 这张图现在在说什么

散点图在双 log 轴上把 App 的「distinct pages/routes」（x）对「interactive actions per app」（y）铺开：实心圆=你们 35 个新 App（按 domain 上色，气泡=任务数），空心方=前作 MobileGym baseline 12 个 App，叉=AndroidWorld / MobileWorld 文献占位，加号=组中位。两条水平虚线标出两组中位，右侧红色双箭头喊出「×6.8 more interactive actions (group median)」。核心主张：**我们的商业 App 在交互深度/页面丰富度上比前作和外部环境高一个量级。**

## 2. 内容张力诊断

主张方向是对的，图也确实在 10 秒内让人看到「你们的云明显在右上、baseline 挤在左下」。但有几处硬伤会被顶会 reviewer 抓：

- **占位叉是定时炸弹。** 你自己已经承认 AndroidWorld / MobileWorld 是「approx., literature」「不是同口径实测」，pages/actions 部分是估计值。可它们现在被画在**同一把 log 尺子的同一散点场**里，还压在最低处——等于用不可比的数据点强化「我们高 6.8×」。审稿人一旦质疑这两个叉，整张图的量化主张全塌。这是 P0。
- **×6.8 的定义模糊 + 只信一个数。** 「group median」是哪两组的中位比？看图像是「新 App 中位 / baseline 中位」在 y 轴（actions）上的比。但 baseline 中位里是否混入了那两个不可比的叉？如果混了，6.8 就是脏的。必须锁定：6.8 只能是「35 新 App actions 中位 ÷ 12 前作 baseline actions 中位」，且明确写在 caption。
- **两条轴的主张混在一起。** 你既想说 pages 多、又想说 actions 多，红箭头却只落在 y（actions）。x 方向那句「pages 更丰富」没有对照量化。读者不知道 6.8 是 actions 的、还是综合的。
- **气泡=任务数是第三维干扰。** 任务数与「交互深度」不是同一件事，读者会误以为「气泡大=交互多」。而你标注的三个 App（Douban 4 tasks / Kapi 23 / WeChat 19）气泡大小反而没讲清跟深度的关系。这条信息稀释了主张。
- **口径合法性没问题的地方**：新 35 / 前作 12、七 domain 上色、log-log 都合法。没看到 215 / 64 / 成功率数字被误用，好。

结论：**方向能撑住「交互深度 leap」，但目前形态经不起 reviewer 质询——占位叉必须处理、6.8 必须定义清、双轴主张要拆清。**

## 3. 张力不够时的补救（本图适用）

- **占位叉：不要删，但请出主散点场。** 两个选择：
  - (推荐) 把 AndroidWorld / MobileWorld 移到图外的一条**灰色阴影参考带**（horizontal shaded band，标「external refs, non-comparable protocol, approx.」），只占 y 轴一个区间，不给精确 (x,y) 坐标点。这样保留「外部环境大致在这个低区」的语境，又不假装同尺实测。
  - 或者做成**小型 inset / 单独子图**，明确加灰底 + 斜纹 + 「not measured under our protocol」。
- **×6.8 改法**：改成明确的组对照。锁死为 `median actions: new 35 apps ÷ prior MobileGym 12 apps`，红框文字写 `×6.8 median interactive actions (35 new vs. 12 prior MobileGym apps)`。**不要把外部叉算进任何中位。**
- **中位对照怎么放**：保留两条水平中位线，但各自加数值标签（如 new median ≈ 185, prior ≈ 27，用你真实数），让 6.8 可被目测验证。加号（group median marker）与虚线重复，去掉加号只留线，减少视觉噪声。
- **双轴主张**：如果也想 claim「pages 更丰富」，加一条竖直方向的中位比（x 轴 median ratio，如 ×N pages），或干脆在 caption 里量化，别让 x 主张悬空。
- **气泡语义**：若任务数不是主张，就**弱化**——统一气泡大小、把任务数移到附录表；或保留但在 caption 明说「bubble = #tasks, orthogonal to depth」，避免误读。

## 4. 视觉元素逐项优化（张力基本成立后）

- **配色**：7 个 domain 用了红/绿/蓝/紫/橙/青/黄绿，Finance 深蓝与 Social 深绿、Productivity 青与 Lifestyle 黄绿在小气泡上难分。换成 color-blind safe（如 Okabe-Ito 8 色）。
- **baseline 空心方**：现在空心方也带 domain 边框色（青、绿、蓝、红），和实心圆的 domain 色撞，读者会误以为同 domain 配对。**baseline 统一成中性灰空心方**，只靠形状区分组别，别再编码 domain。
- **红色元素过载**：红双箭头 + 红框 + 红色 Travel 气泡同色系，视觉打架。把「×6.8」框改成中性深灰边、红字，或把 Travel 换色。
- **引线标注**：Douban/Kapi/WeChat/JD 四条灰引线交叉穿过密集区，Kapi 那条尤其乱。改成短直引线或直接贴标签，避免跨越气泡群。
- **图例**：size legend（3/10/20/39 tasks）与主张无关却占左上黄金位。缩小并下移，或移到底部与 domain 图例并列。
- **网格**：log 次刻度网格线太密（尤其 y 轴 100–1000 段），淡化到 0.15 alpha。
- **中位线标签**：两条虚线目前无数值，加 `median` 文本 + 数值贴在线右端。
- **轴范围**：一旦占位叉移出，x 可从 ~8 起、y 从 ~50 起（或保留但让主群体更大）。目前左下大片空白只为容纳不可比的叉，浪费画布。

## 5. 顶会可投稿重绘方案

**模块清单（阅读顺序）**
1. 主散点场（右上）：35 新 App 实心圆（domain 上色）+ 12 前作 baseline 灰空心方，log-log。
2. 两条 median 参考线 + 右端数值标签。
3. 右侧竖直 `×6.8` 深灰框（actions 中位比，明确组定义）。
4. 底部一条灰色阴影参考带 = external refs（AndroidWorld/MobileWorld），标「approx., non-comparable」，不给精确点。
5. 图例（下方一行）：shape=组别，color=domain，size=#tasks（注明 orthogonal）。
6. 3–4 个代表 App 短标签，不跨越气泡群。

**English caption:**
> **Figure 1. App-level interaction scale.** Each marker is one app plotted by distinct pages/routes (x) vs. interactive actions (y), both log-scale; color = domain, size = #tasks (orthogonal to depth). Our 35 new simulated apps (filled) offer a median of ×6.8 more interactive actions than the 12 prior MobileGym baseline apps (open gray). AndroidWorld / MobileWorld are shown only as an approximate, non-comparable reference band (different measurement protocol) and are not scored on the same scale.

## 6. 必须删掉或改口的元素

- **删/移**：AndroidWorld、MobileWorld 两个叉作为精确散点 → 改为参考带或注明不可比。
- **改口**：`External ref (approx., literature)` → 明确「non-comparable protocol」，别让它进任何 median 计算。
- **改口**：`×6.8 more interactive actions (group median)` → 写清是「35 new vs. 12 prior baseline apps」，不含外部。
- **删**：Group median 加号（与虚线冗余）。
- **改**：baseline 空心方去掉 domain 边框色，统一灰。
- 图内出现的是产品名（WeChat/JD/Douban/Kapi），确认这些是 simulated 版本，caption 里点一句「simulated apps」，避免读成真机真 App。

## 7. 优先级

**P0**
- 把两个外部叉从同尺散点移出，改成注明「approx./non-comparable」的参考带或 inset。
- 锁定 ×6.8 定义为「35 新 App actions 中位 ÷ 12 前作 baseline 中位」，剔除外部数据，caption 写全。

**P1**
- baseline 空心方统一中性灰，取消 domain 边框色；换 color-blind safe domain 配色。
- 两条 median 线加数值标签，删加号。
- caption 注明气泡=#tasks 与深度正交；注明 apps 为 simulated。

**P2**
- 淡化 log 网格、重排图例到底部、清理四条交叉引线、收紧轴范围释放左下空白。
