这是 ICLR 方法章改稿。模型 claude-opus-4-6。

# 基本支使

对着下面「逐段：原文 / 批注」改飞书稿，输出完整英文 LaTeX（\section{MobileGym++} 到 3.5 结束）。
先看批注，再动笔。批注里已经写好的英文原样粘贴，不要改一个词。没点名的句子尽量留。不要发明数字。图表 caption 和对比表单元格沿用文末现稿。simulated，不用 mock。tools 和 function 是同一套，首次说明后称 tools。

作者补充（同一轮看稿时写的，和批注一起执行）：
- 小节不要用 added above 起笔。
- “send revisions back through the same tools” 含糊，正文里的 tools 只留给 3.4 的 app-native tools。
- Details are in Appendix 不像论文口吻；要指向附录就写成一句正经话。
- 3.2 数字不要只罗列：说明深度 3 意味着最短界面路径已经跨层，步数下界来自页面结构。
- 3.3 不要突然写 evaluation。真机商业 app 有跨 app（购物→支付），缺的是可控、可重置的那种。replay 说清楚一次就够，不要反复说同一件事。
- 3.4 不要防御性堆砌；不要把 saving/payment/password/contact/prefill 当重点列出来；不要在 3.4 写 mean steps / 评估；不要说 GUI is the default channel，只说两条路都能完成同一批任务；不要 function/API/tools 混称。
- 3.5 不要写 increasingly include / extend to cross-app，不像创新，跨 app 是手机使用的常态。

# 背景（事实，不要把手册贴进正文）

浏览器仿真手机环境，扩展 MobileGym。观测只有像素，无障碍树，agent 读不到业务状态；设备状态可导出恢复。新建 35，合计 64，七个领域。约 52 个前台暴露 tools。Bench 215 题，109/74/27/5。GUI-only 能做完每道正式题；Hybrid 是同一 store 上的另一条路径。

构建：对照真机。人录屏+长截图；先定对象模型和状态流转（订单/账本/行程如何创建修改关闭），再实现页面——业务闭环不是皮肤。coding agent 写代码，人对照真机验收，不匹配送回同一条流水线。质检细节放附录。中位 37 路由 / 175 动作 / 88 跳转，深度中位 3；前作最厚 100/265、最深 7 步。

Tools：按每个 app 的业务对象设计，查询/定位/草稿为主，不是控件树导出；与点击占同一动作槽，只暴露前台 app，写同一 store。

# 逐段：原文 / 批注

## 3.1 首段
原文：Mobile agents are entering real commercial-application settings---travel booking, online shopping, personal finance, local services---the everyday work agents now need to cover. Yet training and evaluation environments for these apps are largely missing: few let agents practice, and be evaluated, on such applications under controllable, resettable conditions.
批注（整段换成下面英文，原样）：
Mobile agents are increasingly moving toward real-world workflows across commercial applications, such as travel booking on Trip and online shopping on Taobao, where tasks are often long-horizon and grounded in real user needs. However, training and evaluation environments for such commercial applications remain largely missing, leaving agents with limited opportunities to practice and be evaluated in realistic mobile-use scenarios.

## 3.1 第二段
原文：Real-device or Android-emulator setups face login, reset, and real-world side effects that make large-scale training impractical. Prior simulated-app work typically covers only a small slice of commercial apps and rarely provides resettable business state.
批注：本轮无。可留。加 \citep{rawles2025androidworld,kong2025mobileworld}。

## 3.1 第三段
原文：We built MobileGym++, a browser-hosted mobile environment that carries commercial workflows in controllable simulated applications. The runtime extends MobileGym, inheriting serialization, reset, inter-app navigation, and programmatic evaluation, while expanding application content, domain coverage, and the in-app calling channel. In this round we newly built 35 commercial apps, bringing the total with the predecessor to 64 installable applications spanning travel, shopping, finance, content, social, office, and local services. Goods and orders, expenses and budgets, itineraries and changes are live objects in the applications' own stores: actions on the screen change them, and tasks end by checking the resulting business state.
批注：只把 “The runtime extends MobileGym, inheriting…” 整句换成下面英文（MobileGym 后加~\citep{wu2026mobilegym}），其余尽量不动：
The runtime extends MobileGym, preserving its advantages in reset and programmatic evaluation while substantially expanding domain coverage, the number and richness of applications, and support for realistic cross-app workflows.
另：3.2 那句 runtime/观测不要放 3.2，放到本段（观测仍是像素，无障碍树，不能读业务状态；设备状态可导出恢复，可并行）。

## 3.2 构建段
原文：We implemented 35 applications from the corresponding real apps: we collect screen recordings and long screenshots, fix the object model and state transitions first---what an order, a ledger entry, or an itinerary is, and how each is created, modified, and closed---then implement business functions and pages around those objects; interactions that screenshots cannot settle are checked on the real device. Goods and orders, expenses and budgets, itineraries and changes, conversations and messages are maintained as application state, rendered by the UI, and checked at task termination. Before use, each app is checked against the real device by a human, then by automated tests (navigation declarations, interactive bindings, visual comparison to real screenshots) and a human walkthrough; failures are sent back, and fixes enter regression.
批注：「可以大概强调我们有一个 efficient 的 human annotator 和 coding agent 协作的 pipeline，然后大概讲一下流程，比如收集截图、复刻、迭代修订。然后附录里写细节。」「现在这块有点长，读者看不了这么细」
背景里的对象模型先定、业务闭环不是皮肤，点到即可。

## 3.2 深度段
原文：These apps need enough structural depth to carry real commercial flows. On the newly built clients, the median navigation declaration is 37 routes, 175 interactive actions, and 88 transitions; median interaction depth from the root is 3. As a depth reference, the thickest application in MobileGym has 100 routes and 265 actions, and its deepest terminal takes 7 steps to reach. The runtime is inherited from MobileGym: observations remain screen pixels, there is no accessibility tree, and the agent cannot read business state; device state can be exported and restored, and many instances can run in parallel. The function channel is described in Section 3.4.
批注：「不如直接强调我们新增的 app 具备足够的丰富性、交互深度，比 need 更清晰」；runtime 那句从本节删掉。

## 3.3
原文三段：
Several commercial applications sit on one resettable device, each maintaining its own live business state: goods and orders in shopping, expenses and budgets in bookkeeping, itineraries and changes in the calendar, contacts and addresses in the address book. These objects change with on-screen actions and leave a trace in device state.
Clipboard, system broadcasts, and inter-app navigation connect the apps. A workflow can leave the current app, enter a second app, and rewrite that app's own business objects: a payment in shopping can produce a matching expense in bookkeeping; a selected train number in the calendar can enter an itinerary app for a change; an address from contacts can enter a checkout flow. The second app therefore receives a real business write, not only a forwarded message.
Every step of a cross-app workflow acts on the same resettable device state, so the same workflow can be replayed.
批注：「可以提一下现有的 (commercial) app 没有这种 cross-app xxx」；「引入太长了」；replay「这个是啥意思」。

## 3.4
原文：
GUI-only is already a complete setting. To support longer-horizon study we additionally open an app-native function channel on the same application state, so when to use the interface, when to call a function, and how to return to the interface for confirmation can be examined in one world. Hybrid is another completion path, not a requirement.
Approximately 52 applications expose a function interface in the foreground, occupying the same action slot as a tap, swipe, or text input. Functions are a subset of GUI-reachable operations: prefill creates a draft only, while saving, payment confirmation, passwords, and contact selection return to the GUI. Tools are used mainly to locate and organize structured information; both channels write the same state.
批注：动机不是为了长期研究，要写背景（哪怕 experimental）；open an app-native function channel 太空，先引入再给通道；function/tools 是一个东西，重写；按每个 app 的 motivation 设计 tools；Hybrid 与 GUI-only 兼容，不要写完全等价；不要让人以为 tools 都要 GUI 后验，很多是查询类。

## 3.5 开篇
原文：Existing mobile-agent benchmarks cover many single-app GUI operations and increasingly include cross-application workflows and tool interaction. MobileGym++ Bench asks whether an agent can finish long-horizon, realistic, cross-application commercial work in a controllable commercial environment. Task length comes from locating, filtering, confirming, paying, and writing back across apps.
批注：「increasingly include」显得 incremental，换种表达。后面 Task design / Scale / Evaluation protocol 没点名，可留。开篇可加 \citep{rawles2025androidworld,kong2025mobileworld}。

# 现稿图表（照抄）

\label{sec:mobilegym++} \label{sec:method}
3.1 sec:mgpp-env  3.2 sec:mgpp-apps  3.3 sec:mgpp-crossapp  3.4 sec:mgpp-tools  3.5 sec:mgpp-bench
图1 figures/mobilegym_fig1_20260913.pdf fig:mgpp-overview
caption: MobileGym++ combines broad commercial-app coverage with executable single- and cross-app tasks and two interchangeable interaction channels. GUI-only and Hybrid share the same initial state and terminal check.
图3 figures/mobilegym_fig3_20260913.pdf fig:mgpp-hybrid
caption: Hybrid execution in MobileGym++. GUI actions and app-native tools operate on the same business state; a trajectory may hand off between channels before the checker reads the resulting state diff.
表 tab:mgpp-compare：64 (+35) / 215；MobileGym 28 / 416 tmpl.；AndroidWorld ~20 / 116 tmpl.；AppWorld 9 / 750/250 sc.；MobileWorld 20 / 201。不要改单元格。

只输出完整 LaTeX，不要解释。
