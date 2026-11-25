# 同一区域里操作本质相同的题

只标注，不删除。下面每道题的文件都还在这个题包里。

来源只读：`/Users/zhangyingying/CUA/评测集建设/maccua-tasks/zyy-e31-gen-v1`
本目录：`/Users/zhangyingying/CUA/评测集建设/maccua-tasks/zyy-e31-gen-v1p`
生成时间：2026-11-23 22:14:18

判重只在同一个 `region_id` 里面做。先看操作原文：去掉括号里的调研注，再去掉句尾用来交文件的「并导出 PNG」。文件格式、旋转拉直、非破坏、斜杠导出这些不一样就不并。然后满足下面任意一条就标成同质：题号关键词一边包含另一边（例如 `pencil-sketch` 和 `figma-pencil-sketch`）；都是同一类操作、只是手势不同（拖边和重画裁剪框）；去掉括注后二字重合度达到 0.80；或者一句几乎包含另一句，多出来的只是「多个」「在画布上」。设置里的不同面板不会并在一起。屏蔽和取消屏蔽这种相反操作也不会并。

建议保留的那一道，取同组里操作原文最短的；一样短就取题号字典序靠前的。规格里的 distinct_because 原样附在后面，用来人工推翻。

例如 `figma-2` 里 `figma-2-arc-ring`、`figma-2-figma-arc-tool-ring` 被标成同一操作。建议留 `figma-2-arc-ring`，其余先留在包里。
同一区域。文件格式、旋转、非破坏这类区分都是「无」。题号里的关键词一边包含另一边（arc、ring）。

## 统计

| 项 | 数 |
|---|---|
| 题数 | 196 |
| 前缀已换 | 196 |
| 前缀本来就是 v2 | 0 |
| 前缀对不上、没改 | 0 |
| Mail 题 | 39 |
| Mail 清理已加 | 39 |

## figma-2

应用：Figma。这一区 15 道。

### 同质组 1：其他

- `figma-2-arc-ring`
  - 操作：用 Arc tool 制作弧形、半圆或环形并导出 PNG
  - 评分要点：指定路径存在导出的 PNG 文件；PNG 带 alpha 通道（RGBA）；图像中存在非空白的图形像素
- `figma-2-figma-arc-tool-ring`
  - 操作：用 Arc 工具创建圆弧、半圆或圆环（Arc tool: create arcs, semi-circles and rings 在文章名单中，正文未逐篇打开）
  - 评分要点：导出 PNG 存在于指定路径且为带 alpha 通道的 RGBA 图像；图形外轮廓范围内、按半圆或圆环形态应为空的区域像素为透明或背景色；应有图形的区域像素为指定填充色
- 判重理由：同一区域。文件格式、旋转、非破坏这类区分都是「无」。题号里的关键词一边包含另一边（arc、ring）。
- 建议保留：`figma-2-arc-ring`
- 建议先留在包里、不自动删除：`figma-2-figma-arc-tool-ring`
- 规格自己写的区分：
  - `figma-2-arc-ring`：Arc tool（create arcs, semi-circles and rings）是目录点名的独立文章，产物是弧形/环形这一专门几何类别，不同于通用形状工具题
  - `figma-2-figma-arc-tool-ring`：Arc 工具产出的是被掏空或切开的圆形几何，可核点是「本该是空的区域确实透明」，这是普通形状绘制题不会出现的像素形态。

### 同质组 2：图层

- `figma-2-auto-layout`
  - 操作：对选中图层添加自动布局，设置流向、padding 与 gap，并使用 hug contents，导出 PNG
  - 评分要点：指定路径存在导出的 PNG 文件；PNG 带 alpha 通道（RGBA）；图像中对象按给定流向排列；图像中测得的对象间距与给定 gap 一致；图像中测得的边缘空隙与给定 padding 一致
- `figma-2-figma-auto-layout-list`
  - 操作：给一组图层添加自动布局并设置流向、Padding、Gap（Guide to auto layout 专页已核）
  - 评分要点：导出 PNG 存在于指定路径且为带 alpha 通道的 RGBA 图像；图像中各子项之间的像素间距等于指定的 Gap；图像边缘到最外侧子项的像素空隙等于指定的 Padding；子项在图像中沿垂直方向排列
- 判重理由：同一区域。文件格式、旋转、非破坏这类区分都是「无」。题号里的关键词一边包含另一边（auto、layout）。
- 建议保留：`figma-2-auto-layout`
- 建议先留在包里、不自动删除：`figma-2-figma-auto-layout-list`
- 规格自己写的区分：
  - `figma-2-auto-layout`：自动布局有独立的已核验专页（Guide to auto layout），考察的是布局引擎的流向、间距与尺寸行为，是地图明确列出的缺口，不是图形绘制题
  - `figma-2-figma-auto-layout-list`：自动布局是地图表写明的本组缺口，核的是 Padding、Gap、流向这些布局参数在导出图里的几何结果，与 Frame 嵌套题核的填充颜色和容器关系完全不同。

### 同质组 3：图层

- `figma-2-combine-boolean`
  - 操作：合并多个图层（布尔运算）得到组合形状并导出 PNG
  - 评分要点：指定路径存在导出的 PNG 文件；PNG 带 alpha 通道（RGBA）；图像中组合后的轮廓像素可见
- `figma-2-figma-combine-layers-boolean`
  - 操作：合并图层得到组合形状（Layers 101: Combine layers 在文章名单中，正文未逐篇打开；地图表列明布尔运算是本组缺口）
  - 评分要点：导出 PNG 存在于指定路径且为带 alpha 通道的 RGBA 图像；两个原形状覆盖的合并区域像素为同一指定填充色；按组合结果应为空的区域像素为透明或背景色
- 判重理由：同一区域。文件格式、旋转、非破坏这类区分都是「无」。题号里的关键词一边包含另一边（boolean、combine）。一句几乎包含另一句，多出来的只有「多个」。
- 建议保留：`figma-2-combine-boolean`
- 建议先留在包里、不自动删除：`figma-2-figma-combine-layers-boolean`
- 规格自己写的区分：
  - `figma-2-combine-boolean`：Layers 101: Combine layers 是目录点名的文章，且地图缺口明确列出布尔运算；操作是多形状合并为新轮廓，与单形状绘制和遮罩裁剪都不同
  - `figma-2-figma-combine-layers-boolean`：核对的是两个形状经合并后在导出图中呈现为单一连续填充区域这一组合结果，与单独绘制形状、与 Frame 嵌套的父子填充核法都不同。

### 同质组 4：其他

- `figma-2-figma-frame-nesting`
  - 操作：创建 Frame 并在其中放入形状与嵌套子 Frame（Frames in Figma Design 专页已核）
  - 评分要点：导出 PNG 存在于指定路径，宽高与指定的 frame 尺寸一致；导出 PNG 为带 alpha 通道的 RGBA 图像；图像背景区域像素为指定的父 Frame 填充色；图像内指定区域像素为子 Frame 的不同填充色
- `figma-2-frame-nested`
  - 操作：创建一个 top-level frame，在其中放入形状、文字，并嵌套一个子 frame，为 frame 设置尺寸和填充后导出 PNG
  - 评分要点：指定路径存在导出的 PNG 文件；PNG 带 alpha 通道（RGBA）；导出图像的宽高与说明文件给定的 frame 尺寸一致；图像中 frame 填充色区域的像素颜色与给定填充色一致
- 判重理由：同一区域。文件格式、旋转、非破坏这类区分都是「无」。题号里的关键词一边包含另一边（nest）。
- 建议保留：`figma-2-figma-frame-nesting`
- 建议先留在包里、不自动删除：`figma-2-frame-nested`
- 规格自己写的区分：
  - `figma-2-figma-frame-nesting`：核对的是 Frame 作为容器的嵌套与填充这一已核专页写明的功能，而不是单个形状或自动布局的间距；父子两层填充同时出现在导出图里是本题独有的结果。
  - `figma-2-frame-nested`：考察 Frames 专页核验过的容器概念：top-level frame、parent/child 嵌套、frame 的尺寸与填充，这是容器结构题而非画单个图形

### 同质组 5：图层

- `figma-2-figma-mask-crop`
  - 操作：用蒙版限制图层可见范围（Masks 在 Create and edit layers 文章名单中，正文未逐篇打开）
  - 评分要点：导出 PNG 存在于指定路径且为带 alpha 通道的 RGBA 图像；蒙版形状范围内的像素来自被蒙版的内容图层；蒙版形状范围外、内容图层原本覆盖的区域像素为透明或背景色
- `figma-2-mask`
  - 操作：用 Masks 对图层做遮罩裁剪并导出 PNG
  - 评分要点：指定路径存在导出的 PNG 文件；PNG 带 alpha 通道（RGBA）；图像中被遮罩图层只在遮罩形状区域内有像素，区域外为透明或背景
- 判重理由：同一区域。文件格式、旋转、非破坏这类区分都是「无」。题号里的关键词一边包含另一边（mask）。
- 建议保留：`figma-2-mask`
- 建议先留在包里、不自动删除：`figma-2-figma-mask-crop`
- 规格自己写的区分：
  - `figma-2-figma-mask-crop`：蒙版的可核结果是「内容在形状外被裁掉」，即形状外原本有内容的区域变透明，这与布尔合并题核「合并区域为单色」的方向正好相反，不是参数替换。
  - `figma-2-mask`：Masks 是目录点名的独立文章，考察两个图层之间的可见性裁剪关系，不是绘制单个图形也不是容器组织

### 同质组 6：其他

- `figma-2-figma-pencil-sketch`
  - 操作：用铅笔工具在画布上手绘（Sketch on the canvas with the pencil tool 在文章名单中，正文未逐篇打开）
  - 评分要点：导出 PNG 存在于指定路径，宽高与指定尺寸一致；指定区域内存在指定颜色的非背景像素；frame 其余背景区域像素为指定背景填充色
- `figma-2-pencil-sketch`
  - 操作：用 pencil tool 在画布上手绘并导出 PNG
  - 评分要点：指定路径存在导出的 PNG 文件；PNG 带 alpha 通道（RGBA）；图像中存在非空白的笔迹像素
- 判重理由：同一区域。文件格式、旋转、非破坏这类区分都是「无」。题号里的关键词一边包含另一边（pencil、sketch）。都是「其他」，做法不同：figma-2-figma-pencil-sketch 用了手绘，figma-2-pencil-sketch 用了手绘。
- 建议保留：`figma-2-pencil-sketch`
- 建议先留在包里、不自动删除：`figma-2-figma-pencil-sketch`
- 规格自己写的区分：
  - `figma-2-figma-pencil-sketch`：铅笔是自由手绘工具，产物是不规则笔迹，评分只能核「指定区域存在指定颜色的笔迹像素」，与形状、圆弧等几何工具题的精确区域核对方式不同。
  - `figma-2-pencil-sketch`：Sketch on the canvas with the pencil tool 是目录点名的独立文章，自由手绘与形状工具的预设几何绘制是不同操作路径

### 同质组 7：其他

- `figma-2-figma-shape-tools-draw`
  - 操作：用形状工具绘制形状（Shape tools 在 Create and edit layers 文章名单中，正文未逐篇打开）
  - 评分要点：导出 PNG 存在于指定路径，宽高与指定尺寸一致；导出 PNG 为带 alpha 通道的 RGBA 图像；指定位置区域的像素为指定填充色；指定数量的形状区域与背景可区分
- `figma-2-shape-tool`
  - 操作：用形状工具在画布上绘制形状并导出 PNG
  - 评分要点：指定路径存在导出的 PNG 文件；PNG 带 alpha 通道（RGBA）；图像中形状区域非空白、像素可读
- 判重理由：同一区域。文件格式、旋转、非破坏这类区分都是「无」。题号里的关键词一边包含另一边（shape、tool）。一句几乎包含另一句，多出来的只有「在画布上」。
- 建议保留：`figma-2-shape-tool`
- 建议先留在包里、不自动删除：`figma-2-figma-shape-tools-draw`
- 规格自己写的区分：
  - `figma-2-figma-shape-tools-draw`：操作对象是形状工具本身的绘制产物，不涉及容器嵌套也不涉及布局参数；与现有 figma-rect 的区别在于本题要求多个形状按位置落在导出图的可核区域内。
  - `figma-2-shape-tool`：Shape tools 是目录点名的独立文章，操作对象是基础几何形状绘制，不涉及 frame 嵌套、弧形参数或遮罩关系

### 没有并进同质组

- `figma-2-frame-vs-group`
  - 操作：把同一组图层分别用 frame 和 group 两种方式组合
  - 家族「图层」，区分特征「无」。建议保留。

## figma-4

应用：Figma。这一区 8 道。

### 没有并进同质组

- `figma-4-animated-components`
  - 操作：创建并使用动画组件（Create and use animated components）
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-4-component-properties`
  - 操作：使用组件属性（Explore component properties）
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-4-create-component`
  - 操作：把选中的图层转为组件（Create components to reuse in designs）
  - 家族「图层」，区分特征「无」。建议保留。
- `figma-4-create-slots`
  - 操作：创建并使用 slots（Create and use slots）
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-4-create-variants`
  - 操作：创建并使用变体（Create and use variants）
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-4-interactive-variants`
  - 操作：用变体创建交互组件（Create interactive components with variants）
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-4-migrate-slots`
  - 操作：把库迁移为使用 slots（Migrate a library to using slots）
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-4-name-organize`
  - 操作：命名并组织组件（Name and organize components）
  - 家族「其他」，区分特征「无」。建议保留。

## figma-5

应用：Figma。这一区 1 道。

### 没有并进同质组

- `figma-5-figma-create-code-layer`
  - 操作：在 Figma Design 文件中创建一个 code layer（对应官方分组 5 Create code layers）
  - 家族「图层」，区分特征「无」。建议保留。

## figma-6

应用：Figma。这一区 6 道。

### 没有并进同质组

- `figma-6-figma-proto-animation-duration`
  - 操作：在 Prototype 标签里为一条连接设置动画时长
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-6-figma-proto-connect`
  - 操作：在两个顶层 Frame 之间建立一条原型连接（选中热点，拖到目标 Frame）
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-6-figma-proto-multi-flow`
  - 操作：在同一个页面上建立多条 flow
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-6-figma-proto-preview-animation`
  - 操作：预览原型动画（Preview your animation）
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-6-figma-proto-scroll-to`
  - 操作：设置一个 Scroll to 交互，destination 指向同一个顶层 Frame 内部
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-6-figma-proto-starting-point`
  - 操作：为一个顶层 Frame 添加 flow starting point（通过右侧 Flow starting point 面板或右键 Add starting point）
  - 家族「其他」，区分特征「无」。建议保留。

## figma-7

应用：Figma。这一区 8 道。

### 没有并进同质组

- `figma-7-export-jpg-no-alpha`
  - 操作：为选中对象添加 JPG 导出设置并导出
  - 家族「导出」，区分特征「JPG」。建议保留。
- `figma-7-export-pdf`
  - 操作：为选中对象添加 PDF 导出设置并导出
  - 家族「导出」，区分特征「PDF」。建议保留。
- `figma-7-export-slash-nested-folder`
  - 操作：导出设置的名字里使用斜杠，使导出结果落入嵌套文件夹
  - 家族「导出」，区分特征「斜杠嵌套目录」。建议保留。
- `figma-7-export-svg-editable-text`
  - 操作：导出 SVG 时在导出设置里取消 Outline text，保留可编辑文字
  - 家族「导出」，区分特征「SVG、文字」。建议保留。
- `figma-7-figma-7-export-png-alpha`
  - 操作：选中一个图层/Frame，在右侧边栏 Export 区导出 PNG，桌面 App 中改文件名并选保存位置
  - 家族「导出」，区分特征「PNG」。建议保留。
- `figma-7-fill-show-in-exports-off`
  - 操作：在 Frame 的 Fill 里取消 Show in exports，导出 PNG 时不带这块填充
  - 家族「导出」，区分特征「PNG、Show in exports、填充」。建议保留。
- `figma-7-multiple-export-settings`
  - 操作：点 Export 区的加号为同一对象添加多条导出设置，一次导出得到多个文件
  - 家族「导出」，区分特征「一次多条导出」。建议保留。
- `figma-7-slice-export-region`
  - 操作：用 Slice 工具（工具栏 Region tools 下）圈一块画布并导出该区域
  - 家族「导出」，区分特征「Slice」。建议保留。

## mail-2-1

应用：Mail。这一区 1 道。

### 没有并进同质组

- `mail-2-1-mail-writing-tools`
  - 操作：在邮件中使用 Writing Tools
  - 家族「其他」，区分特征「无」。建议保留。

## mail-2-10

应用：Mail。这一区 7 道。

### 没有并进同质组

- `mail-2-10-mail-settings-accounts-panel`
  - 操作：打开 Mail > Settings，进入 Accounts 面板（官方说明：添加、删除、停用账号；Mailbox Behaviors 决定草稿、已发送、垃圾、已删除、已归档存在哪；Server Settings 改收发服务器）
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-10-mail-settings-composing-panel`
  - 操作：打开 Mail > Settings，进入 Composing 面板（官方说明：撰写、填写地址、回复）
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-10-mail-settings-extensions-panel`
  - 操作：打开 Mail > Settings，进入 Extensions 面板（官方说明：管理 Mail 里用的扩展）
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-10-mail-settings-fonts-colors-panel`
  - 操作：打开 Mail > Settings，进入 Fonts & Colors 面板（官方说明：显示邮件用的字体和字号）
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-10-mail-settings-general-panel`
  - 操作：打开 Mail > Settings，进入 General 面板（官方说明：多久检查新邮件，以及搜索时包含哪些信）
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-10-mail-settings-privacy-panel`
  - 操作：打开 Mail > Settings，进入 Privacy 面板（官方说明：Mail Privacy Protection）
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-10-mail-settings-viewing-panel`
  - 操作：打开 Mail > Settings，进入 Viewing 面板（官方说明：邮件在查看器里怎么显示）
  - 家族「其他」，区分特征「无」。建议保留。

## mail-2-11

应用：Mail。这一区 5 道。

### 没有并进同质组

- `mail-2-11-mail-auto-automator-workflow`
  - 操作：自动操作：把多个脚本编辑器动作串成工作流程（例子是给所有联系人发信）
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-11-mail-auto-rule-script`
  - 操作：脚本编辑器：把脚本挂到邮件规则上，条件满足就跑
  - 家族「规则」，区分特征「无」。建议保留。
- `mail-2-11-mail-auto-script-create-draft`
  - 操作：脚本编辑器：用脚本里的术语自动建信（建好后保存为草稿）
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-11-mail-auto-script-send`
  - 操作：脚本编辑器：用脚本里的术语自动发信
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-11-mail-auto-shortcut-add-sender`
  - 操作：快捷指令：用现成的或自己做（例子是把发件人加进通讯录）
  - 家族「其他」，区分特征「无」。建议保留。

## mail-2-12

应用：Mail。这一区 5 道。

### 同质组 1：其他

- `mail-2-12-mail-whatsnew-suggestions-directions`
  - 操作：使用 What's new 里提到的 Suggestions，按对话做进一步动作，示例之一：路线
  - 评分要点：人工在界面上确认：对该对话触发了 Suggestions 的路线动作（材料未写结果落在何处，只能界面确认）
- `mail-2-12-mail-whatsnew-suggestions-reservation`
  - 操作：使用 What's new 里提到的 Suggestions，按对话做进一步动作，示例之一：管理预订
  - 评分要点：人工在界面上确认：对该对话触发了 Suggestions 的管理预订动作（材料未写结果落在何处，只能界面确认）
- `mail-2-12-mail-whatsnew-suggestions-send-mail`
  - 操作：使用 What's new 里提到的 Suggestions，按对话做进一步动作，示例之一：发信
  - 评分要点：Sent 邮箱里出现对应主题的信（发出的信可评分到「Mail 已接受」为止；subject 在字典说明里点了名）
- 判重理由：同一区域。文件格式、旋转、非破坏这类区分都是「无」。去掉括注之后操作原文二字重合度 0.86，像同一句换了一个词。
- 建议保留：`mail-2-12-mail-whatsnew-suggestions-directions`
- 建议先留在包里、不自动删除：`mail-2-12-mail-whatsnew-suggestions-reservation`、`mail-2-12-mail-whatsnew-suggestions-send-mail`
- 规格自己写的区分：
  - `mail-2-12-mail-whatsnew-suggestions-directions`：路线是搜索摘录里 Suggestions 列出的另一类动作，操作对象和结果类型与管预订、发信不同，不是换参数
  - `mail-2-12-mail-whatsnew-suggestions-reservation`：Suggestions 的三个示例动作（管预订、路线、发信）在搜索摘录里是并列的不同动作，管理预订与规划路线、发信是不同的操作类型，不是同一动作换参数
  - `mail-2-12-mail-whatsnew-suggestions-send-mail`：同为 Suggestions 下的动作，但发信的结果会落到 Sent 邮箱这一邮件状态，与管预订、路线两道只停在界面上的动作在结果形态上根本不同

### 没有并进同质组

- `mail-2-12-mail-whatsnew-expanded-search`
  - 操作：使用 What's new 里提到的 Expanded Search Results，按意思搜索而不限于打进去的词
  - 家族「搜索」，区分特征「无」。建议保留。
- `mail-2-12-mail-whatsnew-personalized-writing`
  - 操作：使用 What's new 里提到的 Personalized Writing 功能写信
  - 家族「其他」，区分特征「无」。建议保留。

## mail-2-3

应用：Mail。这一区 5 道。

### 没有并进同质组

- `mail-2-3-mail-account-description`
  - 操作：在 Account Information 面板修改账号的 Description（出现在边栏的名字）
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-3-mail-account-download-attachments`
  - 操作：在 Account Information 面板设置 Download Attachments 选项（All / Recent / None）
  - 家族「附件」，区分特征「无」。建议保留。
- `mail-2-3-mail-account-maildrop`
  - 操作：在 Account Information 面板切换 Send large attachments with Mail Drop
  - 家族「附件」，区分特征「无」。建议保留。
- `mail-2-3-mail-account-server-settings`
  - 操作：核对账号的服务器主机名、端口、TLS（入门页和账号页都说按屏幕提示）
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-3-mail-icloud-custom-domain`
  - 操作：iCloud+ 自定义域名：在系统设置里点自己的名字，再进 iCloud、Mail，配置自定义域名（最多五个，要先有一个主 iCloud Mail 地址）
  - 家族「其他」，区分特征「无」。建议保留。

## mail-2-5

应用：Mail。这一区 6 道。

### 没有并进同质组

- `mail-2-5-mail-emoji-symbols-insert`
  - 操作：用工具栏按钮或 Edit > Emoji & Symbols 在邮件正文插入表情或符号
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-5-mail-pdf-handwritten-sign`
  - 操作：用 Mail 里的标记（或预览 App）给 PDF 做手写签名
  - 家族「其他」，区分特征「PDF」。建议保留。
- `mail-2-5-mail-signature-add-image`
  - 操作：把图像拖进签名预览区，做一条带图像的签名
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-5-mail-signature-below-quote`
  - 操作：取消 “Place signature above quoted text”，使回复时签名放在引用原文下面
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-5-mail-signature-default-choose`
  - 操作：用 Signatures 设置表里的 Choose Signature 为账号指定默认签名，然后新建邮件存草稿
  - 家族「草稿」，区分特征「无」。建议保留。
- `mail-2-5-mail-signature-match-font`
  - 操作：勾选 Signatures 设置表里的 Always match my default message font，使签名跟随 Fonts & Colors 里的邮件字体
  - 家族「文字」，区分特征「无」。建议保留。

## mail-2-6

应用：Mail。这一区 4 道。

### 没有并进同质组

- `mail-2-6-mail-mailbox-create-sub`
  - 操作：新建邮箱时 Location 选一个已有邮箱，使新邮箱成为它的子邮箱
  - 家族「邮箱」，区分特征「无」。建议保留。
- `mail-2-6-mail-mailbox-delete`
  - 操作：选中邮箱后用 Mailbox > Delete Mailbox 删除邮箱
  - 家族「邮箱」，区分特征「无」。建议保留。
- `mail-2-6-mail-mailbox-rebuild`
  - 操作：选中邮箱后用 Mailbox > Rebuild 重建邮箱
  - 家族「邮箱」，区分特征「无」。建议保留。
- `mail-2-6-mail-mailbox-reorder`
  - 操作：在边栏里拖动同一账号下的邮箱排序
  - 家族「邮箱」，区分特征「无」。建议保留。

## mail-2-8

应用：Mail。这一区 2 道。

### 没有并进同质组

- `mail-2-8-mail-block-sender`
  - 操作：Block Sender
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-8-mail-unblock-sender`
  - 操作：Unblock Sender
  - 家族「其他」，区分特征「无」。建议保留。

## mail-2-9

应用：Mail。这一区 4 道。

### 没有并进同质组

- `mail-2-9-mail-filter`
  - 操作：过滤显示邮件
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-9-mail-remind-me`
  - 操作：设置邮件提醒
  - 家族「其他」，区分特征「无」。建议保留。
- `mail-2-9-mail-search`
  - 操作：搜索邮件
  - 家族「搜索」，区分特征「无」。建议保留。
- `mail-2-9-mail-vip-add`
  - 操作：添加 VIP 联系人
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-1

应用：Adobe Photoshop 2026。这一区 8 道。

### 没有并进同质组

- `ps-2-1-ps-whatsnew-copy-character-style`
  - 操作：把字符样式从一个文字块拷贝到另一个文字块（发布说明 version 28.0 新增：字符样式可以跨文字块拷贝）
  - 家族「文字」，区分特征「文字」。建议保留。
- `ps-2-1-ps-whatsnew-generative-recompose`
  - 操作：使用 Generative Recompose 重构图像构图
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-1-ps-whatsnew-generative-restyle`
  - 操作：对图像使用 Generative restyle 改变画面风格
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-1-ps-whatsnew-generative-upscale`
  - 操作：使用 Generative Upscale 放大图像
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-1-ps-whatsnew-prompt-to-edit`
  - 操作：使用 Prompt to edit 以文字提示编辑图像
  - 家族「文字」，区分特征「文字」。建议保留。
- `ps-2-1-ps-whatsnew-quick-compare`
  - 操作：使用 Quick Compare 分屏比较编辑前后的画面
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-1-ps-whatsnew-relight`
  - 操作：使用 version 28.0 新功能 Relight 为照片添加光源（官方写最多三个光源）
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-1-ps-whatsnew-remove-object`
  - 操作：使用新功能去掉照片中的物体及其相关元素
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-10

应用：Adobe Photoshop 2026。这一区 7 道。

### 同质组 1：其他

- `ps-2-10-ps-lasso`
  - 操作：Lasso
  - 评分要点：Selection created using Lasso tool
- `ps-2-10-ps-polygonal-lasso`
  - 操作：Polygonal Lasso
  - 评分要点：Selection created using Polygonal Lasso tool
- 判重理由：同一区域。文件格式、旋转、非破坏这类区分都是「无」。题号里的关键词一边包含另一边（lasso）。
- 建议保留：`ps-2-10-ps-lasso`
- 建议先留在包里、不自动删除：`ps-2-10-ps-polygonal-lasso`
- 规格自己写的区分：
  - `ps-2-10-ps-lasso`：Uses Lasso tool for freehand drawing, different from Polygonal Lasso which uses straight segments
  - `ps-2-10-ps-polygonal-lasso`：Uses Polygonal Lasso tool with straight segments, different from Lasso which is freehand

### 没有并进同质组

- `ps-2-10-ps-deselect`
  - 操作：Deselect
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-10-ps-elliptical-marquee`
  - 操作：Elliptical Marquee
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-10-ps-magic-wand`
  - 操作：Magic Wand
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-10-ps-rectangular-marquee`
  - 操作：Rectangular Marquee
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-10-ps-save-load-selection`
  - 操作：Save and load selections
  - 家族「选区」，区分特征「无」。建议保留。

## ps-2-11

应用：Adobe Photoshop 2026。这一区 6 道。

### 没有并进同质组

- `ps-2-11-clipping-mask`
  - 操作：创建剪贴蒙版
  - 家族「蒙版」，区分特征「蒙版」。建议保留。
- `ps-2-11-layer-mask-add`
  - 操作：添加图层蒙版
  - 家族「图层」，区分特征「蒙版」。建议保留。
- `ps-2-11-mask-disable-apply`
  - 操作：停用或应用图层蒙版
  - 家族「图层」，区分特征「蒙版」。建议保留。
- `ps-2-11-mask-from-transparency`
  - 操作：从透明度创建图层蒙版
  - 家族「图层」，区分特征「透明通道、蒙版」。建议保留。
- `ps-2-11-object-mask`
  - 操作：为检测到的对象创建蒙版
  - 家族「蒙版」，区分特征「蒙版」。建议保留。
- `ps-2-11-vector-mask`
  - 操作：创建矢量蒙版
  - 家族「蒙版」，区分特征「蒙版」。建议保留。

## ps-2-12

应用：Adobe Photoshop 2026。这一区 3 道。

### 没有并进同质组

- `ps-2-12-ps-blend-auto-blend-layers`
  - 操作：对多张已打开的照片使用 Auto-Blend Layers 进行合成
  - 家族「图层」，区分特征「无」。建议保留。
- `ps-2-12-ps-blend-depth-of-field`
  - 操作：按本组目录标题「景深合成」所指的功能，把多张照片合成为一张
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-12-ps-blend-group-photo`
  - 操作：按本组目录标题「多人合影」所指的功能，把多张合影照片合成为一张
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-13

应用：Adobe Photoshop 2026。这一区 7 道。

### 同质组 1：其他

- `ps-2-13-ps-repair-remove-bg`
  - 操作：去掉背景（Remove objects and fill space 目录标题中点名的操作）
  - 评分要点：导出的 PNG 中，原背景区域的像素不再是种子图的背景颜色；主体区域的像素与种子图中的主体一致
- `ps-2-13-ps-repair-remove-tool`
  - 操作：Remove tool（目录标题中点名的操作）
  - 评分要点：导出图像中原物体所在区域的像素与周围背景接近，可与参考图比对；画面其余区域的像素与种子图一致
- 判重理由：同一区域。文件格式、旋转、非破坏这类区分都是「无」。题号里的关键词一边包含另一边（remove、repair）。
- 建议保留：`ps-2-13-ps-repair-remove-tool`
- 建议先留在包里、不自动删除：`ps-2-13-ps-repair-remove-bg`
- 规格自己写的区分：
  - `ps-2-13-ps-repair-remove-bg`：目录标题点名的是去掉整幅图的背景，针对的是背景整体，而不是像 Remove tool 或内容识别填充那样移除画面中的某个局部物体。
  - `ps-2-13-ps-repair-remove-tool`：它是目录中独立列出的 Remove tool，操作方式是用工具直接涂抹，不经过选区加填充命令的流程，与 Content-Aware Fill 是两个不同的功能条目。

### 没有并进同质组

- `ps-2-13-ps-repair-clone-stamp`
  - 操作：仿制图章（Heal and clone 目录标题中点名的操作）
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-13-ps-repair-content-aware-fill`
  - 操作：Content-Aware Fill（目录标题中点名的操作）
  - 家族「填充」，区分特征「无」。建议保留。
- `ps-2-13-ps-repair-generate-background`
  - 操作：Generate Background（目录标题中点名的操作）
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-13-ps-repair-patch`
  - 操作：修补（Heal and clone 目录标题中点名的操作）
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-13-ps-repair-red-eye`
  - 操作：红眼（Heal and clone 目录标题中点名的操作）
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-14

应用：Adobe Photoshop 2026。这一区 6 道。

### 没有并进同质组

- `ps-2-14-ps-channel-manipulation`
  - 操作：HDR 与通道操作（HDR and channel manipulation）：对图像的单个颜色通道做操作，使合成像素发生指定变化
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-14-ps-choose-color-apply`
  - 操作：选择颜色（Choose colors）：选定一个指定颜色并把它用到画面上，使结果像素呈现该颜色
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-14-ps-color-correction-neutral`
  - 操作：颜色校正（Color corrections）：对一张整体偏色的图像做颜色校正，使画面回到中性
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-14-ps-color-effect`
  - 操作：颜色效果（Color effects and techniques）：对图像套用一种颜色效果，使整体色彩呈现与参考一致
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-14-ps-color-profile-embed`
  - 操作：颜色配置文件（Color profiles）：保存文件时嵌入颜色配置文件
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-14-ps-selective-color-adjust`
  - 操作：选择性颜色调整（Selective color adjustments）：只改变画面中某一种颜色范围，其余区域不变
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-15

应用：Adobe Photoshop 2026。这一区 3 道。

### 没有并进同质组

- `ps-2-15-ps-brushes-presets`
  - 操作：Brushes and presets
  - 家族「画笔」，区分特征「无」。建议保留。
- `ps-2-15-ps-create-fill-patterns`
  - 操作：Create and fill with patterns
  - 家族「填充」，区分特征「无」。建议保留。
- `ps-2-15-ps-fill-objects-selections-layers`
  - 操作：Fill objects, selections, and layers
  - 家族「选区」，区分特征「无」。建议保留。

## ps-2-16

应用：Adobe Photoshop 2026。这一区 4 道。

### 没有并进同质组

- `ps-2-16-ps-draw-straight-line`
  - 操作：用绘图工具在打开的图像上画一条实色直线，然后保存并导出为图像文件
  - 家族「导出」，区分特征「无」。建议保留。
- `ps-2-16-ps-pen-filled-shape`
  - 操作：用钢笔工具绘制一个闭合的形状并以实色填充，然后保存并导出为图像文件
  - 家族「导出」，区分特征「填充」。建议保留。
- `ps-2-16-ps-shape-rectangle`
  - 操作：用矩形形状工具在打开的图像上画一个实色填充的矩形，然后保存并导出为图像文件
  - 家族「导出」，区分特征「填充」。建议保留。
- `ps-2-16-ps-shape-star`
  - 操作：用星形在打开的图像上画一个实色填充的星形，然后保存并导出为图像文件
  - 家族「导出」，区分特征「填充」。建议保留。

## ps-2-17

应用：Adobe Photoshop 2026。这一区 2 道。

### 没有并进同质组

- `ps-2-17-ps-text-font`
  - 操作：选择和应用字体
  - 家族「文字」，区分特征「无」。建议保留。
- `ps-2-17-ps-text-on-path`
  - 操作：在路径上添加文字
  - 家族「文字」，区分特征「文字」。建议保留。

## ps-2-18

应用：Adobe Photoshop 2026。这一区 5 道。

### 没有并进同质组

- `ps-2-18-blur`
  - 操作：应用 Blur 滤镜
  - 家族「滤镜」，区分特征「无」。建议保留。
- `ps-2-18-neural-filter`
  - 操作：应用 Neural filter
  - 家族「滤镜」，区分特征「无」。建议保留。
- `ps-2-18-quick-action`
  - 操作：使用 Quick action
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-18-sharpen`
  - 操作：应用 Sharpen 滤镜
  - 家族「滤镜」，区分特征「无」。建议保留。
- `ps-2-18-stylize`
  - 操作：应用 Stylize 滤镜
  - 家族「滤镜」，区分特征「无」。建议保留。

## ps-2-19

应用：Adobe Photoshop 2026。这一区 6 道。

### 没有并进同质组

- `ps-2-19-ps-drag-guide-from-ruler`
  - 操作：从标尺拖出参考线
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-19-ps-measure-and-scale`
  - 操作：Measure and scale（测量与缩放）
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-19-ps-new-guide-menu`
  - 操作：通过 View > Guides > New Guide 创建参考线并设置方向、颜色、位置
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-19-ps-shift-snap-guide`
  - 操作：按住 Shift 拖动参考线使其吸附到标尺刻度
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-19-ps-show-alignment-grid`
  - 操作：在图像上显示对齐网格（Alignment grids）
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-19-ps-show-rulers`
  - 操作：通过 View > Rulers 显示水平和垂直标尺
  - 家族「规则」，区分特征「无」。建议保留。

## ps-2-2

应用：Adobe Photoshop 2026。这一区 4 道。

### 没有并进同质组

- `ps-2-2-home-screen`
  - 操作：访问 Home screen
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-2-learn-tutorials`
  - 操作：打开 Learn 教程
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-2-recent-files-preference`
  - 操作：设置最近文件列表显示数量
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-2-workspace-components`
  - 操作：查看工作区组成部分
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-20

应用：Adobe Photoshop 2026。这一区 3 道。

### 没有并进同质组

- `ps-2-20-ps-video-create-animation-frames`
  - 操作：在当前文档中创建动画帧（Create animation frames）
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-20-ps-video-manage-video-groups`
  - 操作：组织和管理视频组（Organize and manage video groups）
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-20-ps-video-use-keyframes`
  - 操作：使用关键帧（Use keyframes）
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-21

应用：Adobe Photoshop 2026。这一区 4 道。

### 没有并进同质组

- `ps-2-21-ps-action-play-on-image`
  - 操作：播放一个已有动作：在 Actions 面板里选中动作，按 Play，把录好的步骤施加到当前打开的图像上，然后保存图像
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-21-ps-action-record-new`
  - 操作：录制一个新动作：用 Windows > Action 打开 Actions 面板，从面板菜单选 New Action，在 New Action 对话框里设置名称、所属动作集、功能键（Mac 例子为 Command+Shift+F3）和按钮模式的颜色，开始 Record，完成若干编辑步骤后按 Stop
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-21-ps-batch-process-files`
  - 操作：批处理（Process a batch of files 目录下点名的功能）：对一个文件夹里的多张图像执行同一处理
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-21-ps-create-droplet`
  - 操作：快捷批处理（目录点名的功能）：创建一个快捷批处理
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-22

应用：Adobe Photoshop 2026。这一区 2 道。

### 没有并进同质组

- `ps-2-22-ps-data-driven-create`
  - 操作：使用官方目录点名的 Create data-driven graphics 功能，在文档中创建数据驱动图形
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-22-ps-variable-dataset-import`
  - 操作：使用官方目录点名的从外部文件导入变量数据集功能
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-23

应用：Adobe Photoshop 2026。这一区 7 道。

### 没有并进同质组

- `ps-2-23-ps-print-basic`
  - 操作：打印：把当前文档送到打印输出
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-23-ps-print-color-managed`
  - 操作：色彩管理打印：以色彩管理方式打印文档
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-23-ps-print-duotone-inks`
  - 操作：双色调油墨：对文档使用双色调油墨功能
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-23-ps-print-hard-proof`
  - 操作：硬打样：输出文档的硬打样
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-23-ps-print-prep-commercial`
  - 操作：商业印刷准备：对一份打开的图像做提交商业印刷前的准备
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-23-ps-print-separations`
  - 操作：分色：对文档做分色处理
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-23-ps-print-soft-proof`
  - 操作：软打样：在屏幕上打样预览文档
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-24

应用：Adobe Photoshop 2026。这一区 4 道。

### 没有并进同质组

- `ps-2-24-ps-cloud-collab-edit`
  - 操作：云文档协作编辑
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-24-ps-projects`
  - 操作：Projects
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-24-ps-record-timelapse`
  - 操作：录制创作过程延时
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-24-ps-share-review`
  - 操作：分享审阅
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-25

应用：Adobe Photoshop 2026。这一区 4 道。

### 没有并进同质组

- `ps-2-25-ps-export-transparent-png`
  - 操作：使用 Export As 导出透明 PNG
  - 家族「导出」，区分特征「PNG、透明通道」。建议保留。
- `ps-2-25-ps-quick-export-png`
  - 操作：使用 Quick Export 快速导出
  - 家族「导出」，区分特征「无」。建议保留。
- `ps-2-25-ps-save-as-format`
  - 操作：使用 Save As 更改文件格式或位置
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-25-ps-save-copy`
  - 操作：使用 Save a Copy 另存副本
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-28

应用：Adobe Photoshop 2026。这一区 5 道。

### 没有并进同质组

- `ps-2-28-ps-ts-apple-silicon-limitations`
  - 操作：Photoshop for Apple Silicon limitations：核对当前环境是否受 Apple Silicon 限制影响
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-28-ps-ts-macos-crash-report`
  - 操作：macOS 上的崩溃报告：在 Photoshop 崩溃后定位并提供 macOS 崩溃报告
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-28-ps-ts-macos-format-open`
  - 操作：macOS 打不开受支持的格式：排查 Photoshop 在 macOS 上打不开受支持格式文件的问题
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-28-ps-ts-sample-spindump`
  - 操作：Sample Process 或 Spindump：为无响应的 Photoshop 采集 Sample Process 或 Spindump
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-28-ps-ts-script-errors`
  - 操作：脚本错误：排查 Photoshop 脚本运行时的报错
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-3

应用：Adobe Photoshop 2026。这一区 8 道。

### 没有并进同质组

- `ps-2-3-ps-content-credentials-social`
  - 操作：Content Credentials 的社交账号：关联社交账号
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-3-ps-info-panel-read`
  - 操作：Info 面板：打开并使用 Info 面板
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-3-ps-keyboard-shortcut-custom`
  - 操作：键盘快捷键：自定义快捷键
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-3-ps-performance-settings`
  - 操作：性能：调整性能相关设置
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-3-ps-prefs-adjust`
  - 操作：Adjust preferences：打开偏好设置并修改一项偏好
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-3-ps-prefs-backup-reset`
  - 操作：备份和重置偏好
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-3-ps-tool-pointer-style`
  - 操作：工具指针：更改工具指针显示方式
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-3-ps-ui-language-switch`
  - 操作：语言：切换界面语言
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-4

应用：Adobe Photoshop 2026。这一区 1 道。

### 没有并进同质组

- `ps-2-4-ps-ai-assistant-guided`
  - 操作：Work with AI Assistant：在 Photoshop 桌面版中使用 AI Assistant 的分步指导完成一次编辑
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-6

应用：Adobe Photoshop 2026。这一区 5 道。

### 没有并进同质组

- `ps-2-6-new-doc-custom`
  - 操作：用 File > New 新建文档并手动设置宽高、分辨率、颜色模式、背景，然后保存
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-6-new-doc-preset`
  - 操作：从新建对话框的预设分类（Photo、Print、Art & Illustration、Web、Mobile、Film & Video）选择预设建文档
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-6-open-file`
  - 操作：用 File > Open 打开给定的图像文件
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-6-open-pdf`
  - 操作：在 Photoshop 中打开一个 PDF 文件
  - 家族「其他」，区分特征「PDF」。建议保留。
- `ps-2-6-place-file`
  - 操作：把一个外部文件置入到当前打开的文档中（置入文件）
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-7

应用：Adobe Photoshop 2026。这一区 4 道。

### 没有并进同质组

- `ps-2-7-ps-adjustment-fill-layer`
  - 操作：添加调整图层或填充图层
  - 家族「填充」，区分特征「填充」。建议保留。
- `ps-2-7-ps-layer-comps`
  - 操作：创建图层复合
  - 家族「图层」，区分特征「无」。建议保留。
- `ps-2-7-ps-layer-effects`
  - 操作：给图层应用图层效果
  - 家族「图层」，区分特征「无」。建议保留。
- `ps-2-7-ps-smart-object`
  - 操作：把图层转为智能对象
  - 家族「图层」，区分特征「无」。建议保留。

## ps-2-8

应用：Adobe Photoshop 2026。这一区 7 道。

### 没有并进同质组

- `ps-2-8-artboard-add-to-doc`
  - 操作：给当前文档加画板（目录条目：给当前文档加画板）
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-8-artboard-new-doc`
  - 操作：新建画板文档（目录条目：新建画板文档、画板入门）
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-8-artboard-properties`
  - 操作：修改画板属性（目录条目：画板属性）
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-8-frame-from-shape-text`
  - 操作：把形状或文字转成画框（目录条目：把形状或文字转成画框）
  - 家族「文字」，区分特征「文字」。建议保留。
- `ps-2-8-frame-place-image`
  - 操作：把图像放进画框（目录条目：把图像放进画框、画框）
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-8-stroke-apply`
  - 操作：描边（目录条目：描边）
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-8-template-add-pattern`
  - 操作：给模板加图案（目录条目：给模板加图案）
  - 家族「其他」，区分特征「无」。建议保留。

## ps-2-9

应用：Adobe Photoshop 2026。这一区 4 道。

### 同质组 1：裁剪

- `ps-2-9-crop-drag-edges`
  - 操作：用 Crop tool 拖动裁剪框的边或角缩小画面，按 Enter / Return 或点 Done 确认，然后保存
  - 评分要点：保存后的图像文件宽高等于目标像素尺寸；保留下来的画面内容与参考结果像素一致
- `ps-2-9-crop-redraw-frame`
  - 操作：用 Crop tool 重新画一个裁剪框，只保留画面中指定的一块区域，确认后保存
  - 评分要点：保存后的图像只包含指定区域的内容，与参考区域像素一致；保存后的图像宽高与指定区域的尺寸一致
- 判重理由：同一区域。文件格式、旋转、非破坏这类区分都是「无」。都是「裁剪」，做法不同：ps-2-9-crop-drag-edges 用了拖动、边或角，ps-2-9-crop-redraw-frame 用了重新画。
- 建议保留：`ps-2-9-crop-redraw-frame`
- 建议先留在包里、不自动删除：`ps-2-9-crop-drag-edges`
- 规格自己写的区分：
  - `ps-2-9-crop-drag-edges`：这是材料里写明的第一种手势「拖边或角」，评分落点是确认裁剪后的最终尺寸；同组其他题分别考重画裁剪框、旋转裁剪框和非破坏裁剪的恢复，不是同一个动作换尺寸。
  - `ps-2-9-crop-redraw-frame`：材料把「重新画裁剪框」和「拖边或角」写成两种并列手势；本题的评分核的是留下的内容是画面中哪一块（位置正确），而不是像拖边题那样只核收窄后的尺寸。

### 没有并进同质组

- `ps-2-9-crop-nondestructive-restore`
  - 操作：取消勾选 Delete Cropped Pixels 做非破坏裁剪并保存，再重新选 Crop tool 把裁掉的像素调回来，保存第二份文件
  - 家族「裁剪」，区分特征「非破坏裁剪」。建议保留。
- `ps-2-9-crop-rotate-straighten`
  - 操作：把光标放在裁剪框角外旋转裁剪框，把倾斜的画面转正，确认后保存
  - 家族「裁剪」，区分特征「旋转或拉直」。建议保留。

同质组合计 11 个。被标成可合并的题 23 道，建议从中留下 11 道。
