# UX\-Agent

仓库链接🔗

https://gitcode\.com/jeditony/HarmonyArena

https://gitcode\.com/jeditony/TextTruncVerifier

开发分支：fdu\_agent

HDC模拟器：https://developer\.huawei\.com/consumer/cn/deveco\-studio/



**一阶段实现：**

端到端UX问题检测：

1. 纯图片

2. 图片\+组件树

3. 滑动验证扩展

三条链路均跑通并可通过配置和输入控制

> P\.S\. 主要关注文字截断问题
> 
> 

**UX问题**

[第一阶段数据标注规则\.pdf](图片和附件/第一阶段数据标注规则.pdf)

**实际执行**

```Markdown
npm run ux-detect
```

**三种模式**

```Plain Text
npm run ux-detect -- --mode=image
npm run ux-detect -- --mode=layout
npm run ux-detect -- --mode=slide
```

默认模式为 `slide`。

|**模式**|**执行链路**|**当前状态**|
|---|---|---|
|image|截图 → 模型检测|已完成并实机跑通|
|layout|截图 \+ UI 树 → 模型检测 → TextTruncVerifier|已完成并实机跑通|
|slide|layout 链路 → 对 unknown 主动滑动验证|代码已完成，尚未实机端到端测试|

**已完成的核心能力**

- `image` 模式不会获取布局树，也不会执行滑动。

- 新增纯图片检测阶段 `detectSnapshot()`，生产链路和测试共用。

- `layout` 模式使用原始 ArkUI `dumpLayout` 结果调用 `TextTruncVerifier`。

- 布局验证结果通过 `issue_index` 与模型问题关联。

- 布局过滤规则：

    - `true_truncation`：保留。

    - `not_truncation`：移入 `removedIssues`。

    - `unknown`：保留。

- `slide` 模式只滑动验证 `unknown`，静态已确认的问题不再操作设备。

- 滑动结果：

    - `scrollable`：过滤。

    - `confirmed`：保留。

    - `capture_failed`：保留，避免漏报。

- 删除了旧版 `truncation-validator.ts` 和滑动模块中的重复 UI 树过滤。

- 折叠屏不同状态会分别保存对应截图和布局树。

- MCP `ux_detect` 也支持 `image | layout | slide` 三种模式。

- `observe` 保持默认执行完整 `slide` 链路。

**结果结构**

每个屏幕结果现在包含：

- `modelIssues`：模型原始问题。

- `issues`：最终保留的问题。

- `removedIssues`：被布局或滑动阶段过滤的问题。

- `stages.model/layout/slide`：各阶段状态和数量统计。

- `snapshot`：截图、分辨率、布局树产物及折叠状态信息。

- `overall`：根据最终结果重新计算的 `ok | bad | unknown`。

异常时遵循“不能确认就不删除”：

- 布局树获取或解析失败：保留模型问题。

- 滑动或截图失败：保留问题。

- 阶段异常时 `overall` 为 `unknown`。

**输出产物**

根据模式按需生成：

```Plain Text
snapshot.png
snapshot_window.json
snapshot_ui-tree.txt
snapshot_bbox.png
snapshot_bbox_final.png
model_result.json
layout_result.json
slide_result.json
snapshot_ux.json
```

`image` 模式不会生成布局树和滑动产物。

**已完成测试**

- Mock 图片阶段自动化测试：`1 passed`

- HDC \+ 真实截图 \+ Mock 模型的 `image` 模式：通过

- HDC \+ 真实截图/布局树 \+ Mock 模型的 `layout` 模式：通过

