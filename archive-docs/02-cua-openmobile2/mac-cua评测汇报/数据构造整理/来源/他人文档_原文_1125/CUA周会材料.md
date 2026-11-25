# CUA周会材料

## 11\.25

### 框架 @刘一晨

**Done**

1. v2\.0版本集成到xhx @林强

2. 集群@孙伟鑫

    1. E2B接口对接

    2. mac集群接入公司网线

3. v3\.0版本更新：

    1. 对于提示词小窗口的问题 @陈瀚

    2. 系统层级权限确认弹窗提示@陈瀚

    3. finder的右键菜单栏操作

    4. 不同层级窗口的background操作测试

    5. wps某系窗口不支持axpress操作的fallback

**TODO/ON**

* [ ] 新版本的driver接入xhx@林强

* [ ] E2b提供测试样例@孙伟鑫

* [ ] driver层级未修复的bug

    * [ ] 剪映系统drag任务过于严格的检测@林强

    * [ ] ps任务集测试

    * [ ] 单key快捷键的确认，比如blender presskey\("w"\)（测试）

* [ ] agent层级的优化

    * [ ] 提供window checklist和window切换的功能@陈瀚

    * [ ] paste操作适用支持 text/md/html

    * [ ] 加入bring to front操作

    * [ ] Hover操作（低优先级）



### BrowseUse @许辰霆

1. cvpr2027投稿进度：补充材料初版已提交

TODO：补充case轨迹，做一个case的html看版打包，微调语法问题



### 数据  @闫晨阳



### 测评@李鸣谦

#### 

### 刷榜 @李泽豪



### 



## 





## 11\.18

### 框架 @刘一晨

**Done**

1. Mac cua \+ cua\-driver更新（等待测试）https://sensetime\.feishu\.cn/wiki/PQImwBDX7iWzp0kxCLFcvBFin2f?fromScene=spaceOverview：

    1. 把adapter侧决策迁移到driver，每次adapter只需要进行一次driver的访问

    2. 各种action支持background操作

2. bug修复

    1. 右键点击操作\+菜单栏点击

    2. ds图片大小缩放的问题@孙伟鑫

    3. Browser pressKey操作和cua对齐@林强

3. 集群功能变化见群消息，有使用体验变化会通知。@孙伟鑫

4. driver原子测试集@陈瀚：[测试集gitlab仓库](https://gitlab.sh.sensetime.com/cua/driver_bench)。测试集目前设计针对我们的cua\-driver的操作，在真实VM中进行验证。未来旨在对不同的driver的性能评估给出量化评估指标。

5. 新gui后端[aside](https://aside.com/)接入框架，现在gui\_backend丰富为cua\-driver，sky，aside 共3项，aside接入逻辑同sky。从测评分数来看aside完成度比sky强，有需要可用于造数据。aside已经安装在新镜像，更新后可用：[镜像仓库](https://registry.sensetime.com/harbor/projects/1230/repositories/mac-cua-golden/artifacts/sha256:8f33b1104c0f42ce136e895e7441c840439a83815bbb0bff27130ffd403baeb9)。切换方式：[aside切换](https://sensetime.feishu.cn/wiki/FqABw1cxVimC5Fkx3ybcyLBgn4f?from=from_copylink)@陈瀚

6. gpt超50张图片报错解决，同更新[镜像仓库](https://registry.sensetime.com/harbor/projects/1230/repositories/mac-cua-golden/artifacts/sha256:8f33b1104c0f42ce136e895e7441c840439a83815bbb0bff27130ffd403baeb9)后可用。现在当达到token上限或者达到45（默认值）张图片时均会触发压缩。@陈瀚

**On/Todo**

* [x] ~~xhx对接（周四）@林强~~

* [ ] 新版本的driver接入xhx@林强

* [x] ~~E2b接口（周四）@孙伟鑫~~

* [x] ~~@孙伟鑫~~

* [ ] E2b提供测试样例@孙伟鑫

* [ ] driver层级未修复的bug

    * [x] 剪映drag任务和下拉框（sky driver对于drag的操作速度太快了）

    * [ ] ps任务集测试

    * [x] 对于提示词小窗口的问题（见鸣谦测试结果）

    * [x] ~~弹窗点击问题（见鸣谦测试结果）@陈瀚~~

    * [ ] 奇怪的快捷键，比如blender presskey\("w"\)（测试）

    * [x] ~~右键菜单栏的pressKey操作@刘一晨~~

    * [x] ~~对于不同层级窗口的background测试@刘一晨~~

* [ ] paste操作适用支持 text/md/html

* [ ] 加入bring to front操作

* [ ] Hover操作（低优先级）



### BrowserUse @许辰霆

1. cvpr2027投稿进度：正文已提交，后续做补充材料所需的实验

TODO：本周补全所有补充材料的实验内容、设置与case study，整理codebase并打包benchmark

补充材料润色@许辰霆@彭创



### 数据  @闫晨阳

@张荧滢

**配置**

- 提示词两种：Sky 默认提示（只用界面操作）；命令行优先前缀。

**数量**

- 评分通过 1941 条：

    - Opus · Sky · 默认 501，Opus · Sky · 命令行优先 375，Opus · 自研 driver 99；

    - DeepSeek · Sky · 默认 504，DeepSeek · Sky · 命令行优先 366，DeepSeek · 自研 driver 3；

- 应用：WPS 约 950、剪映 494、美图秀秀 127，Obsidian、OBS、LibreOffice、Blender 各五六十。轨迹中位 38 步。

**质量a：主线llmchecker 检查：1766 条没问题，17 条有写具体问题**

1. 汉字变乱码，8 条。例：最终答复：里「我从磁盘重新读了一遍文��」。多数出在模型答复里，像是传输时把汉字切坏了，不是模型行为问题。（答：脏数据但datahub会过滤掉）

2. 答复声称做了其实没做的核对，3 条。例：答复说「抽帧确认画面已倒转」，实际抽了帧但从没打开看过。（答：脏数据且datahub不容易过滤，比例不高、是否需要特殊关注？）

3. 同一个点击原样连点三次，3 条。例：剪映里坐标点击报「找不到窗口」，模型不换做法又点了两次。（答：脏数据但datahub会过滤掉）

4. 答复里混进英文草稿，3 条。例：答复中间夹着「Wait file name is…Let's craft:」。（答：不确定是否属于脏数据目前datahub不会过滤掉）

5. 答复里的数字和实际不符，1 条。答复说 47 条数据，工具读到的是 48 条。（答：脏数据，不明确datahub容不容易检测到，比例不高）

6. 误判 1 条：把命令里正常的引号和转义符当成了混进来的特殊标记。（答：脏数据但datahub会过滤掉）

**质量b：有问题的数据：我们的轨迹分析发现、checker 筛不出来**

1. 模型用AppleScript 或 System Events 绕开界面操作（codex框架内不被允许）/模型误操作造成需要用命令kill app等错误情况但是选择不说。DeepSeek 在推理里明说“不要提，结果做对就可以了”。（答：脏数据且datahub不会过滤掉，需本地过滤）

2. 评分脚本可能误判对一部分题。看到三种：开了筛选但没设条件；用别的软件重建透视表覆盖原表；WPS 高级筛选只存了隐藏行。文件看着对，事没做对。数量还没核，查评分脚本。（答：datahub过滤不掉，需要在设计自动化check的时候更严格一点）

3. 大段无效重试。DeepSeek 54%、Opus 32% 的轨迹里有「没拿到新信息还重复同一操作」，最长的一条剪映拖拽试了一百多步。（答：脏数据但会被datahub过滤掉）

4. 只在 Sky 上才需要的绕法。例：按控件点不动就改按坐标点。换后端后这类经验没用。（答：上周有讨论过这个问题——平台特有的行为模式，数量不多的话默认可以提交）

5. 中间步骤模型经常有错误判断。评分通过的轨迹里，近四成卡点没有报错、模型当时也没察觉。例：加粗快捷键没生效，模型看截图说已加粗，后来复查才补上。（答：需要关注，属于特殊场景下的数据，通过loss：mask会成为比较好的纠错数据、但不经过loss:mask就是脏的数据，目前datahub很难检查出来）\(@刘一晨和天阔确认一下\)

**需要确认**

- 具体收数据的质检方案？参考上述提的一些问题。[\[261118\]评分通过的 1941 条数据质量详情](https://sensetime.feishu.cn/wiki/XEzIwiZVXiGvC9knYMPcWe54ngc?from=from_copylink)@闫晨阳

统一答复：目前datahub的llmchecker会比本地更为严格，其中提到的：

**有问题但是会被datahub过滤掉的**：质量a\(1\) 异常/乱码字符；a\(3\) 连续相同操作；b\(3\)大段无效尝试；a\(6\)特殊字符/标记

需要探讨的情形：a\(2\)step中的问题，难以过滤但频率低、a\(4\)datahub会接收的数据，中英文问题是否需要我们这边额外的过滤呢、a\(5\)频率低，目前不确定datahub是否会过滤掉

**需要特别关注的情形：b\(1\)、b\(2\)、b\(5\)**

- 动作返回能不能区分「没发出去 / 发出去了 / 界面没变」；集群和生产机需要切到 aside吗[\[261118\]轨迹中模型反复操作经常是因为静默失效：动作返回能不能区分"没发出去 / 发出去了 / 发出去了但界面没变"？](https://sensetime.feishu.cn/wiki/VSLowkJBMib5C1kfCnHc54E2nXg?from=from_copylink)@陈瀚

- 新集群镜像没装 Word，Excel 和 PowerPoint 一启动就弹订阅框，请补装并激活；一道 Numbers 题三次没开跑，请帮看。[\[261118\]新集群 golden 镜像没装 Word，Excel 和 PowerPoint 一启动就弹订阅框； Numbers 题为什么没开跑](https://sensetime.feishu.cn/wiki/DhKAw5Dmfi8M2pkFobOcYW0tnFh?from=from_copylink)@孙伟鑫



**后续计划：**

1. 问题解决：

    1. 确认datahub过滤脚本接收数据的边界

    2. AppleScript数据的过滤：针对质量b\(1\)AppleScript 属于Apple系统特有的工具，大量的数据会影响到模型在不同平台的泛化，如果目前只针对mac平台，该数据可以保存；如果后续要在不同平台上，则该数据需要过滤。

    3. 部分错误step的数据过滤：

2. 实验数据打算（针对clean数据以及特殊的dirty数据的训练）：

    1. 目前datahub接收的clean数据

    2. dirty如纠错数据对模型性能的影响

3. 后续数据安排：

    1. 针对飞书、figma等需要账号登录的应用的数据扩充

    2. 多文件系统、不同初始状况的数据



### 测评

#### codex @李鸣谦@林佳欣

点数：[评测汇总表格](https://sensetime.feishu.cn/wiki/VhStwjN8QiED2zkoViDcOw7JnVW?sheet=kcRByB) 

前端：http://10\.210\.9\.14:22337/  （已优化：步数与视频帧数同步 @林佳欣）

1. First50 Round1 收尾

    1. 报告：[first50 round1 报告](https://sensetime.feishu.cn/wiki/YL7awvpHKiuUIykfirkcqhQ3nNf)

    2. driver原子动作任务包 [driver\-test](https://sensetime.feishu.cn/wiki/UloMwa3yLiIHVakyOG9c5wkinfu) @林佳欣@刘一晨

    3. 各模型耗时与花销统计 [耗时和花销](https://sensetime.feishu.cn/wiki/WU9xwnshLif6W4kjaxccVHJnnMe)

2. First50 Round2 收尾

    1. 报告：[first50 round2报告](https://sensetime.feishu.cn/wiki/ZJHJwoqfTihcnpk7KtzciLJDnQf)

    2. null case一共34个基本都是评估链路问题，在修 [评估修复](https://sensetime.feishu.cn/wiki/RTNmwrg84iIHLgkqBNWckOWKnfc)；jianying任务证据获取困难@林佳欣@张荧滢

    3. WPS 桌面访问权限弹窗问题：L5 镜像层手动排；L2 driver层需要具备感知能力 [WPS桌面权限弹窗](https://sensetime.feishu.cn/wiki/FPuswpjvQiGqiykSGe0c21b8nJb) @刘一晨

    4. Numbers app 触发contacts系统权限弹窗：L2 driver层感知 [Numbers\-formula 【焦点未验证】](https://sensetime.feishu.cn/wiki/NiT1w0DgTiRKUlktZ4BcfiMQngd)@刘一晨

    5. Excel\-bond 窗口焦点问题 根因待查 [Excel\-bond【AttachmentUnverified】](https://sensetime.feishu.cn/wiki/GXJYwkdTfiywKSkJ4tmczRDfnHi)@刘一晨

    6. deepseek 有8个失败case，暴露出很多模型能力不足，造数据可以参考 [First50 Round2 · DeepSeek Hybrid 轨迹分析](https://sensetime.feishu.cn/wiki/TgnhwpM4Miighdk4EeTc8iDOnfd) @闫晨阳

    7. GPT 模型触发50张图片上限：L3 agent层上下文管理 [Sol模型50张图片上限](https://sensetime.feishu.cn/wiki/N8NpwAOVSi72aBk95WhcVoTTn0d) @刘一晨

3. First50 Round3 准备中：镜像、任务包与评估管线修复；加测gemini\-4\-argon，kimi\-k3\.1\-pro；框架与driver版本？

4. 后续扩任务集：加app扩到core100 \-\> cross\-app \-\> 脏任务 \-\> 【待定】聊天软件与用户交互任务

#### 小浣熊/box\-agent @兰桂林@邹广文杰

1. 小浣熊客户端 cua 评测管线

    1. 将小浣熊接入  codex\-cua 评测管线并做适配，跑了一版 first50 round2[First50 Round2 小浣熊 Hybrid 评测实验报告｜2026\-11\-17](https://sensetime.feishu.cn/docx/JRgPdEENToydhXx6pIMc98Itnfc)。

    2. 修复小浣熊 cua 评测管线链路问题，正在跑（目前观察到相较于上一版有所改善，上一版部分 0 分/无分的题目，这一版变成 1 分/有分）。

### 刷榜 @李泽豪

1. OSWorld V2\.1 评测结果，DeepSeek V4\.1 flash \+ Claude Code 复现得到的partial score为68\.14，Kimi的报告中汇报的点数为 69\.3，结果大体上一致。测试过程中发现Tokenhub的Anthropic协议调用存在问题，加入图片后返回的input\_tokens会激增，需要先转化成Chat Completion格式再调用[OSWorld V2\.1](https://sensetime.feishu.cn/wiki/DLN4wZn5CiLHfskFVA7crFY2nEb?from=from_copylink)

2. 当前刷榜数据采集方案。[方案介绍](https://sensetime.feishu.cn/wiki/F1Pxwf7aciohphk6J6McTOQEnye?from=from_copylink)

3. 当前完成了第一批通用APP教程和资料的收集，并在初步的框架中尝试生成并采集了少量数据进行测试。[生成任务示例](https://sensetime.feishu.cn/wiki/TC9owiLdeiedEpkQqktcEXcjnNc?from=from_copylink)

    APP 包括：MailHub、Thunderbird、Ubuntu Calendar、TeamChat、WPS Presentation、WPS Spreadsheets、LibreOffice Writer、LibreOffice Impress、Chrome 与 Web Runtime、Linux 文件系统与 PDF 工具、VS Code / Git / 开发工具链

    材料包括：邮件与协作记录、日历与会议数据、财务与交易材料、表格与财务模型、DOCX 与 PDF、PPTX 演示文稿、网站初始状态、文件目录与干扰资料

4. 这周完成第二批专业APP教程和资料收集，并继续完善整条采集链路

    APP环境包括：ExpenseFlow、VaultBank、Insurance Claim、FormCraft、ReviewSphere、CareerLink、CloudCRM、BudgetWise、AWS Console、票务、旅行、签证系统、本地业务网站、Zotero、Obsidian、GIMP、Shotcut、REAPER、MuseScore、StreamView / Studio

    数据材料包括：GIMP 图片处理素材、Shotcut 视频剪辑素材、REAPER 音频、MuseScore 乐谱、VS Code/Git 项目、Zotero / Obsidian、FreeCAD / SolveSpace、KiCad、3D Slicer

### 







## 11\.11

### 框架 @刘一晨

1. Mac cua \+ cua\-driver更新（已经merge）：

    1. 主要针对于上周和周一提出的剪映、wps还有preview模型窗口切换做的更新[Mac\-CUA Codex dev/codex\_v2\.0 2026\-11\-10更新总结](https://sensetime.feishu.cn/wiki/WXJ2wckgaixLGlkc29McwvWYn6e?fromScene=spaceOverview)

    2. 镜像更新可以使用本地签名，不需要重新授权

2. Sky driver的更新@陈瀚：现在gpt系列模型也可以使用sky了，同时处理了sky回传的证据与viewer的兼容问题。在精简prompt前缀的时候，同时更新了sky的部分，参考[未命名文档](https://sensetime.feishu.cn/wiki/LN4OwynWJiKvPnkbJmWcvEzEnLe#share-VflJdB0nBoFVcjxacrHc0SeenSd)中的第一部分。

3. skill内容移动到启动cua js程序的时候自动接入，精简prompt前缀和skill内容。目前的文字部分及变更可以参考文档：[文字部分变更说明](https://sensetime.feishu.cn/wiki/LN4OwynWJiKvPnkbJmWcvEzEnLe?from=from_copylink)

4. mac集群搭建和云端VM容器@孙伟鑫

**Mac\-CUA 公共集群的运行可靠性达到生产级，全面支持自助使**** ****用。**集群现有 10 台 worker，可同时运行 20 个 VM，欢迎将批量任务放到集群运行，提高利用率（https://10\.151\.92\.136:16443/）。

1. **运行达到生产级稳定：465 任务零 VM 故障**

    - 任务受 VM 影响出问题的比例从上周的约 25% 降至 0；最新版近一天运行的 **465 个任务均未出现因 VM 稳定性导致的业务问题**，暂态故障大幅减少且均可自行恢复。

    - **结果归因更清楚**：不同类型的任务失败已整理清楚，区分集群基础设施问题和 agent 问题，便于判断下一步处理。

2. **接入与镜像完全自助化：**

    - **接入更简单**：成员可自助领取、找回令牌、导入配置，自助使用。

    - **镜像自主可控**：遇到弹窗、缺少应用等问题，可自行修复镜像后增量推送至 OCI 镜像仓库，指定给任务使用。（https://registry\.sensetime\.com/harbor/projects/1230/repositories）

3. **后续计划。**

    - **（提问）对齐可靠性目标：**对于这类 Agent 沙盒服务，要达到生产级，业界标准是怎样的（如故障率低于xx）？

    - **E2B 沙盒化改造：**以支持 RL。

    - **硬件支持：**

        - 一台主机做调度服务器 \+ OCI 仓库；

        - 交换机和网线 IT 可提供，已初步测试，目前仍在调试中。预计可进一步提高稳定性和速度。

**ON/TODO**:

* [x] ~~browser presskey接口和cua接口对齐@林强~~

* [x] ~~xhx对接（周四）@林强~~

* [x] ~~adapter拆解，后续会把拆解后的结果把大部分内容移动到driver端。提高速度@刘一晨~~

* [x] ~~background操作@刘一晨~~

* [x] ~~deepseek图片大小@孙伟鑫~~

* [x] ~~E2b接口（周四）@孙伟鑫~~

* [x] ~~@孙伟鑫~~

* [x] ~~gpt 50张图片压缩@陈瀚~~

* [ ] driver层级未修复的bug

    * [ ] 剪映drag任务和下拉框

    * [ ] ps任务集还没测试

    * [ ] 对于提示词小窗口的问题（见鸣谦测试结果）

    * [ ] 弹窗点击问题（见鸣谦测试结果）

    * [ ] 奇怪的快捷键，比如blender presskey\("w"\)（测试）

    * [x] ~~右键菜单栏的pressKey操作@刘一晨~~

* [ ] Hover操作（delay）

### BrowserUse @刘一晨

1. Deepseek flash在long horizon LiveWeb的轨迹刷取，已交付high和max各自七百多条长轨迹@许辰霆

2. cvpr2027投稿进度：

- @许辰霆

1. 补充几轮主实验和相应消融实验，完成论文大纲与正文、补充材料的草稿撰写，目前在qwen3\.5\-9b/27b上sft结果优秀，在Long Horizon LiveWeb上的严格成功率从10\.3%/14\.7%提升至45%/57\.3%，27b ckpt152超越目前所有前沿Flash模型，同时在Odysseys、Web\-bench和Online\-Mind2Web上分别提升7\.2%/6\.6%、6\.9%/0\.9%和6\.2%/6\.6%（单次rollout\+三次judge，三轮rollout取平均还在补充实验）

2. 对loss mask、摘要请求携带等训练trick进行消融，摘要的trick可以提升模型在遇到压缩情况下的稳定性，关闭loss mask有不显著的轻微提升

3. 对vision on/off进行消融，vision on打开时平均轮数减少3\-4轮，rollout正确率变化不显著，最多从效率角度提一下

TODO：本周完善所有消融实验部分，补全所有评测



- @彭创

1. 完善消融实验部分（对比不同harness框架的能力）。[Long\-Horizon Bench 评测结果](https://sensetime.feishu.cn/wiki/HQwBwmBXIi8RJmk1Fs7cttNVnwf)

2. 对比了UI\-Venus\-2 在我们的longhorizon100的能力。以及复现UI\-Venus\-2实际在omd的能力

TODO：

1. 论文草稿的优化

2. 框架图，封面图的优化




- @林强

1. 完成论文中两张figure的绘制，当前已经完成main figure的绘制，目前在对论文首图做修改调整



### 数据  @闫晨阳

新框架sky评估：

1. 和cua\-driver区别（tools稍有不同、gui操作skills内容及返回机制不同、截图动态分辨率处理机制）

2. 运行效率更快（大概5倍的速率提升）[CUA数据](https://sensetime.feishu.cn/wiki/Hws0wjjrdiBc2IkKXGNcOZKuntd?from=from_copylink)

3. 目前还遇到的问题[\[261111\]Sky 后端问题](https://sensetime.feishu.cn/wiki/Yx9IwgHIQi1yt3kx7YYcpu3invb)[\[261111\]框架与集群问题](https://sensetime.feishu.cn/wiki/YBZhwfv0hicP9OkgZeTcBEVinkh)@张荧滢

    1. \[sky\]截图点击问题：sky的截图动态分辨率由模型来做，框架没有转换的机制，这一点希望框架来做

    2. \[sky\]dpsk 的 web search（需确认是否需要开web search、如果开要提供联网搜索支持）

    3. \[sky\]部分应用的问题：剪映（拖拽问题）

    4. \[集群\]上传的同一批次任务中部分会出现worker 未准入、下载可以更自由些（支持不含录屏、部分题下载）\-已解决

    5. \[集群\]集群上版本的同步问题，新的分支改动、集群是否会同步更新

    6. \[次要\]Claude 通道报错被框架统一成 502，看不到真实原因

dpsk行为模式及prompt确定：

评估dpsk在几种不同的prompt上的表现：在要求模型cli为主的模式下，dpsk也能合理使用cli来减少步骤，整体评估下来dpsk相较opus更谨慎[CUA数据](https://sensetime.feishu.cn/wiki/Hws0wjjrdiBc2IkKXGNcOZKuntd?from=from_copylink)

数据搜集：基础能力题2000（目前已跑出来的成功轨迹600\+）

1. WPS、剪映、美图秀秀（250/522、过自动评审、未过LLM评审和人工抽查）[\[261111\]Mac 端 CUA 刷数据进展：WPS 表格、剪映、美图秀秀](https://sensetime.feishu.cn/wiki/W9n8w5UpOiWBC2kDCUKcjygZnHc)@张荧滢

2. Excel、PPT、Blender（407/1417、过自动评审、未过LLM评审和人工抽查）

需要讨论：

1. 框架特色的数据，是否值得保留@张荧滢：

    - Sky 上：拖拽不生效，就去点两次素材上的"\+"；粘贴不对，就改成直接赋值；WPS 主窗口点不了，就走菜单栏，菜单栏里没有的（比如透视表字段）有时去调宏。

    - 自研 driver 上：焦点校验不过就不发输入，模型转去用 AppleScript。同样 8 道题，Opus 在自研 driver 上用了 47 次 AppleScript，在 Sky 上 0 次。Sky 默认提示本身禁 AppleScript，所以不全是后端的原因。

后续安排：

1. 数据轨迹继续增量补充、LLM审核机制\+人工抽查

2. 本地qwen3\.8\-27B训练验证数据质量（本周完成）



附件一 框架与集群问题：联网搜索配置、Claude 通道 502、做完不出分、集群未开跑与下载、截图尺寸、自定义提示同步；每条附查看器链接和定位方法[\[261111\]框架与集群问题](https://sensetime.feishu.cn/wiki/YBZhwfv0hicP9OkgZeTcBEVinkh)

附件二 Sky 后端问题：粘贴、拖拽、导出下拉框、WPS 坐标点击、按键名、自绘按钮点击无效、截图尺寸；每条附查看器链接和建议写进提示的内容[\[261111\]Sky 后端问题](https://sensetime.feishu.cn/wiki/Yx9IwgHIQi1yt3kx7YYcpu3invb)



### 测评 @李鸣谦@林佳欣

点数：[评测汇总表格](https://sensetime.feishu.cn/wiki/VhStwjN8QiED2zkoViDcOw7JnVW?sheet=kcRByB) 

前端：http://10\.210\.9\.14:22337/ 

1. smoke12加跑了一轮hybrid，收尾。没有明显结论，排bug可以参考：[评测汇总表格](https://sensetime.feishu.cn/wiki/VhStwjN8QiED2zkoViDcOw7JnVW?sheet=pjwpmG)

2. first50启动第一轮，5模型\*2模式，有初步结果反馈，还在跑

    1. hybrid路线的模型能力对比：

        1. `Claude Opus-5.5 ≈ GPT-6.1-sol > DeepSeek > GLM` claude性能最好，最省token；gpt性能持平，执行任务最快；deepseek耗token最多；glm全面落后。 [模型能力对比分析](https://sensetime.feishu.cn/wiki/BfFQwomohil9B4kiYLVcp8GJnje)

        2. claude（**91\.67%**）明显优于deepseek（**84\.21%**）。claude模型能力没有明显缺陷，能推断环境状态/识别任务模糊意图/遇到异常及时止损；deepseek擅长结构化任务，能主动纠错，但对CUA环境不那么熟悉，喜欢持续探索，最终导致耗时过长 [First50 Claude hybrid 轨迹分析](https://sensetime.feishu.cn/wiki/KfM5wS7IPi5UYYk18NWcuh7unZd)  [First50 Deepseek hybrid 轨迹分析](https://sensetime.feishu.cn/wiki/Hhzlwd9Csi52qokgWcocJoCQntb)

        3. sol**（90\.24%）**/glm**（71\.79%）**。glm核验常停在值和文字，对原生语义覆盖不足。反复试动作时缺少停止条件，完成声明也可能越过证据。sol能检查保存后的结构，并解释检查本身的误差。会读原生规则，而不只看显示值。[First50 Sol hybrid 轨迹分析](https://sensetime.feishu.cn/wiki/ULKqw8v2DiApN7kXxihcUlCCnMc)[First50 GLM hybrid 轨迹分析](https://sensetime.feishu.cn/wiki/Q92UwOUayiQn2Sk4iHdcoIIGnWd)

    2. 从任务上看：办公任务成功率很高；剪映任务全零分 [剪映任务全零分](https://sensetime.feishu.cn/wiki/PbyHwUY5oiwF76kCzKicgo98njh)；chrome任务切到gui路线掉点明显，需要看一下框架层 [claude对于chrome任务的执行偏好](https://sensetime.feishu.cn/wiki/BXaowi4SCiPm1MkYNhscENEpnBg)

    3. Hybrid vs 纯GUI：

        1. claude的纯GUI路线成功率（**67\.44%**）远远低于Hybrid路线（**91\.67%**），且耗时翻倍

        2. claude的CLI/GUI偏好：[claude在hybrid路线中的CLI/GUI偏好](https://sensetime.feishu.cn/wiki/Md4VwDQAiiIXDikpmnZcr0fZnCg) [claude对于纯gui路线指令的遵循](https://sensetime.feishu.cn/wiki/Y1KOwFBRDiU6a6k1KkQcMZujnwf)

3. 后续：first50 round1全量分析，修评估管线，继续扩充任务集



### 刷榜 @李泽豪

1. OSWorld V2\.1Benchark

解决了tokenhub的代理访问问题，同时加入了互联VPN，加快了截图传输速度，逐一任务确认并解决之前存在的一系列问题，包括部分任务存储需求大（用CFS挂载），后端部署（CVM部署），任务依赖缺失，软件安装代理配置等等，目前评测绝大部分能解决的问题已经先解决了。在Qwen 3\.8\-27B上先进行了初步的复现，结合claude code（推理强度high）的binary score和partial score分别为 12\.96 / 38\.58 ，低于官方点数（19\.4 / 48\.0），目前还在测试推理强度Max，还没测完，但是效果目前来看大概率高于官方点数（应该是纯GUI测试）

2. 数据采集环境搭建

根据OSWorld V2\.1用到的任务软件进行环境和信息的构建，目前搭好了任务构造整体框架，正在进行第一批软件和资料的采集与填充



