# First50 Round2 · DeepSeek Hybrid 轨迹分析

批次：`first50_round2_codex_hybrid_deepseek_20261113`
被测模型：`deepseek-v4.1-flash-1017/huoshan/huoshan`；分析日期：2026\-11\-17。
审查范围：50题冻结配置、评分与前端轨迹，逐题分析8个零分和14个空分；对关键Excel/PPTX产物及评估代码做独立核对。未改评分、未重跑。

**原始结果28个1分、8个0分、14个null。8个零分中有1个已复现的评估误判；14个null中9个Chrome任务卡在评估容量限制。DeepSeek真正需要训练的重点是：输入保护、精确参数与舍入、按完整要求核验，而不只是增加检查次数。**

前端说明：检查时开发机22337尚未收录本批，当前使用[mac3源前端](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113)。该源前端不支持step查询参数，因此链接定位case、文字给出准确前端步骤号；没有将尚不可用的开发机URL伪装成已验证深链。开发机迁移后可替换为 `…/cases/<task>?attempt=attempt-001&step=N`。Judge内部 `step-N` 不是前端步骤号。

## 实验配置

|**配置项**|**本次实验配置**|
|---|---|
|实验批次|first50\_round2\_codex\_hybrid\_deepseek\_20261113|
|任务集|First50，50题、11个应用；Round2 Hybrid冻结包|
|执行模式|Hybrid，允许GUI与CLI结合；指定应用、原生结构、输入保护和任务方法仍须满足|
|被测模型|deepseek\-v4\.1\-flash\-1017/huoshan/huoshan；期望响应模型deepseek\-v4\-1\-flash\-261017|
|推理配置|reasoning\_effort=high，reasoning\_summary=auto；本批最终交付记录确认原始请求均为high|
|评估模型|gpt\-6\-astra/azure/sfa，结合代码检查和rubric判定|
|执行环境|mac3宿主机上的macOS VM；4 CPU、8192MiB内存|
|镜像|personal\-600dd38017b0468e883308dffc0e2357|
|Agent与GUI工具|Codex CLI 0\.153\.4；CUA REPL；Driver 0\.38\.0|
|浏览器|集成CUA的DOM/GUI功能可选；browser JavaScript/evaluate禁用，web\_search禁用|
|并发数|1|
|单任务时限|Agent最多3600秒，不含初始化、评估、清理|
|框架与任务基线|固定Round2 79fdce1a；本批50题task\_sha256与Claude Round2全部一致|
|mac3任务包|/Users/user/git\_repo/mac\-cua/local\-tasks/first50/79fdce1a\-20261113/hybrid|

## 1\. 统计结果

**有效评分成功率28/36＝77\.78%；全任务得分率28/50＝56%。** null单列，不当作0分，也不当作成功。Agent状态为47个completed、2个timeout、1个agent\_error；其中剪映画中画虽completed，却只回复计划、没有执行。

|**应用**|**1分**|**0分**|**null**|
|---|---|---|---|
|chrome|1|0|9|
|excel|12|3|0|
|word|5|0|0|
|wps|5|0|0|
|numbers|1|1|0|
|powerpoint|2|0|2|
|keynote|0|1|0|
|preview|0|1|0|
|finder|1|0|0|
|calendar|1|0|0|
|jiangying|0|2|3|
|**合计**|**28**|**8**|**14**|

- 首题开始至末题结束：北京时间11月16日14:00:18至11月17日01:28:57，约 **11小时28分39秒**；最终交付四舍五入为11小时28分40秒。未发现需要剔除的中断段。

- 50题Agent阶段累计 **10小时16分02秒**，包含工具执行、推理及响应等待，不是纯推理时长。

- 本批最终交付的原始响应口径：输入253,189,616、cached输入247,448,448、缓存写入0、输出1,000,153、推理输出511,702；3,579次请求、3,567次完成、3,545次工具调用。6题session累计与原始响应累计不一致，沿用原始响应口径，不能与session字段混加。

- 最终交付截图口径：逐题去重1,267，图片引用62,586；引用数包含同图多次进入上下文，不能称为“拍了62,586张截图”。以上用量取本批最终交付记录，本次重点复核任务语义与归因，未重复全量响应用量扫描。

- `verify.valid=true/errors=[]` 说明材料封存通过；`all_requirements_met=false/exit_code=1` 不等于所有任务完成或所有业务成功。

**评分可信度：** 食品库存排序的0分已独立复现为日期表示误判，报告保持原分，单列真实语义结论。不能据此将其他0分或null顺手改判。

**与Claude Round2的比较边界：** 两批50题冻结task\_sha256一致，镜像ID和工具版本一致，但宿主机、调用服务、时段与实际运行状态不同。双方都有有效分的32题中，26题双方1分、5题DeepSeek为0而Claude为1、1题双方0；这5题中包含食品库存误判。应逐题比较，不能直接用28对40或77\.78%对97\.56%概括完整能力差距。

## 2\. 8个原始0分case：失败与误判分开

### 2\.1 【L1 输入目标判断与核验；前期伴随L2菜单路由】excel\-r002\-2：排序和原生Table正确，但订单号被覆盖

**真实缺失是原始记录被改坏，不是没建Table。** 归档XLSX有原生Table `A1:E6`，数量48、32、20、12、7也正确；但最大订单的 `HC-101` 被写成了 `A1:E6`。第16步本想向名称框输入选区地址，之后排序菜单已出现异常的 `A1:E6` 表头选项；模型注意到异常却继续。第61步读取磁盘原文件时订单号尚正确，但那时内存编辑尚未保存。第63步重新粘贴了正确的完整记录，第65步又点击同一坐标输入 `A1:E6`；返回AX的名称框值却是 `A3`，并未确认范围输入成功。这是最终订单号被覆盖前最直接的可疑操作，模型随后仍继续建表。第84步最终检查没有解析sharedStrings，输出的是字符串索引，因而漏掉已写入的错误订单号。0分成立。

[excel\-r002\-2，前端第16、26–27、61–66、84–86步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-r002-2?attempt=attempt-001)。第28–52步确有TargetUnverified、窗口变化、菜单/排序面板焦点冲突，但它们不能解释或免除最终记录核验遗漏。训练应加入“输入框定位失败后，选区文字误入数据单元格”的反例，保存前后按主键逐行对比。

### 2\.2 【L1 数值计算与独立验证】excel\-air：杭州Co均值的舍入错一位

**输出Result\!G4是0\.61，精确均值是0\.615，题面要求四舍五入两位，应为0\.62。** 独立读取180行输入，其中杭州30行Co合计18\.45，Decimal计算及ROUND\_HALF\_UP得到0\.62。第8步使用 `round(sum(float(...))/len(...),2)` 得到0\.61，后续将其写入结果并用同一批计算值核验，未发现差异。最终归档结果与冻结期望的关键差异由此确认；不是中文渲染、CSV输出路径或保存失败。

[excel\-air，前端第8、98、109–115步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-air?attempt=attempt-001)。应训练十进制边界值、舍入方式和独立oracle；“脚本算过一次”不等于计算语义正确。

### 2\.3 【L1 输入保护与恢复】preview\-packet：先编辑源PDF，再另存为，源文件已被自动保存修改

**直接失败是main\.pdf被改动，违反“不改输入”。** 第10步规划直接在main文档编辑，约第52步才另存output；第60–61步文件检查发现main从3,824字节变为32,947字节，模型识别出Preview自动保存。之后Undo恢复页数、顺序及倒置页面，第97步再次保存源文件，恢复了可见内容，却没有恢复原始字节。评估的 `input:main.pdf=false`、`input:appendix.pdf=true` 与此吻合。第100步模型已明确意识到“语义恢复可能不等于哈希恢复”，后续仍耗时探索重建原PDF。

[preview\-packet，前端第10、52、60–61、95–100、137–142步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/preview-packet?attempt=attempt-001)。应训练编辑前先复制或另存工作副本，以及输入文件哈希/备份保护；这不是让模型学习事后猜原始PDF生成器。

### 2\.4 【L1 要求绑定与检查遗漏；执行终止为时限耗尽】keynote\-report：把图表标题放成了页面标题

**第二页应叫“规划支持”，图表应叫“项目完成情况”；模型把第二页标题改为“项目完成情况”，图表没有设置要求的标题。** 第2步已读到三个正确页面标题；归档PPTX却是“新业务联动 / 项目完成情况 / 能力建设”，图表XML有 `autoTitleDeleted=1`。第254步读回这些标题时，模型只关注多余的Region 2系列，并在第268步删除；第289、295步检查系列、页数和备注，仍漏掉标题对象绑定错误。

[keynote\-report，前端第2、254–255、268–272、289–295步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/keynote-report?attempt=attempt-001)。3600秒到时被监督器停止，但即使多给时间、直接回复完成，现有标题仍不符合要求。评估另将C03数据项判false；最终提交PPTX的单系列Q1/Q2/Q3、4/7/9已能读到，**C03仍需比较原生重导出和检查实现，不能把这一项直接认作模型数值错误**；已确认的C01/C02缺失足以导致0分。

本题295个前端条目、147个工具调用；可见工具执行累计约362秒，其余时间包含推理、模型响应等待及调度。未见本题413或模型重连耗尽，不能写成“模型服务一次卡住一小时”。

### 2\.5 【L2 观察/输入阻塞；L1恢复不收敛】numbers\-formula：长期观察失败，超时前仍未交付原生文件

**与Claude同题有共同底层症状，不能全归为模型能力。** 第16步创建空白文档后的组合调用即Driver超时；第22步AX不可用，第24、40、63步再次超时。后续偶尔读到AX，但点击或按键仍出现TargetUnverified、焦点校验拒绝等。模型不断重启、读接口实现、探查导入缓存，直到第489步才生成最终XLSX，第496步在Numbers中打开，第498–500步检查临时导入的numbers文件；未将要求的原生文件保存到交付路径，评估 `missing_native_output`。

[numbers\-formula，前端第16–24、40、63、192、278、489–500步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/numbers-formula?attempt=attempt-001)。本题500条前端步骤、259次工具调用，可见工具执行累计约2,537秒，占一小时时限约70%；这是工具观测/输入阻塞加恢复探索，不是单纯模型调用慢。L1可优化点是设定恢复分支和退出条件；L2需复现“首次可读、刷新不可读”的AX/窗口关系。不能仅凭 `focused=false` 断言Driver校验过严，也不能把它称为pressKey键值映射错误。

### 2\.6 【L1 计划后未执行】jiangying\-pip\-101：只有一条开工声明

**约4秒结束、0个工具动作，没有创建草稿。** 唯一前端条目是“我会先检查素材与剪映当前状态……”，随后Agent状态completed；未发现目标草稿JY\_画中画。不是操作了但被焦点问题阻塞，也不是3600秒超时。现有记录最直接支持模型把计划当作本轮最终回复；没有工具错误或模型传输错误证据，不扩大推断为服务故障。

[jiangying\-pip\-101，前端第1步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/jiangying-pip-101?attempt=attempt-001)。训练需覆盖“行动请求→实际调用→观察结果→结束”，并在评测侧单独标注无动作完成。

### 2\.7 【L1 时间线尺度识别与参数核验】jiangying\-text\-101：以坐标推算代替实际时长确认

**要求文字0–5秒，最终约0–6\.2秒，超出5±0\.3秒容差。** 第162步截图的文字右边缘已超过6秒刻度；第163步模型却用估计的像素刻度认定右边缘“=5\.0”，第171步继续认为时长满足要求，最后保存返回首页。此次复核直接查看了第162步时间线截图，与评分的约6\.2秒一致；正文、渐显0\.5秒和草稿名均通过，失败集中在文字片段长度。

[jiangying\-text\-101，前端第162–163、170–171、220–222步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/jiangying-text-101?attempt=attempt-001)。需训练缩放后重新读刻度、拖动后核验结束时间，优先读取精确数值；不能仅因点击/拖动返回成功就确认时长。

### 2\.8 【L4 评估误判】excel\-r001\-26：日期表示变了，排序与整行内容没有错

**归档结果已按日期升序，所有六条记录关联字段正确，0分来自比较方式。** setup快照把日期存成“2026\-10\-18”等字符串；Excel保存后用标准日期序列值46313等存储，并保留日期格式 `yyyy-mm-dd`。冻结 `office.sheet_data()` 读取原始值，`check_excel()` 对整个rows做严格相等，没有根据日期样式及工作簿日期系统归一化。

独立复现：对归档XLSX调用原检查函数得到False；只将C列日期序列转换为相应ISO日期、其他内容不变，再调用得到True。第65、80步模型也已读回全部行并核验日期。**本题不作为DeepSeek训练弱项，保留原始0分并标注误判。** 应修日期语义解析，并覆盖1900/1904日期系统及合法日期单元格类型，不能要求模型把日期强制转文本来迎合评估器。

[excel\-r001\-26，前端第65、80–82步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-r001-26?attempt=attempt-001)。

## 3\. 14个null：评估链路问题

### 3\.1 【L4 单步证据分块】8题Chrome：未调用Judge便超限

Domesday、GPU、Baseball、Landmarks、ECMAScript、Vulnerabilities、Aircraft、Churches均记录 `Single step exceeds text budget; cannot silently truncate evidence`，`judge_calls=0`。这是确定的评估打包失败，不能把这8题统一归为模型任务失败。

代表Domesday第12步返回长页面状态，前端序列化工具输出约5\.9万字符；这是可定位的大块观测，最终评分日志确认有单步超限，但具体计费文本长度及触发项应以冻结分块实现为准。修复方向是对单步中的长DOM/AX按结构切分、保留来源，输出超限证据ID、大小和阈值，不能静默截断或改判0。

[chrome\-domesday\-1415，前端第12步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/chrome-domesday-1415?attempt=attempt-001)。这8题即使模型completed也不等于都完成了网站要求；修复评估后再判定，不能直接补8个成功。

### 3\.2 【L4 综合评审预算；另有L3请求过大】chrome\-attractions\-016：1题，两种故障独立存在

评分已调用Judge16次，最终 `Synthesis budget exceeded`，因此null。与此同时，Agent在第243步以后发生模型请求 `413 Payload Too Large: Entry too big`，重试至8/8后agent\_error。**Agent停止原因和评分空分原因不同。** 现有记录无法确认413究竟由图片数、单条文本、整个请求体或网关内部entry阈值触发，不能直接写成“图片超过50张”。

[chrome\-attractions\-016，前端第233–243步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/chrome-attractions-016?attempt=attempt-001)。评估侧应限制并分层汇总评审材料；框架侧应记录请求大小及组件占比，并对确定性的413避免原样重复发送。不能以评估器出错掩盖Agent事实上也被中断。

### 3\.3 【L4 最终复核选择不完整】剪映音频、PowerPoint图表：2题

两题代码检查通过，但最终复核只附一张原始图、没有原始动作，无法支撑之前的完整完成结论。已直接核对请求体：音频 `call-010.request.json` 为 `steps=[]`、仅 `image-0035`；PowerPoint图表 `call-009.request.json` 为 `steps=[]`、仅 `image-0018`。这不是说原轨迹没有后续证据，而是最终复核没有带齐。

代表剪映音频：前端第119步重启、第121步有最终首页观察，第123步完成回复；最终Judge拿到的却是另一张首页图，无法验证时间线、\-5\.6dB和最终持久化。应把待复核条目的动作及后续图片一起回收；不能让单张中间截图承担全程判定。最终复核未带齐原始证据的问题可以确认，但任务是否最终全部合规仍需重新评估。

[jiangying\-audio\-101，前端第119–123步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/jiangying-audio-101?attempt=attempt-001)；[powerpoint\-r001\-19，前端第109–113步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/powerpoint-r001-19?attempt=attempt-001)。

### 3\.4 【L4 过程/禁止行为覆盖；部分关联L1核验和L5应用状态】3题

**剪映叠化、变速、PowerPoint隐藏页。** 叠化的顺序、转场、1秒及返回首页均pass，仅全程禁止行为unknown；变速还缺少末段原速/曲线变速相关参数的完整核验。不能把“未证明没有违规”改写成“实际违规”。PowerPoint隐藏页的内容和放映跳过已被观察，但最终截图同时出现WPS同名文稿与桌面授权，指定应用条目unknown；有替代应用窗口不等于已经证明它参与编辑。

代表PowerPoint第76步放映跳过隐藏页，第78步返回编辑；未发现足以确定WPS用途的证据。应将应用启动来源、打开/编辑/保存动作与最终文件关联起来，按行为判断指定应用要求，不只看进程是否存在。

[powerpoint\-r001\-13，前端第76–80步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/powerpoint-r001-13?attempt=attempt-001)。剪映应继续按完整行为与效果判定禁止项，同时为“关键参数已展示后回首页”保留有效证据，避免强求首页同时显示全部编辑参数。

**此外，2\.8的食品库存日期误判也是L4问题，但它是原始0分，不重复计入14个null。**

## 4\. 其他未造成直接失败的问题与训练方向

### 4\.1 【L1】模型层：能够推导与核验复杂结构，弱在核验范围和纠错收敛

**强项：愿意检查数据和原生结构，能修正自己的检查脚本。** 5个Word、5个WPS全部1分，15个Excel中12个原始1分，另有食品库存语义完成但误判。`word-table` 第71步回读原生表格、4×2内容及重复表头；`excel-pivot` 第413步审计误把总计行算成SKU，第414步识别问题，第416步修正审计并核对29个SKU。这些表明它并非不会推理或不会办公。

[word\-table，前端第71–76步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/word-table?attempt=attempt-001)；[excel\-pivot，前端第413–418步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-pivot?attempt=attempt-001)。

**弱项一：检查很多，但没有按完整要求检查。** 订单任务查Table范围和数量序，却没解码订单号；Keynote查系列、页数和备注，却没核对三个页面标题和图表标题各自属于哪个对象。应训练“题目约束→检查项→证据→最终声明”的对应关系，检查独立于生成过程，避免只复述自己做过的动作。

**弱项二：遇到反证时会合理化或转向旁枝。** 订单中出现异常 `A1:E6`，仍继续建表；Preview发现输入已变更后，又尝试推测原文件生成方式，而不是清晰界定恢复失败。应训练先暂停后续操作、定位最小差异和可恢复范围，不让额外探索覆盖原始问题。

**弱项三：界面参数依靠估计，缺少操作后的精确读回。** 剪映文字的时间线误读是明确例子；不能将它笼统扩大为所有坐标点击都不准。应区分坐标命中、控件响应、参数提交和任务数值四层。

**弱项四：工具会话与恢复路径仍有成本。** 16/50题实际工具返回出现SyntaxError；28/50题StaleElement、21/50题坐标需要新截图。后两项同时受Driver契约和状态变化影响，不能全部算L1。Numbers一小时内259次调用仍未保存，是底层阻塞叠加恢复策略不收敛；Keynote147次调用最终核验仍漏要求，则更偏核验设计。

**路线倾向只给可复核的窄口径：** 50题中34题首个工具是CUA `js`，15题是 `exec_command`，1题没有工具。首工具常是初始化或读输入，不能等同于“34题纯GUI、15题CLI完成”。本批经常使用GUI完成原生编辑、CLI读文件验证；不要用REPL里出现JavaScript语言判断执行了被禁用的页面JavaScript。

**面向训练DeepSeek的造数据方向（DeepSeek是被训练模型，不是teacher）：**

1. **输入目标与不可变字段保护，优先级最高。** 构造名称框/单元格易混、输入源自动保存的任务；要求编辑前建副本或基线，操作后逐字段对比。验收同时检查输出正确和源数据/主键未变。对应订单、Preview。

2. **精确数值与尺度变化。** 构造0\.005边界均值、百分比/dB转换、缩放后的时间线端点；要求读取真实刻度/参数，使用十进制半入规则。对应空气质量和剪映文字。

3. **对象和要求的绑定。** 题目同时包含页面标题、图表标题、系列名、文件名；加入“文字都存在但放错对象”的负例。对应Keynote；验收按对象关系而非全文包含。

4. **完整而独立的核验。** 给出结构正确但一条主键损坏、结果正确但输入被改、参数输入未提交的状态，要求找到反证并修复。应奖励最少必要检查，不奖励日志长度和无限重开。

5. **有界的GUI恢复。** 从可复现的StaleElement、菜单附属窗口、截图失效开始，训练刷新观察、明确窗口与坐标系、单步恢复。Driver不可恢复的案例作为“识别并报告阻塞”样本，不要求模型学会绕过输入校验。

6. **计划到执行及终止判断。** 行动请求必须进入工具动作；完成声明必须有结果证据。加入“只有计划”和“满足条件后仍扩展任务”的对照。

数据筛选：原始1分仍需检查；食品库存零分可作正确执行＋错误评分的分析样本，不能当作负例动作；null暂不作为成功标签。Teacher应按子能力选，优先使用已验证的短恢复或完整核验片段；Claude同题也有Numbers工具阻塞，不应把其所有轨迹默认当标准答案。

### 4\.2 【L2】CUA Driver：高频仍是状态变化、引用失效与附属面板

下表统计实际工具返回中对应错误文本的case数及出现次数；一个case可命中多类，**不是Driver缺陷数，也不是单步语义失败率**。

|现象|case数/50|返回次数|代表证据|
|---|---|---|---|
|StaleElement|28|54|[chrome\-chemistry\-1290，前端第64步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/chrome-chemistry-1290?attempt=attempt-001)|
|WindowChanged|19|58|[excel\-clean，前端第17、285步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-clean?attempt=attempt-001)|
|截图未刷新|21|24|[excel\-lookup，前端第14步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-lookup?attempt=attempt-001)|
|AttachmentUnverified|10|20|[excel\-clean，前端第134、148步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-clean?attempt=attempt-001)|
|TargetUnverified|9|16|[keynote\-report，前端第87步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/keynote-report?attempt=attempt-001)|
|坐标越界|3|5|[excel\-bubble，前端第216、252、372步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-bubble?attempt=attempt-001)|
|焦点验证拒绝|2|2|[numbers\-formula，前端第278步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/numbers-formula?attempt=attempt-001)|
|Driver超时|3|14|[numbers\-formula，前端第16、24、40步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/numbers-formula?attempt=attempt-001)|
|不支持点击参数|2|4|[numbers\-formula，前端第107、371步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/numbers-formula?attempt=attempt-001)|

**优先修复菜单/面板观测与动作指向不一致。** 订单题第30步重新观察菜单后，第32步局部坐标点击仍报root coordinate frame changed；第38步按键又被告知焦点在“排序”窗口。这类已经刷新仍无法行动的片段值得做Driver复现包。接口应一起给出截图坐标系、AX所属窗口、实际输入目标和可执行的恢复入口，而不是只说“重新观察”。

[excel\-r002\-2，前端第28–38、44–52步](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-r002-2?attempt=attempt-001)。

**pressKey专项：** Numbers第278步因焦点验证拒绝；这只能说明输入路由未通过，不能证明键值映射错。复测要记录是否实际发送、发给哪个窗口及应用前后状态。Browser集成也需单独观察页面引用与原生保存面板间切换，不能把所有DOM或AX错误统称为模型grounding差。

### 4\.3 【L3】框架：请求大小与结束状态需要明确区分

Chrome attractions的413已造成直接中断，见3\.2，不重复算新增问题。对于这种确定性超限，原样重试8次无法恢复，应报告请求体、文本、图片组件大小，并采用受控上下文压缩或明确失败；不能静默删关键证据。

另一个低成本可做的诊断是标出“completed但无任何工具动作”，以便识别剪映画中画这种只有开工声明的执行。诊断不应自动重跑或自动改分。`timeout`也应区分模型等待与工具等待：本轮Numbers的工具阶段占比很高，Keynote则主要时间在工具外；工具外时间不是已确认的模型服务故障。

### 4\.4 【L4】任务与评估：优先三项，不泛化改所有任务

**Excel库存：修日期语义比较。** 已复现误判，优先级明确；结合单元格样式和1900/1904日期系统解析，保留行关联一致性检查。题面无需改成“日期必须文本”。

**Chrome：修长证据的单步分块和综合预算。** 9/10题null都与容量处理有关，导致本批几乎无法从分数评估浏览器能力。优先修这一共性问题，再考虑按任务细调rubric。

**剪映/PowerPoint：修原始证据回收及过程覆盖判断。** 音频和图表已找到仅附一张图的最终复核请求。禁止事项和指定应用应按真实操作及结果判定，不能用“另一个应用窗口存在”直接判违规，也不能把缺少覆盖直接当成功。

空气质量的四舍五入、Keynote的两个标题和原生图表、剪映的5秒区间、Preview的不改输入，题面已明确；本批没有证据表明需要削弱这些要求。Keynote C03与最终导出的一致性另需复核，不能在没有查清原生重导出结果前归罪模型或直接改分。

### 4\.5 【L5】镜像/环境：只保留已见现象，不猜资源瓶颈

PowerPoint隐藏页评分记录的WPS同名文稿与桌面授权提示，说明任务最终应用状态仍有歧义，值得复测应用默认关联、启动路径和TCC授权。现有轨迹不能证明是模型主动用WPS替代，也不能仅因有权限弹窗就判定保存失败。

Numbers的持续AX不可用与Claude同题同类故障相呼应，应联合Driver检查窗口和应用兼容性；尚没有CPU、内存或宿主资源证据支持“mac3资源不足”这一根因。其余环境问题不在本报告扩展罗列。

## 附录A：50题结果明细

保留冻结run任务顺序。Agent秒数不含初始化、评估、清理；前端条目包括推理/回复/工具，不等于工具次数。

|任务|原始Score|Agent状态|Agent秒数|前端条目|核心备注|
|---|---|---|---|---|---|
|[chrome\-domesday\-1415](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/chrome-domesday-1415?attempt=attempt-001)|null|completed|125\.6|53|单步证据超限，Judge未调用|
|[chrome\-gpu\-970](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/chrome-gpu-970?attempt=attempt-001)|null|completed|201\.4|80|单步证据超限，Judge未调用|
|[chrome\-chemistry\-1290](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/chrome-chemistry-1290?attempt=attempt-001)|1|completed|148\.3|81|原始评估通过|
|[chrome\-baseball\-3604](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/chrome-baseball-3604?attempt=attempt-001)|null|completed|329\.5|107|单步证据超限，Judge未调用|
|[chrome\-landmarks\-1134](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/chrome-landmarks-1134?attempt=attempt-001)|null|completed|1931\.4|468|单步证据超限，Judge未调用|
|[chrome\-ecmascript\-1197](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/chrome-ecmascript-1197?attempt=attempt-001)|null|completed|277\.3|98|单步证据超限，Judge未调用|
|[chrome\-vulnerabilities\-2887](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/chrome-vulnerabilities-2887?attempt=attempt-001)|null|completed|590\.8|129|单步证据超限，Judge未调用|
|[chrome\-aircraft\-4426](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/chrome-aircraft-4426?attempt=attempt-001)|null|completed|443\.2|162|单步证据超限，Judge未调用|
|[chrome\-attractions\-016](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/chrome-attractions-016?attempt=attempt-001)|null|agent\_error|1916\.1|243|Agent 413＋评估汇总超限|
|[chrome\-churches\-033](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/chrome-churches-033?attempt=attempt-001)|null|completed|458\.2|121|单步证据超限，Judge未调用|
|[excel\-r001\-26](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-r001-26?attempt=attempt-001)|0|completed|272\.8|82|日期序列/文本比较误判；语义已核对|
|[powerpoint\-r001\-13](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/powerpoint-r001-13?attempt=attempt-001)|null|completed|157\.8|80|指定应用过程证据unknown|
|[powerpoint\-r001\-19](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/powerpoint-r001-19?attempt=attempt-001)|null|completed|526\.1|113|最终复核仅一张中间图|
|[powerpoint\-r001\-26](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/powerpoint-r001-26?attempt=attempt-001)|1|completed|176\.1|75|原始评估通过|
|[excel\-r002\-2](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-r002-2?attempt=attempt-001)|0|completed|262\.7|86|订单号被A1:E6覆盖|
|[excel\-r002\-14](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-r002-14?attempt=attempt-001)|1|completed|284\.4|85|原始评估通过|
|[excel\-r002\-15](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-r002-15?attempt=attempt-001)|1|completed|90\.3|37|原始评估通过|
|[excel\-r002\-21](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-r002-21?attempt=attempt-001)|1|completed|207\.3|60|原始评估通过|
|[powerpoint\-r002\-5](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/powerpoint-r002-5?attempt=attempt-001)|1|completed|78\.0|32|原始评估通过|
|[wps\-absref\-101](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/wps-absref-101?attempt=attempt-001)|1|completed|1494\.8|270|原始评估通过|
|[wps\-goalseek\-101](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/wps-goalseek-101?attempt=attempt-001)|1|completed|466\.4|132|原始评估通过|
|[wps\-outline\-101](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/wps-outline-101?attempt=attempt-001)|1|completed|373\.1|89|原始评估通过|
|[wps\-subtotal\-101](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/wps-subtotal-101?attempt=attempt-001)|1|completed|1010\.4|223|原始评估通过|
|[wps\-numfmt\-101](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/wps-numfmt-101?attempt=attempt-001)|1|completed|604\.1|126|原始评估通过|
|[jiangying\-transition\-101](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/jiangying-transition-101?attempt=attempt-001)|null|completed|867\.4|118|禁止行为覆盖unknown|
|[jiangying\-speed\-101](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/jiangying-speed-101?attempt=attempt-001)|null|completed|2857\.2|161|末段参数及禁止项unknown|
|[jiangying\-text\-101](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/jiangying-text-101?attempt=attempt-001)|0|completed|1187\.0|222|文字约6\.2秒，要求5秒|
|[jiangying\-pip\-101](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/jiangying-pip-101?attempt=attempt-001)|0|completed|4\.4|1|仅计划，无工具动作|
|[jiangying\-audio\-101](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/jiangying-audio-101?attempt=attempt-001)|null|completed|664\.6|123|最终复核仅一张首页图|
|[excel\-air](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-air?attempt=attempt-001)|0|completed|339\.3|115|0\.615误舍入为0\.61|
|[excel\-validation](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-validation?attempt=attempt-001)|1|completed|407\.3|125|原始评估通过|
|[excel\-pivot](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-pivot?attempt=attempt-001)|1|completed|1146\.7|418|原始评估通过|
|[excel\-lookup](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-lookup?attempt=attempt-001)|1|completed|363\.5|93|原始评估通过|
|[excel\-percentiles](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-percentiles?attempt=attempt-001)|1|completed|270\.0|75|原始评估通过|
|[excel\-clean](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-clean?attempt=attempt-001)|1|completed|1416\.2|344|原始评估通过|
|[excel\-window](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-window?attempt=attempt-001)|1|completed|128\.8|43|原始评估通过|
|[excel\-bond](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-bond?attempt=attempt-001)|1|completed|590\.1|152|原始评估通过|
|[excel\-debug](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-debug?attempt=attempt-001)|1|completed|291\.9|80|原始评估通过|
|[excel\-bubble](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/excel-bubble?attempt=attempt-001)|1|completed|2020\.3|428|原始评估通过|
|[numbers\-chart](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/numbers-chart?attempt=attempt-001)|1|completed|906\.6|245|原始评估通过|
|[numbers\-formula](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/numbers-formula?attempt=attempt-001)|0|timeout|3601\.5|500|AX/输入长期受阻，缺原生输出|
|[word\-outline](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/word-outline?attempt=attempt-001)|1|completed|515\.6|154|原始评估通过|
|[word\-pages](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/word-pages?attempt=attempt-001)|1|completed|230\.9|84|原始评估通过|
|[word\-table](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/word-table?attempt=attempt-001)|1|completed|183\.3|76|原始评估通过|
|[word\-revision](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/word-revision?attempt=attempt-001)|1|completed|553\.2|186|原始评估通过|
|[word\-illustrated](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/word-illustrated?attempt=attempt-001)|1|completed|473\.3|152|原始评估通过|
|[keynote\-report](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/keynote-report?attempt=attempt-001)|0|timeout|3601\.1|295|页面/图表标题错位；时限耗尽|
|[preview\-packet](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/preview-packet?attempt=attempt-001)|0|completed|947\.3|142|main\.pdf被改动|
|[finder\-archive](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/finder-archive?attempt=attempt-001)|1|completed|701\.3|120|原始评估通过|
|[calendar\-reschedule](http://内网地址:18081/runs/first50_round2_codex_hybrid_deepseek_20261113/cases/calendar-reschedule?attempt=attempt-001)|1|completed|267\.1|59|原始评估通过|

## 附录B：证据与复核范围

- 原始run在mac3：`/Users/user/git_repo/mac-cua/results/first50_round2_codex_hybrid_deepseek_20261113`。

- 直接复核：50题result/score/task、前端文本与工具错误；关键截图为剪映文字第162步。没有声称逐帧观看全部录像。

- 下载并只读解析了三个Excel零分产物、Keynote最终PPTX、空气质量输入；用冻结office检查函数复现食品库存误判。日期归一化只用于本地诊断内存数据，没有修改产物、评分或评估器。

- 两个薄证据最终复核请求已直接检查内容；Judge内部证据序号与前端步骤号分开。

- 已确认事实、评估器记录、模型自述和未确认假设在正文区分。错误索引为同目录 `error-index.json`，包含全部命中的任务与前端步骤。

