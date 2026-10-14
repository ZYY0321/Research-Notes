# 完整修改稿 · 第二轮（先看这个）

上一轮确实有问题：飞书「完整现在稿」喂了，但我另外冻了现稿 3.2（`The 35 applications added above`），模型就没按飞书那句 *We implemented 35 applications from the corresponding real apps* 重写。

这一轮：飞书原文是唯一 3.2–3.5 底稿；另附复刻手册（人采录屏/长图 → 先冻对象模型 → coding agent 实现 → 人对真机验收）和 tool 设计口径（查询/定位/草稿、按 app 业务对象、同一 store、GUI 也能做完）。

模型又捏了一张对比表（14 个领域、错误任务数）、改了 3.1 节标题、把 52 个 tools 写进 3.1。表、节标题、图、3.5 后半已改回锁死口径。**还没有替换现稿 tex。**

LaTeX：[`完整修改稿-Opus5.tex`](完整修改稿-Opus5.tex)

---

## 3.2 35 high-fidelity commercial applications

We implemented 35 commercial clients as replicas of the corresponding real apps, each built by a human annotator paired with a coding agent, reproducing a business loop rather than a visual skin. The annotator records screen recordings and long screenshots of the core flows and key pages, then freezes the object model and its state transitions before any page is written: what an order, a ledger entry, or an itinerary is, and how each is created, modified, and closed. The coding agent implements pages and business functions around those objects; humans compare the replica against the real device, and mismatches go back into the annotator--agent loop. The procedure is specified in Appendix. Goods and orders, expenses and budgets, itineraries and changes are maintained as application state, rendered by the UI, and read at task termination.

Application count alone is not informative: a client carries a multi-step commercial task—locate, fill, confirm—only if it is structurally thick. On the 35 new clients the median navigation declaration is 37 routes, 175 interactive actions, and 88 transitions, and the median interaction depth from the root is 3, so a typical shortest GUI path already crosses several layers and the step lower bound comes from page structure rather than from the length of the instruction. As a depth reference, the thickest application in MobileGym has 100 routes and 265 actions and its deepest terminal takes 7 steps to reach; the new commercial clients sit inside that structural range rather than below it.

## 3.3 Realistic cross-application workflows

Several commercial applications sit on one resettable device, each keeping its own live business state: orders, expenses, itineraries, contacts. These objects change with on-screen actions and leave a trace in device state. Clipboard, system broadcasts, and inter-app navigation connect them, so a workflow can leave the current application, enter a second one, and rewrite that application's own business objects: a payment in shopping produces a matching expense in bookkeeping; a train number selected in the calendar enters an itinerary app as a change; an address from contacts enters a checkout flow. The second application receives a real business write, not a forwarded message.

Real commercial applications do behave this way on a phone, but not controllably: login, anti-bot defenses, and irreversible side effects make the same multi-application starting point impossible to restore. Here the whole device is one snapshot, so restoring it lets the same cross-application write be run again.

## 3.4 Hybrid GUI and app-native tool use

GUI-only benchmarks assume an application never exposes a programmatic interface, and programmatic-only environments with no phone GUI assume the opposite. Real applications sit in between: they expose lookup, filtering, and drafting over their own records. MobileGym++ puts both paths in one world—the same task, the same initial state, and the same application-owned store.

Approximately 52 applications expose app-native tools. Tools are designed per application from that application's business objects—searching orders, filtering ledger entries, retrieving itinerary fields—rather than exported from the widget tree. A tool call occupies the same action slot as a tap, swipe, or text input while that application is in the foreground. Both channels write the same store, and every official task can be completed with GUI actions alone: Hybrid is a second path through the same world, not a requirement.

## 3.5 MobileGym++ Bench

Existing mobile-agent benchmarks mainly score single-app GUI sequences whose terminal is system state or a UI-level field. Two properties are not given jointly: the terminal is a commercial write in an application's own store—an order, an expense, an itinerary—and the value of that write lives in another application's live state, so the second application is actually rewritten rather than notified. MobileGym++ Bench asks whether an agent can carry those writes to completion inside resettable simulated commercial applications. Task length comes from locating, filtering, confirming, paying, and writing back across applications.

**Task design.** Tasks are organized around executable user goals and checkable terminals. Core tasks close with a business operation such as placing an order, posting an expense, creating an itinerary, sending a message, or modifying an app object. The result of that operation lands in the application's own business state. A single-app task reaches that write only after locating and filling fields across deeper pages. Instructions use user-goal language and do not name widget labels, tool namespaces, or checker fields.

In a cross-application task, the value needed for a write is present in another app's live state rather than written as a fixed constant in the instruction. The agent must identify the source, carry the value across the app boundary, and write it into the correct field; the checker verifies the relation between the resulting business fields.

**Scale and composition.** The current set contains 215 tasks across seven business domains: 109 mention one app, 74 two, 27 three, and 5 four. Tasks are distributed over multiple applications and business objects, so evaluation is not dominated by a handful of apps.

**Evaluation protocol.** Each task has three parts: a natural-language user goal, a bound initial state, and a programmatic terminal check. Success is decided by a programmatic checker: it reads the before/after diff of application business state, does not read the trace or screenshots, and does not use a model judge; different routes that accomplish the same write are equivalent. Allowed state paths are declared, and other mutations are recorded separately from success. The primary metric is task success rate. GUI-only and Hybrid are evaluated on the same tasks, initial states, and terminal checks. Mean steps on successful trajectories measure interaction efficiency conditional on completion; because failed trajectories often reach the step cap, we also report the success rate and the fraction reaching the cap to separate efficiency from reliability.
