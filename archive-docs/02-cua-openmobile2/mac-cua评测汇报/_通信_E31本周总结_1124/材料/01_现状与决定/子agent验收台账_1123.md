类型：核心 ｜ 归属：11-23 E31 子 agent 派活与验收 ｜ 状态：维护中

# 子 agent 验收台账

起因（11-23 19:54 她）：「你派出子agent之后得有明确的验收和反馈，你不能只发不看结果。如果你内部机制实现不了，要显示的记录下来」

## 机制的实话
- 子 agent 回来时我会收到一条完成通知，但**没有任何程序强制我逐条核对**。以前我多次只转述摘要，没有核。
- 做法：每次派活**当场**在本表加一行，写下验收标准；回来后**当轮**填「我核对了什么」和结论。核对只靠我自己去读文件或在生产机上查，不靠子 agent 的自述。
- 状态只有四种：`已验收` / `部分验收（写没核的）` / `未验收` / `采信摘要`。没核的不得写成已验收。
- 她可以随时按本表抽查；表里没有的活，等于没验收。

## 11-23 下午到晚上已派的活（回填）

| 子 agent | 做什么 | 验收标准（事前/事后补） | 我核对了什么 | 结论 | 没核的 |
|---|---|---|---|---|---|
| 路由守护 `4369783b` | 生产机自己维护 192.168.64→bridge100 | 事后补：生产机有 KeepAlive 守护、删路由能自动补回、笔记本旧代理停掉 | 我在生产机查了 `launchctl print`：state=running、pid 38241；`route get 内网地址` 是 bridge100 静态；本机 `print-disabled` 里旧项是 disabled | 已验收 | 「删路由 1 秒补回」是它自测，我没重做 |
| 盯夜间批 `33fc236c` | 盯批、写状态页 | 事后补：批次真在跑、状态页新鲜 | 我自己读了生产机 `run-state.json`、`summary.csv` | 已验收（状态）| 它说的“包装收尾会自动 retry”我没看脚本逻辑 |
| 第二台装环境 `f617cf93` | 装 mac-cua、同步代码、拉镜像 | 事后补：orchard ready、tasks validate 通过、镜像进度可查 | 读了进度文件 `golden-pull.one`（0.45%）和它报的 2%/19MB/s | 部分验收 | `tasks validate = valid` 是它的自述；SSH 免密、校验和我没复核 |
| 查 gui 证据 `bf15cde5` | 三道题为什么没分 | 事后补：给出源码位置和对照 | 我在生产机读了 `collection.py` 第 254–260、494–498 行，和它引用一致（`incomplete_sky_session`、`gui_evidence_failed`） | 已验收（源码位置）| 「模型杀了 Photoshop」「界面调用 0 次」来自它读的轨迹，我没复读轨迹 |
| harbor 盘点 `e63faa54` | 找镜像、测速 | 事后补：能登录、列项目、测速两台 | 看到第二台拉取实际速度约 19 MB/s，与它测的 9.5 MiB/s 同量级；账号登录和项目列表我没自己再查 | 部分验收 | 246 个公开项目、7 块盘/15 个 tag、73 GiB 都是它的自述 |
| 初始文件稿 `3831b907` | Fable 写给晨阳的需求 | 事前没写 | 通读全文，对照 PS 冒烟记录；之后被她指出时机不对，已搁置 | 已验收内容；稿作废待重写 | — |
| 官方调研 `0a459d33` | PS/Mail/Figma 官方功能调研 | 事后补：只用官方域名、每条有 URL、没查到写「未核到」 | 我用命令数了：PS 30 个不同网址、域名只有 helpx.adobe.com / adobe.com / developer.adobe.com；Mail 域名只有 support.apple.com / developer.apple.com；Figma 域名只有 help.figma.com；三份「未核到」分别 51/39/17 处 | 部分验收（来源合规）| 具体事实（如 PS 2026 是 27.x）我没逐条点开核 |
| 同步清单 `f2439e01` | 列 Research-Notes 同步清单 | 事后补：不改仓库、含密码的标出 | 确认 Research-Notes 里已有的三个目录与它说的一致；仓库没被改 | 部分验收 | 「4 处内网地址」「密钥命中」我没复跑 |
| 功能地图 opus55 `5180ea07` | 调模型写功能地图和题单 | 事后补：end_turn、完整、依据调研 | 通读 opus 稿全文；确认 19+2=21 的口径 | 已验收（完整性）| 内容里「未核到」处是否靠谱没独立核 |
| Fable 版功能地图 | 同一材料包 Fable 5.2 写 | — | 只确认完成、end_turn、34 道 | 采信摘要 | **没读全文** |

## 进行中（验收标准现在写下）

| 子 agent | 做什么 | 验收标准（我回来后按这个核） |
|---|---|---|
| 生题管线 `b9219950` | 分区并发生题管线 v0 | ① PS 和 Figma 各一个区域试跑成功；② 产出的 task.json 我抽 3 道读题面和评分；③ 机器闸门（编译、validate、selftest 五类夹具）有报告，并能看到不通过被拦的例子；④ 没有改旧包；⑤ 没在她本机开 GUI/osascript |
| 逐题盘点 `41049d3e` | 32 道「哪些能跑」表 | ① 每行有来源文件；② 我抽 5 道，从生产机 `summary.csv` 复核分数和原因；③ gui_evidence_failed 的分子分母我自己用命令数一遍 | | 20:05 部分验收：night2 第一轮 14 行我用生产机 summary.csv 对了，4 个 1 分、2 个 0 分、未评分各题与表一致；其余历史批次行数、5 道抽查未做、gui_evidence_failed 的 11/52 没自己数（没核）。注意「能跑」按历史有过 1 分判定，不等于今晚能出分（canvas、fill 今晚都是 not_run）|
| v2 题包 `f479a1cb` | 改前缀 + Mail 复位 | ① v2 目录存在，v1 没被改（对比修改时间）；② 随机抽 3 道读 instruction，前缀符合她的口径（不让 AppleScript 驱动应用、不杀应用进程、必须用应用）；③ Mail 清理段在 `tell application "Mail"` 里，selftest 里是 mock；④ 生产机 `tasks validate` 为真；⑤ 没开批次 | | 20:15 部分验收：我数了 32/32 题面前缀一致、mail 题含 e31-mail-clear、PS 题没有。清理脚本没在 VM 里真跑过，等冒烟验证 |
| Fable Mail 误删（11-23 21:40 当场） | 就 Mail 重跑初始状态 / 并发误删发散，原文给荧滢看 | ① 原文文件非空且没有改写；② `.meta.json` 的 stop_reason 是 end_turn（若是 max_tokens，翻倍重发后再核）；③ 材料包含 v2 说明、mail-draft-save 的 task/setup/evaluation、Mail 评分段、Mail登录、冒烟 stdout；④ 文件和回复里没有 key；⑤ 没有在本机开 GUI 或 osascript | 21:48 部分验收：我读了 meta，stop_reason=end_turn，正文 3841 字，文件就是 ask_fable 写下的原文，没有改写；材料包里上述文件都在；正文里没有 key。文中判断我没逐条对照材料。 |

## 以后派活的固定动作
1. 派之前：本表加一行，写验收标准（可检验的，不写“做好”）。
2. 提示里把验收标准告诉子 agent，让它在回报里逐条对。
3. 回来后：我自己去读文件或查生产机，填「核对了什么」，再决定采信。
4. 没核的，在给她的汇报里直接说「没核」，不要转述成事实。
| 生题管线 `b9219950` | 点测 12 道（PS 裁剪 4、Figma 导出 8）已回；全量 48 区域仍在后台 | 20:20 部分验收：我抽看 1 道 PS 题。问题：前缀是旧的；4 道裁剪同功能；Figma 题仍受登录墙；Mail 区域暂为 0。12 道只过机器闸门，没进虚拟机 |
| 后处理 `c82458bb` | 换 v2 前缀、Mail 清草稿、同区域去重标注，输出 zyy-e31-gen-v1p | 验收：脚本幂等；suite validate 过；统计表数字我自己数一遍；去重只标注不删 |
| 集群提交 `（21:20）` | Mail+Figma 在 main-v2 环境上交集群（v2-cli 的可评分题 + gen-v1p 里 mail/figma 过闸题），jobs 20 | 验收：回执里 environment=main-v2、jobs=20、model=deepseek…/zijian_L/sfb、gui_strategy=sky；我用 `status RUN_ID` 自己查；首批任务开始后看是否登录墙/评分闸 |
| Fable 发散 `（21:20）` | 把冒烟+各子agent文档喂 Fable 做洞察与周会反馈 | 验收：产出文件非空、stop_reason 正常；我读结论，引用处抽核原文 |
| 第二台开机+登录 `dc634c0b` | 21:22 派：开机验证三应用、PS/Mail 登录、保存环境、冒烟 ps-canvas-resize | 验收：我自己用 new.sh 查 tart list 与批次 summary；状态区要写她需动手的事；没做到的直说 |
| 集群提交 `f5f99ffb`（21:30 回） | 第一次被 Runner prepare 拒（cua_driver_source_commit 不匹配），加 --runner-branch dev/codex_v2.0 --runner-commit 799a7df 重交，两批 11+31 题 running | 部分验收：我读了它写的批次文件（run_id、回执字段），没有自己再跑 status；我另挂了监控 monitor_runs.py（日志 raw/监控_1123/monitor.log）；21:29 两批 0 完成 0 运行全排队 |
| Fable 发散 `95fe8588`（21:29 回） | reply_冒烟教训与周会反馈.md 15KB，用 fableo | 采信摘要：只读了开头；它自己说没上机核过；其中 413 的说法、旧题面 1 分名单我没核 |
| 轨迹核查 `07750383` | 21:36 派：Q1 v2 两道 1 分题怎么做成的（有无 kill/AppleScript）；Q2 gen-v1p Mail 题主题是否含 E31；Q3 全部 gui_evidence_failed 的 attempt 有无 kill、有无 session_end | 验收：每个结论带证据路径；我抽 1 个 Q3 attempt 回生产机核 |
| Fable 冒烟教训稿 `95fe8588`（21:34 补） | 我已读 4 节全文 | 已读：关键点——「不杀进程」不是她原话；闸门是间歇的不是前缀解决；Mail 并发清理会互相误删；生成题可评分是模型自标；覆盖计数单位待她表态 |
| 轨迹核查 `07750383`（21:47 回） | 已验收（Q3 抽核 ps-jpeg-q60 attempt-001：见 pkill） | 结论：8 个 gui_evidence_failed attempt 全缺 session_end，7 个有 kill/退出 PS 或 Mail；冒烟两道 1 分题是界面做成、没有 kill；v1p 35 道 Mail 题主题全含 E31，2 道没写主题。报告 冒烟与失败轨迹核查_1123.md |
| Fable 误删方案 `90ccc0a5`（21:50 回） | 已读全文 | 已读：Fable 原文 reply_Mail误删与状态隔离.md。采纳方向（评分归属与清理拆开、今晚两批不动、用 deleted= 与 records 测混杂），不采纳处：「前缀拿掉不杀进程」与轨迹核查冲突，待她定；它说的 E31_MAIL_CREDS 是否在集群设置我没核 |
| 集群提交 `f5f99ffb`（21:57 终回） | 已验收（我自己读了 raw 里 4 道 Mail 题 attempt-001 的 events） | 事实：集群 main-v2 里 Mail 是未登录状态（mail-draft-save、mail-draft-search、mail-attachment 的事件里都有 Welcome to Mail / Add Account / Sign In）；mail-draft-save 的 0 分是镜像没登录，不是模型做错；mail-flag 无该字样但也 not_run |
| 生题管线 `b9219950`（22:12 管线 all done） | STATUS：216 规格、173 过闸（69 可评分）、36 未过、区域 42/48；题量建议.md：218/196/81、48 区域 | 数字两份对不上，没核；gen-v1p 现有 196 个任务目录，其中可评分 Mail/Figma 32。不对外引用 |
| v3 题包 `c6f78bd4`（22:15 派） | 删「不杀进程」；Mail 评分归属与清理拆开；setup 记录已有同主题草稿数 | 验收：本机 selftest、生产机 osacompile+validate、前缀统计 32 道；我抽 1 道看 task.json |
| v3 题包 `c6f78bd4`（22:43 报错结束） | 子 agent 最后一轮报「重试无进展」，但文档和产物已落盘 | 部分验收：我自己数了 v3 32 道题面都没有「杀掉」；v3 目录和说明文档存在。生产机 validate/osacompile 结果以它的文档为准，没核；gen-v3p 没生成；评分「只认开始之后的草稿」没做成（读草稿脚本拿不到创建时间），退回为「环境不作数」标注 |
| 第二台开机+登录 `dc634c0b`（22:44 报错结束） | 最后一轮「重试无进展」，工作已完成 | 部分验收：状态页 22:26 写：个人环境已保存、PS 与 Mail 登录（退出重开仍在）、配置已指向、冒烟 ps-canvas-resize 出了 gui_evidence_failed（我读了生产机 summary）；我另起的 e31-m2-ps-night-1123 在跑（进程确认）。镜像检查 check.json 我没读 |
| 数字页+集群已完成任务核查（22:50 派） | 每应用：不同功能题数（换参数不计）、进过 VM 的、有分的、1 分的；集群 main 四批已完成任务的分数/原因/登录墙 | 验收：每个数带来源路径；Figma 是否有登录墙以事件为准；我抽 3 个数回源核 |
| 数字页 `f0c36b33`（23:16 回） | 现在的数_1123.md：PS 功能122/跑过8/有分8/1分7；Mail 41/14/12/5；Figma 35/20/9/3；飞书 8/0 | 部分验收：我复核了「Sign In」其实是文件名「Design Income」的子串（大小写不敏感匹配），Figma 已结束 9 道没有登录墙，撤回我 23:09 的「可能没登录」；PS 只有 ps-crop 没 1 分与我已知一致；Mail 评分 reason/records 取不到。其余数我没回源核 |
| Figma 第二轮生题（11-24 01:25 派） | 对 figma-1/3/4/8（及 mail-2-4、ps-2-23）重出规格与题；解决「no grade points 被丢」；新题 id 清单 + 题包路径 + 每题评分依据；跑 validate；不提交集群 | 验收：我抽 3 题读 grade 代码，看评分依据是否真读到应用/文件状态而非自证；validate 结果我自己重跑 | → 01:50 回：部分验收：我重跑 validate 为 valid:true；读了 figma-1 导出题评分=只要 PNG 存在可读即 1 分（不核内容、可被命令行生成，弱）；mail-2-4 草稿题 4 道可评分但 Mail 评分 AppleScript 在集群会超时，只适合生产机；其余 26 道不可评分，仅收轨迹。其它 3 道抽查未做 |
| PS 生成题产出诊断（11-24 10:05 派） | 两台生产机 e31-gen-ps-m1/m2-1123 已跑的题：按结局分类（有分/timeout/supervisor_error/not_started），逐类读 ≥2 条最后截图与 events，回答为什么 supervisor_error 与 timeout 多、有没有题面或评分问题；标出 1 分是否真在 PS 里做的 | 产出 `analysis/PS生成题产出诊断_1124.md`；我抽 2 条核对 |
| 集群 1 分与付费锁（10:05 派） | 集群 main 各批 Figma/Mail 1 分按应用×评分依据类型拆表；读 combine-boolean、Mail 草稿类 1 分、v2f figma-1 导出题、figma-rep2 的 21 个 1 分里抽 5；回答付费锁/Mail 登录是否影响 | 产出 `analysis/集群1分核查_1124.md`；我抽 2 条核对 |
| PS 诊断回来（10:16）+重评分子任务（10:20 派） | 诊断：1 分仅 mask-disable-apply 且为 PS 脚本写出；9 timeout 多为桌面权限框；5 道 supervisor_error 虚拟机里已有成品未评分；4 道 not_started 缺 Pillow | 部分验收：我核对了生产机 ps-2-11-mask-from-transparency setup/stderr.log 确有 ModuleNotFoundError: PIL，且 gen-v1p 有 21 个 PS 题 setup 用 PIL；桌面权限框与 1 分来源未回源核。重评分子任务：找出把 supervisor_error 但成品在虚拟机的 attempt 补评分的方法（先例：e31-ds-sfb-night-1123-search-regrade），列出能补评的清单，不动正在跑的批次 |
| 集群1分核查回来（10:26） | figma-rep2 21/22；评分只看文件、命令行可绕过但未见；Figma 账单锁横幅 83/83；Mail v2 5 道全 AppleScript 超时；gen 7 道 reason 未下到 | 部分验收：我抽了 combine-boolean 原文含「Boolean Union Export」与「team is locked」（见本行下命令输出），其余未回源核；gen Mail 7 道原因没证据，不得写超时 |
| 补评分方案回来（10:29） | 7 道 PS supervisor_error 补不了：成品未入归档、VM 盘已删、无 regrade 命令；search-regrade 是整题重跑 | 采信摘要：没回源核；与 PS 诊断「5 道 VM 里有成品」矛盾点在于成品没收回，这点我没核 |
| 不可评分归因与补评分（11-24 12:20 派） | 对 gen-v1p/gen-v2f 全部 manual/不可评分题按原因分类（状态在云端/界面瞬时/本机文件或 plist 可读/缺解析库/应用要联网），对「本机可读」的类给出可用评分方案并写进题包新目录；每个新评分必须有正例、反例（near-miss）夹具并 selftest 通过；不做的写清不能做的理由 | 产出 `analysis/不可评分归因与补评分_1124.md`；我抽 3 题读 evaluation.py 与夹具，并问：反例夹具会不会被判 1 分 |
| 基础功能社区搜索（12:20 派） | 对 PS/Mail/Figma 去官方说明书之外的来源（百度知道、知乎、小红书文字帖、Adobe Community、Apple 支持社区、Figma Forum、B站专栏）搜「新手最常做的操作」，对照现有 gen-v1p/v1/人工题的功能，列出说明书没覆盖的基础功能 | 产出 `analysis/基础功能_社区补充_1124.md`；每条带来源链接+原文摘句；我抽 5 条打开链接核 |
| 社区搜索回来（12:12） | 30 个链接；PS/Mail/Figma 各 8 类说明书题没有的基础操作 | 部分验收：随机 6 个链接都能打开（200，仅查可访问，未核摘句是否原文）；小红书没读到，Apple 社区无浏览量 |
| 评分器对抗审计（12:30 派） | 对 gen-v1p/v2f/v2-cli 里所有可评分题（kind≠manual），独立构造「看似对但其实错」的产物（空文件、尺寸对内容错、用命令行生成的假文件、同名旧文件、只改一半），跑评分看是否误判 1 分；纯脚本、不碰应用 | 产出 `analysis/评分器对抗审计_1124.md`：每题一行（能骗过/不能）+复现命令；我抽 3 题自己复跑 |
| kill 与 1 分轨迹精读（12:30 派） | 回答 B1：8 个 gui_evidence_failed 里 7 个有 kill，kill 前三步模型想解决什么；16 个 1 分里是否真在应用里做的；读≥6 条，贴原文 | 产出 `analysis/kill与1分轨迹精读_1124.md`；我抽 2 条核 |
| 旧轨迹转 SFT 与清单（12:30 派） | 找 E20 可收清单「直接收」48 条的原始轨迹在哪（本机/生产机/集群），用框架 convert_trace_to_sft.py 本地转换，校验，输出：条数、总大小、每条路径、sha256、是否有推理文字/截图；不联网上传 | 产出 `/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/analysis/上传清单_1124.md` 与本地目录 raw/sft_out_1124；我核条数与大小 |
| kill与1分精读回来（12:34） | 7 次 kill 全在 v1 题面（night2），v2 含「不杀进程」的 21 条无按名 kill；16 条 1 分 PS 成品 app_signature 全 true、非 sips/PIL 画；gui_evidence_failed 闸门不是 kill 造成（mail-draft-save 无 kill 也缺 session_end） | 部分验收：我在 Mac1 粗 grep killall/pkill/kill -9/to quit：night2(v1) 9 个 attempt 有、night3(v2) 4 个有，v2 的 4 个是否只是引用禁令文字没逐个核；与我之前说「7/8 有 kill」的说法相比，kill 数据来自 v1 批这点是新信息 |
| 不可评分归因回来（12:35） | 141 道 manual：云端 34/瞬时 51/本机可读 17/缺库 21/其他 18；17 道在 zyy-e31-gen-v3s 补了评分，只用标准库 | 部分验收：我重跑 validate=valid:true、17 道在；读了 ps-2-7-layer-effects 的评分与夹具（夹具是 build_psd 合成的，同一作者）；用 v3s 的 parse_psd 解析生产机两个真 Photoshop 2026 PSD（raw/psd真文件_1124/，ps-layer.psd 与 mask-disable-apply.psd）能解析出尺寸与图层标签块，说明解析器能读真文件；但「投影/图层效果/智能对象」等评分没有真实带这些特征的 PSD 校准，不能当已验证 |
| PS 修环境后重开的新题包 v4p（12:50 派） | 从 gen-v1p 的 PS 题派生 zyy-e31-gen-v4p：(a) 准备脚本不再 import PIL（用标准库写 PNG）；(b) 输出目录从 ~/Desktop/e31-newapps 改成 ~/e31-newapps（非 macOS 受保护目录，避免「想访问 Desktop 文件夹」框），种子文件、题面路径、评分一起改且一致；(c) 剔除明确要装插件/联网生成（Neural Filters、生成式放大、生成背景）；题面逐字对应其余不变；本机 selftest+validate 过 | 产出 `analysis/v4p说明_1124.md`；我抽 3 题 diff 对原题只差路径/PIL，并自己重跑 validate |
| PS/Mail/Figma 漏斗表（12:50 派） | 派出→开跑→做完→有 session_end→有分→1分，按应用×机器×题包，数据来自生产机 summary.csv 与集群 status/raw；口径写清（同题多次不按「至少一次」折叠，给每次的分布）；ps-canvas-resize 11 行拆开 | 产出 `analysis/漏斗_1124.md`；我抽 3 个数回源 |
| Figma 1 分真伪（12:50 派） | 打开（读图）figma-rep2/gen-mailfigma 的 1 分导出 PNG 至少 8 张，判断是不是模型这次做的内容、有没有残留旧文件；对同题两轮比步数 | 产出 `analysis/Figma1分真伪_1124.md`，贴图路径；我自己看其中 3 张 |
| 旧轨迹转SFT回来（12:48） | 48 条转出 0 条：41 条 A 批无 rollout-trace，7 条 B/C 批转换器 name KeyError；原始 7 条 bundle 128MB 在 raw/sft_src_1124 | 部分验收：我在 Mac1 核对 E20A 批 trace.jsonl=0、rollout-trace=0、events.jsonl=344（对得上）；night2 批有 15 个 rollout-trace（说明 E31 新批次可转）；7 条 name 错没复现 |
| 对抗审计回来（12:48） | 107 道可评分题每道都至少一种假文件得 1 分；1021 份假文件 234 份得 1 分（22.9%）；最松 png_rgba/mail_draft/mail_flag/png/prefix；3 道代码把整句拆成字符 | 验收：我自己复现了两个：全透明 4×4 PNG 在 png_rgba 评分里得 1（score=1, reason=ok）；0 字节文件得 0。其余数没回源 |
| 收紧共享评分库（12:55 派） | 读审计报告，改写共享评分函数：全透明/单色图不过、抽样点外必须有内容、要求署名的题强制署名、草稿题要新增（相对开始前基线）、prefix 要最小长度和合法尾部、修三处拆字符 bug；产出新共享库副本（不改现有题包），并用审计脚本重跑，误判率应显著下降且正例仍 1 分 | 产出 `analysis/评分器收紧_1124.md` 与新共享库目录；我自己用透明 PNG 等复跑 |
| 框架同学追问回复（12:55） | 后端 Sky；3 个 attempt 的 stop-confirmation：agent.stopped=false（unclassified，attempt.py:96），controller 2 例 success、1 例 sky_service_replaced_or_unowned；Mac1 框架 978f9e8（11-05） | 验收：我自己取了 3 份 stop-confirmation.json 并读字段；全批 72 份只粗扫，结论只代表 3 例 |
| 漏斗表回来（13:08，[PS Mail Figma漏斗表](84272535-69ab-45ab-832d-fc7190d54f3f)） | 235 派出→223 开跑→172 做完→160 session_end→159 有分→70 严格1分 | 部分验收：只抽了 ps-canvas-resize，Mac1 磁盘 11 个 attempt（1分5/0分3/没分3），与表里 13 个（Mac2 另 2 个没分）对得上；其余格子没回源核，注意生成题批次仍在跑数会变 |
| Figma 1分真伪回来（13:09，[Figma一分真伪核查](14590f6c-7447-4979-84fe-4ac67799538c)） | 41 个 1 分：可信 32，可疑 9（切片×2、PDF×2、取消填充×2、透明导出等） | 部分验收：我自己看了 arc-ring、combine-boolean、slice-export-region 三张图并对像素；其余 38 个判断没核 |
| 回陈瀚（13:15） | 读 clipping-mask 原始文件：agent 正常 turn.completed；stop 阶段 0.99s；controller already_absent；events 里 34 处 kill | 已验收：我自己在 Mac1 读了该 attempt 的 events/stderr/status/result.json；vector-mask 没查 kill、layer-copy 没读 events；"kill 导致 Sky 提前退出"是猜测，未验证 |
| v4p 回来（13:18，[v4p修环境新题包](747f67be-9a20-4c90-a889-b8292e18c4dd)） | 109 道（46 可评分/63 人工），剔 10，validate valid=true，21 道准备脚本去 Pillow，输出目录 ~/e31-newapps | 部分验收：我自己重跑 validate 得 valid=true；Desktop 引用从 358 个文件降到 2 个；layer-mask-add 对比 v1p 路径确已改；PIL 只剩 selftest 和 suite.json；没验证：Photoshop 写 ~/e31-newapps 是否还弹权限框（必须上机冒烟） |
| 收紧评分库回来（13:25，[收紧共享评分库](820c12ac-a65a-4eaa-9440-89d65f734309)） | 假文件得 1 分 234/1021(22.9%)→68/1021(6.7%)；mail_draft 仍 25/98（无基线） | 部分验收：我自己用新库 e31_grade_ext.grade 复跑：全透明 PNG→0、整张纯色→0、左半红右半灰真图→1（png_rgba 和 png 都是）；误判率数字没复跑；新库未接入任何题包，旧评分口径仍在 |
| B窗：Mac2 supervisor_error 扫描 + ps-merge-visible 失败原因（13:40 派，grok-4.7-xhigh） | 只读 Mac2（new.sh）与 Mac1（prod.sh）：Mac2 所有 attempt 里 status 为 supervisor_error 的数量、原因文字、按题包分布；ps-merge-visible 各批 events 末尾 + stop-confirmation 字段，是否同为「Agent stop could not be confirmed」；不动运行中批次、不装东西；产出 `analysis/stop扫描_Mac2_1124.md`，每个数写命令 | 待回：我抽 2 个 attempt 回源读 status.json |
| v4p 冒烟（13:45 起） | Mac1 批次 e31-v4p-smoke-m1-1124，2 题（layer-mask-add 原先超时 0 分 + Desktop 框；clipping-mask 原先 stop_unconfirmed） | 待核：回来后我自己读 result.json/score.json、事件里有没有 Desktop 权限框和 kill |
| Mac2 stop 扫描回来（13:48） | Mac2 20 份 status 里 9 份 supervisor_error，同一句停机失败；8 条 controller already_absent，1 条 ps-2-25-ps-save-copy 是 sky_service_replaced_or_unowned；9 条无评分无成品；Mac1 ps-merge-visible 4 条同字段 | 部分验收：我在 Mac2 读了 ps-2-25-ps-save-copy 的 status 与 stop-confirmation（supervisor_error、两处停机失败文字、sky_service_replaced_or_unowned 都对），并数了 e31-gen-ps-m2-1123 批内 supervisor_error=6（与它给的 6 条 gen 题对上）；在 Mac1 确认 ps-merge-visible attempt-001 无 grading、无 outputs。其余 7 条和「全 9 条」总数没逐个核 |
| v4p 冒烟回来（14:10） | 2/2 completed、1 分，无 supervisor_error | 已验收：我自己在 Mac1 读了 agent/status.json、grading/score.json、事件里搜 Desktop 框文字；样本只有 2 题且同一台机，不能说"完全解决"；评分仍是旧口径 |
| 框架升级尝试（14:35） | 新版并行部署到 Mac1，加载与 validate 通过；冒烟因缺 cua_driver_source_commit 失败 | 已验收：我自己跑了 validate 和冒烟，读到报错原文；旧版目录未动；v4p 批次已用旧版重起 |
| 升级镜像验收（14:50） | image qualify：codex.runtime 通过；cua.gui source_mismatch，试了三个提交都不对 | 已验收：我自己跑了三次 qualify 并读到错误码；没找到镜像里驱动的真实提交；旧版没动，v4p 批用旧版重起 |
| Mac1 事故与恢复（15:10） | 新框架 qualify 改了共享 registry，旧框架拒绝启动 | 已验收：我自己恢复并确认批次 e31-v4p-m1c-1124 已出现 tasks 目录；registry.json 仍是被新框架改过的版本（versions 12 条），没回滚，其他环境有没有受影响没查 |
