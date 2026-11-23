类型：材料 ｜ 归属：2026-11-23 CUA classic 品味 ｜ 状态：本轮收集

# classic：2023–2025 被收下或成为事实标准的 CUA / GUI Agent

本表 12 篇。单篇笔记 5 篇是这轮新写的：CogAgent、SeeAct、AndroidControl、VisualWebArena、AitW。Mind2Web、WebArena、SeeClick、OpenCUA、ScreenSpot-Pro 的笔记在收集过程中已经出现在 `notes/`，没有覆盖，表里链到那些文件。

没收入、以及理由：

- ScaleCUA（arXiv:2509.15221，2025-09）：本地审稿记录写 ICLR 2026 Oral。超出本主题「2023–2025 已被接收」的年份，而且本轮 `api2.openreview.net` 返回 403，没有亲自打开论坛，不把未复核的 Oral 写进表。
- AppAgent（arXiv:2312.13771）：打开了摘要。它是 10 个应用、50 个任务上的探索式系统演示，没有查到顶会接收页。作为早期基线被引用，证据厚度不够当经典。
- Claude Computer Use、OpenAI CUA：产品技术博客 / 系统卡，不是可按表号核对的会议论文，数字随模型版本变。
- OSWorld-Verified：没有独立论文。OpenCUA 把它当作 OSWorld 的核对版评测来报分（proceedings 表 2）。
- Agent S2：这轮没有打开原文，不收。收的是 ICLR 2025 的 Agent S。

审稿分数若出现，一律来自本地记录 `/Users/zhangyingying/Desktop/research-lab/testing-survey/reviews/gui-agent-ai-venues.md`。本轮 OpenReview API 403，这些分数是二手。

| 日期/venue | 论文 | 问题（一句话） | 它检查了什么默认假设 | 发现问题的方式 | 解决方式 | 最强证据（数字+表号） | 作者承认的局限 | 我看到的没解决点 | 品味 | 可模仿的一点 | 读深度 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023 NeurIPS D&B Spotlight | [Mind2Web](https://arxiv.org/abs/2306.06070)；笔记 `/tmp/rn/literature/cua-notes/notes/deng2023mind2web.md` | 真实网站上的通用网页智能体，换站点之后还剩多少 | 在固定几个网站上训练测试，就能代表网页智能体 | 三种留出：同站新任务 / 新站 / 新领域 | 数据集 + 两阶段 MindAct（小模型筛元素，大模型做选择题） | 表 2：Flan-T5-XL 步成功率 52.0 / 38.9 / 39.6，整任务成功率只有 5.2 / 5.1 / 2.9 | §6：英语、美国站点、MTurk 标注员；离线缓存遇未见动作就失败，多条路径会假阴性 | 整任务成功率塌掉这件事被写出来了，但主榜仍是「给定真实历史」的步成功率 | A | 报指标时把步成功和整任务成功并排，划分按「见没见过环境」而不是随机切 | 全文（proceedings PDF 主文与表 2） |
| 2024 ICLR Poster | [WebArena](https://arxiv.org/abs/2307.13854)；笔记 `/tmp/rn/literature/cua-notes/notes/zhou2023webarena.md` | 自托管的真功能网站上，任务到底做成没有 | 动作文本和参考轨迹像，就等于做对了 | 用程序检查网站最终状态；另设做不到的题，看模型会不会瞎做 | 4 类网站 + 工具站，812 题，Docker | 表 2：去掉「做不到就停」的提示后 GPT-4 端到端 14.41%；人类 78.24% | §5.1：带该提示时，GPT-4 把 54.9% 做得到的任务提前判成做不到 | 人类是 170 个模板各 1 题、5 名研究生；模型是全基准。表把两个分母放在一起 | A | 成功用结果状态判定，并单列「做不到的题」，看模型会不会编 | 全文（arXiv HTML 主文、表 2） |
| 2024 ACL 长文 | [SeeClick](https://arxiv.org/abs/2401.10935)；笔记 `/tmp/rn/literature/cua-notes/notes/cheng2024seeclick.md` | 只看截图的界面代理，先得学会按指令点中元素 | 通用多模态模型天然会在屏幕上点 | 先单独测定位，再看定位涨了下游涨不涨 | 约 100 万条定位数据继续预训练 Qwen-VL；放出 ScreenSpot | 表 1 平均点击准确率：SeeClick 53.4%，CogAgent 47.4%，GPT-4V 16.2%，Qwen-VL 5.2% | Limitations：动作主要是点按和输入；多步任务仍要在下游数据上再训 | 图标/控件仍差一截（表 1 移动端文字 78.0、图标 52.0）。ScreenSpot 后来被 ScreenSpot-Pro 说成裁过的易图 | A | 把定位从智能体总分里拆成独立基准，并拿同一模型的几个检查点看它和下游是否同向（图 6） | 全文（arXiv HTML 主文、表 1–3） |
| 2024 CVPR | [CogAgent](https://arxiv.org/abs/2312.08914)；笔记 `/tmp/rn/literature/cua-notes/notes/hong2024cogagent.md` | 界面上的字太小，现有视觉语言模型的分辨率不够 | 把原编码器分辨率直接加大就能看清 GUI；GUI 必须读 HTML | 比 FLOPs：原结构拉到 1120 比交叉注意力支路贵 10 倍以上；再在 Mind2Web 上比「看图 / 读 HTML」 | 18B 模型加一条 1120×1120 的高分辨率交叉注意力 | Mind2Web 步成功率整体 58.2，对 Flan-T5-XL 的 43.5、LLaMA2-70B 的 54.4（CVPR PDF 表 3） | §5：坐标不准，不能吃多张图 | AitW 上只比 Auto-UI 高 2.61（表 4），作者又说抽查的错误里四成其实是另一条合法路径 | A | 改分辨率时同时报计算量和一份公开基准，对照用对方的同一划分 | 全文（CVPR PDF 主文） |
| 2024 ICML Poster | [SeeAct](https://arxiv.org/abs/2401.01614)；笔记 `/tmp/rn/literature/cua-notes/notes/zheng2024seeact.md` | 模型写得出网页计划，但落不到正确元素上 | 能描述按钮就等于能点中；离线单路径分够用 | 同一计划接人工定位和三种自动定位；90 题再上真网站 | 先看截图写计划，再用 HTML 与画面的对应做定位 | 表 4（90 题）：在线整任务成功率，人工定位 51.1%，Choice 37.8%，GPT-4 13.3% | §6：自动定位仍比人工低大约 20–25 个百分点；离线会低估，因为一条参考路径盖不住别的走法 | 表 3 是每个划分 30 题。Choice 与人工的差我按表相减是 22.8 / 32.3 / 20.1，Cross-Website 大于结论里的 25。结论又把 51.1 写成约 50% | A | 固定计划模型，只换落地方式，离线分和在线分一起报 | 全文（arXiv HTML 主文、表 3–4） |
| 2023 NeurIPS D&B Poster | [AitW](https://arxiv.org/abs/2307.10088)；笔记 `/tmp/rn/literature/cua-notes/notes/rawles2023aitw.md` | 手机控制缺一份大而能切泛化的人类演示 | 一种机型、一种说法上的策略可以当成一般能力 | 按安卓版本、动词/主语模板、应用域留出 | 715,142 条轨迹 + 离线动作匹配 | 表 2 合计 715,142；表 4 BC-history 部分匹配，标准划分 73.1，没见过的应用域 59.7 | §6.1：标注员、英文、鼠标而非触摸、只有手机。§7：多种合法做法会被匹配判错 | GoogleApps 占 625,542 条，但指令只有 306 条。标准划分按轨迹随机切，测试指令会在训练里出现 | A | 泛化不要只随机留 10%，按「没见过的说法 / 平台版本 / 应用」各留一列，并写明匹配有多松（这里是 14% 屏距或框放大到 240%） | 全文（proceedings PDF + arXiv 表 2） |
| 2024 NeurIPS D&B Spotlight | [AndroidControl](https://arxiv.org/abs/2406.03679)；笔记 `/tmp/rn/literature/cua-notes/notes/li2024androidcontrol.md` | 微调界面代理，数据得到加到多少 | 演示越多就越能得到能用的代理，高层和低层差不多 | 数据量取对数，域内/域外、高层/低层分开外推 | 15,283 条演示，833 个应用，每条同时有高层目标和低层步骤 | 表 4：PaLM 2S 全量 LoRA，域内高层步准确率 71.5%，低层 86.6% | §5：只训了 PaLM 2S；离线分不奖励另一条路径，也不奖励纠正 | §4.4 写域内低层 95% 步准确率约 50 万条，§6 写成 100 万条。1.5 亿是外推不是实验 | A | 用几档数据量画域内和域外，并写明外推假设（步与步独立、对数线性） | 全文（arXiv HTML 主文、表 4、图 5） |
| 2024 ACL 长文 | [VisualWebArena](https://arxiv.org/abs/2401.13649)；笔记 `/tmp/rn/literature/cua-notes/notes/koh2024visualwebarena.md` | 必须看图才能做的网页任务，文本代理行不行 | 无障碍树已经够代表网页 | 910 题全部要看画面；文本和多模态用同一环境并排跑 | 自托管环境 + 手写的视觉结果判定；Classifieds 是新站 | 表 3：GPT-4V+SoM 整体 16.37%，纯文本 GPT-4 7.25%，人类 88.70% | 无单独局限节。分析写了循环切页、缺少对历史状态的跟踪 | 人类是 230 题（每模板 1 题），模型是 910 题。SoM 相对截图路线只从 15.05 到 16.37 | A | 新题要保证「去掉图就无解」，否则文本代理可以不看图蒙对 | 全文（arXiv HTML 表 3 + ACL PDF 页眉） |
| 2024 NeurIPS（proceedings 摘要页已核实；poster 仅二手记录） | [Mobile-Agent-v2](https://arxiv.org/abs/2406.01014) | 手机长操作里，进度和当前该看的内容会在一条上下文里丢 | 一个代理拿着全部图文历史就能自己导航 | 拆成进度导航和焦点导航，再消融规划/反思/记忆 | 规划、决策、反思三个代理 + 一个记忆单元 | 表 1 非英文、进阶、外部应用：Mobile-Agent 1/10，v2 5/10。摘要写任务完成提升超过 30%；正文写英文平均成功率提升 27% | 没看到单独的 Limitations。正文承认不注入人工操作知识时仍会点错 | 每格大约 10 题，多应用只有 2 题。本地审稿记录分数 7、4、6、5：有审稿人写规划–执行–反思是常见做法，且没和 AppAgent、CogAgent 比 | B | 消融时把「谁在压缩历史」单独拿掉（他们的表 4：去掉规划代理掉得最多） | 全文（arXiv HTML 主文、表 1–4） |
| 2025 ICLR（proceedings PDF 与 iclr.cc 论文列表已核实；poster 仅二手记录） | [Agent S](https://arxiv.org/abs/2410.08164) | 长程电脑任务缺最新软件知识、缺子目标、动作空间又太大 | 一个多模态模型看截图就能稳定做完 OSWorld | 在 OSWorld 全量 369 题上比当时的基线，再拆经验、界面接口和错误类型 | 外部网页知识 + 两级记忆 + 分层规划；ACI 把动作收成 `click(element_id)` 这类有界原语 | 表 1：GPT-4o 的 Agent S 整体成功率 20.58%，同表 MMAgent+GPT-4o 11.21%（绝对差 9.37，相对 83.6% 是摘要算法） | 没看到单独局限节。§4.4 把失败分成规划、定位、执行。消融在抽过的 65 题 `testsub` 上，不是 369 | 本地记录只检索到 1 条评分 6：没测任务变多时的速度，也没讨论网上知识稀缺或界面大改时会不会失效。WindowsAgentArena 从 13.3% 到 18.2%（引言） | B | 错误分析按「计划错 / 点错 / 执行中不改」计数，并写明统计的是子集还是全量 | 全文（ICLR proceedings PDF 主文、表 1） |
| 2025 ICLR Workshop（Reasoning and Planning for LLMs；iclr.cc 日程页列出。不是主会） | [ScreenSpot-Pro](https://arxiv.org/abs/2504.07981)；笔记 `/tmp/rn/literature/cua-notes/notes/li2025screenspotpro.md` | 专业软件的整屏高分辨率上，现有定位模型还点不中 | 在 ScreenSpot 上点得准，就等于能用在真实电脑软件里 | 换图：23 个专业应用的整屏，专家当场标注，让当时的模型重测 | 基准 + 免训练的逐级裁剪 ScreenSeekeR | 正文与表 2：OS-Atlas-7B 18.9% 领先，没有别的模型超过 10%，GPT-4o 0.9%。表 4：ScreenSeekeR 把 OS-Atlas-7B 抬到 48.1%。后文又把 GPT-4o 的直接定位写成 0.8% | Limitations：只测定位，不测规划和执行；作者说是为了避开这些软件的许可风险 | 0.8 和 0.9 在同一篇里不一致。方法是「先缩小搜索范围」，不是新的定位训练。它后来变成大家必报的硬定位榜 | A | 若旧榜饱和，就换「目标相对更小」的图重测，先报掉下来的数字，再谈补救方法 | 全文（arXiv HTML 主文、表 2、表 4） |
| 2025 NeurIPS（proceedings PDF 页脚已核实。Spotlight 只见于本地审稿记录，本轮未打开 OpenReview，Spotlight 未复核） | [OpenCUA](https://arxiv.org/abs/2508.09123)；笔记 `/tmp/rn/literature/cua-notes/notes/wang2025opencua.md` | 最强的计算机使用系统不公开数据、配方和模型，外人无法研究它的能力和风险 | 把人类演示收成（状态，动作）对再做监督微调，数据多了就会变好 | 先只用动作对训练，看到数据变大也不涨（图 1 左），再补上带反思的长思维链 | 录制工具 + AgentNet + 反思思维链 + 开源模型 | proceedings 表 2：OpenCUA-72B 在 OSWorld-Verified 上 100 步平均成功率 45.0%。摘要同数。表 1：AgentNet 22,625 条，平均 18.6 步 | 附录 A：规模受人工标注限制；标注者不一定会用快捷键或写脚本；知情同意带来选择偏差 | 45.0% 仍低于文中的 Claude Sonnet 4.5（100 步 61.4%）。Pass@3 到 53.2%，说明单次成功率还不是能力上限 | A | 画「数据量 × 有没有某种标注」的缩放图。若只有动作、没有推理文本时曲线是平的，才有资格说推理标注是缩放的条件 | 全文（NeurIPS 2025 proceedings PDF 主文、表 1–2、附录 A） |

## 本主题风向三句话

2023 到 2024 被顶会收下的那批，几乎都是一份别人能直接用的东西，再加一个会改测法的认识：Mind2Web 用三种留出证明换环境比换任务难，WebArena 改成查最终状态，SeeAct 和 SeeClick 把「点不点得中」从总分里拆出来，AndroidControl 用外推曲线说明域外高层任务不是再标一点就能补上。

系统框架也能过会。Mobile-Agent-v2 和 Agent S 都进了主会，但审稿记录里已经有人说规划、执行、反思是常见模块。它们站住，靠的是真机或 OSWorld 上相对同一基线的涨点，外加能跑的代码；每格题量或消融子集都比上面的基准论文小。

还空着的是「另一条合法路径」。Mind2Web、SeeAct、AitW、AndroidControl 都写了离线单路径会把做对的换路判错，SeeAct 甚至量出离线 13.3 对在线 51.1。没有一篇把「故意换一条合法路径」做成主实验。定位榜和任务榜也仍然分开报。

## 待核实清单

- OpenCUA 是不是 Spotlight：proceedings 只证实 NeurIPS 2025 会议论文。Spotlight 来自本地审稿记录，OpenReview 本轮 403。
- Agent S、Mobile-Agent-v2 是 poster 还是 oral：会议论文身份已用 proceedings 核实，展示形式只见于本地记录。
- 这两篇加上 ScaleCUA 的审稿分数都是二手。本地记录写 Agent S 只检索到 1 条、评分 6；Mobile-Agent-v2 为 7、4、6、5；并写明 meta-review 未查到。
- ScreenSpot-Pro 的 GPT-4o：同一篇 arXiv HTML 里，表 2 讨论写 0.9%，ScreenSeekeR 段写 0.8%。
- AndroidControl：§4.4 域内低层 95% 步准确率约 50 万条，§6 写成 100 万条。域外 §4.4 还有一档 6000 万（高层 95% 步准确率），结论没写。
- SeeAct：表 4 在线人工定位 51.1%，§6 写成约 50%。「低 20–25 个百分点」盖不住表 3 Cross-Website 上约 32 个点的差。
- CogAgent 的表号在双栏 PDF 抽取里和题注错位。58.2 那张用 Flan-T5-XL 的 52.0/38.9/39.6 与 Mind2Web 表 2 对齐；76.88 那张用正文 “+2.61” 对齐。
- WebArena 人类 78.24% 的分母是 170 个模板各 1 题；VisualWebArena 人类 88.70% 的分母是 230 题。模型分母分别是 812 和 910。
- AitW 表 4 的 LLM 行在 PDF 抽取里和置信区间缠在一起，表内点估计没有引用，只用了正文里的 58%（做得出的动作上）和 33%（含非元素点击的轨迹）。
- ScaleCUA（2509.15221）的 ICLR 2026 Oral、AppAgent 的会议身份、Agent S2、Claude / OpenAI 的技术报告，这轮都没有当作已核实篇目。
