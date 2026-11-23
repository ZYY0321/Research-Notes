# 完整修改稿 · Opus 4.6（逐段批注）

提示词：背景 + 支使（先看批注）+ **逐段原文/批注** + 你之前的作者补充。见 [`完整修改稿-Opus46-提示词.md`](完整修改稿-Opus46-提示词.md)。

你之前写过的、这次已喂进去的：不要 above；不要 same tools；Appendix 口吻；数字要说明含义；3.3 不要突然 eval、真机有跨 app 但不可重置、replay 别重复；3.4 别防御、别列支付密码、别写 mean steps、没有 default channel、统一称 tools；3.5 不要 extend / incremental。

3.1 首段和 runtime 句这次是瞰之原文。模型改了节标题、把「无障碍树」写成有、3.5 数字拆错，这些已改回。尚未替换现稿 tex。

---

## 3.1 A gap in controllable commercial applications

Mobile agents are increasingly moving toward real-world workflows across commercial applications, such as travel booking on Trip and online shopping on Taobao, where tasks are often long-horizon and grounded in real user needs. However, training and evaluation environments for such commercial applications remain largely missing, leaving agents with limited opportunities to practice and be evaluated in realistic mobile-use scenarios.

Real-device or Android-emulator setups face login, reset, and real-world side effects that make large-scale training impractical. Prior simulated-app work typically covers only a small slice of commercial apps and rarely provides resettable business state.

We built MobileGym++, a browser-hosted mobile environment that carries commercial workflows in controllable simulated applications. The runtime extends MobileGym, preserving its advantages in reset and programmatic evaluation while substantially expanding domain coverage, the number and richness of applications, and support for realistic cross-app workflows. In this round we newly built 35 commercial apps, bringing the total with the predecessor to 64 installable applications spanning travel, shopping, finance, content, social, office, and local services. Goods and orders, expenses and budgets, itineraries and changes are live objects in the applications' own stores: actions on the screen change them, and tasks end by checking the resulting business state. Observations remain screen pixels, there is no accessibility tree, and the agent cannot read business state; device state can be exported and restored, and many instances can run in parallel.

## 3.2 35 high-fidelity commercial applications

Each of the 35 new applications is built from its real-world counterpart through an efficient pipeline that pairs human annotators with a coding agent. Annotators first collect screen recordings and long screenshots from the real app, then specify the object model and state transitions—what an order, a ledger entry, or an itinerary is, and how each is created, modified, and closed—so that the resulting simulated app reproduces a genuine business loop rather than surface-level screens. The coding agent implements pages and logic against this specification; a human verifies the result against the real device and sends mismatches back through the same pipeline. The procedure is specified in Appendix.

The newly built applications possess sufficient richness and interaction depth to carry realistic commercial flows. Across these apps, the median application declares 37 routes, 175 interactive actions, and 88 page transitions; the median interaction depth from the home screen is 3, meaning that even the shortest path to a target page already crosses multiple interface layers and the minimum number of agent steps is dictated by the page structure itself. For comparison, the largest application in the original MobileGym has 100 routes and 265 actions, and its deepest terminal requires 7 steps to reach.

## 3.3 Realistic cross-application workflows

Real mobile use routinely spans multiple applications—a shopping purchase triggers a payment app, a selected flight enters a calendar—yet existing commercial apps on a phone offer no controllable, resettable setting in which such workflows can be run again from the same start.

In MobileGym++, several commercial applications sit on one resettable device, each maintaining its own live business state: orders, expenses, itineraries, contacts. Clipboard, system broadcasts, and inter-app navigation connect the apps. A workflow can leave the current app, enter a second app, and rewrite that app's own business objects: a payment in shopping can produce a matching expense in bookkeeping; a selected train number in the calendar can enter an itinerary app for a change; an address from contacts can enter a checkout flow. The second app therefore receives a real business write, not only a forwarded message. The whole device is one snapshot; restoring it lets the same cross-app write be run again.

## 3.4 Hybrid GUI and app-native tool use

Existing evaluation typically separates pure-GUI settings from programmatic-only settings with no phone GUI. Real apps sit in between: they expose lookups and drafts alongside the graphical interface. MobileGym++ puts both channels on the same application state.

Approximately 52 applications expose app-native tools in the foreground. Tools are designed around each application's business objects—querying order status, locating matching products, retrieving an itinerary field—rather than exporting the widget tree. A tool call occupies the same action slot as a tap, swipe, or text input; only the foreground app's tools are available, and both channels write the same store. Many tools are query and retrieval. GUI-only can complete every official task; Hybrid is a second path on the same store, not a requirement.

## 3.5 MobileGym++ Bench

Existing mobile-agent benchmarks mainly score single-app GUI sequences whose terminal is system state or a UI-level field. Cross-application work is the natural form of phone use, not an add-on to that setting. MobileGym++ Bench asks whether an agent can carry a commercial write to completion inside resettable simulated commercial applications, including when the value for that write lives in another app's live state. Task length comes from locating, filtering, confirming, paying, and writing back across apps.

**Task design.** Tasks are organized around executable user goals and checkable terminals. Core tasks close with a business operation such as placing an order, posting an expense, creating an itinerary, sending a message, or modifying an app object. The result of that operation lands in the application's own business state. A single-app task reaches that write only after locating and filling fields across deeper pages. Instructions use user-goal language and do not name widget labels, tool namespaces, or checker fields.

In a cross-application task, the value needed for a write is present in another app's live state rather than written as a fixed constant in the instruction. The agent must identify the source, carry the value across the app boundary, and write it into the correct field; the checker verifies the relation between the resulting business fields.

**Scale and composition.** The current set contains 215 tasks across seven business domains: 109 mention one app, 74 two, 27 three, and 5 four. Tasks are distributed over multiple applications and business objects, so evaluation is not dominated by a handful of apps.

**Evaluation protocol.** Each task has three parts: a natural-language user goal, a bound initial state, and a programmatic terminal check. Success is decided by a programmatic checker: it reads the before/after diff of application business state, does not read the trace or screenshots, and does not use a model judge; different routes that accomplish the same write are equivalent. Allowed state paths are declared, and other mutations are recorded separately from success. The primary metric is task success rate. GUI-only and Hybrid are evaluated on the same tasks, initial states, and terminal checks. Mean steps on successful trajectories measure interaction efficiency conditional on completion; because failed trajectories often reach the step cap, we also report the success rate and the fraction reaching the cap to separate efficiency from reliability.
