# 自动选参策略重构与实测核验（2026-11-23）

本轮把机制特有的自动选参接入已有算子策略表，同时检查参数、源码补丁和实际画面。没有引入每算子一个子类或新的插件框架。源码改动以当前Git提交为准；运行原件保存在本机独立目录。

## 1. 架构和行为保持

公共入口parameter_policy.choose_parameters准备前景和行带，建立SelectionContext与新的Selection，再调用策略表中的select函数，最后统一限制裁入距离并写出原有报告字段。新增operator_selection.py保存六类机制规则及共用基础公式。width-clip、line-clip、ellipsis-width共用retained_width；普通父裁切和平移使用公共规则。几何换算、源码模板、组合预算和选择算法保持原样。

- 319项完整回归通过，79.678秒；包括新策略接入、统一裁入边界、结果隔离和条件包装分号处理。
- 1680组受控输入，新旧选参结果一致：1512组返回决定，168组拒绝；覆盖19项注册能力、四个方向、文字/图片/图标/按钮/Web、单行/多行/未知前景，以及百分比和动态padding。受控输入用于等价性检查，不是1680个有效应用缺陷。
- 两款真实应用正常基线上的486组规划结果一致：220组完整计划（含参数、patches和ID）一致，266组拒绝类型及原因一致。另3个正常基线已有裁切的目标在共同前置检查中拒绝，未进入选参。
- 85份安装资源SHA一致；独立安装、全模块导入和实际SDK扫描通过，OhBill扫描到53个site。详细文档13个可执行例子和422个本地链接通过。

等价性参照为重构前提交15104e9中的parameter_policy.py，副本只保存在artifacts/selection-refactor用于此次验证，未把旧算法作为兼容实现留在核心。

## 2. 构建发现并修复的问题

首轮OhBill构建采集成功，Healthy_life构建失败。失败位置为MainPage.ets的TabBuilder：原Image表达式末尾有分号，单实例条件改写留下`if (...) {...} else {...};`，ArkUI报告“Only UI component syntax can be written here”。

修复是：SDK扫描额外记录表达式语句后缀statement_suffix；生成条件补丁时消费末尾分号，保留中间注释，并同步扩大before/end范围。普通组件表达式的分号照常保留。用例覆盖有分号、无分号、带注释，以及按实例键和按索引选择。

首轮失败记录保存在E:/HarmonyDev/MutationRuns/selection-strategy-20261123。修复后使用新目录selection-strategy-final-20261123重新规划、构建和采集，两包各3项修改均完成。Healthy_life最终包仍包含带分号的重复Image实例，确认通过了原来失败的真实构建位置。

## 3. 最终组合包逐目标观察

以下为助手查看正常与修改截图的观察；原质量审核仍保持pending。图树摘要与图片/HAP哈希另由工具核验，六个目标在截图前后的UI树中均稳定。

|应用|机制|实际观察|
|---|---|---|
|OhBill|whitespace-clip，账单图标|右侧组件空白收缩10px，图标主体完整|
|OhBill|scroll-recovery，月份数字|初态第二个数字被裁；自动滑动因目标位于可点击区域，未找到安全轨迹，恢复不计成功|
|OhBill|fixed-parent-clip，经济图表|底部横轴/箭头被裁；父高度缩短27px，同一卡片标题跟随上移|
|Healthy_life|whitespace-clip，空任务插画|右侧空白缩短约20px，插画主体完整|
|Healthy_life|height-clip，首页文字|字形底部笔画缺失；同坐标裁图有色像素纵向范围由29px变为23px|
|Healthy_life|translate-clip，成就图标|图标顶部被裁，原框比可见框向上多17px；修改作用于选中的Builder实例|

![首页文字同坐标放大图：左正常，右修改](../images/selection-strategy/height-detail.png)

这张放大图直接展示缺少的底部笔画，不能只凭Text高度改变就判断注入成功。

![OhBill留白](../images/selection-strategy/app-1-target-1.png)
![OhBill滚动初态](../images/selection-strategy/app-1-target-2.png)
![OhBill固定父裁切](../images/selection-strategy/app-1-target-3.png)
![Healthy_life留白](../images/selection-strategy/app-2-target-1.png)
![Healthy_life文字高度](../images/selection-strategy/app-2-target-2.png)
![Healthy_life图标平移](../images/selection-strategy/app-2-target-3.png)

## 4. 滚动专项与未通过样本

以下保留修复前观察。2026-11-23的后续修复及完整回归见[两例滚动修复](scroll-fix.md)：百分比padding窄包装已提前拒绝，小视口滚动条干扰已修正，并完成原有样例回归。

Healthy_life“任务列表”作为补充目标时，百分比padding在窄包装中改变了字形位置，初态仍完整显示文字。虽然实际滑动执行了两次，分别相对初态移动−117px和−233px，这份样本没有形成预期的先裁切再恢复。像素身份检查也记录different，保留为未通过样本。

![百分比padding目标：正常、初态、两次滑动](../images/selection-strategy/text-scroll.png)

该目标新旧完整计划已逐项比对一致，问题来自已有包装与百分比样式的相互作用，不是这次选参策略拆分新增。没有把它计入有效滚动难负例，也未为让记录通过而调整测量阈值。后续使用普通无百分比padding、不可点击的真实文字目标单独验证恢复能力，结果见下文。

OhBill“暂无数据”不带百分比padding，初态确实裁掉了最后一字的部分内容。自动手势已分发，但树与图都没有显示内容位移；程序按no_forward_progress停止。随后用同一设备连续状态做一次更长、更慢的显式手势重试，仍为0px位移。原有滑动方向和恢复代码本轮未改变；该目标新旧完整计划也一致。本轮保留为“截断已发生、恢复未证实”，不赋可恢复难负例标签；实际不响应手势的原因尚未定位。

![普通文字：正常、初态、自动滑动后](../images/selection-strategy/plain-text-scroll.png)

因此，本轮证明选参重构保持了原决定与补丁，并实际验证了正例裁切和留白负例。滚动构造的静态、动态结果分别保存，部分目标仍需人工筛选。这些未通过观察没有被移除或补写为成功。

## 5. 复查入口

- 参数与完整计划对照：artifacts/selection-refactor/behavior-comparison.json。
- 完整回归：artifacts/selection-refactor/final-tests.log。
- 安装与文档例子：artifacts/selection-refactor/package/result.json。
- 最终组合包：E:/HarmonyDev/MutationRuns/selection-strategy-final-20261123。
- 百分比padding专项：E:/HarmonyDev/MutationRuns/selection-scroll-20261123。
- 普通文字滚动专项：E:/HarmonyDev/MutationRuns/selection-scroll-plain-20261123；显式重试记录在artifacts/selection-refactor/explicit-scroll-retry.json。
- 机器摘要：[selection-strategy.json](selection-strategy.json)；当前实现摘要：[current-source-manifest.json](current-source-manifest.json)。

详细学习文档第2.10节更新策略登记示例，第10.0.1节讲完整选参调用与输入输出，第13.4.1节解释分号边界，第27章同步函数位置。原商业材料、历史失败和UX-Agent代码没有改动。
