# First50 Deepseek 纯gui 轨迹分析

批次：first50\_round1\_codex\_gui\_deepseek\_20261110
模型：deepseek\-v4\.1\-flash\-1017（响应模型 deepseek\-v4\-1\-flash\-261017）
分析日期：2026\-11\-12
前端：[批次页面](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110)
全50题结果表：Markdown / CSV
逐类问题的全部任务及步骤：证据索引

已核对50题最新attempt的结果、评分、前端步骤文本、原始请求和工具时间戳，并检查关键冻结评估代码、归档文件和最终截图；未逐帧观看全部录像，未重跑Agent或Judge，未修改原分。下文均使用开发机前端编号。已实际打开Keynote第80、350步验证深链接定位，其余链接按同一前端API的任务、attempt和步骤核对。4题采用attempt\-002，其余attempt\-001；旧准备attempt不混入结果。

## 实验配置

|**配置项**|**本次实验配置**|
|---|---|
|实验批次|first50\_round1\_codex\_gui\_deepseek\_20261110|
|任务集|First50，50个任务、11个应用|
|执行模式|GUI：指令禁止脚本替代任务操作；允许浏览器GUI，禁止DOM、页面JS等绕过界面的操作。工具并未据此全部禁用|
|被测模型|deepseek\-v4\.1\-flash\-1017/huoshan/huoshan；响应模型deepseek\-v4\-1\-flash\-261017|
|推理配置|**本批reasoning\_effort=medium**；不是high。后续批次应按最新要求设为high|
|评估模型|gpt\-6\-astra/azure/sfa；结合代码检查、任务rubric与GUI路线判定|
|执行环境|mac3宿主机上的macOS VM，镜像personal\-b7b357737d42495c838fbc0bc8cf34f1；4 CPU、8192 MiB|
|Agent与GUI工具|Codex CLI 0\.153\.4，CUA REPL，LocalDriver 0\.38\.0|
|并发数|1|
|单任务时限|Agent执行最多3600秒，不含初始化、评估和清理|
|框架版本|冻结源码12085ebe，另含本批评估适配补丁；与DeepSeek Hybrid比较的548个代码文件一致|

这是历史配置核查，不代表已替本批修改推理档位或禁用工具。浏览器已集成到CUA，调用CUA的JavaScript包装本身不等于执行页面JS，需看具体操作。

## 1\. 统计结果

**原业务评分为21个1、22个0、7个null；有效评分成功率21/43=48\.84%，全样本已确认业务通过21/50=42%。** 21个业务1分中，GUI路线10个fail、10个unknown、仅1个pass；因此不能称21题“纯GUI通过”。严格GUI成功为1个true、36个false、13个null。

**本批最主要的三类问题：** 13题因429重试耗尽而Agent异常，其中11题零分；附属窗口/输入焦点相关错误覆盖41题；模型在受阻后长期探索接口、改用脚本及反复恢复，任务收敛和纯GUI约束遵守不足。429与Driver拒绝不能归成模型不会操作，但模型误删时间线、覆盖源单元格、发现布局问题后未修复，仍是明确的能力改进方向。

|指标|结果|
|---|---|
|Agent状态|26 completed、13 agent\_error、11 timeout|
|22个0分的状态|11 agent\_error（全部429）、9 timeout、2 completed|
|13个429中断的评分|11个0、1个1（excel\-window）、1个null（chrome\-gpu）|
|原GUI路线|20 fail、26 unknown、2 pass、2缺失；pass为wps\-goalseek与excel\-bubble，后者业务0分|
|首题开始至末题结束|北京时间11月10日14:36:44至11月12日07:18:11，40小时41分27秒，包含暂停、续跑及初始化/评估等阶段|
|Agent累计执行时间|82,834\.1秒，约23小时00分34秒；不是纯模型推理计算时间|
|模型请求 / 完整响应|5,934 / 5,912；22个未完成请求的usage未知，不补零|
|工具调用|5,907：CUA REPL 5,481、exec\_command 373、REPL reset 37、view\_image 13、write\_stdin 3|
|输入token / 缓存读取|500,001,721 / 493,669,760（98\.73%）|
|缓存写入token|完整响应记录均为0；只描述归档字段|
|输出token / 其中推理token|1,572,749 / 909,060；推理包含在输出内，不重复相加|
|模型输入图片|逐题去重合计1,646张；引用176,240次，不是录像帧数|

统一使用原始完成响应usage。excel\-lookup、excel\-pivot、powerpoint\-r001\-19的session汇总与原生逐响应汇总存在差异，未混用。50个最新attempt均已终结；批末verify包含54个attempt，50个valid、4个旧准备attempt的evidence\_index\_mismatch，故整体valid=false，不能写成归档全部验收通过。

DeepSeek Hybrid原业务评分32/38=84\.21%、全样本32/50=64%；本批GUI下降，但本批有13题429、两批null集合不同，且GUI路线大多未确认通过。**不能把差值直接解释为模型从Hybrid切到纯GUI后的净能力下降。**

## 2\. 22个0分case：bad case分析

### 【L4 题面与验收口径；L1 结构核验不足】数据正确但缺少原生Table：excel\-r002\-15

归档output\.xlsx的A1:C6表头和五条记录正确，但没有xl/tables。冻结评估要求该范围存在原生Table，因此判0。第204步Quick Look能读出正确内容，第206步宣布完成，却没有验证Table结构。题面只说“整理成Excel表”，并未明确“Excel原生Table对象”；普通单元格区域和Table不是同一结构，复制粘贴数据本身没有错。应先澄清任务要求，不能单凭当前评分把“没建Table”全归为模型能力不足；若明确要求Table，粘贴后还需插入表格、确认范围和表头并保存。 **证据：** [excel\-r002\-15 第204步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-r002-15?attempt=attempt-001&step=204)、[excel\-r002\-15 第206步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-r002-15?attempt=attempt-001&step=206)。

### 【L1 最终视觉核验；L4 输入兼容性待查】页脚存在但与异常正文重叠：powerpoint\-r001\-26

代码检查确认页脚文本存在，视觉项visible\_footer失败。第43、45步及独立最终截图可见正文挤成竖列并延伸到页脚附近，模型之后仍结束任务。不能说没写页脚，也不能仅以XML文本正确判成功。打开修复/版式异常属于前置输入或兼容性线索，需要与原始输入对照；本报告未把全部原布局问题归给模型，但完成前未处理可见重叠是核验缺口。 **证据：** [powerpoint\-r001\-26 第43步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/powerpoint-r001-26?attempt=attempt-001&step=43)、[powerpoint\-r001\-26 第45步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/powerpoint-r001-26?attempt=attempt-001&step=45)、[powerpoint\-r001\-26 第55步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/powerpoint-r001-26?attempt=attempt-001&step=55)。

### 【L1 选区与输入后核验】名称框操作误写单元格，发现后未完成修复：excel\-pivot

模型确实创建了原生透视表，C02通过，但结果检查C01失败。第264步读回文件，第265步明确发现Data\!B61被写成“A1:B61”、C1被写成“B1”；独立解包也确认这两个值。它把本来用于定位的文本写进了工作表。第268–274步试图修复，最后一次调用未返回便超时。不能说不会创建透视表；也不能仅凭最终坐标误写就断言Driver偏移。数据污染是确定事实，是否独自解释C01的全部差异仍需逐项对照预期。 **证据：** [excel\-pivot 第264步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-pivot?attempt=attempt-001&step=264)、[excel\-pivot 第265步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-pivot?attempt=attempt-001&step=265)、[excel\-pivot 第270步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-pivot?attempt=attempt-001&step=270)、[excel\-pivot 第274步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-pivot?attempt=attempt-001&step=274)。

### 【L1 图表配置与恢复；L2 面板焦点】系列绑定未完成：excel\-bubble

模型长时间调整气泡图系列，末段仍在处理默认系列值与配置入口。第356步实际打开的是“更改图表类型”，第357步意识到坐标估计有问题；第358步Escape返回焦点验证错误，随后又遇WindowChanged，最终未保存规定output\.xlsx。这不是一次请求卡了一小时，而是多轮配置和恢复未收敛；按键报错后的界面可能已变化，不能把错误返回统一当成“完全没执行”。 **证据：** [excel\-bubble 第356步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-bubble?attempt=attempt-001&step=356)、[excel\-bubble 第357步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-bubble?attempt=attempt-001&step=357)、[excel\-bubble 第358步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-bubble?attempt=attempt-001&step=358)、[excel\-bubble 第360步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-bubble?attempt=attempt-001&step=360)、[excel\-bubble 第362步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-bubble?attempt=attempt-001&step=362)。

### 【L2 图表附属窗口输入；L1 恢复未收敛】图表数据编辑受阻：keynote\-report

第80、84步向图表数据编辑浮窗输入Q1，被拒绝为window\_id 62 is layer 3, not an ordinary layer\-0 window；第219、237步仍有同类错误，之后改尝试粘贴、切窗口、Numbers与Safari。到第350步仍未建立可靠输入路径，也未交付规定文件。独立最终截图是Safari覆盖Keynote，后者仍有默认月份图表及重叠表格，不能说图表已经完成。第346步还用了不支持的grave键名；这是模型接口使用错误，和前面的layer校验不是一回事。 **证据：** [keynote\-report 第80步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/keynote-report?attempt=attempt-002&step=80)、[keynote\-report 第84步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/keynote-report?attempt=attempt-002&step=84)、[keynote\-report 第237步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/keynote-report?attempt=attempt-002&step=237)、[keynote\-report 第346步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/keynote-report?attempt=attempt-002&step=346)、[keynote\-report 第350步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/keynote-report?attempt=attempt-002&step=350)。

### 【L2 附属面板路由；L1 恢复效率】源文档打开及查找输入反复受阻：word\-pages

第14、65、107步分别涉及打开、编码/面板输入与按键的layer\-8拒绝；末段第415、419、425、429步在查找输入/退出上仍报AttachmentUnverified。最终未交付要求的Word文件。窗口路由限制是明确卡点，模型也把大量时间用在重复探索和切换路径上；不能由本次超时推导它不会分页或页眉页脚功能。 **证据：** [word\-pages 第14步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/word-pages?attempt=attempt-001&step=14)、[word\-pages 第65步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/word-pages?attempt=attempt-001&step=65)、[word\-pages 第107步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/word-pages?attempt=attempt-001&step=107)、[word\-pages 第415步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/word-pages?attempt=attempt-001&step=415)、[word\-pages 第429步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/word-pages?attempt=attempt-001&step=429)、[word\-pages 第431步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/word-pages?attempt=attempt-001&step=431)。

### 【L2 文件面板输入；L5 Desktop权限；L1 恢复漂移】未进入可靠分类汇总流程：wps\-subtotal\-101

第19、52、124步出现路径输入/面板按键被layer\-8校验拒绝。之后尝试结束进程、Finder、Safari等路径，第615–621步已在Safari操作，没有交付output\.xlsx。独立最终截图明确显示WPS请求Desktop访问权限，WPS主页、Safari和强制退出窗口同时存在。权限弹窗是结束时的确定阻塞，不能据此认定它在整个一小时都存在；也不能把这题全算成模型不会分类汇总。应先复测权限弹窗接管和文件面板输入，再评模型原生功能能力。 **证据：** [wps\-subtotal\-101 第19步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/wps-subtotal-101?attempt=attempt-001&step=19)、[wps\-subtotal\-101 第52步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/wps-subtotal-101?attempt=attempt-001&step=52)、[wps\-subtotal\-101 第124步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/wps-subtotal-101?attempt=attempt-001&step=124)、[wps\-subtotal\-101 第615步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/wps-subtotal-101?attempt=attempt-001&step=615)、[wps\-subtotal\-101 第621步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/wps-subtotal-101?attempt=attempt-001&step=621)。

### 【L1 编辑选择与回退；L2 拖放限制】误删时间线，最终只有背景轨：jiangying\-pip\-101

第95、107、149步拖放返回no\_drop，前期入轨受阻。末段第327步执行删除，第328步模型自己发现整个时间线已空；第329–330步只重新加了背景并承认还需加A素材。最终截图与第333步末态相符：只有背景轨，默认名称“11月11日”，并未完成画中画和指定命名。直接业务缺失不只是名称不对，更不是已经做完却一直验证；误删与恢复不足是明确L1，后台拖放限制是L2前置因素。 **证据：** [jiangying\-pip\-101 第95步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=95)、[jiangying\-pip\-101 第149步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=149)、[jiangying\-pip\-101 第327步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=327)、[jiangying\-pip\-101 第328步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=328)、[jiangying\-pip\-101 第330步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=330)、[jiangying\-pip\-101 第333步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=333)。

### 【L2 保存面板按键路由；L4 文件识别】图表已渲染，最终保存受阻：chrome\-aircraft\-4426

第233步渲染图表，第238步进入保存面板；第240步pressKey\("super\+shift\+g"\)返回file panel receiver identity mismatch; no key sent。这是明确的按键发送前接收窗口验证失败，不是模型按错快捷键。归档另有22,882字节的临时文件\.com\.google\.Chrome\.q3q8Hk，内容头是RIFF/WEBP，但评估按后缀未识别成image，答案抽取因此reported=0、deliverable\_missing。这里有文件类型识别缺口；同时模型没有确认最终命名/保存完成，故不能直接改判成功。评分not\_reported也不能解释为五个数字都算错。 **证据：** [chrome\-aircraft\-4426 第233步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-aircraft-4426?attempt=attempt-001&step=233)、[chrome\-aircraft\-4426 第238步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-aircraft-4426?attempt=attempt-001&step=238)、[chrome\-aircraft\-4426 第240步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-aircraft-4426?attempt=attempt-001&step=240)。

### 【L1 布局调整与交付优先级】反复改图，未导出：chrome\-vulnerabilities\-2887

末段仍在PlantUML图表布局迭代。第212–214步添加不支持的ticks后渲染失败，第215步认出语法问题，第216–218步撤回后重试；第219–220步仍在调整被截断的标签，没有导出图像。外部绘图语法和布局是任务内可处理的问题，本次主要暴露模型没有设定有限修复次数与最小交付检查，不能用最终timeout笼统归为模型调用卡死。 **证据：** [chrome\-vulnerabilities\-2887 第214步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-vulnerabilities-2887?attempt=attempt-001&step=214)、[chrome\-vulnerabilities\-2887 第215步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-vulnerabilities-2887?attempt=attempt-001&step=215)、[chrome\-vulnerabilities\-2887 第218步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-vulnerabilities-2887?attempt=attempt-001&step=218)、[chrome\-vulnerabilities\-2887 第220步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-vulnerabilities-2887?attempt=attempt-001&step=220)。

### 【L1 检索覆盖与任务收敛】仍在补查地点，未交付GeoJSON：chrome\-attractions\-016

末段仍补查地点页。第197步点击后未见预期导航，第199步AX索引失效；第201–203步重新观察和点击后可导航，第205步尝试的两个Paris Catacombs地址返回404。没有最终GeoJSON。能看到浏览器观察/点击状态变化，但尚不能把单次未导航认定为集成框架缺陷；404是该页面的外部环境线索，不代表整个站点不可用。 **证据：** [chrome\-attractions\-016 第197步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-attractions-016?attempt=attempt-001&step=197)、[chrome\-attractions\-016 第199步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-attractions-016?attempt=attempt-001&step=199)、[chrome\-attractions\-016 第203步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-attractions-016?attempt=attempt-001&step=203)、[chrome\-attractions\-016 第205步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-attractions-016?attempt=attempt-001&step=205)。

### 【L3 模型服务限流】其余11个0分：均以429重试耗尽结束

下列11题的**直接终止原因均是429**，不是正常完成后的任务自检失败。部分题在429前已存在GUI阻塞或内容缺失，但中断轨迹不能用于断言模型在完整预算内也无法完成。4题没有任何前端模型步骤，只链接case，不杜撰步骤。

**chrome\-baseball\-3604 — 【L3】429中断。** 仅启动并定位击球数据页，尚无图像交付。Agent耗时32\.3秒。证据：[chrome\-baseball\-3604 第10步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-baseball-3604?attempt=attempt-001&step=10)；429记录来自该题原始inference/agent\_errors，前端末步表示中断前进度，不冒充429消息本身。

**excel\-air — 【L3】429中断。** 没有模型步骤，未执行任务。Agent耗时1\.9秒。证据：[excel\-air（无模型步骤）](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-air?attempt=attempt-001)；429记录来自该题原始inference/agent\_errors，前端末步表示中断前进度，不冒充429消息本身。

**excel\-bond — 【L3】429中断。** 刚读取债券参数并开始公式处理，未交付结果。Agent耗时83\.3秒。证据：[excel\-bond 第30步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-bond?attempt=attempt-001&step=30)；429记录来自该题原始inference/agent\_errors，前端末步表示中断前进度，不冒充429消息本身。

**jiangying\-audio\-101 — 【L3】429中断。** 第133、139步拖放no\_drop；末尾仍在清理浮窗/保存重开，未形成JY\_BGM交付。Agent耗时1231\.8秒。证据：[jiangying\-audio\-101 第133步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-audio-101?attempt=attempt-001&step=133)、[jiangying\-audio\-101 第139步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-audio-101?attempt=attempt-001&step=139)、[jiangying\-audio\-101 第202步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-audio-101?attempt=attempt-001&step=202)；429记录来自该题原始inference/agent\_errors，前端末步表示中断前进度，不冒充429消息本身。

**jiangying\-speed\-101 — 【L3】429中断。** 第23步附属面板layer\-8输入拒绝，第25步索引失效；早期即中断，未形成JY\_慢放。Agent耗时96\.5秒。证据：[jiangying\-speed\-101 第23步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-speed-101?attempt=attempt-001&step=23)、[jiangying\-speed\-101 第25步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-speed-101?attempt=attempt-001&step=25)、[jiangying\-speed\-101 第37步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-speed-101?attempt=attempt-001&step=37)；429记录来自该题原始inference/agent\_errors，前端末步表示中断前进度，不冒充429消息本身。

**jiangying\-text\-101 — 【L3】429中断。** 没有模型步骤，也没有新建的目标草稿。Agent耗时1\.9秒。证据：[jiangying\-text\-101（无模型步骤）](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-text-101?attempt=attempt-001)；429记录来自该题原始inference/agent\_errors，前端末步表示中断前进度，不冒充429消息本身。

**jiangying\-transition\-101 — 【L3】429中断。** 没有模型步骤，也没有新建的目标草稿。Agent耗时2\.0秒。证据：[jiangying\-transition\-101（无模型步骤）](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-transition-101?attempt=attempt-001)；429记录来自该题原始inference/agent\_errors，前端末步表示中断前进度，不冒充429消息本身。

**word\-illustrated — 【L3】429中断。** 没有模型步骤，未执行图文排版。Agent耗时2\.1秒。证据：[word\-illustrated（无模型步骤）](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/word-illustrated?attempt=attempt-001)；429记录来自该题原始inference/agent\_errors，前端末步表示中断前进度，不冒充429消息本身。

**word\-revision — 【L3】429中断。** 尚在源文档打开和窗口恢复阶段，未交付修订文件。Agent耗时141\.8秒。证据：[word\-revision 第16步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/word-revision?attempt=attempt-001&step=16)、[word\-revision 第32步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/word-revision?attempt=attempt-001&step=32)、[word\-revision 第55步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/word-revision?attempt=attempt-001&step=55)；429记录来自该题原始inference/agent\_errors，前端末步表示中断前进度，不冒充429消息本身。

**wps\-numfmt\-101 — 【L3】429中断。** 已有较长操作，但终止时没有规定output\.xlsx；不能把中断直接解释为不会数字格式。Agent耗时2137\.7秒。证据：[wps\-numfmt\-101 第284步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/wps-numfmt-101?attempt=attempt-001&step=284)；429记录来自该题原始inference/agent\_errors，前端末步表示中断前进度，不冒充429消息本身。

**wps\-outline\-101 — 【L3】429中断。** 产物存在，但原生分级outline\_ok与collapsed\_ops均false；429发生前未完成对应结构与折叠验收。Agent耗时1555\.1秒。证据：[wps\-outline\-101 第330步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/wps-outline-101?attempt=attempt-001&step=330)；429记录来自该题原始inference/agent\_errors，前端末步表示中断前进度，不冒充429消息本身。

### 超时中的模型耗时与操作绕路

以下是原始trace区间去重统计。模型区间包含排队、生成、传输；与工具区间有少量重叠，不能相加当总时长。完整响应最大值不含任务末尾被超时截断的未完成请求。

|任务|完整响应 / 工具|模型区间\(s\)|工具区间\(s\)|单次响应中位 / 最大\(s\)|
|---|---|---|---|---|
|excel\-pivot|137 / 136|3339\.9|254\.4|21\.7 / 108\.0|
|excel\-bubble|178 / 178|3418\.7|153\.6|18\.6 / 60\.8|
|keynote\-report|174 / 174|3289\.0|305\.5|13\.6 / 191\.7|
|word\-pages|213 / 213|3272\.7|318\.1|12\.6 / 92\.6|
|wps\-subtotal\-101|308 / 308|3207\.3|370\.5|6\.2 / 72\.1|
|jiangying\-pip\-101|170 / 170|3260\.4|299\.7|14\.2 / 66\.7|
|chrome\-aircraft\-4426|113 / 113|3366\.2|221\.6|29\.7 / 80\.1|
|chrome\-attractions\-016|99 / 99|3205\.9|325\.0|8\.3 / 234\.7|
|chrome\-vulnerabilities\-2887|110 / 110|3069\.4|524\.0|23\.7 / 215\.3|

这些任务持续产生了多轮模型响应和工具返回。模型服务延迟增加耗时，但操作轮数、错误恢复和重复观察也消耗预算；不能把“运行一小时”都解释成单次模型请求卡死。应分别优化服务吞吐、Driver恢复能力及模型操作效率。

## 3\. 7个null及其他评估链路问题

null不等于0分，也不等于“做对了被误判”。下面按发生阶段分类。评估/收集发生在Agent结束之后，没有对应的模型操作步骤；链接用于定位交付现场，错误依据是同题原始score、phase或outputs记录。

### 【L4 过程证据判定】4题Chrome因insufficient\_evidence没有业务分

chrome\-gpu\-970、chrome\-landmarks\-1134、chrome\-ecmascript\-1197、chrome\-churches\-033的业务检查均返回process\.status=insufficient\_evidence。不是四个模型都没动，也不是四次JSON解析异常：Landmarks和ECMAScript已经completed，GeoJSON/CSV产物类型门禁通过，但若干过程条款仍unknown；GPU则因429中断，Churches为timeout。

**示例：** Landmarks第181、206步直接读取并检查17点GeoJSON，第208步完成；评分中未知条款为0、2、3。文件存在只能证明交付物存在，不能代替“逐站点查询”等过程要求。应让评估对每项条款输出可复核的证据缺口，并区分“违反要求”“观察覆盖不足”“Judge没判定”，不能把unknown自动补为成功或失败。[chrome\-landmarks\-1134 第181步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-landmarks-1134?attempt=attempt-001&step=181)、[chrome\-landmarks\-1134 第206步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-landmarks-1134?attempt=attempt-001&step=206)、[chrome\-landmarks\-1134 第208步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-landmarks-1134?attempt=attempt-001&step=208)。其余现场：[chrome\-ecmascript\-1197 第367步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-ecmascript-1197?attempt=attempt-001&step=367)；[chrome\-gpu\-970 第278步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-gpu-970?attempt=attempt-001&step=278)；[chrome\-churches\-033 第134步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-churches-033?attempt=attempt-001&step=134)。

### 【L3 收集器＋L4 任务路径】1题Excel在评分前被/tmp路径收集规则拦住

excel\-r001\-26已completed，第81、83步检查原路径文件，第85步宣布保存。outputs记录为invalid/symlink\_forbidden，agent\_collection失败，因此没有进入有效评分。题目要求的/tmp路径与macOS路径解析/收集器禁止符号链接规则存在冲突；不能据此认定Excel没保存，也没有证据归为Desktop权限。应在启动前检查任务output与收集策略兼容，在明确边界下规范化路径或统一为允许的真实目录，并保留安全检查。**证据：** [excel\-r001\-26 第81步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-r001-26?attempt=attempt-001&step=81)、[excel\-r001\-26 第83步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-r001-26?attempt=attempt-001&step=83)、[excel\-r001\-26 第85步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-r001-26?attempt=attempt-001&step=85)；原始outputs/outputs\.json和result\.json。

### 【L4 评估脚本调用应用超时】1题Numbers导出检查超时

numbers\-formula的评分脚本用osascript打开output\.numbers并导出XLSX，120秒超时，故业务分null。与此同时，Agent本身也超时：第195步把应用自带SampleDocument\.numbers直接复制为output\.numbers，第218–220步仍在读取输入、尝试继续编辑。不能因为有文件就判公式完成，也不能把评估超时全部解释成脚本无权限。应记录打开/导出阶段、弹窗和进程状态，先区分文件不可用、应用模态阻塞与评估调用自身异常，再决定是否单独重评。**证据：** [numbers\-formula 第195步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/numbers-formula?attempt=attempt-001&step=195)、[numbers\-formula 第218步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/numbers-formula?attempt=attempt-001&step=218)、[numbers\-formula 第220步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/numbers-formula?attempt=attempt-001&step=220)；score中的TimeoutExpired。

### 【L3 VM评分阶段响应】1题Preview的guest\.response\_unavailable

preview\-packet已completed，但评分阶段返回TaskPhaseError / guest\.response\_unavailable，未得到业务分。现有记录不足以确定是VM连接、评估进程还是响应回收故障，不能归为PDF内容错误或Judge判断不准确。需要保存guest阶段标准输出、退出状态和通道错误，并支持保留产物后的独立重评。**证据：** [preview\-packet 第411步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/preview-packet?attempt=attempt-001&step=411)为Agent结束现场；根因证据在result\.json、grading/phase\.json和score\.failure，不把最后模型步骤误称为评估报错步骤。

### 【L3 Judge输出/轨迹适配＋L4 路线判定】19题存在judge\_error，多数不影响已有业务分

19题记录judge\_error：8个JSONDecodeError、9个JudgeError（包括Incomplete judge response与Invalid evidence reference）、2个Native tool result missing。它们主要让GUI路线unknown，不能与上面7个业务null混算。例：excel\-lookup业务1分，但路线阶段报告Native tool result missing；powerpoint\-r001\-19同类。该记录说明Judge读取路径没拿到所需工具结果，尚不足以证明原始Agent没有执行该工具。应把原生call/result关联、压缩/分块读取与Judge证据编号逐项核对，并对结构化输出做校验和有界重试。

**证据：** [excel\-lookup 第751步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-lookup?attempt=attempt-001&step=751)、[powerpoint\-r001\-19 第663步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/powerpoint-r001-19?attempt=attempt-001&step=663)为各题完成现场；各题score\.details\.judge\_error包含具体缺失call\_id。Keynote虽业务0分，路线另报Invalid evidence reference，不能把后者当作Keynote业务失败根因。[keynote\-report 第350步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/keynote-report?attempt=attempt-002&step=350)。

### 【L4 产物类型识别】1题临时WEBP没有标准后缀，被排除在图像读取之外

chrome\-aircraft归档临时文件头可确认是WEBP，门禁却按q3q8hk后缀判right\_type=false，答案抽取随后报告deliverable\_missing、五项not\_reported。应组合文件魔数/可解码性与任务要求识别产物，并单独检查最终名称和目录；“识别为图像”与“最终交付符合要求”是两项判断。它同时存在保存按键被拒绝和超时，不能只修门禁就直接给1分。**证据：** [chrome\-aircraft\-4426 第238步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-aircraft-4426?attempt=attempt-001&step=238)、[chrome\-aircraft\-4426 第240步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-aircraft-4426?attempt=attempt-001&step=240)；归档文件头与score\.code\.details\.artifact/answer。

## 4\. 没有直接导致失败的问题与优化方向

以下聚焦成功轨迹也出现的现象和跨任务改进；前文已明确致败的案例仅作为代表证据引用，不重复计数为新的独立故障。

### 【L1 模型层】DeepSeek的强项、弱项与训练方向

**强项：能理解结构化办公目标，也会主动检查和纠错。** WPS单变量求解确实使用原生功能：第346步运行，第348步观察求解结果，B1=973124\.356272411、B4≈6000，第381步保存；这是唯一业务与GUI路线都通过的题。Word大纲的原生TOC、Numbers图表的原生图表及数据绑定、Excel查找公式等也通过业务检查，但其GUI路线并未全部确认，不能扩大为纯GUI能力证明。[wps\-goalseek\-101 第346步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/wps-goalseek-101?attempt=attempt-001&step=346)、[wps\-goalseek\-101 第348步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/wps-goalseek-101?attempt=attempt-001&step=348)、[wps\-goalseek\-101 第381步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/wps-goalseek-101?attempt=attempt-001&step=381)；[word\-outline 第235步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/word-outline?attempt=attempt-001&step=235)；[numbers\-chart 第200步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/numbers-chart?attempt=attempt-001&step=200)。

**弱项一：故障恢复有探索意愿，但****缺少收敛规则****。** Keynote350步、Word页面431步、WPS分类汇总621步仍未完成；成功的Excel查找也用了751个前端步骤。前端步骤包含推理/消息，不等于操作次数，但足以定位重复探索。需要训练“识别窗口变化—观察当前目标—执行一个动作—检查实际结果”，而不是遇阻后持续重启、换应用、猜接口。Driver明确拒绝输入时，正确的策略还应包含识别能力边界和报告阻塞，不能要求模型无限试错解决工具缺陷。[keynote\-report 第80步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/keynote-report?attempt=attempt-002&step=80)、[keynote\-report 第350步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/keynote-report?attempt=attempt-002&step=350)；[excel\-lookup 第751步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-lookup?attempt=attempt-001&step=751)。

**弱项二：****操作目标与实际选中对象不一致时，容易继续执行****。** Excel把定位文本写进单元格，剪映删除错对象；两题都在推理中发现了问题，但没在预算内恢复。需要加强每次高影响操作前的选中对象确认，以及有反证后立刻撤销/修复的能力。[excel\-pivot 第264步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-pivot?attempt=attempt-001&step=264)、[excel\-pivot 第265步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-pivot?attempt=attempt-001&step=265)；[jiangying\-pip\-101 第327步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=327)、[jiangying\-pip\-101 第328步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=328)。

**弱项三：****结构与视觉验收不完整****。** 页脚文本存在不代表可见、无重叠；普通单元格数据不等于Table。Table任务本身有歧义，需要先修题面，再用明确任务训练原生结构核验；不能把隐含要求当负样本硬灌给模型。[powerpoint\-r001\-26 第43步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/powerpoint-r001-26?attempt=attempt-001&step=43)、[powerpoint\-r001\-26 第45步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/powerpoint-r001-26?attempt=attempt-001&step=45)；[excel\-r002\-15 第204步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-r002-15?attempt=attempt-001&step=204)、[excel\-r002\-15 第206步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-r002-15?attempt=attempt-001&step=206)。

**弱项四：纯GUI受阻后容易回到CLI。** 原路线20题fail；其中10题业务仍为1。Finder第239步报告GUI整理结束，随后直接读文件/标签元数据核验，说明偏离可能发生在“验证”而非主体编辑阶段。读取工具文档本身允许，exec数量不能直接当违规数，REPL包装也不是页面JS。是否违规必须看冻结指令和具体调用。[finder\-archive 第239步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/finder-archive?attempt=attempt-001&step=239)、[finder\-archive 第274步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/finder-archive?attempt=attempt-001&step=274)、[finder\-archive 第276步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/finder-archive?attempt=attempt-001&step=276)；GeoJSON例中的直接jq文件核验：[chrome\-landmarks\-1134 第181步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-landmarks-1134?attempt=attempt-001&step=181)、[chrome\-landmarks\-1134 第206步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-landmarks-1134?attempt=attempt-001&step=206)。

**DeepSeek是待训练模型，造数据应优先补以下能力：**

- **短程窗口恢复****。** 从保存sheet、图表浮窗、失效AX等状态出发，训练识别当前窗口/元素、刷新引用、单步动作和结果确认。仅保留真实恢复成功片段；Driver无法发送的样本应标注工具阻塞。

- **选中对象与输入路由****。** 构造名称框/单元格、素材库/时间线、多选/单选等易混场景，要求输入或删除前验证目标，误操作后优先Undo并重新观察。

- **原生结构＋视觉双重验收****。** 明确要求原生Table、透视表、TOC、图表绑定等；输出结果正确仍须核对结构。文稿另检查重叠、越界、正文和页脚关系。

- **约束内核验****。** 提供“只允许GUI”的同目标变体，演示如何用应用属性面板、公式栏、原生对话框核验，避免任务完成后再用脚本导致路线失败；Hybrid轨迹另标，不混作纯GUI示范。

- **有限预算下的交付****。** 教会模型先形成完整最小产物，再有限次优化；给定图表标签裁切等反证时，要求修正并验证，达到标准后停止。不要把大量失败重试整段作为高质量示范。

数据筛选需分开业务分、路线与基础设施状态：429题不能直接作为能力负样本，null不能自动当成功；业务1而路线fail的片段也不能标为纯GUI正例。后续训练/复测的DeepSeek配置按要求改为high，但本批medium不能回填为high。

### 【L2 CUA Driver层】高频窗口/输入问题，以及需谨慎归因的引用与坐标错误

以下按**50题最新attempt的前端工具返回文本**扫描；同一返回同类标记计一次，不累加嵌套child副本。它是“出现错误/状态标记”的频率，不是根因数量、单步语义失败率，也不是Driver缺陷率。类别可重叠。

|现象|涉及任务 / 50|返回次数|
|---|---|---|
|焦点/附属输入校验（AttachmentUnverified、bring\_to\_front、receiver mismatch）|41|254|
|其中非layer\-0窗口拒绝|27|97|
|失效AX引用|39|136|
|WindowChanged|23|58|
|坐标越界|16|22|
|拖放no\_drop|4|7|
|REPL变量重复声明|20|26|
|不支持的按键名|1|1|

**窗口焦点与附属面板：** 最普遍的可复现问题是看到面板但输入校验仍要求普通窗口。Keynote第80步为layer\-3，Word第65步为layer\-8；成功任务也会遇到，例如Numbers图表第75–103步多次焦点错误。优化应区分观察窗口、输入接收窗口和宿主窗口，并把附属关系及拒绝原因显式返回；不能只要求模型重复activate。[keynote\-report 第80步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/keynote-report?attempt=attempt-002&step=80)；[word\-pages 第65步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/word-pages?attempt=attempt-001&step=65)；[numbers\-chart 第75步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/numbers-chart?attempt=attempt-001&step=75)、[numbers\-chart 第103步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/numbers-chart?attempt=attempt-001&step=103)。

**pressKey重点复测：** Chrome飞机第240步明确“no key sent”，是发送前身份验证拒绝；Excel气泡第358步Escape之后又有WindowChanged，则需要验证是否已发送部分动作。Keynote第346步grave不支持属于键名使用错误。三类应分别记录“未发送/已发送/效果未确认”，保留接收进程、窗口、焦点元素和前后截图，不能统一按返回异常认定快捷键失效。[chrome\-aircraft\-4426 第240步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-aircraft-4426?attempt=attempt-001&step=240)；[excel\-bubble 第358步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-bubble?attempt=attempt-001&step=358)、[excel\-bubble 第360步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-bubble?attempt=attempt-001&step=360)；[keynote\-report 第346步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/keynote-report?attempt=attempt-002&step=346)。

**AX引用和坐标：** 失效AX覆盖39题，坐标越界覆盖16题。这可能由模型复用旧引用、窗口切换或画面尺寸变化造成，不能只按错误文本归为Driver。建议引用绑定snapshot/window版本，报错返回最新目标信息；截图附原始尺寸、坐标空间与原点，裁剪/缩放图不能悄悄沿用原坐标。代表：Chrome景点第199步刷新后第203步可以继续；Excel气泡第357步模型自行修正尺度估计。[chrome\-attractions\-016 第199步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-attractions-016?attempt=attempt-001&step=199)、[chrome\-attractions\-016 第203步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-attractions-016?attempt=attempt-001&step=203)；[excel\-bubble 第357步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-bubble?attempt=attempt-001&step=357)。

**拖放：** 4题7次no\_drop，发生于Preview、剪映音频、剪映画中画和PowerPoint\-r001\-19。应先确认Driver支持的前台/后台拖放条件，并返回是否开始、移动、释放及是否接收。不要把未投递成功等同于模型不会拖拽。[jiangying\-audio\-101 第133步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-audio-101?attempt=attempt-001&step=133)、[jiangying\-audio\-101 第139步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-audio-101?attempt=attempt-001&step=139)；[jiangying\-pip\-101 第95步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=95)、[jiangying\-pip\-101 第107步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=107)、[jiangying\-pip\-101 第149步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=149)；[preview\-packet 第69步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/preview-packet?attempt=attempt-001&step=69)；[powerpoint\-r001\-19 第287步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/powerpoint-r001-19?attempt=attempt-001&step=287)。

**浏览器与CUA集成：** 本批可确认保存面板接收窗口校验失败；景点页的点击/AX变化只构成复测线索，还不能证明整个集成有缺陷。复测应固定同一页面、窗口及snapshot，比较网页GUI输入和原生保存面板路由。页面JS禁用属于后续执行约束，应在工具层明确限制；不要把CUA REPL本身禁掉，也不要仅凭使用browser接口判违规。

### 【L3 Harness/轨迹层】限流止损、GUI约束与归档一致性

**13题429是本批最直接的非能力损失。** 11题零分、GPU空分，但excel\-window已产出合格文件仍得1。Agent错误与业务结果必须分列。运行器已有连续两题429止损及后续续跑记录，说明“无限重试”不是本批事实；但恢复后仍继续出现限流，应在正式派题前验证服务可用性，并把被限流的attempt原样保留，恢复后采用新attempt，不能覆盖原失败。[excel\-window 第216步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-window?attempt=attempt-001&step=216)；[chrome\-gpu\-970 第278步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-gpu-970?attempt=attempt-001&step=278)。

**纯GUI目前主要依靠指令约束和事后路线检查。** 20个route fail说明仅写前缀不足以保证路线。后续应按模式限制页面JS/DOM、直接文件改写和脚本驱动应用，同时保留文档阅读与允许的框架操作；给出清晰拒绝原因。业务分和路线仍应分列，避免只看Score得出“纯GUI做对”的结论。代表：[numbers\-formula 第195步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/numbers-formula?attempt=attempt-001&step=195)、[chrome\-landmarks\-1134 第206步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-landmarks-1134?attempt=attempt-001&step=206)。

**归档与usage：** 4个旧准备attempt存在evidence\_index\_mismatch；50个最新attempt的verify valid均为true，但不能据此声称整个批次valid=true。保留旧记录并修复索引生成/中断恢复流程，明确验证范围。3题session/native用量差异应保留两套原值及口径，22个未完成请求不能补零。前端步骤链接要绑定attempt，尤其本批4个attempt\-002任务。Judge工具结果缺失和结构化输出异常的具体修复见第三部分。

### 【L4 任务/评估器层】只保留需要处理的app问题

**Excel：** excel\-r002\-15明确写“创建Excel原生Table，范围A1:C6，首行作表头”；若意图只是整理普通数据，则应改评估而不是强加Table。excel\-r001\-26统一任务output路径与收集器规则，避免任务要求保存/tmp、收集器却拒绝。两类均在前文给出独立文件/阶段证据。

**Chrome：** 修正临时图片的类型识别，分开“内容可读取”与“最终目录/命名满足要求”；过程证据不足需逐条说明，不能把已有合格GeoJSON/CSV直接说成没文件。网页变化或某个地址404需记录，不必为每个绘图网站现象预置skill。

**PowerPoint：** 对页脚题输入在目标Office版本中做打开/渲染预检。将原正文版式异常和模型新增页脚问题分开，最终仍检查可见与不重叠，不能只检查字符串存在。

**Numbers：** 评估前应记录文件能否打开以及导出失败阶段；应用导出120秒超时不能自动当公式错误，也不能直接当评估器误判。

其余任务没有足够证据支持必须修改题面或评估，因此不列普遍性任务重构建议。

### 【L5 镜像/环境层】确认权限与前置状态，不泛化为全部失败原因

WPS分类汇总最终截图明确显示Desktop权限请求未处理；这是本次确认的一题权限阻塞，不是全批权限问题。镜像预检应在与Agent相同应用/账户上下文检查所需目录访问，保留跨进程系统弹窗可见性与接管能力；不应靠模型不断切换应用来绕过。[wps\-subtotal\-101 第621步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/wps-subtotal-101?attempt=attempt-001&step=621)；独立最终截图。

Chrome景点末段的具体页面404需要记录为外部页面状态；不要把未取齐数据全归模型，也不要据单个404判站点不可用。PowerPoint输入兼容性仍需复测，不能仅由截图推断宿主资源不足。未发现足以把本批所有超时归为宿主资源不足的共同证据。

## 附：核查口径与材料

- 全50题顺序沿用冻结comparison\.json的report\_order，不按成功/失败或字母重排。

- 逐题表保留原业务Score、Agent状态和独立L1–L5；GUI路线附在结果栏。没有确认的问题写“未确认”，不写成保证无问题。

- 逐类证据索引包含可追溯的任务/步骤链接；统计与逐题JSON保留计数、usage、路线和证据。

- 独立最终截图：PowerPoint页脚、剪映画中画、Keynote、WPS分类汇总。这些是阶段截图，不冒充某个模型步骤返回的图片。

- 对归档文件和评估记录的核查没有修改实验原件；未把局部可疑现象直接提升为已确认根因。

