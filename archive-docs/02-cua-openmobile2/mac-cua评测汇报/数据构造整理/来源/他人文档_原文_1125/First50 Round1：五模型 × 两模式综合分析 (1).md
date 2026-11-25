# First50 Round1：五模型 × 两模式综合分析

前端：http://10\.210\.9\.14:22337/

点数表：[评测汇总表格](https://sensetime.feishu.cn/wiki/VhStwjN8QiED2zkoViDcOw7JnVW?sheet=kcRByB)

各run单独报告：[first50 round1 报告](https://sensetime.feishu.cn/wiki/YL7awvpHKiuUIykfirkcqhQ3nNf)



分析日期：2026\-11\-13。范围：10批、500次任务运行，业务任务共50题、11个应用。保留原评分与旧版八批报告。本报告复核新增Astra的100条前端轨迹文本、评分和工具记录，并结合此前400条审计；不是500条录像逐帧重评。

## 核心结论

1. **Hybrid teacher不应再只选Opus：Astra应成为并列主候选。** 五模型共同可评、排除明确异常终止的31题，Opus/Astra各30题通过，Sol/DeepSeek各29题，GLM25题。五模型共同成功的24题上，Astra耗时中位数279\.1秒、叶工具28\.5次，均最低；响应速度含服务因素，但调用数也支持其路径更简洁。1题优势不足以判定谁全面更强。

2. **严格GUI示范优先从Astra和Sol挑选，而不是直接采用Opus全部成功轨迹。** 原评strict true分别为Astra6、Sol3、DeepSeek1、Opus0、GLM0；Opus GUI业务通过29题，但其中27题路线fail。unknown很多，strict数量只是已确认可用候选，不是完整能力排名。

3. **两模式确有差异，但不能把全部落差都归模型。** 同题配对中，各模型几乎都更多出现Hybrid成功、GUI失败；GUI又叠加输入面板拒绝、服务中断、评估不完整及路线违规。应同时看业务、路线、运行健康三列。

4. **最普遍可复现的底层卡点仍是窗口/面板输入路由。** 本版统一扫描明确错误返回，GUI 202/250题、Hybrid115/250题出现焦点或非layer\-0窗口拒绝；包括恢复成功的任务，不等于Driver致败率。Astra也在WPS和剪映遇到相同阻塞。

5. **服务与评估故障已经足以影响排名。** Sol/Astra合计20次50图片上限，DeepSeek GUI13次429；Preview10批全空分，食品库存旧路径9批空分，Astra Hybrid修收集路径后为1分。后者不能当模型进步。

6. **DeepSeek造数据重点不变：反证后纠错、输入目标绑定、有限恢复、原生结构与交付核验。** 新增Astra提供了更短路径与合规GUI候选；不要将429、Driver拒绝或题面歧义当作学生能力负例。

## 1\. 实验配置与比较边界

|**配置项**|**本次核对结果**|
|---|---|
|任务集|First50，50题、11应用；每模型Hybrid/GUI各一批|
|模式|Hybrid允许脚本辅助；GUI禁止脚本/DOM/页面JS替代操作，但历史运行主要靠指令约束，并非工具全部禁用|
|Agent / GUI工具|Codex CLI 0\.153\.4、CUA REPL、LocalDriver 0\.38\.0|
|镜像|personal\-b7b357737d42495c838fbc0bc8cf34f1；同ID不保证应用每次启动状态一致|
|评估|gpt\-6\-astra/azure/sfa，代码检查与rubric组合；空分/路线unknown保留|
|时限与并发|各批jobs=1，Agent单题3600秒；不含准备、评估和清理|
|源码与任务|沿用Round1冻结体系；Astra与Claude同模式任务哈希GUI50/50相同、Hybrid49/50相同；库存题差异见下|
|统计attempt|每批最新归档attempt；不混入Astra 11月11日故障批、Round2，或11月13日Excel单题另批补测|

|**模型**|**Hybrid批次日期 / GUI批次日期**|**宿主**|**实际路由**|**推理配置**|
|---|---|---|---|---|
|GPT\-6\.1\-sol|11\-09 / 11\-10|data1|gpt\-6\.1\-sol/azure\_L/sfl|medium|
|Claude Opus\-5\.5|11\-06 / 11\-09|mac2|claude\-opus\-5\-5/awsb\_L/sfa|high|
|DeepSeek|11\-09 / 11\-10|mac3|deepseek\-v4\.1\-flash\-1017/huoshan/huoshan|medium|
|GLM\-5\.3\-flash|11\-09 / 11\-10|backup|glm\-5\.3\-flash/tencent/sfb|high|
|GPT\-6\-astra|11\-12 / 11\-12|Hybrid=data2；GUI=data1|gpt\-6\-astra/azure/sfa|medium|

DeepSeek历史两批真实effort为medium，后续要求high不回填历史。模型档位不是等量算力，耗时含供应商响应与工具执行。Astra与Sol同模式50条题面逐项一致；但Astra Hybrid库存题outputs由`/tmp/家庭食品库存.xlsx`改成`/private/tmp/家庭食品库存.xlsx`，题面不变、收集契约不同。此题展示原分，但不用于模型优势判断；共同交集中它本来就因其他模型null而被排除。

**公平比较口径：** 主表保留全部1/0/null；同题交集排除null、agent\_error、supervisor\_error、not\_started/transport\_error及已确认空末响应。普通timeout保留，因为在可用环境下的效率也属于执行能力。交集偏向可稳定评分的题，不能冒充校正后的全样本成功率。GUI业务分与路线分分别展示；不能用违规绕过后的1分证明纯GUI更强。

## 2\. 统计结果

**`GPT-6-astra > Claude Opus-5.5 ≈ GPT-6.1-sol > DeepSeek > GLM`**

|**模型**|**模式**|**1分**|**0分**|**null**|**有分通过率**|**全50题通过率**|**completed/timeout/agent\_error**|**Agent累计小时**|
|---|---|---|---|---|---|---|---|---|
|**GPT\-6\.1\-sol**|hybrid|37|4|9|**90\.24%**|74%|46/0/4|**8\.50**|
|**Claude Opus\-5\.5**|hybrid|33|3|14|**91\.67%**|66%|47/0/2|**10\.26**|
|**DeepSeek**|hybrid|32|6|12|**84\.21%**|64%|43/4/0|**12\.24**|
|**GLM\-5\.3\-flash**|hybrid|28|11|11|**71\.79%**|56%|45/3/0|**15\.89**|
|**GPT\-6\-astra**|hybrid|37|3|10|**92\.50%**|74%|48/0/2|**6\.74**|
|**GPT\-6\.1\-sol**|gui|22|22|6|**50\.00%**|44%|38/6/6|**19\.72**|
|**Claude Opus\-5\.5**|gui|29|14|7|**67\.44%**|58%|39/10/1|**24\.29**|
|**DeepSeek**|gui|21|22|7|**48\.84%**|42%|26/11/13|**23\.01**|
|**GLM\-5\.3\-flash**|gui|11|31|8|**26\.19%**|22%|28/22/0|**36\.46**|
|**GPT\-6\-astra**|gui|26|16|8|**61\.90%**|52%|38/3/9|**14\.22**|

**合计：276个1、132个0、92个null。** 有分408/500，业务通过276/408=67\.65%；全样本业务通过55\.2%。这是500次运行，不是500道独立任务。Hybrid另有Opus1个supervisor\_error、DeepSeek2个supervisor\_error和1个not\_started、GLM1个supervisor\_error和1个not\_started；表中三类Agent状态未包含这些。completed不等于业务成功，timeout/agent\_error也可能已产生1分产物。

累计Agent时间不是批次起止墙钟，不含暂停，也不是纯模型生成时间。Astra GUI26个1中有2个agent\_error和1个timeout，不能全部称为干净完成。

### 同模式、五模型共同可评样本

模式对比：hybrid远远好过纯gui

模型对比：glm明显差，另外四个模型看不出啥

|**模式**|**题数**|**GPT\-6\.1\-sol**|**Claude Opus\-5\.5**|**DeepSeek**|**GLM\-5\.3\-flash**|**GPT\-6\-astra**|
|---|---|---|---|---|---|---|
|hybrid|31|29/31|30/31|29/31|25/31|30/31|
|gui|21|14/21|19/21|17/21|8/21|16/21|

Hybrid上Astra/Opus同为30/31，Sol/DeepSeek29/31，GLM25/31；差距很小，不作显著性结论。GUI列仍只是业务结果：Opus19/21与DeepSeek17/21混有不合规路线，不能据此排在Astra16/21和Sol14/21之前。

**评估健康限制比一个总分更重要：** 如再要求五模型共同题都没有`judge_error`，GUI交集为0题。部分任务代码检查已有业务分，但路线评估解析/证据错误；这不自动推翻其代码分，却使严格GUI比较缺少完整依据。不能为了凑排名把unknown补成pass或fail。

### GUI路线合规

|**模型**|**路线pass/fail/unknown/缺失**|**strict true/false/null**|**业务1中的pass/fail/unknown/缺失**|
|---|---|---|---|
|GPT\-6\.1\-sol|15/1/32/2|3/22/25|3/0/19/0|
|Claude Opus\-5\.5|1/41/5/3|0/42/8|0/27/2/0|
|DeepSeek|2/20/26/2|1/36/13|1/10/10/0|
|GLM\-5\.3\-flash|2/21/25/2|0/40/10|0/5/6/0|
|GPT\-6\-astra|15/0/33/2|6/16/28|6/0/20/0|

Astra没有原评路线fail，不等于50题全已证明合规；33题unknown、2题缺失。其50次shell调用经文本核对均是读取工具说明，未发现任务数据处理脚本；浏览器页面JS dispatch为0。Opus的路线fail可能发生在读取初始材料或交付核验，不能一概说整个任务都是脚本编辑。

## 3\. 模型能力、GUI/CLI偏好与效率

|**模型**|**模式**|**CUA cell**|**shell叶调用**|**含osascript题数**|**原生AX/坐标点击**|**AX占比**|**页面JS dispatch**|
|---|---|---|---|---|---|---|---|
|GPT\-6\.1\-sol|hybrid|1949|453|15|343/361|48\.7%|342|
|Claude Opus\-5\.5|hybrid|1397|525|27|298/253|54\.1%|177|
|DeepSeek|hybrid|3094|1362|27|464/394|54\.1%|357|
|GLM\-5\.3\-flash|hybrid|2711|1104|34|446/299|59\.9%|642|
|GPT\-6\-astra|hybrid|1538|461|13|245/249|49\.6%|240|
|GPT\-6\.1\-sol|gui|3185|100|0|764/557|57\.8%|0|
|Claude Opus\-5\.5|gui|3043|335|1|617/931|39\.9%|0|
|DeepSeek|gui|5481|373|0|1051/899|53\.9%|0|
|GLM\-5\.3\-flash|gui|5797|312|0|1059/1025|50\.8%|4|
|GPT\-6\-astra|gui|3058|50|0|695/520|57\.2%|0|

**统计口径：** 展开functions\.exec包装里的实际叶工具调用；CUA cell一次可包含多个动作；原生点击按CUA evidence dispatch参数区分AX token与x/y，含已下发但失败的动作，不是单步语义成功率。浏览器元素点击、System Events与脚本注入不在原生AX/坐标分母中。页面JS可用于读取，不全是编辑；CUA REPL的JavaScript载体不等于页面JS。不同模型应用分布和轨迹长度不同，不能据坐标比例推断grounding好坏。

**Hybrid路线：** Astra原生AX/坐标接近各半，osascript覆盖13题；Sol15题，Opus/DeepSeek27题，GLM34题。Astra和Sol更少调用应用脚本，仍会用CLI读写文件、计算与核验；Opus/DeepSeek更常利用应用自动化。脚本多不代表完成更好，是否选择正确方法及最终交付才是关键。

**GUI路线：** Astra和Sol较遵守GUI边界，二者原生点击均更偏AX；Opus更偏坐标，DeepSeek/GLM更接近均衡。Astra的50次shell全是文档读取，不能写成“每题用CLI做任务”。操作频率是路线偏好，不是能力或成功率。

### 五模型共同成功的Hybrid题：效率比较

效率：**`GPT-6-astra > Claude Opus-5.5 ≈ GPT-6.1-sol > DeepSeek/GLM`**

1. astra明显效率最高，调用次数少且耗时短

2. deepseek调用次数最多

3. glm耗时最长

|**模型**|**共同成功题数**|**Agent耗时中位数（秒）**|**叶工具调用中位数**|
|---|---|---|---|
|GPT\-6\.1\-sol|24|309\.8|37|
|Claude Opus\-5\.5|24|530\.3|39|
|DeepSeek|24|390\.8|71\.5|
|GLM\-5\.3\-flash|24|733\.7|64\.5|
|GPT\-6\-astra|24|279\.1|28\.5|

Astra在本批共同成功题上路径最短、墙钟也最短；Sol次之。DeepSeek工具数较Opus高，墙钟却更短，说明“步骤多”与“模型响应慢”必须分开。上述中位数只反映24道共同成功题，不代表全部任务或失败恢复的总体效率。

### 五模型的能力判断

**Astra****：高效Hybrid与合规GUI都值得选样。** 原生Table题第15步打开“创建表”，第21步可见表名称与“转换为区域”控件，提供了原生结构建立的证据；但第29步又转WPS核验，后续窗口报错，说明成功后仍存在不必要的跨应用验证空间。[GPT\-6\-astra gui · excel\-r002\-15 · 第15步](http://内网地址:18081/runs/56fe210a-f0c6-41e6-bd60-d9201a69c8b0/cases/excel-r002-15?attempt=attempt-001&step=15)、[GPT\-6\-astra gui · excel\-r002\-15 · 第21步](http://内网地址:18081/runs/56fe210a-f0c6-41e6-bd60-d9201a69c8b0/cases/excel-r002-15?attempt=attempt-001&step=21)、[GPT\-6\-astra gui · excel\-r002\-15 · 第29步](http://内网地址:18081/runs/56fe210a-f0c6-41e6-bd60-d9201a69c8b0/cases/excel-r002-15?attempt=attempt-001&step=29)。GUI面对WPS拒绝会报告未完成，而不是用脚本绕过，这有利于路线合规；不能把诚实停止当业务成功。

**Opus****：原生办公与完整任务规划仍是主teacher候选。** 与Astra共同样本成绩持平；对Excel Table的文件结构核验可作Hybrid示范。弱项是GUI模式下路线边界，以及视觉布局反证未必被最终核验覆盖。[Claude Opus\-5\.5 hybrid · excel\-r002\-15 · 第29步](http://内网地址:22337/runs/first50_round1_codex_hybrid_claude_20261106/cases/excel-r002-15?attempt=attempt-001&step=29)。

**Sol：效率与模式遵守兼顾。** 在本批共同成功题中仅次于Astra；GUI多数阻塞没有脚本绕过。它有Numbers导出坐标与公式修复的成功对照，但轨迹含底层包操作，提炼修复原则即可，不应无审查推广脆弱文件补丁。[GPT\-6\.1\-sol hybrid · numbers\-formula · 第69步](http://内网地址:22337/runs/first50_round1_codex_hybrid_sol_20261109/cases/numbers-formula?attempt=attempt-001&step=69)、[GPT\-6\.1\-sol hybrid · numbers\-formula · 第76步](http://内网地址:22337/runs/first50_round1_codex_hybrid_sol_20261109/cases/numbers-formula?attempt=attempt-001&step=76)。

**DeepSeek：办公推导基础较好，状态闭环和恢复成本更值得训练。** Hybrid与Sol共同交集同分，说明不是普遍不会做；GUI13题429造成的终止要排除。具体弱项见第7节，不以更长思考或更多核验脚本代替真实纠错。

**GLM：有可用局部能力，但整体收敛和验收较弱。** 当前共同交集落后，Keynote图表数据未过、Excel清洗数量不符是具体内容缺失；另外存在空末响应被completed的框架问题，不能全部算“模型主动结束”。[GLM\-5\.3\-flash hybrid · keynote\-report · 第84步](http://内网地址:22337/runs/first50_round1_codex_hybrid_glm_20261109/cases/keynote-report?attempt=attempt-001&step=84)、[GLM\-5\.3\-flash gui · excel\-clean · 第116步](http://内网地址:18081/runs/0886f578-ddc3-4722-bd75-ffc03c7c5ccd/cases/excel-clean?attempt=attempt-001&step=116)。

## 4\. 两模式对比

hybrid远远好过纯gui

|**模型**|**同题配对数**|**H1/G1**|**H1/G0**|**H0/G1**|**H0/G0**|
|---|---|---|---|---|---|
|GPT\-6\.1\-sol|34|20|13|0|1|
|Claude Opus\-5\.5|30|26|3|0|1|
|DeepSeek|26|17|6|0|3|
|GLM\-5\.3\-flash|36|10|16|1|9|
|GPT\-6\-astra|32|24|7|0|1|

几乎所有差异都朝Hybrid成功、GUI未成功方向发展。Astra32道配对题中有7道H1/G0；DeepSeek26道中有6道。原因不能合并成“GUI模型能力下降”：Hybrid可绕过部分面板输入，GUI受可用交互限制；不同批次又有服务故障、输入修复提示、评估缺失和脚本违规。

DeepSeek两模式共同成功且无异常中断的17题，Hybrid耗时中位数365\.9秒、工具62次，GUI1143\.6秒、工具115次；同一批题中时间约3\.1倍、调用约1\.9倍。训练目标应包括可迁移的短程恢复，不只是把成功任务做得更长。

未来模式对照需固定任务包/评估版本、实际禁用页面JS等违规入口，并修好合法的GUI输入路径。不能用“更敢绕过约束”解释GUI能力更强，也不能用“遵守约束但Driver挡住”解释模型能力更弱。

### 应用维度结果：仅用于定位差异，不做App能力总排名

从应用看：

1. Hybrid 的优势集中在 Chrome、WPS 和 PowerPoint，这几个app从hybrid模式切到gui模式掉点很明显

2. Word 所有模型表现都很好

3. Astra 最突出的应用优势是 Excel

4. 剪映任务全零分

每格为1/0/null；同一应用题数少，且环境/评估故障集中。

**Hybrid**

**GUI（指令约束模式）**

**各模型对于模式切换的敏感性：**

GUI能力优先看Astra。Astra不太依赖CLI，GUI能力比较强；其次是Sol。

Opus不太守规则，在GUI路线下依然会用CLI，所以最终成功率最高。

## 5\. 核心失败原因与评估问题

以下类别可在同一任务叠加，不相加成根因比例。前端链接定位操作证据；评分/收集错误发生在Agent之后，来源是归档result/score，不能把前端末步冒称评分步骤。

### 【L2】附属面板能看到，但输入被拒绝：跨模型最普遍的卡点

统一按CUA `js`返回中的“not verified as”“not an ordinary layer\-0”“Focus verification failed”等明确字符串统计，GUI202/250题、Hybrid115/250题命中；只计任务是否出现，不以重复次数放大。`no key sent`另有GUI88/250、Hybrid64/250题；两者重叠，不相加。本口径比旧版“焦点相关标记”更窄，不直接与旧174/200比较。

Astra GUI WPS格式题第7、16、43、91步被layer\-8校验拒绝；剪映音频第10步已看到通知弹窗及取消按钮，第15、28步仍拒绝输入，最终未开始编辑。DeepSeek Keynote第80步和Chrome第240步也是同类面板/发键问题。**应由Driver返回实际接收窗口、焦点元素、按键是否已投递；不能把一次pressKey调用返回当作键已经发出。** [GPT\-6\-astra gui · wps\-numfmt\-101 · 第91步](http://内网地址:18081/runs/56fe210a-f0c6-41e6-bd60-d9201a69c8b0/cases/wps-numfmt-101?attempt=attempt-001&step=91)、[GPT\-6\-astra gui · jiangying\-audio\-101 · 第15步](http://内网地址:18081/runs/56fe210a-f0c6-41e6-bd60-d9201a69c8b0/cases/jiangying-audio-101?attempt=attempt-001&step=15)、[DeepSeek gui · keynote\-report · 第80步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/keynote-report?attempt=attempt-002&step=80)、[DeepSeek gui · chrome\-aircraft\-4426 · 第240步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-aircraft-4426?attempt=attempt-001&step=240)。

但不是所有未完成都由这个错误解释：点击无效果、目标选错和后续恢复策略仍须逐步核实。

### 【L3】图片上限、服务限流与异常终止：先修请求管理

Sol9题（H4/G5）＋Astra11题（H2/G9）触发最多50张图片的服务错误，共20/200次这两个模型的运行。Astra GUI画中画已完成主要画面和30%比例，但最终未返回首页，随后因图片上限agent\_error；这不能简化为“不会做画中画”。DeepSeek GUI13题429是服务可用性，不是13条模型推理失败。另有旧四模型审计确认的5次空末响应被标completed，保留原始终止证据，不当正常交付。

**修复方向：** 按实际发送请求计算图片预算，移除过时重复观察并保留关键证据；区分可重试服务错误与不可恢复错误；空响应/refusal不标正常完成。Astra画中画[GPT\-6\-astra gui · jiangying\-pip\-101 · 第84步](http://内网地址:18081/runs/56fe210a-f0c6-41e6-bd60-d9201a69c8b0/cases/jiangying-pip-101?attempt=attempt-001&step=84)，Sol转场[GPT\-6\.1\-sol hybrid · jiangying\-transition\-101 · 第103步](http://内网地址:22337/runs/first50_round1_codex_hybrid_sol_20261109/cases/jiangying-transition-101?attempt=attempt-001&step=103)，Opus空末响应前现场[Claude Opus\-5\.5 gui · keynote\-report · 第179步](http://内网地址:22337/runs/first50_round1_codex_gui_claude_20261109/cases/keynote-report?attempt=attempt-001&step=179)。链接展示终止前操作，服务错误以agent\.errors为准。

### 【L1】已经看到错误，却没有修复到交付：DeepSeek最明确的训练缺口

Numbers第301步读出导出坐标偏移，第313步仍宣布完成；Excel透视表第265步发现定位文本被写进数据；剪映画中画第328步发现误删时间线。这是三种不同的闭环缺失：反证触发修复、输入前确认对象、破坏性动作后回退。[DeepSeek hybrid · numbers\-formula · 第301步](http://内网地址:22337/runs/first50_round1_codex_hybrid_deepseek_20261109/cases/numbers-formula?attempt=attempt-001&step=301)、[DeepSeek hybrid · numbers\-formula · 第313步](http://内网地址:22337/runs/first50_round1_codex_hybrid_deepseek_20261109/cases/numbers-formula?attempt=attempt-001&step=313)、[DeepSeek gui · excel\-pivot · 第265步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-pivot?attempt=attempt-001&step=265)、[DeepSeek gui · jiangying\-pip\-101 · 第328步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=328)。

不要拿Driver未发出的按键训练为模型操作错误，也不要因为模型写了长篇反思就把恢复判成功；要看对象、数据和交付是否真正恢复。

### 【L3/L4】固定空分与不完整评估：按原因拆开

**输出收集路径：** 食品库存在旧8批与Astra GUI共9批为null，Astra Hybrid把outputs改为`/private/tmp`后为1。原因是任务输出路径与严格收集规则冲突，不是9个模型都没保存。该变化属于任务/收集修复，不能计模型优势；本报告不混入11月13日单题补跑结果。[GPT\-6\-astra hybrid · excel\-r001\-26 · 第37步](http://内网地址:22337/runs/first50_round1_codex_hybrid_astra_20261112/cases/excel-r001-26?attempt=attempt-001&step=37)、[GPT\-6\-astra gui · excel\-r001\-26 · 第40步](http://内网地址:18081/runs/56fe210a-f0c6-41e6-bd60-d9201a69c8b0/cases/excel-r001-26?attempt=attempt-001&step=40)。

**VM评分响应：** Preview10批全部null，归档错误为`guest.response_unavailable`；具体底层退出原因仍未确认，不能一律称权限问题或PDF内容错误。这10次与库存9次合计19/92个null。[GPT\-6\-astra gui · preview\-packet · 第39步](http://内网地址:18081/runs/56fe210a-f0c6-41e6-bd60-d9201a69c8b0/cases/preview-packet?attempt=attempt-001&step=39)。

**Judge响应/证据不完整：** Astra GUI29/50题details含judge\_error，常见Incomplete judge response、JSONDecodeError和Invalid evidence reference；部分业务代码分仍保留，所以不等于29个null。必须分别保留业务分、路线判定与评分错误。Astra Hybrid的WPS绝对引用/分组为JSON解析失败而空分，不能判文件失败。[GPT\-6\-astra hybrid · wps\-absref\-101 · 第39步](http://内网地址:22337/runs/first50_round1_codex_hybrid_astra_20261112/cases/wps-absref-101?attempt=attempt-001&step=39)。

**禁止行为与全过程unknown：** Astra Hybrid剪映PIP、音频多个结果条件pass，但`no_forbidden`unknown导致空分；变速还包含过程要求unknown。没有看到违规不等于已证明全程没有，但截图批次缺少文本也不该无条件推翻已有完整工具记录。应保留逐条证据覆盖，而非靠一句unknown合并掉整条结果。[GPT\-6\-astra hybrid · jiangying\-pip\-101 · 第98步](http://内网地址:22337/runs/first50_round1_codex_hybrid_astra_20261112/cases/jiangying-pip-101?attempt=attempt-001&step=98)、[GPT\-6\-astra hybrid · jiangying\-audio\-101 · 第89步](http://内网地址:22337/runs/first50_round1_codex_hybrid_astra_20261112/cases/jiangying-audio-101?attempt=attempt-001&step=89)。这些是原评结果，未独立重判1分。

### 【L4，伴随L1交付核验】Hybrid许可与WPS保存门槛不一致

Astra Hybrid `wps-numfmt-101`第18步直接修改XLSX样式、第19–25步在WPS检查显示，原评0的首个原因是`not_saved_by_wps`。冻结代码在检查内容前先调用`wps_saved()`；而Hybrid题面删除了GUI版“不要用脚本生成文件”，仅保留“用WPS打开”“另存为”。因此不能直接把0分写成“数字格式没做好”，也不能直接宣布评分误判：需要明确是否要求WPS真正执行一次保存，并独立核验格式、公式、原值与其他区域。[GPT\-6\-astra hybrid · wps\-numfmt\-101 · 第18步](http://内网地址:22337/runs/first50_round1_codex_hybrid_astra_20261112/cases/wps-numfmt-101?attempt=attempt-001&step=18)、[GPT\-6\-astra hybrid · wps\-numfmt\-101 · 第23步](http://内网地址:22337/runs/first50_round1_codex_hybrid_astra_20261112/cases/wps-numfmt-101?attempt=attempt-001&step=23)。

如果指定方法必须原生保存，应写入Hybrid题面并保留过程证据；如果允许脚本生成后在App核验，就不应只凭生成器痕迹否决内容。Excel“整理成表”但检查原生Table同理，应明确术语后再拿作学生负例。

### 【L4/L5，伴随L1验收】输入文稿修复与导出坐标差异

Astra GUI PowerPoint能源图题第17–20步已出现修复提示，随后转LibreOffice编辑，第67–69步保存，第94步自述重开核验未完成，机器语义检查为false。能确认“输入兼容异常＋交付未通过”，尚不能仅凭提示把全部失败归模型或全部归环境。[GPT\-6\-astra gui · powerpoint\-r001\-19 · 第17步](http://内网地址:18081/runs/56fe210a-f0c6-41e6-bd60-d9201a69c8b0/cases/powerpoint-r001-19?attempt=attempt-001&step=17)、[GPT\-6\-astra gui · powerpoint\-r001\-19 · 第69步](http://内网地址:18081/runs/56fe210a-f0c6-41e6-bd60-d9201a69c8b0/cases/powerpoint-r001-19?attempt=attempt-001&step=69)。

Numbers图表GUI题原生图表两项通过、导出表结构C01失败；这类应保留原生/导出两项独立验收。不要为每个App现象预置特殊skill，而是训练在指定输出上验证坐标、类型与结构。[GPT\-6\-astra gui · numbers\-chart · 第52步](http://内网地址:18081/runs/56fe210a-f0c6-41e6-bd60-d9201a69c8b0/cases/numbers-chart?attempt=attempt-001&step=52)。

## 6\. L1–L5最值得做的改进

|**层级**|**优先改进**|**理由与代表证据**|
|---|---|---|
|【L1】模型|反证后的修复、输入对象确认、有限恢复、交付后停止|DeepSeek Numbers301/313与透视表265；用实际修复结果验收，不奖励长推理|
|【L2】CUA Driver|宿主/附属窗口与真实输入接收者分离；返回AX快照身份、焦点元素、发键状态和截图坐标系|本批GUI202/250题出现明确拒绝；Astra剪映音频15、WPS格式91可复现|
|【L3】Harness|请求图片预算、服务错误续跑、空响应终止语义；按模式真正禁用页面JS/DOM/API绕过|Sol/Astra20次图片上限；DS GUI13次429；旧5次空末响应。CUA REPL JS应保留|
|【L4】任务/评估|统一outputs路径、明确原生Table/WPS保存要求；分开业务、指定方法、路线和证据覆盖|库存9空＋修路径后1分；WPS not\_saved\_by\_wps；严格GUI共同无judge\_error样本为0|
|【L5】镜像/环境|在真实App和账户预检输入可打开/渲染、权限与登录弹窗；保留初始现场|Astra PPT17步修复、剪映通知弹窗；旧DeepSeek WPS Desktop权限现场|

优先修会阻止所有模型合法操作的L2输入问题，以及使结果不可评的L3/L4问题；模型训练同时围绕已确认的L1错误推进。不要为了训练回避工具缺陷，也不要用环境问题替所有错误恢复行为免责。上述步骤链接见第5节；权限代表现场：[DeepSeek gui · wps\-subtotal\-101 · 第621步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/wps-subtotal-101?attempt=attempt-001&step=621)

## 7\. DeepSeek弱项深挖：面向被训练模型的造数据方向

以下沿用已逐案例确认的DeepSeek证据；新增Astra不会改变学生原始错误。DeepSeek是被训练模型，不称teacher。

### 现有能力边界

DeepSeek不是本项目teacher，而是待训练模型。当前Hybrid表现说明它并不缺普遍的脚本理解或办公计算能力；Word五题全部通过，Excel查找/透视/清洗等多项通过。GUI不足也不能全部归为模型：13题429、Keynote/保存面板Driver拒绝都应排除出直接能力负例。最值得训练的是以下四种可观测行为。

### 优先级1：把“核验发现错误”变成“修复后交付”

**证据与诊断：** Numbers导出坐标偏移已读出来却没有修；PPT页脚下沿越界已经算出仍接受结果。这不是观察缺失，也不是靠增加思考长度就必然解决，更像没有让验收条件约束最终决策。[DeepSeek HYBRID · numbers\-formula · 第301步](http://内网地址:22337/runs/first50_round1_codex_hybrid_deepseek_20261109/cases/numbers-formula?attempt=attempt-001&step=301)；[DeepSeek HYBRID · powerpoint\-r001\-26 · 第104步](http://内网地址:22337/runs/first50_round1_codex_hybrid_deepseek_20261109/cases/powerpoint-r001-26?attempt=attempt-001&step=104)、[DeepSeek HYBRID · powerpoint\-r001\-26 · 第105步](http://内网地址:22337/runs/first50_round1_codex_hybrid_deepseek_20261109/cases/powerpoint-r001-26?attempt=attempt-001&step=105)。

**造任务：** 给模型一个几乎完成但有一项确定反证的产物：导出坐标偏一行、页脚部分越界、图表类别和数值交换、保存后参数回退。要求它自己观察，指出不满足项，只修改必要部分，再重新打开或独立核验。

**验收：** 不以“发现问题/写出检查代码”给成功标签；必须同时满足错误消除、其他内容不被破坏、重新核验通过。区分“没看到反证”“看到但合理化”“修复动作无效”“修复后又损坏”，方便定位训练增益。

### 优先级2：绑定当前窗口、选中对象和输入目标

**证据与诊断：** Excel将“A1:B61”写入B61，剪映删除了整个时间线；模型事后能识别，但预防与恢复不足。AX索引失效、截图坐标空间变化又会放大这个问题。[DeepSeek GUI · excel\-pivot · 第264步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-pivot?attempt=attempt-001&step=264)、[DeepSeek GUI · excel\-pivot · 第265步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-pivot?attempt=attempt-001&step=265)；[DeepSeek GUI · jiangying\-pip\-101 · 第327步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=327)、[DeepSeek GUI · jiangying\-pip\-101 · 第328步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/jiangying-pip-101?attempt=attempt-002&step=328)。

**造任务：** 同一意图设置两个易混焦点：名称框与单元格、素材库与时间线、单个片段与整轨、多选与单选、主窗与附属面板。改变窗口位置、尺寸、缩放及对象排序；用同一个控件在不同App中的变体测试迁移。

**验收：** 动作前定位对象，动作后验证效果；误操作立即Undo并重新观察。考核的是选对对象和状态更新，不是背固定坐标。Driver明确“no key sent”的样本标工具阻塞，不强迫模型编造恢复成功。

### 优先级3：有限步骤的恢复与交付优先级

**证据与诊断：** DeepSeek GUI Keynote350个前端步骤、Word页面431步、WPS分类汇总621步仍未完成；Hybrid与Opus共同成功30题上，DeepSeek工具调用中位数71\.5，对方39。它愿意尝试、会探索接口，但常重复观测、换路、重新打开，恢复成本高。与此同时DeepSeek的同题墙钟中位数比Opus短，不能把多步问题误称为响应慢。[DeepSeek GUI · keynote\-report · 第350步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/keynote-report?attempt=attempt-002&step=350)；[DeepSeek GUI · word\-pages · 第431步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/word-pages?attempt=attempt-001&step=431)。

**造任务：** 从保存面板、失效引用、输入未提交、可控模态遮挡等可恢复状态开始；规定少量合理恢复动作后必须重新诊断，而不是无限重试相同失败动作。另设真正不可恢复的Driver错误，训练正确报告阻塞并保留现场。

**验收：** 按成功率、无效重复数、恢复到正确状态的动作数、是否保留已有成果评分；不硬设所有场景同一个步数阈值。截图/AX观察应有明确目的；已经满足目标后一次有针对性验收即可结束。

### 优先级4：原生结构、持久化和路线约束同时满足

**证据与诊断：** GUI Finder主体整理成功后使用shell核验造成路线fail；原生Table题存在歧义，必须先修任务再训练；Numbers原生坐标和导出坐标需要分别检查。问题不是要给每个App预装专门skill，而是让模型理解“用户要的结构/操作”和“文件里出现同样文字”不同。[DeepSeek GUI · finder\-archive · 第274步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/finder-archive?attempt=attempt-001&step=274)；[DeepSeek GUI · excel\-r002\-15 · 第204步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/excel-r002-15?attempt=attempt-001&step=204)。

**造任务：** 明确要求原生Table、TOC、透视表、图表数据源、指定原生分组/单变量求解；制作Hybrid和严格GUI成对题。两种模式业务目标相同，但核验方法都必须遵守各自限制。加入“已输入未提交”“界面改了但保存没生效”“原生正确而导出不一致”的对照。

**验收：** 结果、结构/指定方法、保存持久化、路线四项分别打标。Hybrid脚本路线单列；不能用它训练后声称学生学会了GUI。保存/提交的原生控件恢复需Driver支持，不能用模型训练掩盖L2缺口。

### 数据生产与验收建议

- **先做少量高质量成对样本，再扩量。** 同一输入制作“正确示范＋典型错误＋修复”三段；每类覆盖多个应用、不同窗口布局/数据规模。初期不建议按App平均铺量。

- **正例从验证后的片段开始。** 业务1也要审结构与路线；0分可保留正确中间操作，不能把整条轨迹当失败；null只说明无有效评估，不直接给训练成功标签。

- **单独隔离服务故障与工具不可恢复错误。** 429、图片超限、空响应、权限弹窗等先标清，避免训练模型在工具未执行时声称完成。

- **用留出的变体衡量迁移。** 以新数据、新窗口位置、其他App中的同类面板测试；主看任务语义成功、错误后恢复、约束遵守和无效重复，而非是否复现teacher的同一串坐标。

- **high配置重新建立基线。** 后续DeepSeek设high，固定输入、Driver与服务策略后再与本批medium比较；不能预先声称提高effort就能解决状态控制与纠错问题。

### 新增Astra后，怎样补齐学生对照数据

- **短路径对照：** Astra共同成功题调用中位数28\.5，DeepSeek71\.5。但不能把每条长轨都标负例；对同题定位完成必要动作，再比较重复观察、无效恢复、额外核验，按可删步骤和语义保持标注。

- **原生结构对照：** 从Astra创建Table及Opus验证Table中抽取“结构确实创建”的证据；先把题面改清楚，再制作变体。不要让学生靠猜评估器隐含结构得分。

- **严格GUI验收对照：** Astra的Word表格/修订/大纲、Excel查找/气泡图、Calendar是6个strict true候选；Sol另有3个。优先检查这些候选的完整动作、文件和最终界面，再提炼可迁移片段。

- **明确不可恢复的对照：** Astra剪映/WPS正确报告工具阻塞可用于训练诚实状态报告，但不是完成任务正例。真正的恢复正例需Driver修复后再生成。

训练验收拆成任务结果、约束遵守、错误恢复、保存持久化、无效重复五项；以新App/新窗口布局做留出集，不能只复现teacher坐标。

## 8\. Teacher选择：按训练目标选片段

|**训练用途**|**建议teacher**|**本批依据与限制**|
|---|---|---|
|Hybrid办公规划、原生结构、交付核验|Astra与Opus并列主候选，互相校验|共同31题各30成功；Opus有结构核验，Astra有更简洁路径。不能按总分单选|
|高效动作序列、减少无效操作|Astra优先，Sol对照|24道共同成功题Astra279\.1秒/28\.5叶调用，Sol309\.8秒/37次；仍需控制供应商与工具开销|
|严格GUI示范|优先审Astra6条与Sol3条strict true；DS1条可自举|Opus的现有GUI业务高分大量路线fail，需工具受限后重新生成|
|反证纠错、原生与导出一致性|同题真正完成修复的最佳片段，不绑定模型|Sol Numbers对照、Opus/Astra Table结构；不能直接采用底层包补丁作为通用操作|
|面板焦点、按键未发送的恢复|先修Driver，再同状态复测teacher|五模型都受相同底层阻塞，无证据证明某模型能稳定教会不可执行动作|
|剪映全流程|暂不选本批整轨为自动teacher|两模式共50次仍无业务1；Astra Hybrid部分结果通过但过程unknown，可人工核实片段，不能把null改成功|

**推荐方案：****Astra＋Opus作为Hybrid双主候选****，Sol提供效率/合规GUI对照，逐片段验收后再入库。** 现有证据不支持“Opus任何任务都最好”，也不支持“Astra原分高就全用Astra”。学生已掌握且严格验收通过的片段可以自举；服务故障、空分、方法歧义和工具未执行片段必须隔离。

teacher正例至少验证：业务语义正确、原生结构/指定方法符合、结果持久化、路线合规。评估器一次1分、模型自述完成、工具调用成功都不能单独替代这四项。

## 9\. 证据范围、链接与附件

保留八批旧报告；本版新增Astra100题原始result/score、完整前端步骤文本与CUA dispatch，并将500题统一成结果矩阵。11月13日重新读取旧八批的最新attempt、分数、状态及finished\_at，与此前审计一致，全部50题有终结记录。Astra Hybrid采用11月12日正式批；11月11日故障批不替换进来，另批Excel单题修复也不混算。没有修改原评分、任务包或启动重跑。

Astra Hybrid及既有6批引用开发机22337；GUI Sol/GLM沿用源端链接，Astra GUI当前开发机仍为上传中目录、未在API索引发布，因此使用data1的18081与UUID路由。所有新引用都与抓取的case/attempt/step对应；不声称尚未发布的开发机链接已可达。旧引用沿用此前验证的步骤证据，本版不声称重新逐页打开全部旧链接。

“共同可评”不能消除所有评估和供应商混杂；任务包哈希一致也不证明应用运行状态一致。频率仅是错误返回覆盖率，不是根因贡献率。本文没有全量逐图标注所有点击落点，因此不提供伪精确的grounding语义成功率。

附件：500行结果矩阵、操作偏好逐题表、配对样本与排除原因、案例步骤证据、统计口径与症状覆盖。

## 【附】null case针对性分析

以下可直接贴入附录。统计范围为十批中的 **92个 null**；“出现过某错误”不等于“该错误直接导致空分”。步骤链接均固定 `attempt-001`；非模型执行阶段的问题链接到 case，并注明应查看的日志阶段。

**1\. 【L2/L3】浏览器操作和观测超时，不能全部归为评估证据不足**

38个 Chrome null 中，19个出现过浏览器超时。其中13个涉及等待 daemon、6个涉及 `Runtime.evaluate`、7个涉及页面加载等待，类别有重叠。

**结论边界：** 已确认浏览器链路发生超时，值得检查集成、daemon响应和页面状态；尚不能统一归因于版本不匹配或某一个集成缺陷。错误中的“verify browser\-harness installation/upgrade”是提示，不是根因证据。

**2\. 【L2/L3】原生 Driver 超时后关闭连接，操作结果未知**

6个 null、8个前端步骤返回：

> `Driver timed out; outcome unknown. Connection closed; do not replay.`
> 
> 

代表证据：

- DeepSeek GUI · `chrome-ecmascript-1197`：[第178步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/chrome-ecmascript-1197?attempt=attempt-001&step=178)，调用 `TextEdit.getScreenshot()`，约32秒后返回上述错误。

- DeepSeek GUI · `numbers-formula`：[第63步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/numbers-formula?attempt=attempt-001&step=63)、[第123步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/numbers-formula?attempt=attempt-001&step=123)、[第147步](http://内网地址:22337/runs/first50_round1_codex_gui_deepseek_20261110/cases/numbers-formula?attempt=attempt-001&step=147)，多次出现同类返回。

**结论边界：** 这是连接和执行状态不确定性，区别于明确拒绝输入。后续应重新观察状态，不能假设前一步成功或直接重放；不能据此断言这些任务的 null 全由 Driver 导致。

**3\. 【L3】Agent 停止确认失败，阻断正常评分：4个 null**

四个 case 的 `controller_stop` 阶段均记录：

> `control.stop_unconfirmed`
> `Agent and control components were not confirmed stopped`
> 
> 

细分记录中，controller显示停止成功，但Agent返回 `Agent stop could not be confirmed`。

**证据位置：** 对应 attempt 的 `result.json → errors`，阶段为 `controller_stop`。这是生命周期日志，没有对应的模型步骤号。

**结论边界：** 直接故障是“停止状态未被确认”，不能进一步断言Agent进程确实残留，或模型业务操作未完成。

**4\. 【L3/L5】初始化失败，模型未开始执行：2个 null**

- [DeepSeek Hybrid · numbers\-chart](http://内网地址:22337/runs/first50_round1_codex_hybrid_deepseek_20261109/cases/numbers-chart?attempt=attempt-001)

- [GLM Hybrid · numbers\-chart](http://内网地址:22337/runs/first50_round1_codex_hybrid_glm_20261109/cases/numbers-chart?attempt=attempt-001)

两题的 `result.json → errors` 均显示：

> `stage: setup`
> `Task setup: failed`
> `code: guest.response_unavailable`
> 
> 

Agent为 `not_started`，前端模型步骤数为0。

**结论边界：** 这两次不能作为模型不会操作Numbers的证据。客体响应为什么不可用，仍需检查setup进程和客体日志，不能直接归为权限或模型问题。

**5\. 【L3/L5】Agent完成后，收集阶段被中断：1个 null**

Opus GUI · `wps-numfmt-101`：

- [第214步](http://内网地址:22337/runs/first50_round1_codex_gui_claude_20261109/cases/wps-numfmt-101?attempt=attempt-001&step=214)：Agent最终说明格式已设置，并披露使用Finder复制重命名绕过另存为输入。

- 归档已包含 **10,295字节的 ****`output.xlsx`**，独立检查发现 `000000` 及红色负数格式。

- `result.json → errors` 在 `agent_collection` 阶段记录 **`KeyboardInterrupt`**；原评分为 `not_run/null`。

- 后续resume保留已settled记录，没有补跑或补评该题。

**结论边界：** 可以确认“产物已收集，但后续收集／轨迹审计被中断”。批次同时有低磁盘止损记录，但单题证据不足以独立证明这次中断的具体触发者。因此，上条回复直接称其为“磁盘止损导致”过于确定，应改为上述表述。

**6\. 【L3】413请求体过大后持续重试，最终超时**

[GLM GUI · chrome\-attractions\-016](http://内网地址:18081/runs/0886f578-ddc3-4722-bd75-ffc03c7c5ccd/cases/chrome-attractions-016?attempt=attempt-001)

`result.json → agent.errors` 记录多次：

> `413 Payload Too Large: Request body too large. Please reduce the request body size.`
> 
> 

重连记录从2/8持续到6/8，最终Agent状态为 `timeout`；评分阶段另有 `Judge HTTP 400`。

**结论边界：** Agent请求413与Judge请求400是两个阶段的问题，不能合并为一次评估错误。现有证据支持检查请求字节预算和413后的重试策略，但尚未证明每次重试的请求体完全相同。

**7\. 【L3】模型通道503及平台数据库故障，不能只统计429**

**证据位置：** 各case的 `result.json → agent.errors`，不以最后一个模型步骤代替服务错误记录。

**8\. 【L1／接口使用】浏览器JS参数错误反复出现，缺少有效纠正**

这个我之后在round2禁了browser\.evaluate

GLM Hybrid · `chrome-attractions-016` 在15个前端步骤中出现同类参数错误：

> `browser_jsArguments.expression`
> `Input should be a valid string`
> `input_type=list`
> 
> 

- [第63步](http://内网地址:22337/runs/first50_round1_codex_hybrid_glm_20261109/cases/chrome-attractions-016?attempt=attempt-001&step=63)：同一cell先用普通字符串执行点击并返回按钮HTML，随后用模板标签形式 `tab.evaluate` 调用观测，触发list/string类型错误。

- [第92步](http://内网地址:22337/runs/first50_round1_codex_hybrid_glm_20261109/cases/chrome-attractions-016?attempt=attempt-001&step=92)：仍出现相同类型校验错误。

**结论边界：** 已确认模型反复使用不被接口接受的调用形式，恢复没有有效收敛；也说明“cell报错”不等于其中所有动作都未执行。是否还存在文档或兼容性问题，需要另查，不能直接归为browser集成实现缺陷。

以上步骤号已与本地保存的前端步骤记录核对；链接沿用综合报告使用的开发机或源端入口，本次未重新逐一验证在线可达性。

