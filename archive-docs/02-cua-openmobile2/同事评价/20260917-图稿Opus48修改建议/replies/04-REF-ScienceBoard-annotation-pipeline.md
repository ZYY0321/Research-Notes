# 04-REF-ScienceBoard-annotation-pipeline

- model: `claude-opus-4-8`
- elapsed_s: 62.9
- finish_reason: stop
- usage: {"prompt_tokens": 2240, "completion_tokens": 3100, "total_tokens": 5340, "usage_semantic": "openai", "usage_source": "anthropic", "prompt_tokens_details": {"cached_tokens": 0, "text_tokens": 0, "audio_tokens": 0, "image_tokens": 0}, "completion_tokens_details": {"text_tokens": 0, "audio_tokens": 0, "image_tokens": 0, "reasoning_tokens": 0}, "input_tokens": 2240, "output_tokens": 0, "input_tokens_details": null, "claude_cache_creation_5_m_tokens": 0, "claude_cache_creation_1_h_tokens": 0}
- images: 数据标注app制作参考流程图.jpeg

---

# 审稿意见：ScienceBoard Figure 3（参考图，用作 App construction 图的布局母版）

---

## 1. 这张图现在在说什么（1 段）

这是 ScienceBoard 的**任务标注管线**：五步流水线，从「读教程」→「任务构思（Task Curation，含 Agentic Prompt / Difficulty / Task 文本）」→「任务形式化与验证（多条候选带对勾/叉筛选）」→「任务配置（App 安装、文件下载到一台仿真机）」→「写评测函数（`def eval(...) pass` 代码卡 + Check & Validation 回折验证）」。它讲的是**如何为一个已存在的科学软件出题并落地可判分**，核心产物是"任务 + 评测函数"，不是"软件本身"。

---

## 2. 这张图为什么一眼能读（可搬的视觉语法）

审稿人 10 秒能读懂，靠的是六条语法，请**全部搬到你们的 App construction 图**：

1. **显式步骤编号 + 粗体一句话标题**（Step 1…Step 5）。读者不用推理顺序，编号强制线性阅读。
2. **Z 字形回折布局**：上排从左到右三步，下排从右到左两步。避免五个框挤成一条会缩小字号的长横条，双栏宽度下每个模块都还够大。
3. **每步一张"产物卡片"**：不是抽象箭头，而是把该步的**具体产出物**画出来（提示卡、带对勾的候选列表、一台装好软件的机器、代码块）。产物可视 = 可信。
4. **对勾 ✅ / 叉 ❌ 表达筛选语义**：一眼看出"多进少出、有淘汰"。
5. **虚线 = 反馈/校验回路**（Check & Validation 回到执行）；**实线灰箭头 = 主流程前进**。两种箭头语义分离得干净。
6. **图标承担角色**：人（标注员）、显示器（执行/校验）、机器（配置环境），减少文字。

---

## 3. 绝不能原样搬的内容（否则读者以为你在画 Bench 出题管线）

这张图的**语义骨架是"出题 + 判分"**，你们要画的是**"复刻一个商业 App 世界"**。以下元素若照搬，会让审稿人把你们的 App construction 误读成 Bench 任务标注管线——这是致命歧义：

- **Task Curation / Agentic Prompt / Task 文本卡** → 删。你们这一步不是"想任务"，是"确定要复刻哪个商业 App 的哪些业务对象/页面/store"。
- **Difficulty 标签** → 删。难度是 Bench 侧属性（109/74/27/5 那套单/双/三/四应用口径），不属于 App 构建。放进来会把"造 App"和"出题"混成一条线。
- **Write Evaluation Function（`def eval` 代码卡）+ Check & Validation** → 删或彻底改写。你们的成败判据是**业务状态差分（业务 store diff）**，不是逐任务手写 eval 函数。若保留代码卡，读者会以为你们也在为每个任务写判分脚本。要画就画"业务 store 的可读/可重置状态"，而不是 eval()。
- **Task Formalization and Verification（多候选打勾筛选）** → 删。这是"选任务"，不是"造 App"。
- **File Download / Task Configuration 那台"装软件的机器"** → 语义要换。你们不是安装真实软件，是**在浏览器仿真手机里构造 simulated App**（对外说 simulated，不说 mock、不说真机）。可以借"一台设备上装好 App"的构图，但标注必须写成"64 可安装 App 之一，simulated"。

**一句话原则**：可搬**布局语法**（编号、回折、产物卡、勾叉、双箭头），不可搬**语义标签**（Curation / Difficulty / eval / Formalization）。

---

## 4. 你们五步如何映射到这种清晰度（内容重写）

保持"5 步 + Z 字回折 + 每步产物卡 + 双箭头"，但把每步换成 App 复刻语义。建议映射（步骤内容按你们真实管线调整，我只给能撑住主张且不越界的口径）：

| 你们的 Step | 标题（英文，粗体） | 产物卡片画什么 | 严禁写 |
|---|---|---|---|
| Step 1 | **Select Reference App** | 目标商业 App 截图缩略 + 领域标签（七个领域之一） | 不写 Task / Difficulty |
| Step 2 | **Model Business Store & Objects** | 前台可见的业务对象示意（如订单/购物车条目），标注 "app-native store" | 不写 eval 函数；store 是业务状态，不是判分脚本 |
| Step 3 | **Build GUI (pixels + a11y tree)** | 仿真手机页面 + 无障碍树侧栏，标注 "observation = pixels + a11y tree" | 不写"截图像不像"当判据 |
| Step 4 | **Register App-native Tools (同一 store, 前台 App)** | 工具卡（查询/定位/草稿），标注"与 click 同一动作槽 / 只暴露前台 App / 预填≠提交" | 不写 API/function/tools 混称；不写"与 GUI 完全等价" |
| Step 5 | **Install into Simulated World (64 apps, 7 domains)** | 仿真手机里已装好该 App，角标 "simulated · resettable" | 不写 110+ 训练 apps（那是另一集合，禁混）；不写 Difficulty |

**回折反馈线（虚线）**语义改为：**"business-state diff for verification"**（业务状态差分校验该 App 可判可重置），而不是 Check & Validation 的手写 eval 回路。

**判据信息条**（图注或底部小字）：成败看**业务状态差分**，不看截图相似、不看路径；GUI-only 是一等公民（正式题必有纯 GUI 路径），Hybrid 是同一 store 上的可选第二通道。

---

## 5. 顶会可投稿重绘方案（模块清单 + 阅读顺序 + caption）

**布局**：双栏宽，上排 Step1→2→3 从左到右，下排 Step5→4 从右到左回折（下排从右接住上排末端），保持母图的 Z 字。

**模块清单**：
- 5 个粗体编号标题
- 5 张产物卡片（按上表）
- 灰实线箭头 = 构建流程前进
- 蓝虚线 = business-state diff 校验回路（连回 Step 5 的 simulated 设备）
- 一枚统一角标系统："simulated"、"a11y tree"、"same store"

**阅读顺序**：编号 1→5 强制线性；虚线单独一层，读完主线再读校验回路。

**建议英文 caption**：
> *Figure X: Constructing a simulated commercial App. We replicate a reference App's front-facing UI (pixels + accessibility tree) and its app-native business store, register store-consistent tools alongside GUI actions, and install it into the resettable simulated world (64 installable Apps across 7 domains). Task success is judged by business-state diff, not screenshot similarity or trajectory.*

---

## 6. 必须删掉或改口的元素

- 删：Task Curation、Agentic Prompt、Difficulty、Task Formalization、Write Evaluation Function、`def eval` 代码卡、Check & Validation 文案。
- 改口：File Download / App Install → "install into **simulated** world"；一切"mock"→"simulated"；避免"真机/更真"。
- 改口：任何工具卡文字统一为 app-native tools（查询/定位/草稿），不用 API/function 混称，不标"与 GUI 等价"。
- 加：判据信息条（业务状态差分）+ GUI-only 一等公民标注。

---

## 7. 优先级

- **P0**：删掉 Curation / Difficulty / eval / Formalization 四类语义标签，替换为"选 App / 建 store / 建 GUI / 注册 tools / 装入 simulated 世界"，否则整图被读成 Bench 出题管线。
- **P0**：虚线回折改标为 "business-state diff verification"，禁止出现手写 eval 判分含义。
- **P1**：保留 Z 字回折 + 编号 + 5 张产物卡 + 双箭头语义（实线前进 / 虚线校验），沿用母图清晰度。
- **P1**：Step 5 设备角标写 "simulated · resettable · 64 apps / 7 domains"，禁止混入 110+ 训练集。
- **P2**：加 a11y tree 侧栏与 "same store" 角标，让"像素观测 + 同一 store 双通道"一眼可辨；工具卡加"预填≠提交"小字。
