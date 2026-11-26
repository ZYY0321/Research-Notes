# First50 Round3 DeepSeek Hybrid 轨迹分析报告

这一批跑得不顺利，deepseek模型调用一直在切换渠道



5个失败

- 模型只返回推理，没有工具调用也没有答复，所以框架直接中止退出

- 其他都是deepseek模型能力问题

20个null

- 17个：judge模型（astra）调用HTTP 503报错

- 2个：judge预算问题 \-\> 已解决

- 1个：缺证据 chrome\-vulnerabilities\-2887 任务是成功的，但当时judge模型（变笨了）没有做到18项数据来源的一一匹配，导致评分为null

批次：`first50_round3_codex_hybrid_deepseek_20261120_full`
分析日期：2026\-11\-24；来源：mac3。原评分不修改，未重跑任务。

**这是跨批选取的50题结果，不是一次连续执行的50题评测。** `selection.json`保留各题首次 `completed + finished_at` 的记录，不按得分择优；49题正常结束，attractions保留用户指定的最终超时记录。此前失败重试没有进入本报告的50题统计，因此不能将本批成功率当成首跑成功率，与其他单次run直接排名。

**主要结论：****25个1分、5个0分、20个null****。** 20个null中，17个是Judge HTTP 503，2个是评审预算预检查失败，只有1个是`insufficient_evidence`，且该题存在Judge跨条款证据不一致。5个零分包括：1个只有推理却未继续调用保存工具的异常结束，2个数据与单元格位置不一致，1个折价摊销符号错误，1个图表空系列/空类别引发的结构判定争议。模型的突出弱项是**核验没有覆盖内容与位置、字段含义的对应关系，发现局部反证后也未完整回归检查**。

## 实验配置

|**配置项**|**本次实验配置**|
|---|---|
|实验批次|`first50_round3_codex_hybrid_deepseek_20261120_full`，跨6个来源run选取|
|任务集|First50，50题、11个应用；逐题顺序按汇总包`task-index.json`|
|执行模式|Hybrid：允许GUI与CLI/脚本结合，仍须满足指定应用、原生结构和方法要求|
|被测模型|`deepseek-v4.1-flash-1017`；首批选入7题为`zijian/sfb`，其余43题为`huoshan_L/sfc`|
|推理配置|high；50题协议模型审计均`observed_match`|
|评估模型|`gpt-6-astra/azure/sfa`；代码检查与任务rubric结合|
|执行环境|mac3宿主机的macOS VM；`personal-5f6398b6d33f4401bcd301e52ac01538`|
|Agent与GUI工具|Codex CLI 0\.153\.4；CUA REPL；LocalDriver 0\.38\.0，源码`80bcb204`|
|框架版本|冻结源码`43778f7b4124eb4aa4ee4739725b7a34e8f62b2e`|
|并发与时限|任务串行；单题Agent最多3600秒，不含初始化与评估|
|浏览器限制|集成CUA浏览器可用；web search与浏览器JavaScript/evaluate禁用。未检出实际调用参数中的`.evaluate(`；不等于完整路线合规认证|

**证据链接说明：** 2026\-11\-24核实开发机`内网地址:22337`目录未收录本批。以下使用mac3 `18081`的实际来源run链接。当前mac3前端`readRoute()`只读取attempt，不读取step，故链接打开case后需按标注步号手动定位；没有伪装成已经支持自动跳步。步号均按该来源case的前端完整步骤序列计数，不使用Judge内部`step-N`编号。汇总包的六个来源均存在于mac3前端。

## 一、统计结果

|指标|结果|
|---|---|
|原始评分|1分25题（50%）；0分5题（10%）；null20题（40%）|
|Agent状态|completed49题；timeout1题（chrome\-attractions\-016）|
|已有数值评分中的通过率|25/30＝83\.3%；**不是全任务能力通过率**，20个null不能排除后用它代表全部任务|
|选中50个attempt的Agent累计耗时|**10小时44分49秒**，包含模型响应、工具与Agent执行开销；不含未选入的历史失败重试、冷却和暂停|
|选中记录首题开始至末题归档结束|北京时间11月20日11:00:55至11月24日09:51:26，约94小时50分31秒；不能当纯执行耗时|
|模型调用|inference\_started 3,076；completed 3,075；failed 0；attractions末次请求未见完成记录。该数仅限选中attempt，不代表历史渠道无故障|
|完成模型响应累计区间|32,263\.8秒（约8小时57分44秒）；包含服务响应等待/输出，不是纯推理计算时间|
|工具调用|3,053次顶层调用；不能等同于叶动作数或语义成功次数|
|已知输入 / cached|210,815,564 / 201,272,576 token（cached占输入95\.5%）|
|已知输出 / 推理|910,428 / 461,643 token；推理为输出中的子项，不相加|
|缓存写入|原生记录0；不据此判断供应商具体缓存实现|
|图片|各题图片ID去重后求和1,326；模型上下文图片引用56,833次，重复引用不等于新截图|

工具结果累计耗时约6,215\.6秒。它和模型区间按不同日志计时，不能要求严格相加等于Agent耗时，也不能把剩余时间全算为模型推理。token为归档已知用量，未完成请求不能按零补齐。

|应用|题数|1分|0分|null|
|---|---|---|---|---|
|excel|15|12|3|0|
|numbers|2|2|0|0|
|word|5|4|1|0|
|keynote|1|0|1|0|
|powerpoint|4|0|0|4|
|jianying|5|0|0|5|
|chrome|10|4|0|6|
|wps|5|0|0|5|
|preview|1|1|0|0|
|finder|1|1|0|0|
|calendar|1|1|0|0|

PowerPoint、WPS、剪映全为null，**不能据此写成模型在这些应用全失败**。这些题均Agent completed、代码部分得1，但方法/应用/内容rubric的Judge未完成；尤其剪映代码1只确认命名草稿等有限条件，不确认完整剪辑内容。

## 二、bad case分析

以下分别解释5个原始零分和1个Agent超时，保留评分争议，不把错误码直接当根因。

### 【L3 终止处理；上游响应归属待核】excel\-percentiles：保存尚未执行，只有推理的响应被作为回合完成

模型只返回推理，没有工具调用也没有答复，所以框架直接中止退出

**直接失败原因是没有生成指定****`output.xlsx`****，不是分位数算错，也不是保存动作被Driver拒绝。** 第5步算出的四组数量与分位数符合冻结规则，第18步写入表格；第47步打开保存附属面板，第53步进入正确目录，但文件名仍为“工作簿1”。第54步推理明确计划将字段37改为`output.xlsx`再点保存，之后没有工具调用。原生最后响应`payloads/156.json`只有`reasoning`，没有`function_call`或最终答复；紧接着`codex_turn_ended status=completed`，会话`task_complete.last_agent_message=null`。整个Agent仅203\.8秒，没有超时或限流错误；归档无output\.xlsx，评估`missing_or_unsafe_output`正确。

**定位：** 当前证据能定位到“只返回推理→回合正常结束”的协议/终止边界，不能进一步断言是DeepSeek主动放弃、网关丢工具调用，还是适配层遗漏。`agent.final_answer`还回填了较早的进度消息，不应当作最终交付声明。建议【L3】把只有推理、无动作且无最终答复的终止单独标记，并在受限次数内续接；保留原始响应供模型服务方核查。不要在Driver层补猜测保存动作。

证据：[excel\-percentiles，第5、18、47、53、54步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_recover_sfc_20261123_001/cases/excel-percentiles?attempt=attempt-001)；原生尾部摘录见本报告同目录`percentiles-native-tail.txt`。

---

**目前不能确定是DeepSeek模型本身的问题；能确认的是：框架收到了一次“****只有推理、没有工具调用或最终答复****”的响应，随后正常结束了回合。**

日志里的终止过程很明确：

1. **第53步工具成功执行**，进入目标保存目录，没有Driver报错。

2. **末次模型请求约6\.6秒后完成**，推理还在说：“把字段37改为`output.xlsx`，然后点击保存。”

3. 但响应实际只有一个`reasoning`项，**没有****`function_call`****，也没有最终答复**。

4. 约5毫秒后记录`codex_turn_ended: completed`，随后`task_complete.last_agent_message=null`。没有再请求模型继续。

所以，**不是保存操作失败，而是保存调用根本没有产生；也不是3600秒超时、限流或模型调用一直不返回。**

责任需要分两段看：

**因此报告不宜把它写成“模型收敛能力差、主动放弃”。** 更准确的是：

> **【L3，模型/服务侧成因待核】推理响应之后缺少动作或答复，框架直接结束回合，导致未保存。**
> 
> 

要进一步判断是不是模型本身，需要查末次请求的**上游原始流、停止原因及转换前的工具调用字段**。目前的`payloads/156.json`是Codex记录的响应，不能证明它完整等同于模型服务的原始输出。

框架可以先加一个有限恢复机制：遇到“仅推理、无动作、无最终答复”的结束，标记异常并让模型继续一次；不能直接把`completed`理解为任务已完成。

### 【L1 状态判断与回归核验；L2 控件动作语义需澄清】excel\-clean：想查看删除菜单，却改变了数据；只修B2，没恢复整列

主要是模型不熟悉CUA driver操作和excel环境

**最终B列物料编号整体上移一格，采购订单与物料不再对应。** 初始筛选逻辑正确：第7步算出24条保留记录，第43步粘贴正确数据。第157步读回发现B2被误写成`A1:D25`，其余记录当时仍正确；模型清空B2后，又为删除题目未要求删除的input工作表继续操作。第170步对“删除”控件执行`click(41)`，本意查看菜单；第171步推理已经注意到它可能直接删除了选中单元格，且出现“重复 删除”，却认为B2本来是空的、没有影响。随后第186步读回显示B2变成原B3的物料号、末行B25为空，与删除B2并上移的结果一致。

第188–192步仅再次清空B2，核验只断言行数、表头、B2为空及数量/状态条件，并未逐行对照物料号。最终产物B3为`CNBI005335-01`而应为`CNBI003606-02`，B25为空而应为`CNBI003613`，共20处B列值与冻结期望不同。冻结首行、筛选、打印均通过，不能掩盖数据损坏。**主要根因是****模型把局部清空当成恢复****；Driver的“menu button”默认点击是否应展开菜单，还需要对控件的AXPress/AXShowMenu分开复测，现有轨迹不足以直接判Driver实现错误。**

证据：[excel\-clean，第157、170、171、186、188、192、199步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_recover_sfc_20261123_001/cases/excel-clean?attempt=attempt-001)。训练重点是清空内容与删除单元格的区别，以及有反证后整行/整列回归核验；不要增加任务无要求的整理。

### 【L1 业务语义与核验】excel\-bond：公式可联动，但折价摊销列符号反了

**E列用了“票息－实际利息”，输出负的折价摊销；期末余额又通过减负数得到正确值，因此****只看余额容易漏掉****。** 第18、34步写入`E2=D2-C2`、`F2=B2-E2`并逐年延续；第92步读回实际利息1405\.0646、票息1000、折价摊销−405\.0646。任务要求的折价摊销应为实际利息减票息，即正405\.0646；期末账面价值应在期初上加该正摊销额。

I2:I5假设、I6 RATE及B2:F7公式均存在，C02通过；C01数值及C03参数扰动后的目标列语义未通过。**不能将C03失败简化成“没有原生公式”或“完全不会联动”。** 第90–92步已有可检查公式和值，模型仍在第100步宣布完成。修复方向是逐列检查经济含义和符号，而非只验证公式存在与最终余额等于面值。

证据：[excel\-bond，第18、34、90、92、100步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_recover_sfc_20261123_001/cases/excel-bond?attempt=attempt-001)。

### 【L1 原生结构写入与逐单元格核验】word\-illustrated：有2×2表格，但四项内容都在左上角

**模型创建了表格，却****把整段TSV粘在第一个单元格内，没有填入四个独立单元格****。** 第52步遇到StaleElement后，第54–56步重新观察并成功建表，这个Driver报错已恢复；真正导致零分的是第58步`paste("项目\t结果\n外观检查\t待检查")`的输入语义。第82步截图清楚显示四项文本都在左上单元格，右列和第二行为空；归档`word/document.xml`确认同样结果。

第79步把XML扁平化为全文，第88步仅数1张表、2行、4格，均无法判断文本在哪一格，最终却声明两列表格已正确。图片尺寸曾错误，但第70–79步被模型发现并修复，最后C02通过。因此这题是**有局部纠错能力，但表格核验缺少“单元格→内容”的映射**，不是表格不存在或图片权限问题。

证据：[word\-illustrated，第52、56、58、79、82、88、90步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_recover_sfc_20261123_002/cases/word-illustrated?attempt=attempt-001)；第82步截图已人工核看。

### 【L1 结构清理不足；L4 空结构判定边界】keynote\-report：三个柱子正确，导出仍留有空系列和空类别

**原始0分的触发点是原生图表XML与规则不完全一致，不是没有制作图表，也不是Q1/Q2/Q3的4/7/9算错。** 第85步直接粘贴数据后布局混乱，模型逐项修复；第131–147步主要清空多余内容，没有删除多余行列。第209步截图有正确标题、Q1/Q2/Q3和4/7/9三根柱子。归档PPTX却包含4个`c:ser`：一个有效系列“完成项目”，另外3个空系列；类别缓存均多一个空类别。冻结评估要求恰好一个系列、类别长度恰好3，因此C03失败，其余5项通过。

第244步输出已经包含重复类别和空值；第245步推理注意到空类别风险，却误认为XML只有一个系列，并推测评估会忽略空项。**模型应通过解析确认并删除多余行列，而不是猜测检查器宽容程度****。** 同时【L4】应明确“唯一数值系列”是否排除完全无值的占位系列：按可见数据语义，本题三根柱子正确；按原生结构严格规则则有多余结构。建议检查器区分“多了有效数据”与“空占位”，不要把本题直接记为画错图，也暂不擅自改判为1分。

证据：[keynote\-report，第85、131、147、209、244、245、246步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_recover_sfc_20261123_002/cases/keynote-report?attempt=attempt-001)；已核对第209步截图、导出chart1\.xml及冻结`business.py`第225–242行。

### 【L1 长任务恢复与收敛；浏览器动作异常需单独复现】chrome\-attractions\-016：反复清理地图后重新导入，预算耗尽

**最终选中attempt不是单次模型请求卡住一小时，而是****多轮操作与推理****累计用完3600秒。** 176次模型响应完成，最长56\.53秒，累计模型响应区间3105\.6秒；176次顶层工具结束，最后另有1次请求开始但无结束记录。第106步已称采集19个来源，第177步已出现19个地图点；后续围绕可见标签、空图层/空标记和保存状态反复调整。

第341步仍怀疑19条数据中有空点及缺失实体，第343步尝试下载推测的GeoJSON端点返回404；第351–355步恢复编辑，第357步删除图层，第363步停在重新选择导入文件。归档末态没有完成本轮重新导入、最终公开可见性及从站点导出的闭环。其自制GeoJSON不能替代任务要求的站点产物链。模型注意到异常是合理的，但在预算末期采取整层删除/重建，风险和剩余时间不匹配；若未确定空项代表什么，应先核对身份与持久化状态。

个别DOM点击无可见变化、快捷键反而生效，值得复测浏览器集成和pressKey；**仅凭“没变化”不能证明Driver点错，也不能直接归为模型坐标不准。** 此题原始null还叠加Judge HTTP503；Agent timeout本身是实际未完成，不能随Judge恢复被消除。

证据：[chrome\-attractions\-016，第106、177、241、246、321、343、351、357、363步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_recover_sfc_20261123_005/cases/chrome-attractions-016?attempt=attempt-001)。只分析`recover…005`这一选中attempt，不把此前413、限流和其他超时混入本次因果链。

## 三、评估问题

### 【L4 评估服务】Judge HTTP503：17/50，不能解释为缺证据

4个PowerPoint、5个WPS、5个剪映及ECMAScript、churches、attractions共17题。Office/WPS/剪映的代码部分均1分，但Judge失败后相应rubric保持unknown；**unknown原因是服务未完成判定，不等于该rubric没有证据。** 剪映的代码1仅是草稿存在检查，仍不可直接补成最终1。

示例：powerpoint\-r001\-13原始score记录`code.score=1, semantic_match=true`，`specified_app=unknown`，`judge_error="Judge HTTP 503"`。[powerpoint\-r001\-13，第27步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_recover_sfc_20261123_001/cases/powerpoint-r001-13?attempt=attempt-001)是Agent结束位置；503发生在之后的`grading/score.json`，不是这个Agent步骤抛错。应支持复用冻结产物与轨迹**只重评**，不为Judge服务异常重跑Agent；保留每次评估版本和原分。

### 【L4 评审预算】group\_call\_budget\_preflight：2/50

baseball、landmarks的评估记录均为`ReviewBudgetError / group_call_budget_preflight`。这是评审执行预算预检查拒绝，不能沿用“模型没有把HR列和来源明确绑定”的旧解释。预算预检未完成，就没有可靠的负面能力结论。

示例：[chrome\-baseball\-3604，第93步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120/cases/chrome-baseball-3604?attempt=attempt-001)为Agent收尾，后置评估code\.details记录上述错误；landmarks同类。应在Agent前检查任务rubric和证据批次数是否适配Judge预算，超限时明确报评估配置错误，或调整分批/共享证据策略。

### 【L4 Judge证据合并】vulnerabilities：1/50，条款之间对同一来源证据判断矛盾

此题是唯一明确`insufficient_evidence`的null。5条过程rubric中：①来源→图表因果链通过；②逐页访问18/18通过；③站点生成并保存、来源值与图片对应为unknown；④不借搜索摘要/第三方通过；⑤展示中间输入过程通过。产物PNG自身检查也通过。

③的理由承认已保存清晰的降序图表，但只认可4项来源，称另14项未被证实；①和②却明确列出了全部18项的独立NVD来源读取。这是**评审分组后的事实没有一致共享**，不是可以直接采信的“模型漏读14页”。第264步确认覆盖保存，第266步检查PNG文件，第268–270步重新打开并截图，不能只取保存弹窗中间态认定没保存。

证据：[chrome\-vulnerabilities\-2887，第264、266、268、270、274步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120/cases/chrome-vulnerabilities-2887?attempt=attempt-001)及原始`score.details.code.details.process.reviews`。应在unknown返回前对共享实体事实与其他条款的pass结论做一致性检查，并保留按实体绑定的来源值。暂保留null，不自行改分；本轮没有重新盲评所有18项。

#### 【附】chrome\-vulnerabilities\-2887 复核judge分数为1

**重新审查后，我判这个case通过，建议复核分为1。原始null保留，不修改。** 这是我对冻结轨迹和产物的独立复核，没有重新调用原评估模型。

这次不仅核对了原Judge的文字，也逐项核对了来源返回、最终图表和归档文件。

**18项对应关系如下**，我已经逐行与最终PNG核对：

最终图片在[第270步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120/cases/chrome-vulnerabilities-2887?attempt=attempt-001&step=270)可见：18行齐全，17条按分数降序排列的横条，Unavailable项没有画成0分。图片排版略紧，但标签、数值和条形可读，符合题目要求。

**因此，这次可以确认是【L4】评估器的证据合并问题，导致本应通过的任务被判为null。** 原Judge的③明确说其余14项“没有被确立的独立来源读取及对应值”，但这些证据实际存在；而且④已经逐项说明全部来源值与保存图表一致。这不只是“读过来源”和“图中对应正确”的概念差别，两者这次都能核实。

需要修的是：**在输出unknown之前，按CVE共享并核对“来源页→版本→数值→图中标签/数值”的证据，检查其他条款是否已经确认同一事实。** 不应要求Agent为了不同rubric重复读取同一批页面。

### 【L4 评分边界】Keynote空系列不是错误数值，Word空单元格则是真实缺失

keynote\-report的空系列/空类别应按业务语义明确处理，见第二部分。与之相反，word\-illustrated的四格内容放错位置、excel\-clean物料错位、excel\-bond摊销负号都属于实际产物缺陷，不能因“文字都在”“最终余额对”判为评估器误判。

## 四、其他高频问题与优化方向

### 【L1】DeepSeek能力：能推导、能检查，也能恢复；弱点在检查覆盖范围与基于证据收敛

**强项。** 能先用脚本整理输入，再通过原生应用实现结构，最后解析文件核验。excel\-pivot得1，第220–224、251步检查实际透视表定义；Word图片宽度错误能在第70–79步发现并改正；Finder通过原生整理后在第124–130步检查标签扩展属性，最终1分。这些说明它不是“不会原生GUI”或“不推理”。已知输出中推理token占50\.7%，但推理多本身不代表正确。

证据：[excel\-pivot，第220、224、251步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_recover_sfc_20261123_001/cases/excel-pivot?attempt=attempt-001)；[word\-illustrated，第70、75、79步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_recover_sfc_20261123_002/cases/word-illustrated?attempt=attempt-001)；[finder\-archive，第124、128、130步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_recover_sfc_20261123_002/cases/finder-archive?attempt=attempt-001)。

**弱项。** Word只看全文和表格数量，未看格内映射；Excel清洗只校验行数和筛选条件，未逐记录比较；债券只看公式与最终余额，未检查各列含义；Keynote发现空项后推测可接受，没有精确解析或收尾。attractions中为纠正异常不断重建，却没有把剩余预算纳入策略。这些比“多截图、调用慢”更适合作为训练目标。

**GUI/CLI偏好。** 3,053次顶层工具调用中：CUA REPL的`code`调用2,691次（88\.1%），shell/进程交互341次（11\.2%），其他21次。按首个非说明性工具调用入口，30题先CUA、20题先CLI；这里CUA初始化也计入，不能叫“首个业务动作偏好”。Hybrid中呈现**以GUI执行为主、CLI读输入和查产物辅助**；少量脚本也可能直接构建内容，不能把整个run当纯GUI示范。源码静态调用点中坐标click473处、非坐标click865处（原生AX与浏览器DOM合计，未混称AX）、pressKey805处；循环和一调用多动作会影响实际执行次数，未给伪精确语义成功率。50题`route_compliance=not_applicable`、`strict_gui_success=null`，原分只代表结果维度。

**给DeepSeek造训练数据的优先方向：**

1. **位置保持与完整核验****。** 在含空单元格、重复订单和相似编号的Excel数据中做清洗；在Word表格内输入TSV。验证每个单元格及对应记录，而非只比全文/行数。保留正确恢复操作，拒绝“局部断言通过就完成”的轨迹。

2. **业务不变量****。** 债券任务改变价格、利率和票息，要求每一列的符号与经济含义正确；不能只看终值或公式存在。正确样本同时覆盖模型推导、原生写入和独立公式/扰动检查。

3. **有反证后的回归修复****。** 给出B列上移、单元格内多段文本、导出残留系列等真实反证，要求识别受影响范围，回到原数据恢复，并复核整块内容。不要教模型忽略反证或猜评估器宽松。

4. **有预算约束的恢复****。** 设置网站空图层、焦点切换和编辑/浏览状态混淆，训练先确认状态、采取最小恢复动作；临近时限避免无备份地删整层重做。每次恢复用最终站点状态验证。

5. **动作意图与执行证据一致****。** “准备保存”的推理不算保存；“2×2表格”不算四格已填；“按下快捷键”不算目标效果完成。推理后无动作的异常终止需协议层与数据质检共同拦截。

这批成功/零分轨迹都应按片段核验再选入训练数据。模型异常结束、Judge服务错误和缺证据null不能直接贴“业务失败”或“成功”标签。Teacher宜按上述子能力选择已验收片段，不凭单一总分选整条轨迹。

### 【L2】观察与目标有效性：高频拒绝输入，但不能全部当Driver故障

以下统计实际工具返回，不包含工具说明中的示例；按选中50题去重，类别可重叠。

|返回类型|case数|工具返回次数|代表证据|
|---|---|---|---|
|StaleElement|25/50|45|[excel\-air，第41步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_continue_sfc_20261123/cases/excel-air?attempt=attempt-001)|
|WindowChanged|25/50|42|[excel\-validation，第152步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_continue_sfc_20261123/cases/excel-validation?attempt=attempt-001)|
|AttachmentUnverified|8/50|12|[excel\-air，第93步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_continue_sfc_20261123/cases/excel-air?attempt=attempt-001)|
|TargetUnverified|4/50|8|[word\-pages，第88步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_recover_sfc_20261123_001/cases/word-pages?attempt=attempt-001)|
|Fresh screenshot required|3/50|3|[chrome\-attractions\-016，第149步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_recover_sfc_20261123_005/cases/chrome-attractions-016?attempt=attempt-001)|
|页面加载等待超时|3/50|4|[chrome\-baseball\-3604，第18步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120/cases/chrome-baseball-3604?attempt=attempt-001)|

StaleElement/WindowChanged说明旧目标不再可用，既可能是正确保护，也可能是刷新或路由能力不足。Word第52步在同一调用中多个setValue再click，随后重观察即恢复；不应把这种报错单独算为任务根因。AttachmentUnverified第93步明确`input not sent`，说明连Escape也受到目标绑定约束。优先改进动作后的窗口/元素状态回传、给出当前模态目标和可恢复路径；不要靠无条件放松校验强行输入。

Excel“删除”控件有主按钮/展开菜单的语义差异，应分别暴露或清楚说明AX动作；click接收成功不等于展开菜单成功。pressKey仍需专项留意：本轮有WindowChanged拒绝快捷键和浏览器点击无变化后快捷键生效的例子，但没有足够证据证明按键映射本身损坏。网页等待超时实际为`document.readyState`未到complete，不能写成原生Driver服务卡死。

### 【L3】运行状态、来源和证据契约

**1/50出现reasoning\-only结束。** excel\-percentiles归档完整、调用无错误，但没有交付动作就completed；应与业务完成区分，保留“缺最终答复/待续接”诊断。不能把早期进度消息作为最终答复。

**50/50是结果分与路线分分离。** 报告不能根据成功分推定严格GUI达标；操作频率按顶层调用还是叶动作必须明确。跨批汇总保留source/attempt、选择规则和历史失败，以免将多次恢复当一次成功。

**归档完整性例外要限定范围。** 汇总README明确：选中domesday的`.DS_Store`有修改、attractions的`.DS_Store`未封存；历史未选入的excel\-bubble超时attempt缺manifest/grading\-materials并有evidence\-index不一致。不能把它们当50题全部证据缺失，也不能把复制字节校验通过当原始证据封存全部通过。本报告未重新封存或修复记录。

**前端链接。** 本机旧Viewer不支持step定位、开发机尚未导入；应先迁移保留相对符号链接与selection，再使用支持step的前端生成正式证据链接。当前报告保留可用来源链接和人工步号，不改前端服务。

### 【L4】任务层只保留需要处理的两点

**Keynote：** 定义无值系列/空类别是否允许，由检查器按可见数据和可编辑结构共同判断，避免默认模板空占位触发整题0；同时保留对多余有效系列的严格检查。

**Chrome：** baseball/landmarks先解决Judge预算配置；vulnerabilities先解决共享来源事实矛盾。不要通过强行要求Agent输出某种固定句子来掩盖评估证据合并问题。其他零分任务题面已明确，未发现必须改题才能解决的歧义，不逐app罗列低优先问题。

### 【L5】默认Python依赖缺失：18/50遇到openpyxl导入失败

共20次工具返回`No module named 'openpyxl'`，主要发生在读输入或校验XLSX。模型通常改用ZIP/XML解析继续执行，例如[excel\-bond，第86、88、90步](http://内网地址:18081/runs/first50_round3_codex_hybrid_deepseek_20261120_recover_sfc_20261123_001/cases/excel-bond?attempt=attempt-001)。它增加绕路，但不是该题折价符号错误的根因，也不能拿它解释整批零分。

Hybrid环境可提供明确的分析Python路径和固定库清单，或在入口说明默认环境不可用哪些库；不要让每题重复尝试安装/探测。同样，Judge HTTP503属于评估服务可用性，不能通过给VM安装库解决。

## 五、逐题结果（保留汇总包顺序）

来源缩写：A＝初始20261120；B＝continue\_sfc\_20261123；C＝recover…001；D＝recover…002；E＝recover…004；F＝recover…005。每题均attempt\-001。

|\#|任务|Score|Agent状态|Agent耗时\(s\)|来源|主要结论|
|---|---|---|---|---|---|---|
|1|excel\-air|1|completed|1090\.4|B|原始代码/评估通过；不等于路线认证|
|2|excel\-validation|1|completed|748\.7|B|原始代码/评估通过；不等于路线认证|
|3|excel\-pivot|1|completed|1296\.3|C|原始代码/评估通过；不等于路线认证|
|4|excel\-lookup|1|completed|529\.8|C|原始代码/评估通过；不等于路线认证|
|5|excel\-percentiles|0|completed|203\.8|C|未落盘；末次只有推理即结束【L3边界】|
|6|excel\-clean|0|completed|1350\.6|C|B列错位，局部修复后未完整比较【L1】|
|7|excel\-window|1|completed|325\.3|C|原始代码/评估通过；不等于路线认证|
|8|excel\-bond|0|completed|515\.5|C|折价摊销符号反了，余额正确掩盖问题【L1】|
|9|excel\-debug|1|completed|209\.8|C|原始代码/评估通过；不等于路线认证|
|10|excel\-bubble|1|completed|2523\.3|E|原始代码/评估通过；不等于路线认证|
|11|numbers\-chart|1|completed|618\.9|C|原始代码/评估通过；不等于路线认证|
|12|numbers\-formula|1|completed|1238\.3|C|原始代码/评估通过；不等于路线认证|
|13|word\-outline|1|completed|346\.3|C|原始代码/评估通过；不等于路线认证|
|14|word\-pages|1|completed|485\.6|C|原始代码/评估通过；不等于路线认证|
|15|word\-table|1|completed|295\.0|C|原始代码/评估通过；不等于路线认证|
|16|word\-revision|1|completed|404\.9|D|原始代码/评估通过；不等于路线认证|
|17|word\-illustrated|0|completed|363\.1|D|四项文本全落在第一个表格单元格【L1】|
|18|keynote\-report|0|completed|1878\.4|D|有效三柱正确；空系列/空类别触发严格规则【L1/L4】|
|19|excel\-r001\-26|1|completed|261\.2|D|原始代码/评估通过；不等于路线认证|
|20|powerpoint\-r001\-13|null|completed|56\.2|C|Judge HTTP503；原null，未判业务失败【L4】|
|21|powerpoint\-r001\-19|null|completed|1287\.2|C|Judge HTTP503；原null，未判业务失败【L4】|
|22|powerpoint\-r001\-26|null|completed|110\.2|C|Judge HTTP503；原null，未判业务失败【L4】|
|23|excel\-r002\-2|1|completed|143\.5|C|原始代码/评估通过；不等于路线认证|
|24|excel\-r002\-14|1|completed|369\.0|C|原始代码/评估通过；不等于路线认证|
|25|excel\-r002\-15|1|completed|152\.0|C|原始代码/评估通过；不等于路线认证|
|26|excel\-r002\-21|1|completed|384\.1|C|原始代码/评估通过；不等于路线认证|
|27|powerpoint\-r002\-5|null|completed|144\.8|C|Judge HTTP503；原null，未判业务失败【L4】|
|28|jianying\-transition\-101|null|completed|1286\.7|C|Judge HTTP503；原null，未判业务失败【L4】|
|29|jianying\-speed\-101|null|completed|1124\.2|C|Judge HTTP503；原null，未判业务失败【L4】|
|30|jianying\-text\-101|null|completed|2740\.2|C|Judge HTTP503；原null，未判业务失败【L4】|
|31|jianying\-pip\-101|null|completed|3449\.6|C|Judge HTTP503；原null，未判业务失败【L4】|
|32|jianying\-audio\-101|null|completed|566\.2|B|Judge HTTP503；原null，未判业务失败【L4】|
|33|chrome\-domesday\-1415|1|completed|287\.3|A|原始代码/评估通过；不等于路线认证|
|34|chrome\-gpu\-970|1|completed|220\.3|A|原始代码/评估通过；不等于路线认证|
|35|chrome\-chemistry\-1290|1|completed|145\.3|A|原始代码/评估通过；不等于路线认证|
|36|chrome\-baseball\-3604|null|completed|368\.9|A|评审预算预检失败【L4】|
|37|chrome\-landmarks\-1134|null|completed|188\.2|A|评审预算预检失败【L4】|
|38|chrome\-ecmascript\-1197|null|completed|2023\.6|C|Judge HTTP503；原null，未判业务失败【L4】|
|39|chrome\-vulnerabilities\-2887|null|completed|1106\.5|A|Judge跨条款来源证据矛盾；原null【L4】|
|40|chrome\-aircraft\-4426|1|completed|262\.5|A|原始代码/评估通过；不等于路线认证|
|41|chrome\-attractions\-016|null|timeout|3604\.4|F|地图清理重建未收尾，超时；另叠加Judge503【L1/L4】|
|42|chrome\-churches\-033|null|completed|665\.5|C|Judge HTTP503；原null，未判业务失败【L4】|
|43|wps\-absref\-101|null|completed|447\.7|C|Judge HTTP503；原null，未判业务失败【L4】|
|44|wps\-goalseek\-101|null|completed|340\.5|C|Judge HTTP503；原null，未判业务失败【L4】|
|45|wps\-outline\-101|null|completed|640\.4|D|Judge HTTP503；原null，未判业务失败【L4】|
|46|wps\-subtotal\-101|null|completed|271\.5|B|Judge HTTP503；原null，未判业务失败【L4】|
|47|wps\-numfmt\-101|null|completed|422\.8|B|Judge HTTP503；原null，未判业务失败【L4】|
|48|preview\-packet|1|completed|237\.7|D|原始代码/评估通过；不等于路线认证|
|49|finder\-archive|1|completed|646\.7|D|原始代码/评估通过；不等于路线认证|
|50|calendar\-reschedule|1|completed|310\.2|D|原始代码/评估通过；不等于路线认证|

## 复核范围与材料

已核对50题选取来源、原始评分、Agent状态、模型配置、原生调用统计及完整前端步骤；批量检索工具错误，并对5个零分、超时及三类评估错误进行重点复核。对4个已产出Office文件做只读XML检查，人工核看Word与Keynote关键截图。没有逐帧重评所有成功题，也没有代替原Judge重判50题。

报告附件：`statistics.json`保存选中结果/来源/耗时；`error-index.json`保存工具错误与前端步号；`artifact-checks.json`保存最终产物结构；`percentiles-native-tail.txt`保存异常终止证据。原始材料仍在mac3 `/Users/user/git_repo/mac-cua/results/first50_round3_codex_hybrid_deepseek_20261120_full`，以`selection.json`指定attempt为准。

