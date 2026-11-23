# 独立研究工具

这些工具从源码仓库中按需运行，**不属于 `truncator` 的自动生成流程，也不进入它的 wheel 安装包**。依赖方向是研究脚本读取核心模块和运行产物；核心不导入 `research`。

|目录或脚本|做什么|怎样使用|
|---|---|---|
|`production_evidence/`|商业图树比较、来源登记、可选现实依据审核|`python -m research.production_evidence --help`|
|`controls/`|读取和核验历史四状态对照，必要时单独导出|只供历史实验脚本调用；不恢复已退休的四状态生成入口|
|`foreground/`|前景测量基准、截图编码分析与核验|`python -m research.foreground.evaluate_foreground --help`|
|`validation/`|真实工程构建矩阵、采集与算子条件验证|`python -m research.validation.validate_build_matrix --help`|
|`viewport/`|窗口变化、首次宽度缓存、视口恢复等专项实验|先查看脚本；多数绑定本机历史材料与设备状态|
|`ux_agent/`|外部检测器调用、交互与结果汇总|独立运行；调用前核对模型配置、费用和实验输入|

在仓库根目录执行模块命令；只安装 `harmony-truncator` 时不会安装这些研究模块。

目录按实验目的组织。同一UX-Agent专项使用的Python与MJS传输脚本放在一起；研究脚本定位仓库根目录和读取profile的路径已同步更新。`fixtures/`保留研究工具的离线输入。这些脚本仍有实际复核用途，本轮没有因它们不在普通campaign调用链中就删除。

函数层面的研究残留也已分离：`controls/replay.py`保存历史动作记录的复核；`controls/dataset.py`自行选择四份状态并组织实验清单，调用核心`export_capture()`复用普通采集也需要的审核、哈希和复制规则。核心导出不接收四状态专用采集列表。

## 商业依据实验

人工先选择商业原图树、目标 selector（定位条件）和待比较的注入目标。工具提取边界关系并计算差异；研究者结合截图解释含义。

```powershell
python -m research.production_evidence inspect-target --tree <原树> --screenshot <原图> --selector <选择器.json> --out <研究目录/目标.json>
python -m research.production_evidence compare-targets --reference <商业目标.json> --injected <注入目标.json> --out <研究目录/对比.json>
python -m research.production_evidence case-template --capture <采集目录> --out <研究目录/依据草稿.json>
python -m research.production_evidence case-review --capture <采集目录> --review <填写后的依据.json> --out <研究目录/核验后的依据.json>
```

尖括号是需要替换的路径。新命令明确指定 `--out`，把研究记录写到独立目录。`production_evidence.json` 是历史来源登记，不决定算子能否执行。`mechanism-control`、`production-supported`、`unresolved` 是这里可选的研究分类，核心计划、报告、导出与样本质量审核均不要求它们。

历史脚本 API `record_case_review` / `export_case_review` 保留供既有证据复核；普通 `truncator export` 不再调用。商业依据的充分程度与生成样本的内容损失、恢复结果分开解释。

## 通用统计仍属于核心

```powershell
python -m truncator dataset-audit --exports <导出A> <导出B> --out <统计目录/audit.json>
python -m truncator dataset-audit --exports <导出A> --targets <配额.json> --candidates <剩余计划目录> --out <统计目录/补充建议.json>
```

通用统计服务于批量构造的交付，保留在 `truncator/review/datasets/`。它核对绑定的质量审核，按组件、机制、方向、内容标签统计；相同目标状态去重，矛盾审核单列。核心 `export` 继续自动产生 `balance.json`，也可用 `dataset-audit` 汇总多个导出。统计不要求商业依据等级，不执行四状态专用核验。

组合包生成时的算子平衡、页面预算、补丁冲突检查仍由核心 `planning/composition.py` 完成；这与生成结束后的跨批次统计是两个阶段。

## 版本与保留内容

拆分前完整版本保存在 `archive/production-evidence-20261123`（提交 `229a99c`）；更早四状态生成入口保存在 `archive/four-state-20261122`。历史图树、HAP、报告及原始比较结果保留，不按新版流程重新解释旧结果。
