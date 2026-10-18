# 已有 arXiv 编号核对

核查日：2026-10-18。每条均对照 https://arxiv.org/abs/<id> 的题名、v1 日期、最新版本、comments、journal-ref（经 arXiv API 与 abs 页字段核对）。正式场合再查 DBLP SPARQL（题名精确匹配，以及对尚无会议条目者按第一作者核对）、OpenReview notes search、ACL Anthology（DOI 前缀 10.18653 的 Anthology id；抽查 https://aclanthology.org/2026.acl-long.278/ 与 https://aclanthology.org/2026.findings-acl.184/ 可打开）。conf.researchr.org 的公开检索 GET 不执行 `q`，POST 返回 404；ICSE、FSE、ISSTA、ASE、TOSEM、TSE 改以收录这些场合的 DBLP 为准，97 篇题名及无会议条目论文的第一作者均未对上上述场合。第一作者单位取自 arXiv HTML 或 PDF 首页（abs 页不列单位）。

「新增正式录用」只计能确定发生在 2026-04-30 之后、且该条仓库原文没有写同一场合的主会录用。范围：ICLR / ICML / NeurIPS / ACL / EMNLP / CVPR 的 2026 届，ICSE / FSE / ISSTA / ASE 2026，TOSEM / TSE。计入：OpenReview 主会 venue 为 ICML 2026（决定在 2026-05）；以及 arXiv 在 2026-04-30 之后的版本里写明 ACL 2026 录用、但仓库该条没写的。不计入：ICLR 2026（决定在 2026-01）；版本日期不晚于 2026-04-30 的 CVPR 2026 Findings；arXiv 在 2026-04-30 当日或之前已经写明的 ACL 2026；只有 DBLP/Anthology 记录、arXiv 版本不晚于 2026-04-30 且页面没写接收日期的 ACL 2026（接收日无法从这些页面判定）。Workshop、ARR 在投、被拒、撤稿不算。

## 汇总

- 总数：97
- 编号错误：1
- 不一致：19
- 新增正式录用：5
- 标题/名称变更：11
- （表内另有：一致 33，仓库未写场合 44。这两项不在要求的计数里。）

## 编号错误

- `2310.13518` Vision-Based Mobile App GUI Testing：文献综述.md 写「未正式发表」，现为 ACM Computing Surveys (2026)；DOI 10.1145/3773027；文献综述.md 将 2310.13518 写成「The Rise and Potential of Large Language Model Based Agents: A Survey」，该编号实际是「Vision-Based Mobile App GUI Testing: A Survey」

## 不一致

- `2402.01680` Large Language Model based Multi-Agents：文献综述.md 写「未正式发表」，现为 IJCAI 2024
- `2402.15116` Large Multimodal Agents：文献综述.md 写「未正式发表」，现为 Visual Intelligence (2025)；DOI 10.1007/s44267-025-00093-y
- `2406.03679` On the Effects of Data Scale on UI Control：AndroidWorld.txt 使用 v1 题名，现题为「On the Effects of Data Scale on UI Control Agents」
- `2501.12948` DeepSeek-R1：0429_文献总览表.md 发表/投向写「arXiv」，现为 Nature volume 645, pages 633-638 (2025)；DOI 10.1038/s41586-025-09422-z；0429_文献核查报告.md 会议写「arXiv preprint」，现为 Nature volume 645, pages 633-638 (2025)；DOI 10.1038/s41586-025-09422-z
- `2504.00906` Agent S2：0429_文献总览表.md 发表/投向写「arXiv」，现为 COLM 2025；0429_文献核查报告.md 会议写「arXiv preprint」，现为 COLM 2025
- `2510.02250` Scaling Agents (Agent S3 + BJudge)：0429_文献总览表.md 发表/投向写「arXiv」，现为 TMLR (2026)
- `2510.09038` CoMEM：0429_文献总览表.md 写「NeurIPS 2025」，各来源未找到对应正式录用，现为预印本
- `2512.10371` AgentProg：0429_文献总览表.md 发表/投向写「arXiv」，现为 MobiSys 2026
- `2512.19396` EchoTrail-GUI：0429_文献总览表.md 发表/投向写「arXiv」，现为 CVPR 2026 Findings
- `2601.01885` AgeMem：0429_文献总览表.md 发表/投向写「arXiv」，现为 ACL 2026；0429_文献核查报告.md 会议写「arXiv preprint」，现为 ACL 2026
- `2601.04500` GUITester：0429_文献总览表.md 发表/投向写「arXiv」，现为 ACL 2026 Findings；0429_文献核查报告.md 会议写「arXiv preprint」，现为 ACL 2026 Findings
- `2601.07779` OS-Symphony：0429_文献总览表.md 写「ACL 2026 Main」，各来源未找到对应正式录用，现为预印本；0429_文献核查报告.md 会议写「ACL 2026 Main Conference」，现为预印本
- `2601.19199` MAGNET：0429_文献总览表.md 发表/投向写「arXiv」，现为 ACL 2026
- `2602.16313` MemoryArena：0429_文献总览表.md 发表/投向写「arXiv」，现为 ACL 2026 Workshop KnowFM；0429_文献核查报告.md 会议写「arXiv preprint」，现为 ACL 2026 Workshop KnowFM
- `2602.20502` ActionEngine：0429_文献总览表.md 用的是旧标题「ActionEngine: From Reactive to Programmatic GUI Agents via State Machine Memory」，现题为「ActionEngine: From Reactive to Programmatic Web Agents via State Machine Memory」
- `2604.09581` OpenFlo：0429_文献总览表.md 用的是旧标题「OpeFlo: Automated UX Evaluation via Simulated Human Web Interaction with GUI Grounding」，现题为「Avenir-UX: Automated UX Evaluation via Simulated Human Web Interaction with GUI Grounding」
- `2604.16385` StressWeb：0429_文献总览表.md 时间写 2026-04，v1 日期为 2026-03-27
- `2604.05477` VeriGUI：0429_文献总览表.md 发表/投向写「arXiv」，现为 ACL 2026；0429_文献核查报告.md 会议写「arXiv preprint」，现为 ACL 2026
- `2605.25160` ScaleWoB：18-论文故事与社区价值路线图.md 称作「SimuWoB」，现题系统名已变为「ScaleWoB」

## 新增正式录用

- `2601.01885` AgeMem：ACL 2026。版本 v3（2026-07-23）。ACL 2026（ACL Anthology 2026.acl-long.981）
- `2601.04126` InfiniteWeb：ACL 2026。版本 v3（2026-06-30）。ACL 2026（ACL Anthology 2026.acl-long.1313）
- `2601.20732` Continual GUI Agents：ICML 2026。版本 v4（2026-03-25）。ICML 2026（OpenReview: ICML.cc/2026/Conference, venue=ICML 2026 regular）
- `2602.14296` AutoWebWorld：ICML 2026。版本 v1（2026-02-15）。ICML 2026（OpenReview: ICML.cc/2026/Conference, venue=ICML 2026 regular）
- `2605.14747` Video2GUI：ICML 2026。版本 v1（2026-05-14）。ICML 2026（OpenReview: ICML.cc/2026/Conference, venue=ICML 2026 regular）

## 标题/名称变更

比较的是同一 arXiv 编号的 v1 题名与当前最新版本题名。

- `2305.08144` v4（2024-06-13）
  - v1：Mobile-Env: A Universal Platform for Training and Evaluation of Mobile Interaction
  - 现题：Mobile-Env: Building Qualified Evaluation Benchmarks for LLM-GUI Interaction
- `2404.16054` v2（2024-08-02）
  - v1：LlamaTouch: A Faithful and Scalable Testbed for Mobile UI Automation Task Evaluation
  - 现题：LlamaTouch: A Faithful and Scalable Testbed for Mobile UI Task Automation
- `2406.03679` v6（2024-11-13）
  - v1：On the Effects of Data Scale on Computer Control Agents
  - 现题：On the Effects of Data Scale on UI Control Agents
- `2406.08451` v2（2025-08-01）
  - v1：GUI Odyssey: A Comprehensive Dataset for Cross-App GUI Navigation on Mobile Devices
  - 现题：GUIOdyssey: A Comprehensive Dataset for Cross-App GUI Navigation on Mobile Devices
- `2501.01149` v3（2026-01-12）
  - v1：A3: Android Agent Arena for Mobile GUI Agents
  - 现题：A3: Android Agent Arena for Mobile GUI Agents with Essential-State Procedural Evaluation
- `2508.15144` v2（2025-09-01）
  - v1：Mobile-Agent-v3: Foundamental Agents for GUI Automation
  - 现题：Mobile-Agent-v3: Fundamental Agents for GUI Automation
- `2510.02250` v2（2026-02-03）
  - v1：The Unreasonable Effectiveness of Scaling Agents for Computer Use
  - 现题：Scaling Agents for Computer Use
- `2512.19432` v3（2025-12-30）
  - v1：MobileWorld: Benchmarking Autonomous Mobile Agents in Agent-User Interactive, and MCP-Augmented Environments
  - 现题：MobileWorld: Benchmarking Autonomous Mobile Agents in Agent-User Interactive and MCP-Augmented Environments
- `2602.20502` v2（2026-09-28）
  - v1：ActionEngine: From Reactive to Programmatic GUI Agents via State Machine Memory
  - 现题：ActionEngine: From Reactive to Programmatic Web Agents via State Machine Memory
- `2604.09581` v2（2026-04-14）
  - v1：OpeFlo: Automated UX Evaluation via Simulated Human Web Interaction with GUI Grounding
  - 现题：Avenir-UX: Automated UX Evaluation via Simulated Human Web Interaction with GUI Grounding
- `2605.25160` v2（2026-06-18）
  - v1：SimuWoB: Simulating Real-World Mobile Apps for Fast and Faithful GUI Agent Benchmarking
  - 现题：ScaleWoB: Guiding GUI Agents with Coding Agents via Large-Scale Environmental Synthesis

## 逐条记录

按 v1 日期排序。

| arXiv id | 简称 | 完整标题 | 首发日期(v1) | 最新版本号与日期 | 第一作者单位 | 当前正式场合 | 与仓库内记载是否一致 | 不一致处 |
|---|---|---|---|---|---|---|---|---|
| 2105.13231 | AndroidEnv | AndroidEnv: A Reinforcement Learning Platform for Android | 2021-05-27 | v1（2021-05-27） | DeepMind | 仍为预印本 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2106.00133 | AppBuddy | AppBuddy: Learning to Accomplish Tasks in Mobile Apps via Reinforcement Learning | 2021-05-31 | v2（2021-06-06） | University of Toronto（论文注明 work done at Samsung AI Center, Toronto） | Canadian AI 2021（DBLP） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2211.07615 | UGIF | UGIF: UI Grounded Instruction Following | 2022-11-14 | v2（2023-05-23） | Google | 仍为预印本 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2305.08144 | Mobile-Env | Mobile-Env: Building Qualified Evaluation Benchmarks for LLM-GUI Interaction | 2023-05-14 | v4（2024-06-13） | Shanghai Jiao Tong University, Shanghai, China | 仍为预印本 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2307.13854 | WebArena | WebArena: A Realistic Web Environment for Building Autonomous Agents | 2023-07-25 | v4（2024-04-16） | Carnegie Mellon University | ICLR 2024（DBLP） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2309.11436 | You Only Look at Screens | You Only Look at Screens: Multimodal Chain-of-Action Agents | 2023-09-20 | v4（2024-06-07） | School of Electronic Information and Electrical Engineering, Shanghai Jiao Tong University | ACL 2024 Findings（ACL Anthology 2024.findings-acl.186） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2310.13518 | Vision-Based Mobile App GUI Testing | Vision-Based Mobile App GUI Testing: A Survey | 2023-10-20 | v3（2025-10-20） | State Key Laboratory for Novel Software Technology, Nanjing University, Nanjing | ACM Computing Surveys (2026)；DOI 10.1145/3773027 | 编号错误 | 文献综述.md 写「未正式发表」，现为 ACM Computing Surveys (2026)；DOI 10.1145/3773027；文献综述.md 将 2310.13518 写成「The Rise and Potential of Large Language Model Based Agents: A Survey」，该编号实际是「Vision-Based Mobile App GUI Testing: A Survey」 |
| 2312.08914 | CogAgent | CogAgent: A Visual Language Model for GUI Agents | 2023-12-14 | v3（2024-12-27） | Tsinghua University；Zhipu AI | CVPR 2024 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2312.13771 | AppAgent | AppAgent: Multimodal Agents as Smartphone Users | 2023-12-21 | v3（2026-07-05） | Tencent | CHI 2025 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2401.10935 | SeeClick | SeeClick: Harnessing GUI Grounding for Advanced Visual GUI Agents | 2024-01-17 | v2（2024-02-23） | Nanjing University；Shanghai AI Laboratory | ACL 2024（ACL Anthology 2024.acl-long.505） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2402.01680 | Large Language Model based Multi-Agents | Large Language Model based Multi-Agents: A Survey of Progress and Challenges | 2024-01-21 | v2（2024-04-19） | University of Notre Dame | IJCAI 2024（DBLP） | 不一致 | 文献综述.md 写「未正式发表」，现为 IJCAI 2024 |
| 2402.02716 | Understanding the planning of LLM agents | Understanding the planning of LLM agents: A survey | 2024-02-05 | v1（2024-02-05） | University of Science and Technology of China, Hefei, China | 仍为预印本 | 一致 | 无 |
| 2402.03300 | DeepSeekMath | DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models | 2024-02-05 | v3（2024-04-27） | DeepSeek-AI；Tsinghua University | 仍为预印本 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2402.03578 | LLM Multi-Agent Systems | LLM Multi-Agent Systems: Challenges and Open Problems | 2024-02-05 | v3（2026-01-28） | University of California, Irvine, CA, USA | 仍为预印本 | 一致 | 无 |
| 2402.06596 | Understanding the Weakness of Large Langua | Understanding the Weakness of Large Language Model Agents within a Complex Android Environment | 2024-02-09 | v1（2024-02-09） | Peking University | KDD 2024 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2402.15116 | Large Multimodal Agents | Large Multimodal Agents: A Survey | 2024-02-23 | v1（2024-02-23） | The Chinese University of Hong Kong, Shenzhen；Shenzhen Research Institute of Big Data | Visual Intelligence (2025)；DOI 10.1007/s44267-025-00093-y | 不一致 | 文献综述.md 写「未正式发表」，现为 Visual Intelligence (2025)；DOI 10.1007/s44267-025-00093-y |
| 2402.17553 | OmniACT | OmniACT: A Dataset and Benchmark for Enabling Multimodal Generalist Autonomous Agents for Desktop and Web | 2024-02-27 | v3（2024-07-21） | Carnegie Mellon University | ECCV 2024 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2404.05719 | Ferret-UI | Ferret-UI: Grounded Mobile UI Understanding with Multimodal LLMs | 2024-04-08 | v1（2024-04-08） | Apple | ECCV 2024 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2404.07972 | OSWorld | OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments | 2024-04-11 | v2（2024-05-30） | The University of Hong Kong | NeurIPS 2024 Datasets and Benchmarks（DBLP: NeurIPS；OpenReview: Datasets and Benchmarks Track） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2404.16054 | LlamaTouch | LlamaTouch: A Faithful and Scalable Testbed for Mobile UI Task Automation | 2024-04-12 | v2（2024-08-02） | State Key Laboratory of Networking and Switching Technology, Beijing University of Posts and Telecommunications | UIST 2024 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2404.13501 | A Survey on the Memory Mechanism of Large  | A Survey on the Memory Mechanism of Large Language Model based Agents | 2024-04-21 | v1（2024-04-21） | Gaoling School of Artificial Intelligence, Renmin University of China, Beijing, China | 仍为预印本 | 一致 | 无 |
| 2405.11106 | LLM-based Multi-Agent Reinforcement Learning | LLM-based Multi-Agent Reinforcement Learning: Current and Future Directions | 2024-05-17 | v1（2024-05-17） | Department of Electrical and Computer Engineering, Rutgers University–New Brunswick | 仍为预印本（arXiv comment: submitted to IEEE RA-L） | 一致 | 无 |
| 2405.14573 | AndroidWorld | AndroidWorld: A Dynamic Benchmarking Environment for Autonomous Agents | 2024-05-23 | v5（2025-04-06） | Google DeepMind | ICLR 2025（DBLP） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2406.01014 | Mobile-Agent-v2 | Mobile-Agent-v2: Mobile Device Operation Assistant with Effective Navigation via Multi-Agent Collaboration | 2024-06-03 | v1（2024-06-03） | Beijing Jiaotong University | NeurIPS 2024（DBLP） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2406.03679 | On the Effects of Data Scale on UI Control | On the Effects of Data Scale on UI Control Agents | 2024-06-06 | v6（2024-11-13） | Google DeepMind | NeurIPS 2024 Datasets and Benchmarks（arXiv comment；DBLP: NeurIPS） | 不一致 | AndroidWorld.txt 使用 v1 题名，现题为「On the Effects of Data Scale on UI Control Agents」 |
| 2406.08451 | GUIOdyssey | GUIOdyssey: A Comprehensive Dataset for Cross-App GUI Navigation on Mobile Devices | 2024-06-12 | v2（2025-08-01） | Shanghai AI Laboratory；Shanghai Jiao Tong University | ICCV 2025 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2407.18901 | AppWorld | AppWorld: A Controllable World of Apps and People for Benchmarking Interactive Coding Agents | 2024-07-26 | v1（2024-07-26） | Stony Brook University | ACL 2024（ACL Anthology 2024.acl-long.850） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2408.00118 | Gemma 2 | Gemma 2: Improving Open Language Models at a Practical Size | 2024-07-31 | v3（2024-10-02） | Google DeepMind | 仍为预印本 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2409.08264 | Windows Agent Arena | Windows Agent Arena: Evaluating Multi-Modal OS Agents at Scale | 2024-09-12 | v2（2024-09-13） | Microsoft | ICML 2025（DBLP） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2411.02006 | Foundations and Recent Trends in Multimo | Foundations and Recent Trends in Multimodal Mobile Agents: A Survey | 2024-11-04 | v3（2025-09-14） | Australian Artificial Intelligence Institute, Sydney | 仍为预印本（ACL ARR 2024 October Submission；ACL ARR 2024 December Submission；ACL ARR 2025 February Submission） | 一致 | 无 |
| 2411.04890 | GUI Agents with Foundation Models | GUI Agents with Foundation Models: A Comprehensive Survey | 2024-11-07 | v2（2025-02-13） | Huawei Noah’s Ark Lab | 仍为预印本（ACL ARR 2025 May Submission） | 一致 | 无 |
| 2411.17465 | ShowUI | ShowUI: One Vision-Language-Action Model for GUI Visual Agent | 2024-11-26 | v1（2024-11-26） | Show Lab, National University of Singapore | CVPR 2025 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2412.16256 | Aria-UI | Aria-UI: Visual Grounding for GUI Instructions | 2024-12-20 | v2（2025-07-08） | The University of Hong Kong | ACL 2025 Findings（ACL Anthology 2025.findings-acl.1152） | 一致 | 无 |
| 2501.01149 | A3 | A3: Android Agent Arena for Mobile GUI Agents with Essential-State Procedural Evaluation | 2025-01-02 | v3（2026-01-12） | MMLab, The Chinese University of Hong Kong；vivo AI Lab | ACL 2026 Findings（ACL Anthology 2026.findings-acl.184） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2501.12326 | UI-TARS | UI-TARS: Pioneering Automated GUI Interaction with Native Agents | 2025-01-21 | v1（2025-01-21） | ByteDance Seed | 仍为预印本 | 一致 | 无 |
| 2501.12948 | DeepSeek-R1 | DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning | 2025-01-22 | v2（2026-01-04） | DeepSeek-AI | Nature volume 645, pages 633-638 (2025)；DOI 10.1038/s41586-025-09422-z | 不一致 | 0429_文献总览表.md 发表/投向写「arXiv」，现为 Nature volume 645, pages 633-638 (2025)；DOI 10.1038/s41586-025-09422-z；0429_文献核查报告.md 会议写「arXiv preprint」，现为 Nature volume 645, pages 633-638 (2025)；DOI 10.1038/s41586-025-09422-z |
| 2501.19393 | s1 | s1: Simple test-time scaling | 2025-01-31 | v3（2025-03-01） | Stanford University；Allen Institute for AI；Contextual AI | EMNLP 2025（ACL Anthology 2025.emnlp-main.1025） | 一致 | 无 |
| 2502.12110 | A-MEM | A-MEM: Agentic Memory for LLM Agents | 2025-02-17 | v11（2025-10-08） | Rutgers University | NeurIPS 2025（DBLP） | 一致 | 无 |
| 2502.13923 | Qwen2.5-VL Technical Report | Qwen2.5-VL Technical Report | 2025-02-19 | v1（2025-02-19） | Qwen Team, Alibaba Group | 仍为预印本 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2503.02268 | AppAgentX | AppAgentX: Evolving GUI Agents as Proficient Smartphone Users | 2025-03-04 | v3（2025-04-15） | Westlake University, China；Henan University, China | 仍为预印本 | 一致 | 无 |
| 2504.00906 | Agent S2 | Agent S2: A Compositional Generalist-Specialist Framework for Computer Use Agents | 2025-04-01 | v1（2025-04-01） | Simular Research | COLM 2025（OpenReview venueid colmweb.org/COLM/2025/Conference；DBLP 无同题 inproceedings） | 不一致 | 0429_文献总览表.md 发表/投向写「arXiv」，现为 COLM 2025；0429_文献核查报告.md 会议写「arXiv preprint」，现为 COLM 2025 |
| 2504.07981 | ScreenSpot-Pro | ScreenSpot-Pro: GUI Grounding for Professional High-Resolution Computer Use | 2025-04-04 | v1（2025-04-04） | National University of Singapore | ACM Multimedia 2025 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2504.10458 | GUI-R1 | GUI-R1 : A Generalist R1-Style Vision-Language Action Model For GUI Agents | 2025-04-14 | v4（2025-10-01） | Shenzhen Institute of Advanced Technology, Chinese Academy of Sciences | 仍为预印本（Submitted to ICLR 2026（被拒）） | 一致 | 无 |
| 2504.14239 | InfiGUI-R1 | InfiGUI-R1: Advancing Multimodal GUI Agents from Reactive Actors to Deliberative Reasoners | 2025-04-19 | v1（2025-04-19） | Zhejiang University | 仍为预印本（Submitted to ICLR 2026（被拒）） | 一致 | 无 |
| 2505.15810 | GUI-G1 | GUI-G1: Understanding R1-Zero-Like Training for Visual Grounding in GUI Agents | 2025-05-21 | v2（2025-05-22） | Gaoling School of Artificial Intelligence, Renmin University of China | NeurIPS 2025（DBLP） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2506.01391 | AgentCPM-GUI | AgentCPM-GUI: Building Mobile-Use Agents with Reinforcement Fine-Tuning | 2025-06-02 | v2（2025-06-17） | Tsinghua University | EMNLP 2025 System Demonstrations（ACL Anthology 2025.emnlp-demos.12） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2506.05176 | Qwen3 Embedding | Qwen3 Embedding: Advancing Text Embedding and Reranking Through Foundation Models | 2025-06-05 | v3（2025-06-11） | Tongyi Lab, Alibaba Group | 仍为预印本 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2508.15144 | Mobile-Agent-v3 | Mobile-Agent-v3: Fundamental Agents for GUI Automation | 2025-08-21 | v2（2025-09-01） | Tongyi Lab, Alibaba Group | 仍为预印本 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2508.21767 | UItron | UItron: Foundational GUI Agent with Advanced Perception and Planning | 2025-08-29 | v1（2025-08-29） | Meituan | 仍为预印本（ICLR 2026 Conference Withdrawn Submission（撤稿）） | 一致 | 无 |
| 2509.06477 | MAS-Bench | MAS-Bench: A Unified Benchmark for Shortcut-Augmented Hybrid Mobile GUI Agents | 2025-09-08 | v2（2026-04-15） | Zhejiang University | ACL 2026（ACL Anthology 2026.acl-long.316） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2509.21823 | ProRe | ProRe: A Proactive Reward System for GUI Agents via Reasoner-Actor Collaboration | 2025-09-26 | v2（2026-04-15） | NTU | The Fourteenth International Conference on Learning Representations, 2026 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2509.25047 | Scaling Synthetic Task Generation for Agen | Scaling Synthetic Task Generation for Agents via Exploration | 2025-09-29 | v1（2025-09-29） | Apple | ICLR 2026（DBLP） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2510.02250 | Scaling Agents (Agent S3 + BJudge) | Scaling Agents for Computer Use | 2025-10-02 | v2（2026-02-03） | Simular Research | TMLR (2026)（DBLP） | 不一致 | 0429_文献总览表.md 发表/投向写「arXiv」，现为 TMLR (2026) |
| 2510.09038 | CoMEM | Auto-scaling Continuous Memory for GUI Agent | 2025-10-10 | v1（2025-10-10） | University of California, San Diego | 仍为预印本（Submitted to ICLR 2026（被拒）） | 不一致 | 0429_文献总览表.md 写「NeurIPS 2025」，各来源未找到对应正式录用，现为预印本 |
| 2510.18395 | MASMP | Memory-Augmented State Machine Prompting: A Novel LLM Agent Framework for Real-Time Strategy Games | 2025-10-21 | v1（2025-10-21） | National University of Defense Technology, Changsha, China | 仍为预印本（arXiv comment: submitted to conference） | 一致 | 无 |
| 2510.19949 | Surfer 2 | Surfer 2: The Next Generation of Cross-Platform Computer Use Agents | 2025-10-22 | v2（2025-10-24） | H Company — Alphabetical order | 仍为预印本 | 一致 | 无 |
| 2510.24168 | MGA | MGA: Memory-Driven GUI Agent for Observation-Centric Interaction | 2025-10-28 | v3（2026-04-14） | Shanghai Tech University, Shanghai, China | 仍为预印本（arXiv comment: submitted to ACM MM 2026） | 一致 | 无 |
| 2510.24563 | OSWorld-MCP | OSWorld-MCP: Benchmarking MCP Tool Invocation In Computer-Use Agents | 2025-10-28 | v2（2025-11-11） | Peking University；Tongyi Lab, Alibaba Group | ICLR 2026（DBLP） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2511.09127 | HAR-GUI | History-Aware Reasoning for GUI Agents | 2025-11-12 | v1（2025-11-12） | Zhejiang University | AAAI 2026 | 一致 | 无 |
| 2512.10371 | AgentProg | AgentProg: Empowering Long-Horizon GUI Agents with Program-Guided Context Management | 2025-12-11 | v2（2026-05-08） | Tsinghua University, Beijing, China | MobiSys 2026（DBLP） | 不一致 | 0429_文献总览表.md 发表/投向写「arXiv」，现为 MobiSys 2026 |
| 2512.13564 | Memory Survey | Memory in the Age of AI Agents | 2025-12-15 | v2（2026-01-13） | 未单列第一作者；核心贡献者单位含 National University of Singapore、Renmin University of China、Fudan University、Peking University 等 | 仍为预印本 | 一致 | 无 |
| 2512.15431 | Step-GUI | Step-GUI Technical Report | 2025-12-17 | v2（2025-12-19） | StepFun（GELab-Team） | 仍为预印本 | 一致 | 无 |
| 2512.19396 | EchoTrail-GUI | EchoTrail-GUI: Building Actionable Memory for GUI Agents via Critic-Guided Self-Exploration | 2025-12-22 | v3（2026-04-10） | Taobao & Tmall Group of Alibaba；East China Normal University | CVPR 2026 Findings（OpenReview: thecvf.com/CVPR/2026/Conference） | 不一致 | 0429_文献总览表.md 发表/投向写「arXiv」，现为 CVPR 2026 Findings |
| 2512.19432 | MobileWorld | MobileWorld: Benchmarking Autonomous Mobile Agents in Agent-User Interactive and MCP-Augmented Environments | 2025-12-22 | v3（2025-12-30） | Tongyi Lab, Alibaba Group | ACL 2026（ACL Anthology 2026.acl-long.278） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2601.01885 | AgeMem | Agentic Memory: Learning Unified Long-Term and Short-Term Memory Management for Large Language Model Agents | 2026-01-05 | v3（2026-07-23） | School of Cyber Science and Engineering, Wuhan University；Alibaba Group | ACL 2026（ACL Anthology 2026.acl-long.981） | 不一致 | 0429_文献总览表.md 发表/投向写「arXiv」，现为 ACL 2026；0429_文献核查报告.md 会议写「arXiv preprint」，现为 ACL 2026 |
| 2601.04126 | InfiniteWeb | InfiniteWeb: Scalable Web Environment Synthesis for GUI Agent Training | 2026-01-07 | v3（2026-06-30） | Peking University | ACL 2026（ACL Anthology 2026.acl-long.1313） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2601.04500 | GUITester | GUITester: Enabling GUI Agents for Exploratory Defect Discovery | 2026-01-08 | v1（2026-01-08） | Beijing Jiaotong University | ACL 2026 Findings（ACL Anthology 2026.findings-acl.946） | 不一致 | 0429_文献总览表.md 发表/投向写「arXiv」，现为 ACL 2026 Findings；0429_文献核查报告.md 会议写「arXiv preprint」，现为 ACL 2026 Findings |
| 2601.07779 | OS-Symphony | OS-Symphony: A Holistic Framework for Robust and Generalist Computer-Using Agent | 2026-01-12 | v1（2026-01-12） | University of Science and Technology of China | 仍为预印本 | 不一致 | 0429_文献总览表.md 写「ACL 2026 Main」，各来源未找到对应正式录用，现为预印本；0429_文献核查报告.md 会议写「ACL 2026 Main Conference」，现为预印本 |
| 2601.15876 | EvoCUA | EvoCUA: Evolving Computer Use Agents via Learning from Scalable Synthetic Experience | 2026-01-22 | v2（2026-01-23） | Meituan | 仍为预印本（workshop: ICML 2026 AIWILD） | 一致 | 无 |
| 2601.19199 | MAGNET | MAGNET: Towards Adaptive GUI Agents with Memory-Driven Knowledge Evolution | 2026-01-27 | v2（2026-01-31） | Fudan University, Shanghai, China | ACL 2026（ACL Anthology 2026.acl-long.1299） | 不一致 | 0429_文献总览表.md 发表/投向写「arXiv」，现为 ACL 2026 |
| 2601.20732 | Continual GUI Agents | Continual GUI Agents | 2026-01-28 | v4（2026-03-25） | Department of Computer Science and Technology, Tsinghua University, China | ICML 2026（OpenReview: ICML.cc/2026/Conference, venue=ICML 2026 regular） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2602.05832 | UI-Mem | UI-Mem: Self-Evolving Experience Memory for Online Reinforcement Learning in Mobile GUI Agents | 2026-02-05 | v1（2026-02-05） | Multimedia Laboratory (MMLab), The Chinese University of Hong Kong | 仍为预印本 | 一致 | 无 |
| 2602.11524 | Adaptive Milestone Reward for GUI Agents | Adaptive Milestone Reward for GUI Agents | 2026-02-12 | v1（2026-02-12） | Shanghai Jiao Tong University | 仍为预印本 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2602.12268 | CM2 | CM2: Reinforcement Learning with Checklist Rewards for Multi-Turn and Multi-Step Agentic Tool Use | 2026-02-12 | v2（2026-02-20） | 作者块未逐人对应；并列单位起首为 University of California, Santa Barbara（另有 Zoom、UCF、UCLA、UIC） | 仍为预印本 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2602.14038 | FluxMem | Choosing How to Remember: Adaptive Memory Structures for LLM Agents | 2026-02-15 | v1（2026-02-15） | University of Technology Sydney, Sydney, Australia | 仍为预印本（ICLR 2027 Conference Submission） | 一致 | 无 |
| 2602.14083 | Plan-MCTS | Plan-MCTS: Plan Exploration for Action Exploitation in Web Navigation | 2026-02-15 | v1（2026-02-15） | Shanghai Jiao Tong University | 仍为预印本 | 一致 | 无 |
| 2602.14296 | AutoWebWorld | AutoWebWorld: Synthesizing Infinite Verifiable Web Environments via Finite State Machines | 2026-02-15 | v1（2026-02-15） | The Hong Kong University of Science and Technology (Guangzhou)；DeepWisdom | ICML 2026（OpenReview: ICML.cc/2026/Conference, venue=ICML 2026 regular） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2602.16855 | Mobile-Agent-v3.5 (GUI-Owl-1.5) | Mobile-Agent-v3.5: Multi-platform Fundamental GUI Agents | 2026-02-15 | v1（2026-02-15） | Tongyi Lab, Alibaba Group | 仍为预印本 | 一致 | 无 |
| 2602.16313 | MemoryArena | MemoryArena: Benchmarking Agent Memory in Interdependent Multi-Session Agentic Tasks | 2026-02-18 | v2（2026-09-17） | Stanford University | ACL 2026 Workshop KnowFM（OpenReview: aclweb.org/ACL/2026/Workshop/KnowFM）。arXiv comment 仅写 “ICML 2026”，未写 Accepted；DBLP 与 OpenReview 均无 ICML 主会条目 | 不一致 | 0429_文献总览表.md 发表/投向写「arXiv」，现为 ACL 2026 Workshop KnowFM；0429_文献核查报告.md 会议写「arXiv preprint」，现为 ACL 2026 Workshop KnowFM |
| 2602.20502 | ActionEngine | ActionEngine: From Reactive to Programmatic Web Agents via State Machine Memory | 2026-02-24 | v2（2026-09-28） | Georgia Tech | 仍为预印本 | 不一致 | 0429_文献总览表.md 用的是旧标题「ActionEngine: From Reactive to Programmatic GUI Agents via State Machine Memory」，现题为「ActionEngine: From Reactive to Programmatic Web Agents via State Machine Memory」 |
| 2604.09581 | OpenFlo | Avenir-UX: Automated UX Evaluation via Simulated Human Web Interaction with GUI Grounding | 2026-02-25 | v2（2026-04-14） | University College London, London, United Kingdom | 仍为预印本 | 不一致 | 0429_文献总览表.md 用的是旧标题「OpeFlo: Automated UX Evaluation via Simulated Human Web Interaction with GUI Grounding」，现题为「Avenir-UX: Automated UX Evaluation via Simulated Human Web Interaction with GUI Grounding」 |
| 2604.09587 | MobiFlow | MobiFlow: Real-World Mobile Agent Benchmarking through Trajectory Fusion | 2026-02-28 | v1（2026-02-28） | Institute of Parallel and Distributed Systems (IPADS), Shanghai Jiao Tong University | 仍为预印本 | 一致 | 无 |
| 2603.05044 | WebFactory | WebFactory: Automated Compression of Foundational Language Intelligence into Grounded Web Agents | 2026-03-05 | v2（2026-04-14） | Fudan University（作者块同时列出 IMean AI、The Chinese University of Hong Kong、Tsinghua University） | ICLR 2026（DBLP） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2603.10291 | HyMEM | Hybrid Self-evolving Structured Memory for GUI Agents | 2026-03-11 | v1（2026-03-11） | University of California, San Diego | 仍为预印本 | 一致 | 无 |
| 2603.18429 | AndroTMem | AndroTMem: From Interaction Trajectories to Anchored Memory in Long-Horizon GUI Agents | 2026-03-19 | v1（2026-03-19） | HKUST(GZ)（作者块还列出其他单位） | 仍为预印本 | 一致 | 无 |
| 2604.16385 | StressWeb | StressWeb: A Diagnostic Benchmark for Web Agent Robustness under Realistic Interaction Variability | 2026-03-27 | v1（2026-03-27） | Inclusion AI, Ant Group | 仍为预印本（ACL ARR 2026 March Submission） | 不一致 | 0429_文献总览表.md 时间写 2026-04，v1 日期为 2026-03-27 |
| 2604.05477 | VeriGUI | Don't Act Blindly: Robust GUI Automation via Action-Effect Verification and Self-Correction | 2026-04-07 | v1（2026-04-07） | Beijing University of Technology, Beijing, China；Baidu Inc., Beijing, China | ACL 2026（ACL Anthology 2026.acl-long.1335） | 不一致 | 0429_文献总览表.md 发表/投向写「arXiv」，现为 ACL 2026；0429_文献核查报告.md 会议写「arXiv preprint」，现为 ACL 2026 |
| 2604.06995 | UILoop | What's Missing in Screen-to-Action? Towards a UI-in-the-Loop Paradigm for Multimodal GUI Reasoning | 2026-04-08 | v3（2026-10-02） | Zhejiang University；ZJU-Ant Group Joint Lab of Knowledge Graph | ACL 2026 Findings（ACL Anthology 2026.findings-acl.876） | 一致 | 无 |
| 2604.11716 | SWE-AGILE | SWE-AGILE: A Software Agent Framework for Efficiently Managing Dynamic Reasoning Context | 2026-04-13 | v1（2026-04-13） | Key Laboratory of Multimedia Trusted Perception and Efficient Computing Ministry ofEducation of China, Xiamen University | ACL 2026 Findings（ACL Anthology 2026.findings-acl.868） | 一致 | 无 |
| 2604.13531 | RiskWebWorld | RiskWebWorld: A Realistic Interactive Benchmark for GUI Agents in E-commerce Risk Management | 2026-04-15 | v1（2026-04-15） | Ant International, Ant Group | 仍为预印本 | 一致 | 无 |
| 2604.13954 | HINTBench | HINTBench: Horizon-agent Intrinsic Non-attack Trajectory Benchmark | 2026-04-15 | v2（2026-09-16） | Baidu Inc., Beijing, China；Beijing Institute of Technology, Beijing, China | 仍为预印本（ACL ARR 2026 May Submission；ACL ARR 2026 March Submission） | 一致 | 无 |
| 2604.21375 | VLAA-GUI | VLAA-GUI: Knowing When to Stop, Recover, and Search, A Modular Framework for GUI Automation | 2026-04-23 | v3（2026-09-24） | UC Santa Cruz | 仍为预印本 | 一致 | 无 |
| 2605.12481 | ToolCUA | ToolCUA: Towards Optimal GUI-Tool Path Orchestration for Computer Use Agents | 2026-05-12 | v2（2026-09-19） | Tongyi Lab, Alibaba Group（首页同时标注 Fudan University、Shanghai Artificial Intelligence Laboratory） | 仍为预印本 | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2605.14747 | Video2GUI | Video2GUI: Synthesizing Large-Scale Interaction Trajectories for Generalized GUI Agent Pretraining | 2026-05-14 | v1（2026-05-14） | National Key Laboratory for Multimedia Information Processing, School of Computer Science, Peking University；LLM-Core, Xiaomi | ICML 2026（OpenReview: ICML.cc/2026/Conference, venue=ICML 2026 regular） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2605.16116 | ShopGym | ShopGym: An Integrated Framework for Realistic Simulation and Scalable Benchmarking of E-Commerce Web Agents | 2026-05-15 | v1（2026-05-15） | North Carolina State University；Shopify | 仍为预印本（workshop: ICML 2026 RLxF Workshop） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |
| 2605.25160 | ScaleWoB | ScaleWoB: Guiding GUI Agents with Coding Agents via Large-Scale Environmental Synthesis | 2026-05-24 | v2（2026-06-18） | Institute for AI Industry Research (AIR), Tsinghua University | 仍为预印本 | 不一致 | 18-论文故事与社区价值路线图.md 称作「SimuWoB」，现题系统名已变为「ScaleWoB」 |
| 2606.24551 | GUI vs. CLI | GUI vs. CLI: Execution Bottlenecks in Screen-Only and Skill-Mediated Computer-Use Agents | 2026-06-22 | v1（2026-06-22） | NYU Shanghai | 仍为预印本（ACL ARR 2026 October Submission） | 仓库未写场合 | 来源文件只给出编号或译名，未写正式场合 |

