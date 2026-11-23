# Harmony Truncator

面向UX-Agent显示截断检测的鸿蒙ArkUI源码构造工具。修改真实工程源码，构建HAP，按配置路径采集原生PNG与UI树，保存计划、差异、观察和审核证据。普通截断、可滚动恢复和只裁留白可以共同进入自由组合包。

学习项目请读[完整源码与实验零基础详解](完整源码与实验零基础详解.md)：第2.10节串起当前调用链，第4—13章讲源码与算子，第14—19章讲组合和执行，第22、24、25章保留商业例子、实际运行和UX-Agent评测。仅维护Markdown，图片在docs/images下，无需PDF。

汇报与设计讨论请读[架构与实证汇报](项目汇报_架构与实证.md)，含4张不同粒度的流程图；[19种算子附录](汇报附录_19种算子图树与代码.md)提供逐项截图、关键UI树和源码例子。最新修复及回归见[滚动问题修复记录](docs/verification/scroll-fix.md)。

## 当前主线

2026-11-23当前结构（包含前一轮重构）：

- 核心负责构造、执行、质量检查、审核重建、导出与通用统计。商业依据和历史四状态专用处理移至[research](research/README.md)，不进入安装包；核心不导入它们。拆分前版本保存在archive/production-evidence-20261123。

- 生成入口收敛为combined；单修改包也使用同一流程，设max_total=1。四状态生成与运行保存在[历史分支](https://github.com/SEKIROYUSHI/harmony-truncator/tree/archive/four-state-20261122)，本地实验原件保留。
- campaign默认在副本插桩、验证正常构建；失败后记录原因并回退原工程。已有基线或已插桩profile沿用其身份。
- 一个目标的Baseline与前景统计供多种算子复用。源码数值解析独立于binding，父祖先绑定共用ID优先、类型唯一的规则。
- 常见静态Extend按组件类型、文件作用域及相对导入展开，记录margin、clip、layoutWeight等有效属性和依赖摘要。
- 算子策略连接各自的自动选参、几何参数、稳定布局和源码模板，preserve_slot由支持它的策略调用公用包装。
- 每个组合包只构建一次，再采多条路径；依赖临时网络失败有界重试，损坏计划按包隔离。滚动目标可自动补最多2次滑动证据；内容已覆盖或没有继续前进时提前停止。

本轮验证数据、构建条件、已知测量失败见[重构验证记录](docs/verification/refactor-verification.md)。UX-Agent本身未修改；历史模型评测仍见[实测报告](docs/experiments/实测报告.md)，本轮构建回归不计作新一轮模型评测。

## 安装与配置

需要Python 3.10以上、Pillow、json5，以及本机DevEco Studio的Node、SDK、ohpm、hvigor和hdc。

```powershell
python -m pip install -e .
python -m truncator --help
python -m truncator init-profile --source <应用源码目录> --studio <DevEco目录> --out <profile.json>
```

尖括号内容要替换成实际路径。profile明确记录源码、产品/模块、工具链、启动包名、HAP输出和必要工程适配。已有profiles/apps包含本机五款开源工程的配置；换机器需修改路径。无法在当前SDK直接构建的旧工程，需要先完成正常工程适配。

recipe描述到页操作和检查点。例如启动后点“我”，再确认页面出现“亚瑟王”：

```json
{
  "settle_seconds": 6,
  "actions": [{"equals": "我", "wait": 3}],
  "checks": [{"equals": "亚瑟王"}]
}
```

动作执行时根据当前UI树重新定位坐标。recipe由研究者按目标页面配置；程序不会自行发现所有业务路径。

## 生成组合包

```json
{
  "applications": [{
    "profile": "profiles/apps/my-app.json",
    "max_total": 6,
    "max_per_page": 3,
    "max_area_ratio": 0.3,
    "seed": 17,
    "pages": [
      {"name": "home", "recipe": "profiles/recipes/my-app/home.json"},
      {"name": "detail", "recipe": "profiles/recipes/my-app/detail.json"}
    ]
  }]
}
```

```powershell
python -m truncator campaign --spec campaign.json --runs <新运行目录> --device <hdc目标>
python -m truncator report --runs <运行目录>
```

上面的例子把`campaign.json`放在仓库根目录。任务中的`profile`、`recipe`、`baseline_run`相对路径以任务JSON所在目录为起点；放入`profiles/campaigns/`后应改用`../apps/...`、`../recipes/...`。参见[配置索引](profiles/README.md)。

默认候选为12项：height-clip、width-clip、line-clip、ellipsis-width、ellipsis-lines、parent-clip、fixed-parent-clip、translate-clip、ancestor-translate-clip、child-overflow-clip、scroll-recovery、whitespace-clip。

可在应用或页面显式写`operators`列表（或单数`operator`，不能同时写）。页面设置会整体替换应用层选择。可用`file`限定源码路径片段。候选数量不等于最终修改数量；规划拒绝不适用写法，组合阶段再检查源码区间、页面影响和预算，并兼顾组件和机制分布。

operators.json中的default_campaign、default_reason是默认池的统一调整位置。freeze-viewport-width、cache-viewport-width需要窗口变化；window-edge-clip与viewport-width-mismatch涉及更大的关联布局，这四项保留显式入口。三种遮挡历史实现不属于当前截断任务。

应用级可选项：

|选项|默认|作用|
|---|---|---|
|instrument|true|自动插桩；false时使用原工程|
|baseline_run|未提供|明确复用指定基线及其源码身份|
|verify_recovery|true|对入选的scroll-recovery目标补有界滑动证据|
|seed|0|同样输入下复查随机选择|

应用级选项放在`applications`中的应用项。把`verify_recovery`、`instrument`、预算、`seed`、`profile`或`baseline_run`等放入`pages`的某一页，会在执行前明确报错；页面覆盖只用于实际按页面读取的路径、源码筛选、算子选择、密度等字段。

源码、配置或默认策略变更时使用新运行目录。对未改变的配置重跑同一命令会复用已有准备、构建与有效采集。回退来源固定记录在source-choice.json；不会在续跑时悄悄换回另一套源码。

## 看结果与审核

|文件|用途|
|---|---|
|results.json、review-queue.json|应用、页面、包与采集状态|
|source-choice.json、effective-profile.json|本轮使用原工程还是插桩工程及原因|
|catalog.json、pages/*/bindings.json|源码发现和图树绑定|
|selection.json、plans/*.json|候选拒绝、平衡选择、参数与补丁|
|mutations/*/mutation.diff|最终源码差异|
|mutations/*/build.json|实际HAP摘要与构建记录|
|capture-*/snapshot.png及前后树|真实运行证据；以capture记录中的文件名为准|
|capture-*/scroll-recovery.json|滚动动作、后续采集、相对位移及内容核验|
|report/index.html|离线报告与逐目标位置|

滑动证据、截图测量和几何观察都用于帮助审核；样本的内容损失和恢复结果分别记录；商业依据另做独立研究。动态商品消失或换位时记录问题，当前没有自动重规划重建闭环。

审核及按组筛除使用annotate、record-review、curate等命令，具体参数见`--help`和详解第19章。移除一个修改组会连同其关联补丁一起去掉。export导出已审核证据与应用，并生成balance.json；dataset-audit汇总分布、去重及审核冲突。需要商业比较时另运行`python -m research.production_evidence`。

## 多批次汇总与重建历史

`truncator/`是程序代码包；各批次数据分别放在自己的运行目录。核心统计可以同时读取多个批次：

```powershell
python -m truncator run-summary --runs <批次A> <批次B> --out <运行汇总.json>
python -m truncator dataset-audit --exports <导出A> <导出B> --out <最终数据统计.json>
python -m truncator dataset-audit --exports <导出A> <导出B> --revisions all --out <全部历史统计.json>
```

run-summary统计执行尝试，包括失败和未开始的应用、配置页面、包构建及已有审核决定。dataset-audit统计已审核交付，默认沿明确重建关系选最新版本；独立批次保留，重复目标状态去重，存在多条末端分支时单列提示。页面覆盖的分母是配置路径，不推测整个App的未知页面。

curate的重建计划保存祖先计划与HAP摘要，`curation-history/`保存逐轮审核者、理由、删除决定及内容摘要，并随导出携带。保留修改的参数不重抽，新包重新采集和审核。最终删掉所有修改时，保留包版本记录，缺陷目标数为0。详细过程见讲解第19.8、25.4节。

## 代码阅读顺序

|职责|文件|
|---|---|
|配置预检、自动源工程准备、批量编排|campaign_policy.py、campaign_source.py、campaign.py|
|源码扫描与共享样式|scan.cjs、scan-styles.cjs及实例键辅助模块|
|源码值与运行节点|source_attributes.py、binding.py、baseline.py|
|测量与自动选参|visual.py、parameter_policy.py、calibration.py|
|算子实现|operator_strategies.py、operator_selection.py、operator_geometry.py、operator_renderers.py|
|公用文本编辑与具体补丁|source_edits.py、operators.py、mutations.py|
|几何计划、组合选择|planning.py、composition.py|
|工程、构建、设备与恢复|project.py、build.py、workflow.py、runtime.py、recovery.py|
|审核与数据交付|review_evidence.py、review_policy.py、curation.py、dataset.py及delivery.py|

低层scan、bind、geometry-plan、prepare等命令保留用于检查与复现；普通任务直接使用campaign。研究脚本、测试和本机artifacts不进入Python安装包。

## 验证

```powershell
python -m unittest discover -s tests -t . -q
python research/foreground/evaluate_foreground.py --out <新测量目录> --font <字体文件>
python research/validation/validate_build_matrix.py --profiles profiles/apps/ohbill.json profiles/apps/healthy_life.json profiles/apps/multishopping.json profiles/apps/wechat_harmonyos.json --out <新构建目录>
```

SDK相关测试需要本机有效profile，设备验证使用保留的鸿蒙模拟器。前景基准的真值来自独立文字掩膜；普通平色和圆角例子效果较好，装饰图形混入文字区域时会误测，完整分组结果保留在验证记录。

Git仓库保存源码、测试、配置、说明和正文图片；本机原始实验、构建目录、凭据与缓存不上传。历史完整实现位于archive/four-state-20261122分支。

## 业务代码目录（2026-11-22整理）

根包仅保留初始化与命令行入口，不设置旧模块路径的转发层。

```text
truncator/
  __main__.py    命令行入口
  source/        SDK扫描、插桩、源码属性、节点绑定、工程准备
  planning/      基线、自动选参、几何计划、组合选择与页面预算
  mutation/      算子策略、源码模板、补丁与执行能力表
  execution/     campaign、构建、设备采集、路径回放、滑动与筛除重建
  imaging/       几何与像素测量、内容身份和覆盖
  review/        离线观察、样本质量审核、报告、导出与通用统计
  common/        存储、锁、基础校验与采集文件约定
```

例如测量入口现在是`truncator.imaging.visual.foreground`，源码扫描是`truncator.source.project.scan`。包内统一使用完整导入路径，测试、研究脚本、SDK资源和安装配置一并迁移。review的离线读取不依赖启动设备，原架构测试仍检查这一点。模块按职责分组，不引入新插件或继承层。

[profiles逐文件索引](profiles/README.md)解释应用构建、页面recipe、批量campaign三类JSON的实际用途。

支持目录也按用途分类：

```text
profiles/       apps/、recipes/<应用>/、campaigns/
tests/          source/、planning/、mutation/、execution/、review/等职责测试
research/       production_evidence/、controls/、foreground/、viewport/、ux_agent/等专项
docs/           verification/、experiments/、真实前景材料和图片
```

[测试说明](tests/README.md)、[研究工具](research/README.md)、[文档入口](docs/README.md)分别说明调用方式和依赖。运行与导出产物继续按批次、应用/组合包、页面采集组织，保留计划ID、审核历史和版本关系；它们不写回profiles。

### 选择性增加第三层（2026-11-23）

只有职责成组且文件较多的部分再聚合：

```text
execution/
  campaign.py、campaign_source.py、workflow.py、build.py、curation.py
  device/       设备会话、到页动作、截图采集、恢复手势及实现指纹
review/
  review_evidence.py、review_policy.py等样本质量审核与证据规则
  reporting/    HTML报告、页面资源、审核界面和review.js
  datasets/     数据导出、应用交付、分布统计、去重与审核一致性
```

source、planning、mutation、imaging、common保持原层次。新子包表示可以一同阅读的业务职责；不创建“一文件一目录”的包装。旧导入不保留转发层，核心构造命令保持，profiles按应用配置、页面路径和批量任务分类。商业比较改用research中的独立入口，通用统计保留在核心。安装配置、采集指纹里的文件路径、测试mock和研究脚本同步迁移。

新页面验证见[前景留出报告](docs/foreground-holdout/README.md)。
