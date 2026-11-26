# First50 Claude hybrid 轨迹分析

批次：`first50_round1_codex_hybrid_claude_20261106`

模型：`claude-opus-5-5`

分析日期：2026\-11\-09

前端：http://10\.210\.9\.14:22337/runs/first50\_round1\_codex\_hybrid\_claude\_20261106

点数：[评测汇总表格](https://sensetime.feishu.cn/wiki/VhStwjN8QiED2zkoViDcOw7JnVW?sheet=kcRByB)

全50题结果表：[评测汇总表格](https://sensetime.feishu.cn/wiki/VhStwjN8QiED2zkoViDcOw7JnVW?sheet=i1QGSN)

## 实验配置

## 统计结果

claude opus 5\.5模型成功率是**33/36（91\.67%）**

**50题：33个成功（1分）、3个失败（0分）、14个未获得有效评分（null）。** 

## **3个0分的case：bad case分析**

### 【**L4 任务输入＋L1 模型判断**】powerpoint\-r001\-26：页脚重叠，模型发现后未处理

**原因与层级：L4 任务输入＋L1 模型判断。** 输入文稿存在兼容性和布局问题；模型已发现页脚与正文重叠，但选择保留。最终页脚虽然写入并保存，却不满足“无遮挡”的要求。\*\*证据：\*\*第7–13步打开文稿时触发修复；第17步模型明确指出重叠；第31、38步应用页脚并保存；第42步最终回复说明原文本框异常，并明确没有修改。[查看轨迹](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/powerpoint-r001-26?attempt=attempt-001)。

### **【L3模型请求通道故障】numbers\-chart：导出表头错位，修正前被502中断**

**直接终止原因与层级：L3 模型请求通道故障。** Numbers导出XLSX时额外加入表标题，使表头从A1移到A2。模型已发现问题并准备修正，但后续请求连续502、重试耗尽，留下的文件未满足表格位置要求。\*\*证据：\*\*第35步保存并导出；第37步读出A1为`input`、数据区为A2:C10；第39–40步明确计划关闭表标题并重新导出；第41步开始修正，之后请求日志显示502重试至8/8。图表标题和数据检查均通过，失败项是表格位置。**502究竟来自上游服务还是桥接实现，尚未确认。**[查看轨迹](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/numbers-chart?attempt=attempt-001)。

### 【**L3 模型请求通道故障；前期卡点：****L2 文件面板输入与背景拖放限制。** 】jiangying\-pip\-101：面板与拖放受阻，最终被502中断

**直接终止原因：L3 模型请求通道故障；前期卡点：L2 文件面板输入与背景拖放限制。** 模型经过多次恢复尝试，尚未完成目标草稿就因502重试耗尽停止。\*\*证据：\*\*第18、21、24步出现面板输入拒绝、多窗口歧义和`AttachmentUnverified`；第26步激活剪映后，第28、30步仍被拒绝；第40、42步拖放返回`no_drop`；第50步改用Quartz辅助脚本，随后模型请求失败。评估只发现默认名称“11月6日”的草稿，未找到要求的`JY_画中画`，因此判0。**502的底层根因仍未确认。**[查看轨迹](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-pip-101?attempt=attempt-001)。

## **14个nul的case：评估链路问题**

评估管线要修的部分

### **\[L4\] Judge输出无法解析或引用无效：4题**

**原因：** 两题Judge返回的JSON格式错误，另两题引用了未通过校验的证据ID，导致评分没有完成。这不是已确认的业务失败；代码检查通过，也不能替代完整评估。

**示例：****`wps-outline-101`****。** 第98步检查保存文件中的公式，第99步提交完成说明；代码检查全部通过，但`grading/score.json`记录`JSONDecodeError: line 1 column 278`，最终为null。[查看轨迹](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/wps-outline-101?attempt=attempt-001)。

### **\[L4；部分关联L1\] 评分所需证据不足，或原始证据未被综合评估充分使用：7题**

**原因：** 部分任务缺少最终参数、完整网站展示或指定操作过程的证据；另有案例原轨迹包含相关信息，但Judge综合意见仍称缺少支持，存在摘要丢失证据的可能。需要逐题区分，不能统一认定为模型没有完成。

**示例：****`chrome-churches-033`****。** 第30步实际返回4个教堂官网的活动名称和重复日程，第31步说明计数口径，第40步写入SQL，第46步重载核对结果。但Judge综合意见称缺少支持计数的上游日程与推导信息，判为证据不足。应回查这些原步骤；计数口径是否正确仍需复核，不能直接改判成功。[查看轨迹](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/chrome-churches-033?attempt=attempt-001)。

### **\[L3；关联L4输出声明\] 严格产物收集失败，未进入评分：1题**

**原因：** 输出路径被收集器判为`symlink_forbidden`，使必需产物不完整。明确故障在收集阶段；是否由macOS的`/tmp`路径别名触发，尚需复现，不能认定是模型创建了软链接。

**示例：****`excel-r001-26`****。** 第47步保存，第49–50步读取文件核验排序，第51步提交完成说明。随后`outputs/outputs.json`将声明路径`/tmp/家庭食品库存.xlsx`对应的输出标为invalid，错误为`symlink_forbidden`，因此未评分。[查看轨迹](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-r001-26?attempt=attempt-001)。

### **\[L3\] Agent停止未确认，阻止评分：1题**

**原因：** Agent已有最终回复，但监督程序没有确认Agent停止，触发`control.stop_unconfirmed`。停止检查为何失败尚未查明，不能将此等同于模型没有完成操作。

**示例：****`numbers-formula`****。** 第66步重开文件并读取公式和值，第67步关闭文档，第69步提交最终结果。随后`result.json`在`controller_stop`阶段记录停止未确认，任务标为`supervisor_error`，评分为`not_run/null`。[查看轨迹](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/numbers-formula?attempt=attempt-001)。

### **\[L3；L5根因待查\] 评估阶段客体响应不可用：1题**

**原因：** 评估执行未取得有效客体响应，返回`guest.response_unavailable`。现有日志不能进一步确定是客体进程、连接还是响应通道问题，也没有据此判定产物错误。

**示例：****`preview-packet`****。** 第81步检查输出PDF页数和文本，第88步查看对照图，后续有完成回复。但`grading/score.json`记录`TaskPhaseError / guest.response_unavailable`，最终为null。[查看轨迹](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/preview-packet?attempt=attempt-001)。

## 其他未造成直接失败的问题

### 【L1】模型层：结构化任务和错误恢复较强，工具使用与最终检查仍需改进

造任务可以参考的部分

**强项一：能够完成有****明确结构和计算规则****的任务，并****检查****保存后的文件。** 本批15个Excel任务中14题通过，另1题因收集失败未评分；5个Word任务全部通过。这支持Claude在本批办公任务中的表现，但不能直接推广到所有Office任务。例如，`excel-pivot`不仅创建透视表，还在第65步检查透视表和缓存结构，第69–72步重开确认没有修复提示；`word-table`第109步直接确认原生表格、重复表头和文字内容，而不是只看文件是否存在。[Excel证据：第65、69–72步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-pivot?attempt=attempt-001)；[Word证据：第109步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/word-table?attempt=attempt-001)。

**强项二：能够****根据返回结果修改方案****，而不只是重复原动作。** `excel-validation`第41步遇到失效AX引用，第42步重新观察，第43步使用新状态继续操作，最终通过。`numbers-formula`则通过系统进程的窗口信息发现隐藏权限提示，第47步拒绝通讯录访问后恢复应用。这两类行为适合用来训练“观察错误—定位原因—选择下一步”的能力。[Excel证据：第41–43步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-validation?attempt=attempt-001)；[Numbers证据：第45–48步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/numbers-formula?attempt=attempt-001)。

**弱项一：会****猜工具参数****，也会在状态变化后继续****使用旧索引****。** 4/50题出现`Unsupported click options`，其中2题最终通过。22/50题出现`StaleElement`，其中12题最终通过；但这22题不能全部归因模型，仍需区分旧索引复用和观察后的状态变化。例如，`wps-numfmt-101`第22步尝试带`modifiers:["shift"]`的点击，第100步又遇到不支持的右键参数；任务最终完成，但增加了试错。[证据：第22–23、100–101步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/wps-numfmt-101?attempt=attempt-001)。

不支持点击参数的case：

|任务|前端步骤|
|---|---|
|[excel\-r001\-26](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-r001-26?attempt=attempt-001)|14|
|[powerpoint\-r001\-13](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/powerpoint-r001-13?attempt=attempt-001)|30|
|[wps\-absref\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/wps-absref-101?attempt=attempt-001)|25|
|[wps\-numfmt\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/wps-numfmt-101?attempt=attempt-001)|22、100|

**弱项二：****结果检查****偏重文件结构，对****视觉效果和指定操作过程****的检查不够一致。** 文件中有文字、有公式，不一定证明显示正确，也不一定证明用了要求的方法。前述PPT页脚属于视觉问题；`wps-absref-101`第26–27步采用区域选中后批量输入，不能据此证明执行了“先填B2，再向右、向下填充”的指定过程。这里不宜把所有证据不足都归为模型问题，但模型确实需要更明确地区分“结果正确”和“过程符合要求”。[证据：第25–27步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/wps-absref-101?attempt=attempt-001)。

**作为teacher模型，建议重点构造以下任务，而不是直接复制整条长轨迹：**

- **结构化数据处理任务****。** 围绕查找、聚合、数据验证、透视表、文档表格等生成变体，改变数据、字段和边界情况。要求使用真实公式、原生表格或透视表，并用独立程序检查结果。重点蒸馏Claude的数据理解、应用操作和保存后核验能力。

- **有明确原因、可恢复的错误任务。** 从已打开菜单、附属保存面板、失效AX引用等状态开始，训练模型先重新观察，再选有效动作。保留“错误返回—新观察—恢复操作—成功验证”的短片段，剔除无必要的重复尝试。

- **原生文件与导出文件一致性任务。** 例如Numbers导出多一行标题、日期被转换、公式导出后变化。要求发现差异、修正并再次检查，利用Claude能读取文件结构、解释应用行为的能力。

- **结果与过程分别验收的任务。** 一组允许Hybrid自由完成，另一组明确要求原生功能或指定操作。两组分别筛选数据，避免把脚本生成结果的轨迹用于训练“必须通过GUI完成”的能力。

- **给成功任务补充反例。** 如公式值正确但公式被写死、文字存在但重叠、文件保存了但路径错误。让teacher指出具体不满足项并修复，训练学生模型避免仅凭“文件存在”或“工具返回成功”结束任务。

蒸馏样本应保留必要观察、动作、简短判断依据和验证结果。**原评1也需检查任务方法与产物；null不能直接作为成功样本；失败轨迹只选取经核验的恢复片段。** 不应把Claude的无效参数尝试、环境绕行和主观完成声明原样当成标准答案。

### 【L2】CUA Driver层：AX引用、面板焦点和背景输入是主要问题

driver要修的部分

**1\. ****AX引用失效：22/50题****，其中12题最终通过。** 这是出现最多的明确错误，但不等于22个Driver缺陷。`excel-validation`第41步在一次调用里连续点击两个索引，随后报`StaleElement`；重新观察后可以继续。应让观察结果和动作明确关联同一窗口、同一快照，状态变化后提示模型刷新引用，减少依赖位置索引的连续操作。[证据：第41–43步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-validation?attempt=attempt-001)。

|任务|前端步骤|
|---|---|
|[excel\-bubble](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-bubble?attempt=attempt-001)|58|
|[excel\-lookup](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-lookup?attempt=attempt-001)|45、82|
|[excel\-r001\-26](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-r001-26?attempt=attempt-001)|10|
|[excel\-r002\-15](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-r002-15?attempt=attempt-001)|9、14、15|
|[excel\-validation](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-validation?attempt=attempt-001)|41|
|[excel\-window](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-window?attempt=attempt-001)|23、25、41|
|[jiangying\-audio\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-audio-101?attempt=attempt-001)|25|
|[jiangying\-speed\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-speed-101?attempt=attempt-001)|15、29|
|[jiangying\-text\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-text-101?attempt=attempt-001)|9、32|
|[jiangying\-transition\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-transition-101?attempt=attempt-001)|28|
|[powerpoint\-r001\-26](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/powerpoint-r001-26?attempt=attempt-001)|20|
|[powerpoint\-r002\-5](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/powerpoint-r002-5?attempt=attempt-001)|19|
|[preview\-packet](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/preview-packet?attempt=attempt-001)|32、48|
|[word\-illustrated](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/word-illustrated?attempt=attempt-001)|71|
|[word\-outline](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/word-outline?attempt=attempt-001)|32、43|
|[word\-revision](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/word-revision?attempt=attempt-001)|21、41|
|[word\-table](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/word-table?attempt=attempt-001)|24、34、40、47、54、88、96|
|[wps\-absref\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/wps-absref-101?attempt=attempt-001)|60|
|[wps\-goalseek\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/wps-goalseek-101?attempt=attempt-001)|8、26、40|
|[wps\-numfmt\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/wps-numfmt-101?attempt=attempt-001)|46、72、78|
|[wps\-outline\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/wps-outline-101?attempt=attempt-001)|9|
|[wps\-subtotal\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/wps-subtotal-101?attempt=attempt-001)|84|

**2\. ****焦点或附属面板输入被拒绝：20/50题****，其中13题最终通过。** 这说明它不只出现在失败任务，也增加了成功任务的恢复步骤。例如，`excel-air`第34步在保存面板输入文件名时返回`AttachmentUnverified: another surface blocks the target`，第35步仍能观察到“存储”sheet，模型随后继续处理并最终保存。需要具体区分父窗口、附属面板、遮挡窗口和真实焦点，而不是只返回笼统的激活失败。[证据：第34–36步及后续保存](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-air?attempt=attempt-001)。

|任务|前端步骤|
|---|---|
|[chrome\-landmarks\-1134](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/chrome-landmarks-1134?attempt=attempt-001)|36、40、53、65、69、76|
|[excel\-air](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-air?attempt=attempt-001)|34|
|[excel\-bond](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-bond?attempt=attempt-001)|43、46、49、52、53、59、63、68|
|[excel\-clean](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-clean?attempt=attempt-001)|47|
|[excel\-lookup](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-lookup?attempt=attempt-001)|44、49、51、57、61、68、75、80、83、94|
|[excel\-percentiles](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-percentiles?attempt=attempt-001)|52|
|[excel\-pivot](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-pivot?attempt=attempt-001)|59|
|[excel\-validation](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-validation?attempt=attempt-001)|58|
|[excel\-window](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-window?attempt=attempt-001)|36、40|
|[jiangying\-audio\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-audio-101?attempt=attempt-001)|21、24|
|[jiangying\-pip\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-pip-101?attempt=attempt-001)|18、21、24、28、30|
|[jiangying\-speed\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-speed-101?attempt=attempt-001)|23|
|[jiangying\-text\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-text-101?attempt=attempt-001)|27|
|[jiangying\-transition\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-transition-101?attempt=attempt-001)|24、27|
|[powerpoint\-r002\-5](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/powerpoint-r002-5?attempt=attempt-001)|38|
|[preview\-packet](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/preview-packet?attempt=attempt-001)|60|
|[word\-outline](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/word-outline?attempt=attempt-001)|50、54|
|[word\-pages](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/word-pages?attempt=attempt-001)|78、81、85|
|[word\-revision](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/word-revision?attempt=attempt-001)|45、53、57、62、67|
|[word\-table](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/word-table?attempt=attempt-001)|69、72、74、77、89|

**3\. ****背景拖放限制：6/50题****，包含全部5个剪映任务和Preview。** 其中5题Agent最终正常结束，后续为null；不能把这些null都归因拖放，但模型为继续操作编写了额外脚本。例如，`jiangying-audio-101`第40、48步拖放失败，第52步改用Quartz辅助输入，后来完成草稿并返回首页。Driver应提供明确、可用的前台拖放入口，而不是让每个模型自己探索系统输入方案。[证据：第40、48、52步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-audio-101?attempt=attempt-001)。

|任务|前端步骤|
|---|---|
|[jiangying\-audio\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-audio-101?attempt=attempt-001)|40、48|
|[jiangying\-pip\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-pip-101?attempt=attempt-001)|40、42|
|[jiangying\-speed\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-speed-101?attempt=attempt-001)|36、42|
|[jiangying\-text\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-text-101?attempt=attempt-001)|41、53|
|[jiangying\-transition\-101](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-transition-101?attempt=attempt-001)|40、49、59|
|[preview\-packet](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/preview-packet?attempt=attempt-001)|40、42|

**4\. ****部分应用不接受后台坐标点击****：至少确认1题。** `powerpoint-r001-13`改用LibreOffice后，第29步返回`pointer_reading_toolkit`，明确说明该工具包忽略后台鼠标事件；第30步尝试前台参数又被拒绝，之后通过第32步翻页快捷键和第35步菜单操作完成任务。这里不是坐标点得不准，而是该输入方式不被应用支持。Driver应在操作前明确暴露这种限制及支持的替代方法。[证据：第29–35步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/powerpoint-r001-13?attempt=attempt-001)。

### 【L3】Harness层：部分请求错误能够恢复，但记录不足以解释耗时

**12/50题记录过模型请求错误，其中10题最终completed，2题中断。** 本节关注这10题：错误没有直接终止任务，但会增加等待时间，因此不能把任务耗时全部归为模型推理或GUI操作慢。例如，`word-table`记录过请求错误，但最终第109步完成文件结构检查，第111–113步关闭并提交，原评分为1。[操作完成证据：第109–113步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/word-table?attempt=attempt-001)。请求错误本身见原生请求日志，不对应一个GUI步骤。

**用量记录也有缺失：2,072次请求中，219次没有usage，另1次只有部分usage。** 这没有直接造成业务失败，但影响成本和效率比较。需要分别记录模型响应时间、失败等待、重试时间和工具执行时间；缺失usage应保持未知，不能按零计算，也不能仅用总耗时评价模型速度。

### 【L4】任务层

#### PowerPoint：输入文稿在目标应用中不能稳定打开

**至少2题出现打开后要求修复。** `powerpoint-r001-13`修复后丢失幻灯片文字，模型转用LibreOffice完成；`powerpoint-r001-26`也触发修复，且正文布局异常，与新增页脚重叠。前者虽然得1分，也不能直接视为PowerPoint操作能力验证通过。

**建议：** 冻结任务前，在PowerPoint中实际打开输入文件，确认不要求修复、文字完整、布局正常；同时明确是否允许其他应用完成。

**证据：** [powerpoint\-r001\-13，第20、23–25、43步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/powerpoint-r001-13?attempt=attempt-001)；[powerpoint\-r001\-26，第7–17、42步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/powerpoint-r001-26?attempt=attempt-001)。

#### Numbers：原生表格与导出文件的坐标要求需要明确

`numbers-chart`在Numbers中的表格和图表已经建立，但导出XLSX时，表标题`input`占据A1，导致表头移到A2。`numbers-formula`也遇到同类情况，随后通过关闭表标题修正。**这不直接证明评估器错误，而是任务需要明确：A1要求针对原生文件、导出文件，还是两者。**

**建议：** 分别定义原生文件和导出文件的验收要求，并验证Numbers默认导出行为不会引入题面未说明的差异。

**证据：** [numbers\-chart，第35、37、39–40步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/numbers-chart?attempt=attempt-001)；[numbers\-formula，第69步交付说明](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/numbers-formula?attempt=attempt-001)。

#### WPS：Hybrid允许脚本，但部分题仍要求指定操作过程

`wps-absref-101`的公式、数值和格式全部通过，但任务要求先在B2输入，再向右、向下填充。模型实际采用区域选中后批量输入，不能证明满足指定过程。**结果要求和操作方法要求同时存在，容易让模型误把“结果正确”当成全部完成。**

**建议：** 每题明确区分“必须得到的结果”和“必须执行的方法”。保留方法要求时，应在题面显著说明Hybrid也不能替代该步骤，并保留可验证的过程证据。

**证据：** [wps\-absref\-101，第25–27、90–92步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/wps-absref-101?attempt=attempt-001)。

#### 剪映：最终回首页与编辑参数验收需要配套设计

音量和变速任务要求完成后回首页，但首页无法展示音量、各片段速度等参数。`jiangying-audio-101`中，Judge认可中途出现过−6dB，却因最终编辑状态没有再次展示而无法确认；`jiangying-speed-101`也缺少首末段最终速度的直接证据。

**建议：** 任务明确要求“完成编辑→展示关键参数→返回首页”；评估按这个顺序使用证据。全程未导出、未登录等要求，应检查完整操作记录，不能仅靠最终首页截图判断。

**证据：** [jiangying\-audio\-101，第99、101、122–124步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-audio-101?attempt=attempt-001)；[jiangying\-speed\-101，第88–89、106步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-speed-101?attempt=attempt-001)。

#### Chrome：计数口径和网站展示要求需要更具体

`chrome-churches-033`中的“weekly services”存在解释空间：是每周重复的活动条目数，还是一周实际举行次数；Church Tour等活动是否算service，也需要明确。地图类任务则同时要求导出数据正确和网站上标签、弹窗正确，单靠GeoJSON不能证明后者。

**建议：** 计数任务明确计数单位与排除项；地图任务明确标签/弹窗需要展示哪些字段，并允许通过逐项观察或网站DOM验证，不要求所有标记同时出现在一张截图中。

**证据：** [chrome\-churches\-033，第30–31步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/chrome-churches-033?attempt=attempt-001)；[chrome\-landmarks\-1134，第81–83步及评分记录](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/chrome-landmarks-1134?attempt=attempt-001)。

### 【L5】镜像与环境层：隐藏权限提示和多版本工具增加排查成本

环境/镜像要看的部分

**1\. 隐藏的系统权限提示：明确确认1题。** `numbers-formula`第45步通过System Events读到UserNotificationCenter中的通讯录权限请求，第47步点击Don’t Allow后Numbers恢复。模型之前的应用级观察没有直接呈现该提示。应在冷克隆验收时覆盖首次启动权限状态，并让观察工具能够发现跨进程阻塞窗口；不需要为此提前允许无关的通讯录权限。该提示已经恢复，没有证据证明它造成了后续停止确认失败。[证据：第45–48步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/numbers-formula?attempt=attempt-001)。

**2\. ****PATH中的CLI与配置后端版本不同：明确确认1处****。** `jiangying-pip-101`第47步执行`cua-driver --help`，显示0\.25\.0，而本批配置使用的REPL后端为0\.38。这个差异没有被证明直接导致失败，也不能据此认定实际操作后端是0\.25；但模型自行查帮助时可能得到另一版本的接口说明。应记录活动后端的路径、版本和hash，并明确区分它与PATH中的CLI。[证据：第47步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/jiangying-pip-101?attempt=attempt-001)。



