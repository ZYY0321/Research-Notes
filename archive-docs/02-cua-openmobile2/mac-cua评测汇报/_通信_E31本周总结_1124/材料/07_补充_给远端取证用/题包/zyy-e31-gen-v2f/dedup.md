# 同一区域里操作本质相同的题

只标注，不删除。下面每道题的文件都还在这个题包里。

来源只读：`/Users/zhangyingying/CUA/评测集建设/maccua-tasks/zyy-e31-gen-v1`
本目录：`/Users/zhangyingying/CUA/评测集建设/maccua-tasks/zyy-e31-gen-v2f`
生成时间：2026-11-24 01:44:05

判重只在同一个 `region_id` 里面做。先看操作原文：去掉括号里的调研注，再去掉句尾用来交文件的「并导出 PNG」。文件格式、旋转拉直、非破坏、斜杠导出这些不一样就不并。然后满足下面任意一条就标成同质：题号关键词一边包含另一边（例如 `pencil-sketch` 和 `figma-pencil-sketch`）；都是同一类操作、只是手势不同（拖边和重画裁剪框）；去掉括注后二字重合度达到 0.80；或者一句几乎包含另一句，多出来的只是「多个」「在画布上」。设置里的不同面板不会并在一起。屏蔽和取消屏蔽这种相反操作也不会并。

建议保留的那一道，取同组里操作原文最短的；一样短就取题号字典序靠前的。规格里的 distinct_because 原样附在后面，用来人工推翻。

这一版里没有两道题被判成同一操作。

## 统计

| 项 | 数 |
|---|---|
| 题数 | 31 |
| 前缀已换 | 31 |
| 前缀本来就是 v2 | 0 |
| 前缀对不上、没改 | 0 |
| Mail 题 | 6 |
| Mail 清理已加 | 6 |

## figma-1

应用：Figma。这一区 5 道。

### 没有并进同质组

- `figma-1-figma-create-first-file-export`
  - 操作：新建第一个设计文件，并从该文件导出一张 PNG 到指定路径（对应新手课第 3 课「建第一个设计文件」；地图行写明「新建后导出的图可评分」）
  - 家族「导出」，区分特征「PNG」。建议保留。
- `figma-1-figma-navigate-in-file`
  - 操作：在已打开的设计文件内导航（对应新手课第 5 课「在文件里导航」）
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-1-figma-tour-explore`
  - 操作：按 Tour the interface 下的 Explore 子分区进行界面探索浏览
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-1-figma-tour-file-browser`
  - 操作：打开 Figma 桌面应用并浏览文件浏览器（对应新手课第 2 课「先看文件浏览器」）
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-1-figma-tour-file-utilities`
  - 操作：按 Tour the interface 下的 File utilities 子分区查看文件相关的实用功能区域
  - 家族「其他」，区分特征「无」。建议保留。

## figma-3

应用：Figma。这一区 1 道。

### 没有并进同质组

- `figma-3-figma-draw-probe`
  - 操作：在 Figma 中探查 Figma Draw 分组对应的功能入口（官方分组 3 Figma Draw，专页正文未核到，只做到达与观察，不预设具体绘制步骤）
  - 家族「其他」，区分特征「无」。建议保留。

## figma-4

应用：Figma。这一区 7 道。

### 没有并进同质组

- `figma-4-component-slots`
  - 操作：创建和使用 slots
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-4-create-component-2`
  - 操作：创建组件
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-4-create-style`
  - 操作：创建和使用样式
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-4-create-variable`
  - 操作：创建和使用变量
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-4-create-variant`
  - 操作：创建变体
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-4-interactive-component-variant`
  - 操作：创建交互式组件
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-4-share-library`
  - 操作：创建和分享库
  - 家族「其他」，区分特征「无」。建议保留。

## figma-8

应用：Figma。这一区 5 道。

### 没有并进同质组

- `figma-8-add-comment`
  - 操作：在 Figma Design 文件中添加评论（Comments）
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-8-create-branch`
  - 操作：为设计文件创建分支（Branching）
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-8-local-copy-collab-limit`
  - 操作：为带评论的文件保存本地副本，核对协作数据不随副本落地
  - 家族「其他」，区分特征「无」。建议保留。
- `figma-8-merge-branch`
  - 操作：将分支合并回主文件（merging）
  - 家族「其他」，区分特征「合并图层」。建议保留。
- `figma-8-multiplayer-invite`
  - 操作：使用多人协作工具（Multiplayer tools）邀请他人进入同一文件共同编辑
  - 家族「其他」，区分特征「无」。建议保留。

## mail-2-4

应用：Mail。这一区 6 道。

### 没有并进同质组

- `mail-2-4-mail-bcc-draft`
  - 操作：在新邮件里显示 Bcc 栏并用密送收件人保存草稿
  - 家族「草稿」，区分特征「无」。建议保留。
- `mail-2-4-mail-forward-save-draft`
  - 操作：转发一封已收到的邮件给指定收件人并存草稿
  - 家族「草稿」，区分特征「无」。建议保留。
- `mail-2-4-mail-group-expand-recipients`
  - 操作：用通讯录列表名作为收件人并用 Expand Group 展开成员地址后存草稿
  - 家族「草稿」，区分特征「无」。建议保留。
- `mail-2-4-mail-plain-text-compose`
  - 操作：把一封正在写的邮件用 Format > Make Plain Text 转为纯文本后存草稿
  - 家族「文字」，区分特征「文字」。建议保留。
- `mail-2-4-mail-reply-save-draft`
  - 操作：对一封已收到的邮件点回复并把回复存为草稿
  - 家族「草稿」，区分特征「无」。建议保留。
- `mail-2-4-mail-windows-friendly-attachment`
  - 操作：附加文件时勾选 Send Windows-Friendly Attachments 并存草稿
  - 家族「草稿」，区分特征「无」。建议保留。

## ps-2-23

应用：Adobe Photoshop 2026。这一区 7 道。

### 没有并进同质组

- `ps-2-23-ps-print-basic-2`
  - 操作：打印
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-23-ps-print-color-managed-2`
  - 操作：色彩管理打印
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-23-ps-print-commercial-prep`
  - 操作：商业印刷准备
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-23-ps-print-duotone`
  - 操作：双色调油墨
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-23-ps-print-hard-proof-2`
  - 操作：硬打样
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-23-ps-print-separations-2`
  - 操作：分色
  - 家族「其他」，区分特征「无」。建议保留。
- `ps-2-23-ps-print-soft-proof-2`
  - 操作：软打样
  - 家族「其他」，区分特征「无」。建议保留。

同质组合计 0 个。被标成可合并的题 0 道，建议从中留下 0 道。
