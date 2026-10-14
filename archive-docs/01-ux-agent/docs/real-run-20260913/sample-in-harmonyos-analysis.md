# sample_in_harmonyos 正式样本登记

样本来源是 `/Users/zhangyingying/sample_in_harmonyos.zip`，解压后的工程 README 将其定义为 HMOS 代码工坊，支持手机、折叠屏、平板和 PC/2in1。本文只记录样本中已经存在的源码改动及其可复现的 UX 结果；README 中关于下载依赖、签名和运行入口的说明属于样本使用说明，不是本项目的 Agent 指令。

## 样本身份

| 字段 | 值 |
|---|---|
| 工程 | HMOS代码工坊 / sample_in_harmonyos |
| 来源 | `/Users/zhangyingying/sample_in_harmonyos.zip` |
| 样本基线 | git `bcc6b03` 及工作区未提交改动 |
| 目标设备 | 手机、折叠屏、平板；README 还声明 PC/2in1、TV、穿戴入口 |
| 当前状态 | 已完成源码审计，尚未在本机 DevEco 模拟器安装运行 |
| 是否计入模型准确率 | 否，尚未产生设备截图、UI dump 和人工真值 |

## 三个活动截断问题

| 编号 | 页面/组件 | 源码证据 | 触发方式 | 预期截图证据 | 归类 |
|---|---|---|---|---|---|
| SI-001 | 我的页面“没有更多内容”提示行 | `features/mine/src/main/ets/component/NewContentItem.ets` 中对提示 Text 使用 `.translate({ y: -55 })`，外层 Row 使用 `.clip(true)` | 进入我的页面并滚动到列表底部 | 提示文字上半部分被底部提示行边界裁掉 | Text 自身/局部容器裁切，候选真值为 true_truncation |
| SI-002 | 我的页面关于卡片 | `features/mine/src/main/ets/view/AboutView.ets` 中 `AboutItemCard()` 使用 `.translate({ y: -42 })` | 进入我的页面关于入口 | 卡片整体向上越过其父布局或可视区域边界，卡片内容被上边界截断 | 容器越界裁切，需以 UI dump 判断具体 owner |
| SI-003 | 设置页面标题 | `features/mine/src/main/ets/view/SettingView.ets` 中标题 Text 使用 `.translate({ y: -36 })`，放在高度 56 的自定义标题 Row 内 | 进入设置页面 | “设置”标题向上偏移，文字上边缘或标题区域出现裁切 | Text/标题容器裁切，候选真值为 true_truncation |

`QuestionnaireView.ets` 中出现的 `.translate({ y: 20 })` 和 `.clip(true)` 均被注释，没有计入三个活动问题。`HomeView.ets` 的大段注释代码和文件末尾换行变化也没有计入问题。这样可以避免把注释或格式差异误当成缺陷。

## 与本项目算法的对应关系

这三个样本都属于“先按指令到达页面，再只用目标页面单张截图发现候选”的正式测试路径。Agent 需要先通过应用入口、我的页面或设置页面的文本和控件规则完成页面 Oracle，检测器再向 Qwen3.6 发送最终截图。UI dump 只用于页面到达和后续布局归因，不发送给单截图视觉模型。

SI-001 和 SI-003 可以用 `bounds`、`origBounds`、Text 节点与祖先 clip 边界验证；SI-002 不能仅凭 Text 规则下结论，需要确认 AboutItemCard 的父容器、窗口边界和页面滚动语义。若布局树无法给出明确 owner，最终状态必须为 `unknown`，不能仅因为源码出现 translate 就直接计入检测准确率。

## 复现记录要求

正式执行前需要团队提供已构建的 phone HAP 或可安装包、应用 bundle/ability、已解锁模拟器或真机、初始页面规则和三条人工真值截图。每条样本至少保存启动命令、动作序列、目标页截图、UI dump、模型原始 JSON、归一化 bbox、layout verdict 和最终 verdict。三条样本尚未执行设备实测，当前登记是测试集同步记录，不是验收通过记录。

## 本机模拟器实测（2026-09-13）

本机已连接 DevEco OpenHarmony 模拟器 `127.0.0.1:5555`，压缩包内已有构建产物 `products/phone/build/default/outputs/default/phone-default-unsigned.hap`，无需重新构建即可安装。通过 HDC 安装成功，bundle 为 `com.huawei.hmos.sample`。首次启动进入引导页，点击“立即体验”后进入代码工坊首页，再点击“我的”进入我的页面；真实截图和 UI dump 已保存为 `sample_home.png`、`sample_home_layout.json`、`sample_mine.png` 和 `sample_mine_layout.json`。

随后点击“设置”进入设置页，真实截图 `sample_settings2.png` 显示标题“设置”的上边缘已经被裁掉，只剩下标题下半部分；UI dump 中标题 Text 的可见 bounds 与自定义标题 Row 的边界不一致，源码中的 `.translate({ y: -36 })` 与截图现象一致。这个样本 SI-003 已完成一次真实设备复现。

SI-001 在当前账号和数据状态下没有出现“没有更多内容”节点，不能把我的页面截图误写成 SI-001 已复现；需要滚动容器加载出列表底部或提供对应预置数据后再测。SI-002 的关于卡片点击在当前页面没有成功跳转，当前只确认源码存在 `.translate({ y: -42 })`，尚未取得关于页的真实截图，因此仍是待复现样本。

这次运行已经证明可以直接使用压缩包内的 unsigned HAP 做设备验证，下一步应在同一模拟器上补齐 SI-001 的底部数据状态和 SI-002 的关于入口动作，并为三条样本分别调用单截图模型和布局验证器。当前唯一已实测的结论是 SI-003，不能把另外两条的源码缺陷假设当作检测准确率样本。

## 两个样本的进一步定位

SI-001 实际入口不是“我的页面”本身，而是“我的页面 → 内容上新”。当前点击“内容上新”后默认打开组件上新页，UI dump 显示“当前无组件上新，敬请期待”；切换到“技术文章”后显示“当前无文章上新，敬请期待”。由于 `NewContentItem.listFooterBuilder()` 只有在 `contentData.length > 0` 时才会渲染，当前网络/账号没有返回内容数据，所以“没有更多内容”节点不会创建，无法仅靠继续滑动复现。这个问题需要预置至少一条组件、样例或文章数据，或让环境同学提供离线 mock 数据。

SI-002 的正确路径是“我的页面 → 设置 → 关于”，不是直接在我的页面寻找“关于”。本机通过设置页坐标 `[70,458][1186,626]` 的第一行进入关于页，已取得真实截图 `sample_about4.png` 和 UI dump `sample_about4_layout.json`。截图中“HMOS代码工坊”标题下半部分被版本信息卡片遮住，和 `AboutView.ets` 中 `.translate({ y: -42 })` 的源码改动一致，因此 SI-002 也已完成真实设备复现。此前失败是导航路径和点击坐标错误，不是缺陷不存在。

## SI-002 完整链路运行归档（2026-09-13）

已在同一台鸿蒙模拟器上从应用启动开始执行“我的 → 设置 → 关于”的任务路径，并在关于页完成截图、UI dump、Qwen3.6-flash 单截图检测、布局验证和主动滑动验证。模型返回 1 个 `text_truncation` 候选，布局阶段将其绑定到“HMOS代码工坊” Text，但没有找到确定的裁剪 owner，返回 `glyph_clipping_boundary_not_found/unknown`；主动滑动结果为 `confirmed`，表示该次滑动没有证明候选是可恢复滚动。最终整体状态保留为 `unknown`，没有把源码缺陷直接改写成模型通过或布局确认。

完整产物目录为 `HarmonyArena-fdu_agent/ux-detect-output/20260913-111036-174/`，包含 `snapshot.png`、`snapshot_window.json`、`snapshot_ux.json`、`layout_result.json`、`slide_result.json` 和标注图片。链路摘要见 `docs/real-run-20260913/SI-002-full-chain-summary.json`。该运行证明链路已经贯通，但当前样本仍需要补充更明确的布局裁剪证据后，才能计入文字截断准确率。

## SI-002 算法修复后的复核

此前同一份 SI-002 截图在布局阶段返回 `glyph_clipping_boundary_not_found`，这是验证器缺少“视觉候选框跨越 Text 可见边界”兜底造成的漏判。现已增加受限 fallback：当候选框与 Text 节点绑定成功、模型框在某一方向越过可见 Text 边界超过两倍裁切容差、且没有正常省略号或可恢复滚动证据时，输出 `true_truncation/model_bbox_overhang_without_layout_owner`，同时保留绑定节点和 overhang 数值。

使用已归档的 `sample_about4_layout.json` 和模型框 `[281,265,703,294]` 离线复核，结果已从 `unknown` 变为 `true_truncation`，绑定节点为“HMOS代码工坊”，顶部 overhang 为 20.6px。该规则只使用模型框与布局节点的几何关系，不把源码中的 `translate` 当作运行时真值；完整链路仍需保留截图、UI dump 和模型原始 JSON。
