# 两例滚动问题修复与回归（2026-11-23）

本轮业务代码只修改公共容器模板及一项包装约束。没有改变自动选参公式、组合选择算法或审核标签规则。每次HAP构建后均执行完整测试集；共4个HAP构建和1次Python安装包构建检查，各次均为322项测试通过。

## 1. Healthy_life：百分比内边距改变了预期裁切位置

“任务列表”使用共享样式，包含左右／上下百分比padding。正常父宽2224px，新横向Scroll宽232px，左内边距由约73px缩为约8px，初态文字因此完整显示，原先预期的截断没有发生。

处理方式是提前拒绝：`container()`调用`reject_changed_padding_reference()`，当新包装宽度与固定子内容宽度不同，拒绝百分比padding以及无法静态求值的padding。固定数值内边距继续支持；原宽占位的自身高度裁切、同宽纵向包装继续保留。这项检查也覆盖手工提供参数的入口。

百分比的参考规则见[华为组件尺寸文档](https://developer.huawei.com/consumer/cn/doc/HarmonyOS-references/ts-universal-attributes-size/)。本轮没有新增猜测原父容器内容宽度的换算逻辑。

![原有百分比padding高度裁切回归](../images/report/padding-height-regression.png)

这个保留的高度裁切路径仍裁掉字形底部，周围原有3个目标的位置和像素均保持原样。

## 2. OhBill：小视口的滚动条干扰内容手势

“暂无数据”目标正常宽200px，生成的Scroll可见宽159px、高59px。原向左手势无位移；额外诊断发现向右拖动反而使内容左移41px，表现为拖动了滚动条。

生成的Scroll增加`.scrollBar(BarState.Off)`，保持子内容尺寸与裁切参数不变。同一自动向左手势现在使内容左移41px；前后两次可见范围为`[0,159]`和`[41,200]`，覆盖了完整字形，像素身份与内容尺寸检查均通过。相关API默认滚动条状态见[华为滚动组件文档](https://developer.huawei.com/consumer/cn/doc/HarmonyOS-references/ts-container-scrollable-common/)。

![正常、裁切初态及向左滑动后](../images/report/ohbill-scroll-fixed.png)

关闭滚动条没有取消Scroll本身的手势。原有横向长文本与纵向多行案例分别移动−692px、−102px，均观察到完整前景覆盖。纵向测试前两次分别在hdc读取进程信息、读取布局JSON时超时；原包第三次执行通过，失败日志保留。

## 3. 回归范围与结果

|检查|结果|
|---|---|
|修复前完整测试|319项通过|
|每次HAP构建后的完整测试|4次，各322项通过|
|Python安装包构建后的完整测试|322项通过|
|两款应用全部486组正常基线候选的新旧完整规划对照|458组完全一致；24组仅新增关闭滚动条；4组改为明确拒绝；额外差异0|
|原有两个组合包的6个目标重新构建、采集|所有目标bounds、origBounds、文字、类型一致；目标区域逐通道平均像素差异均为0|
|额外百分比padding高度裁切|构建采集成功，原有字形底部裁切机制保留|
|OhBill短文字、原横向长文字、原纵向多行文字|实际移动、身份与覆盖检查通过|
|独立安装检查|85份资源哈希一致；全部模块导入；SDK扫描53个site|
|详细文档|13个可执行例子通过；详细文档424处本地链接无失效，汇报等7份文档共526处链接通过检查|

全测试集包含18份历史源码替换回归、源码扫描、共享样式、参数规划、补丁与组合冲突、构建恢复、采集、图像测量、审核和架构依赖检查。486组候选对照与设备复测补充检查业务行为；没有把486次规划计为486个有效缺陷。

## 4. 可复查记录

- [机器摘要](scroll-fix.json)。
- 逐候选对照：`artifacts/scroll-fix/behavior-regression.json`。
- 四次构建后完整测试：`artifacts/scroll-fix/{ohbill,directions,app-1,app-2}-full-tests.log`。
- 安装包及最终测试：`artifacts/scroll-fix/package/result.json`、`package-full-tests.log`。
- 新包：`E:/HarmonyDev/MutationRuns/scroll-fix-ohbill-20261123`、`scroll-fix-directions-20261123`、`scroll-fix-combined-20261123`。
- 旧失败与诊断保留在`artifacts/selection-refactor`，没有覆盖历史采集。

图像观察由助手执行；正式独立审核记录继续保持pending。此轮没有调用UX-Agent模型，也没有修改UX-Agent代码。
