# SenseNova Flash 284B Vision v16 step400 DPO v2 模板模式失败原因分析

## 1. 分析范围与结论

本报告分析以下一次模板模式跑批：

```text
/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839
```

核心结论：这次失败主要发生在“模板任务编排和工具执行阶段”，不是页面 HTML 已生成后再渲染失败，也不是评分阶段失败。47 个 case 中有 12 个未形成有效页面产物，且这 12 个 case 的 `html_pages` 全部为 0。

其中最直接的模型响应异常是：模型把内部 DSML 工具调用协议直接作为普通文本输出，导致后续工具没有被执行；同时，多数失败 case 在生成任务包、信息包、大纲或资产清单时反复遇到路径、JSON、脚本语法和模板槽位问题，最终没有进入页面生成阶段。

## 2. 总体量化结果

跟踪文件：

- [batch_summary.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/batch_summary.json)
- [events.jsonl](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/events.jsonl)


| 指标 | 数量 | 占 47 个 case 的比例 | 说明 |
|---|---:|---:|---|
| 总 case | 47 | 100% | `batch_summary.json.case_total` |
| 真正完成且有页面 | 35 | 74.5% | `terminal_class=done`，且 `html_pages>0` |
| `render_suspect` | 11 | 23.4% | 实际均为 `html_pages=0`，没有进入有效页面交付 |
| `done_no_html` | 1 | 2.1% | agent 状态为完成，但没有任何页面 |
| 未产出有效页面 | 12 | 25.5% | 11 个 `render_suspect` 加 1 个 `done_no_html` |
| `case_ok` | 36 | 76.6% | 该字段把 1 个 `done_no_html` 也算作 ok，不能直接当作页面交付成功率 |

失败 case 的耗时合计约 7.32 小时，平均约 36.6 分钟，中位数约 24.4 分钟，最长为 `seq_1157` 的约 2.51 小时。失败耗时主要消耗在重复修复和工具调用，而不是 HTML 生成或渲染。

## 3. 失败 case 明细

下表中的“证据”均来自对应 case 的 `main.json`；事件状态来自 run 目录下的 `events.jsonl` 和 `batch_summary.json`。

| case | 终态 | 耗时 | 页面数 | 主要失败位置 | 具体证据 |
|---|---|---:|---:|---|---|
| `prod_603992e9` | `render_suspect` | 26.1 分钟 | 0 | 工具路径与准备阶段 | `main.json` 中出现 `Unsupported path prefix`，最后停在“切片结果与大…” |
| `prod_912af214` | `render_suspect` | 38.4 分钟 | 0 | 信息包和准备阶段 | `info_pack.json` 校验报 `invalid JSON`；随后仍停在大纲确认前 |
| `prod_adda7bc8` | `render_suspect` | 69.3 分钟 | 0 | 信息包、资产清单 | 多次 `JSONDecodeError`；`slice_stage5_inputs` 报 `missing file .../asset_map.json` |
| `prod_fb0f04fb` | `done_no_html` | 13.2 分钟 | 0 | 内容子任务后停止 | 最后只有“子任务确认…”，没有大纲、切片或页面生成步骤 |
| `seq_0674` | `render_suspect` | 1.2 分钟 | 0 | 准备阶段 | 出现错误路径格式，最后停在“任务约束文件校验通过” |
| `seq_1157` | `render_suspect` | 150.8 分钟 | 0 | 大纲生成脚本反复修复 | 多次 `SyntaxError`、`AssertionError`、`IndexError`、`NameError`，最终脚本仍不能稳定执行 |
| `seq_1293` | `render_suspect` | 26.1 分钟 | 0 | 工具调用协议 | 最后一条 assistant 内容是字面量 `<｜DSML｜tool_calls>...`，不是实际工具调用 |
| `seq_1559` | `render_suspect` | 13.4 分钟 | 0 | 输入图表素材与 OCR | 日志明确说环境没有 OCR，图表数值无法可靠读取，随后停止 |
| `seq_1585` | `render_suspect` | 66.5 分钟 | 0 | 信息包和大纲重建 | 多次 `JSONDecodeError`，后续又出现 `KeyError`，最后停在模板映射修复 |
| `seq_1690` | `render_suspect` | 3.3 分钟 | 0 | 模板准入后停止 | `preflight` 路径先错，修正后只到“启动模板编排与大纲生成” |
| `seq_1784` | `render_suspect` | 22.8 分钟 | 0 | 切片完成后未生成页面 | 最后停在“切片完成，10 页就绪。现在派发页面生成阶段” |
| `seq_2016` | `render_suspect` | 7.9 分钟 | 0 | 非法 JSON 与协议输出 | 连续 `JSONDecodeError`，最后输出字面量 DSML `execute_code` 调用 |

## 4. 主要失败类型及数量

以下统计允许一个 case 同时命中多个问题，因此不能把各行相加后当作 12 个互斥类别。

### 4.1 所有失败都没有进入有效页面交付：12/12

证据来自 [batch_summary.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/batch_summary.json) 的 `results[*].deck_quality.html_pages`：

- 11 个 `render_suspect` 的 `html_pages=0`；
- 1 个 `done_no_html` 的 `html_pages=0`；
- `events.jsonl` 中这 12 个 case 都只有 `case_done`，没有对应的页面交付成功事件；
- 失败 case 的 `main.json` 没有页面生成完成回执。

因此，本次 `render_suspect` 不能理解为“页面已经生成但视觉渲染不好”。更准确的含义是：流程在页面生成之前或页面生成任务没有真正执行。

### 4.2 工具调用协议或响应形态异常：至少 2/12

明确命中的 case 是：

- `seq_1293`
- `seq_2016`

两者的 `main.json` 都包含 assistant 普通文本中的：

```text
<｜DSML｜tool_calls>
<｜DSML｜invoke name="...">
```

这说明模型没有通过结构化 `tool_calls` 字段调用工具，而是把工具协议文本直接输出到 response 中。对于执行框架来说，这只是普通文本，不能触发 `create_subtask` 或 `execute_code`，所以流程会停在原地。

这类问题是最直接的“response 不正常”。它不是业务内容质量问题，而是协议层输出问题。

### 4.3 JSON 或结构化中间产物反复失败：至少 5/12

明确命中的 case 是：

- `prod_912af214`：`info_pack.json` 报 `invalid JSON`；
- `prod_adda7bc8`：多次 `JSONDecodeError`；
- `seq_1157`：大纲构造脚本和断言反复失败；
- `seq_1585`：多次 `JSONDecodeError`，之后出现 `KeyError`；
- `seq_2016`：连续多次 `JSONDecodeError`。

这些失败不是一次性校验失败后立即退出，而是模型尝试通过字符串替换、局部代码补丁和重新写入来修复。由于输入文件本身已经包含嵌套引号、控制字符、字段结构或脚本语法问题，修复过程又产生了新的错误，导致大量时间消耗在中间产物自救上。

### 4.4 路径或脚本入口使用错误：至少 6/12

明确命中的 case 是：

- `prod_603992e9`
- `prod_912af214`
- `prod_fb0f04fb`
- `seq_0674`
- `seq_1293`
- `seq_1559`
- `seq_1690`

其中有几类重复错误：

- 把普通绝对路径传给要求 `local://...` 的文件工具，触发 `Unsupported path prefix`；
- 把 `preflight.py` 错误地当成 `ppt-maker/scripts/preflight.py`，实际脚本位于模板模式目录；
- 把 `slice_stage5_inputs.py` 错误地放在 `ppt-maker/scripts/` 下；
- 在环境不存在时尝试进入 `/mnt/data/result` 或读取通配路径。

这类问题说明模型没有稳定遵守当前环境的工具路径约束，且没有先通过一次可靠的路径确认建立后续工作流。

### 4.5 大纲、模板槽位和脚本修复失控：至少 3/12

最典型的是 `seq_1157`，其 `main.json` 中可以看到连续的：

- `SyntaxError: invalid syntax`
- `SyntaxError: unmatched ')'`
- 模板表格槽位断言失败
- `AssertionError`
- `IndexError`
- `NameError`
- 字符串匹配补丁找不到目标

`seq_1585` 也出现模板映射页码类型不一致导致的 `KeyError`。`prod_adda7bc8` 则在资产清单缺失后继续尝试修复，最后还出现对 `/mnt/make_asset.py` 的 `Permission denied`。

这些 case 的共同点是：模型把“生成 PPT”转化成了“不断修复自己生成的脚本”，但没有及时回退到最小合法产物，也没有在前置产物失败时停止并返回明确失败原因。

### 4.6 输入素材能力缺口：至少 2/12

明确命中的 case 是：

- `seq_1559`：需要从上传的调查结果 deck 中提取图表数据，但日志说明当前环境没有 OCR；
- `seq_1157`：输入医学材料的图片或图表处理与大纲脚本修复相互叠加，最终仍没有进入页面阶段。

这里要区分“模型响应问题”和“环境能力缺失”：如果输入关键数据只存在于图片，而运行环境没有可用 OCR 或图像读取能力，模型即使响应格式正常，也无法可靠完成数据型 PPT。

## 5. 为什么成功 case 不能证明失败原因只是偶发工具错误

成功 case 也会出现一些路径错误、JSON 修复和 DSML 字样，但它们后来继续完成了页面生成。例如成功 case 的最后通常有：

```text
<ppt_task_finished>
<status>success</status>
</ppt_task_finished>
```

因此需要用“是否有 HTML 页面”和“最后是否有完成回执”作为最终判定，而不能只统计某个错误字符串是否出现。

本次失败 case 与成功 case 的关键差异是：

| 对比项 | 成功 case | 失败 case |
|---|---:|---:|
| `terminal_class=done` | 35 | 0 |
| `html_pages>0` | 35 | 0 |
| 页面生成完成回执 | 有 | 无 |
| 是否停在准备、大纲、资产或切片阶段 | 少数短暂出现，之后恢复 | 12/12 最终停在这些阶段或协议异常 |
| 是否形成可评分的页面产物 | 是 | 否 |

## 6. 模型response不正常


### 直接的协议异常

`seq_1293` 和 `seq_2016` 把 DSML 工具调用写进了普通 assistant 文本。这是明确的结构化响应协议失败，直接阻断后续工具执行。

### 更广泛的流程响应异常

另外 10 个失败 case 不一定都出现 DSML 字面量，但它们表现出：

- 工具路径格式反复写错；
- 文件和脚本入口没有先确认就直接调用；
- 生成非法 JSON 后继续局部字符串修补；
- 大纲脚本报错后持续修改自生成脚本；
- 资产清单缺失时没有按降级规则快速生成合法空清单；
- 已经没有足够上下文完成页面阶段时仍继续在中间产物上循环。

这属于长链路任务控制能力不稳定，而不仅是单次 response 格式错误。

## 7. 失败主因排序

按对页面交付的直接影响，建议排序如下：

1. **前置编排链路过长且可被中间产物错误卡死**：覆盖至少 10/12 个失败 case 的证据。
2. **JSON、脚本语法和模板槽位修复反复失败**：至少 5/12 个失败 case 明确出现。
3. **工具路径和脚本入口不稳定**：至少 7/12 个失败 case 明确出现。
4. **结构化工具调用退化为普通文本 DSML**：至少 2/12 个失败 case 明确出现，但属于最严重的协议级问题。
5. **输入图表缺少 OCR 或素材读取能力**：至少 2/12 个失败 case受到影响。

这里的“至少”是因为多个问题经常叠加在同一个 case 中；统计采用保守口径，只统计从 `main.json` 或失败工具结果中可以直接确认的证据。



## 文件清单

### Run

- [batch_summary.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/batch_summary.json)
- [events.jsonl](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/events.jsonl)
- [_effective_config.yaml](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/_effective_config.yaml)

### 失败case

- [prod_603992e9/main.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/prod_603992e9/main.json)
- [prod_912af214/main.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/prod_912af214/main.json)
- [prod_adda7bc8/main.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/prod_adda7bc8/main.json)
- [prod_fb0f04fb/main.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/prod_fb0f04fb/main.json)
- [seq_0674/main.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/seq_0674/main.json)
- [seq_1157/main.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/seq_1157/main.json)
- [seq_1293/main.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/seq_1293/main.json)
- [seq_1559/main.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/seq_1559/main.json)
- [seq_1585/main.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/seq_1585/main.json)
- [seq_1690/main.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/seq_1690/main.json)
- [seq_1784/main.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/seq_1784/main.json)
- [seq_2016/main.json](/home/gui-5d025-2/zyy/xhx_agent_v3/output/testset_v2_sensenova-flash-284b-vision-v16-20260908-sft-step400-dpo-v2_tpl_20260917_224839/seq_2016/main.json)
