> **文首（2026-09-11）**：这是**打分侧**用法（`/home/gui-5d025-2/zyy/benchmark`，conda `ppt-eval`）。下文题库偏 test40 / minset。日常 47 题生成+打分走本机看台 http://10.151.196.17:8770/automation ，操作以同包 `[260710]xhx-agent-v3评测手册-给agent读.md` 为准。生成和打分可以分开跑。人读入口：`[260911]评测交接（人读）.md`。

环境：GUI-5D02502 机器
conda activate ppt-eval
工作目录：/home/gui-5d025-2/zyy/benchmark

---
一、运行评测
cd /home/gui-5d025-2/zyy/benchmark
conda activate ppt-eval

# 标准运行
python -u run_from_config.py configs/<config>.yaml 2>&1 | tee results/<run_name>.log

# Dry-run（只检查数据，不调 API）
python -u run_from_config.py configs/<config>.yaml --dry-run

# 断点续跑（直接重跑相同命令，已完成的自动跳过）
python -u run_from_config.py configs/<config>.yaml

---
二、题库
题库位于 data/ 下，当前可用：
暂时无法在飞书文档外展示此内容
2.1 题库结构
data/0427_minset_40_tasks/
    index.json               ← 40 题索引（数组，每项包含 seq/modality/场景等）
    seq_0007/
        query.json           ← 题目完整定义
    seq_0115/
        query.json
    ...
2.2 附件（有源材料的题）
data/0427_attachments/
    _manifest.json           ← 40 题附件清单（哪些题有附件、文件名、大小）
    seq_1030/
        01_xxx.pdf
        02_xxx.docx
    seq_1622/
        01_xxx.docx
    ...
只有带附件的题才会跑三值忠实度评估（faithfulness）。无附件时 content_score = checklist_score。
2.3 query.json 字段
{
  "id": "S1_complex_direct",
  "prompt": "制作一个关于并购财务尽调的PPT，学术报告风格，紫色系配色",
  "prompt_rewritten": "制作一份《并购财务尽职调查》主题PPT...",
  "category": "一句话生成",
  "input_type": "纯文本",
  "complexity": "复杂",
  "topic": {...},
  "expected_capabilities": ["复杂需求理解", "结构化规划", ...],
  "observation_points": ["是否主动询问细节", ...]
}
2.4 如何新增题目
1. 在题库目录下新建 seq_XXXX/query.json
2. 如有附件，在 data/0427_attachments/seq_XXXX/ 下放对应文件
3. 更新 index.json 和 _manifest.json

---
三、评测数据组织（Agent 产出）
评测入口是一个根目录（input_root），每个子文件夹 = 一个 agent 对一道题的产出。
3.1 目录结构
data/<input_root>/
    <agent_name>_<dataset>-<date>-<query_id>/
        images/              或 *.pptx 或 code/*.html
        attachments/         ← 从题库复制的附件
        query_info.txt       ← 题目描述
3.2 三种输入格式
代码自动检测并转换，只需提供其中一种：
暂时无法在飞书文档外展示此内容
转换结果缓存到 images/，不会重复转换。
3.3 query_info.txt
Query序号: 7
来源: min40
输入类型: 详细要求
使用场景: 商业提案
页数: 10-15页
Prompt: 制作一份关于并购财务尽调的PPT，学术报告风格，紫色系配色
附件文件名: 01_尽调报告模板.pdf
附件下载URL:
暂时无法在飞书文档外展示此内容
3.4 文件夹命名规则
{agent_name}_{任意唯一后缀}
代码从文件夹名提取 agent_name（匹配 _test40 或 _val48 之前的部分；无匹配时取整个名称）。
3.5 完整示例：为新 agent "myagent" 组织一道题的数据
# 假设题目是 seq_0007，agent 产出了 PPTX
mkdir -p data/my_eval/myagent_exp1-20260617-seq_0007/

# 放入 agent 产出（三选一）
cp /path/to/output.pptx data/my_eval/myagent_exp1-20260617-seq_0007/
# 或者已有截图：
# cp /path/to/images/*.png data/my_eval/myagent_exp1-20260617-seq_0007/images/

# 放入题目信息
cp data/0430_test40_eval/kimi_test40-20260430-seq_0007/query_info.txt \
   data/my_eval/myagent_exp1-20260617-seq_0007/

# 有附件时复制
cp -r data/0427_attachments/seq_0007 \
   data/my_eval/myagent_exp1-20260617-seq_0007/attachments

---
四、配置文件（YAML）
run_name: "my_run"                      # 结果文件前缀
description: ""

input:
  input_root: "data/my_eval"            # 相对于 benchmark/
  agents: []                            # 空=全部；填 ["myagent"] 只跑指定

output:
  results_dir: "results"

run:
  workers: 8              # 并发题数
  heartbeat_seconds: 12
  skip_done: true         # 断点续跑
  no_repair: true         # 关闭修复闭环
  debug: true             # 保存原始 prompt/response

model:
  eval_model: "gemini-3.1-pro-preview"  # 裁判模型

v2:
  enabled: true
  agentic_hard_check: false
  constraint_llm: false
  substantiveness_eval: false

pairwise:
  enabled: false

pairwise_visual:
  enabled: false

---
五、评测管线
每个 (agent, query) 依次经过 3 步：
Step 1: 逐页视觉评测 (PageEvaluator)
- Hard Check：4 项 pass/fail — boundary_crop / occlusion_overlap / content_integrity / image_quality
- 细粒度美学：6 维（0/1/2）— layout_alignment / layout_spacing_balance / component_style_consistency / text_legibility / font_hierarchy / line_spacing_typesetting
- 高层次美学：5 维（0/1/2）— color_scheme / information_visualization / visual_design_quality / layout_creativity / visual_impact
Step 2: 全套评测 (DeckEvaluator，采样 10 张)
- 结构完整性（1~5）
- 跨页视觉一致性（1~5）
- 内容质量/完整性
Step 3: 内容评测 (ContentEvaluator，全部图片)
- 动态 Checklist 生成 → L0/L1/L2 三级评估
- 三值忠实度（有源材料时）

---
六、评分公式
page_score = 0.35 × hard_check + 0.40 × aesthetic_fine + 0.25 × aesthetic_high

deck_score = 0.40 × structure + 0.35 × consistency + 0.25 × content_quality

checklist_score = 0.20 × L0 + 0.35 × L1 + 0.45 × L2
content_score   = 0.60 × checklist + 0.40 × faithfulness  （有源材料）
content_score   = checklist_score                          （无源材料）

overall_score = 0.30 × page + 0.35 × deck + 0.35 × content

---
七、输出
results/
    <run_name>.jsonl              ← 每题一行 JSON
    <run_name>_debug/             ← 原始 prompt/response
JSONL 字段
暂时无法在飞书文档外展示此内容
输出示例
{
  "agent_name": "kimi",
  "overall_score": 0.9184,
  "page_score": 0.9889,
  "deck_score": 0.8125,
  "content_score": 0.964,
  "hard_check_score": 1.0,
  "aesthetic_fine_score": 1.0,
  "aesthetic_high_score": 0.956,
  "content_checklist_score": 0.94,
  "content_faithfulness_score": 1.0,
  "pages_with_hard_fail": [],
  "query_meta": {
    "scenario": "培训教学",
    "input_type": "一句话",
    "page_number": "1-10页（约）",
    "query": "做一份《叉车安全操作与装卸搬运作业要点》PPT..."
  }
}

---
八、裁判模型
当前Gemini 3.1 Pro：
- YAML 填 eval_model: "gemini-3.1-pro-preview"
- 网关：http://34.96.214.178:3000/v1
备用通道：TokenHub Claude claude-sonnet-4-6（endpoint: https://tokenhub.sensetime.com/v1）
切换模型只需改 YAML 中 eval_model。路由逻辑在 models/gemini_model.py。

---
九、常用操作
暂时无法在飞书文档外展示此内容

---
十、代码结构
benchmark/
├── run_from_config.py       ← 主入口（YAML → 评测）
├── run_benchmark.py         ← 底层编排
├── config.py                ← 全局配置（API/权重）
├── aggregator.py            ← 分数聚合
├── models/gemini_model.py   ← 模型封装（多网关路由）
├── evaluators/
│   ├── page_evaluator.py    ← 单页评测
│   ├── deck_evaluator.py    ← 全套评测
│   ├── content_evaluator.py ← 内容评测
│   └── prompts/             ← prompt 模板
├── data/
│   ├── folder_loader.py     ← 数据加载 + 自动格式转换
│   ├── 0427_minset_40_tasks/← 题库（40 题）
│   ├── 0427_attachments/    ← 附件库
│   └── 0430_test40_eval/    ← 评测数据集（agent 产出）
├── configs/                 ← YAML 配置文件
└── results/                 ← 输出

---
问题联系张荧滢。
