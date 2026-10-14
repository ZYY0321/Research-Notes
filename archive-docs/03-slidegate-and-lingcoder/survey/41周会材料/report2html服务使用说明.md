有两种使用方式
服务地址：http://10.151.196.17:8000
网页界面：http://10.151.196.17:8000/


---
使用前必读
建议每次请求都传入自己的 API Key，不要依赖服务端默认模型。 服务端默认使用的模型容易触发限流。自己带 key 结果更稳定。推荐流程：
把所有要处理的报告整理成一个 JSONL 文件（每行一条），
配置模型
使用下面的命令（或使用网页）通过文件上传接口一次提交批次。
视模型并发限制，设置 parallel_jobs并发数 

推荐使用命令：
export SERVER=http://10.151.196.17:8000

curl -s -X POST $SERVER/api/v1/batch/upload \
  -F "file=@/path/to/your_reports.jsonl" \
  -F "parallel_jobs=2" \
  -F 'model_config_json={"core":{"provider":"anthropic","model":"claude-opus-4-6","api_key":"sk-YOUR_KEY","base_url":"your_base_url"}}' \
  | python3 -m json.tool --no-ensure-ascii

 JSONL 文件，每行一个 JSON 对象：
example1：{"report": "# 报告标题\n...", "page_number": "4页"}
example2：{"id": "job-01", "report": "# 另一篇\n...", "query": "主题描述"}
字段
必填
说明
report
是
报告正文（Markdown）
page_number
否
目标页数，如 "5页" / "8-12页"
id
否（建议填写）
自定义 job_id，不填自动生成 UUID
query
否
PPT 生成指令，不填模型自动推断
1. 服务端是单线程队列，多个单条任务串行排队，后面的任务会等前面的全部跑完才开始。
2. 每个报告生成时间约 5~15 分钟（取决于页数和模型），批量任务提交后不需要盯着等，可以先检查模型连接状态，确认任务正在执行之后，等状态变成 done 或 partial_done 再来下载。
3. 任务未完成时下载会报错，下载前先查一下状态确认完成。
4. 外网机器可能会有连接不上的问题
5. 下载的 ZIP 里用 page_insert_image/ 下的 HTML 文件，这是插图后的最终结果；page_result/ 是中间产物可以忽略。
6. 同一个 job_id 重新提交会自动清空旧目录重新跑，不会累积旧文件。

---

网页使用

打开 http://10.151.196.17:8000/ 有三个页面。

单条提交
[图片]
1. 点击顶部 Pill 按钮（Claude Opus ）快速填充模型
注意：建议填入新的api和key。provider的选择决定了响应格式；
2. 点击"🔌 测试连接"确认模型可用
3. 粘贴报告内容（Markdown 格式），填写目标页数（如 4页、8-12页），任务id
4. 提交后等待进度条，完成后下载 ZIP
[图片]
展开"高级"可为风格提取、页面代码生成、Vision 分别指定不同模型。
[图片]
批量上传
[图片]


---

命令行使用

环境变量
export SERVER=http://10.151.196.17:8000
# 加 --no-ensure-ascii 避免中文乱码
curl ... | python3 -m json.tool --no-ensure-ascii

健康检查

curl -s $SERVER/health | python3 -m json.tool --no-ensure-ascii

单条 — 手动填写模型和 Key

curl -s -X POST $SERVER/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report": "# 报告标题\n\n## 第1页\n内容...",
    "page_number": "4页",
    "model_config": {
      "core": {
        "provider": "openai",
        "model": "claude-opus-4-6",
        "api_key": "sk-YOUR_KEY",
        "base_url": "https://your-endpoint/v1"
      }
    }
  }' | python3 -m json.tool --no-ensure-ascii

provider 选项：

provider
说明
需要 Key
openai
OpenAI 兼容接口（GPT / Claude 中转 / Qwen / Kimi 等）
是
anthropic
Anthropic 官方
是
gemini_official
Google 官方 Gemini
是

单条 — 不配置模型（服务端默认 gemini）

curl -s -X POST $SERVER/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report": "# 报告标题\n\n## 第1页\n内容...",
    "page_number": "4页"
  }' | python3 -m json.tool --no-ensure-ascii



单条 — 各步骤指定不同模型

curl -s -X POST $SERVER/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report": "# 报告标题\n\n## 第1页\n内容...",
    "page_number": "4页",
    "model_config": {
      "core": {
        "provider": "openai",
        "model": "claude-opus-4-6",
        "api_key": "sk-CLAUDE_KEY",
        "base_url": "https://your-endpoint/v1"
      },
      "design_style_extract": {"preset": "qwen"},
      "page_code_gen": {
        "provider": "openai",
        "model": "qwen3-coder-480b",
        "api_key": "sk-QWEN_KEY",
        "base_url": "https://api.tokenpony.cn/v1"
      },
      "vision": {"preset": "kimi"}
    }
  }' | python3 -m json.tool --no-ensure-ascii

可配置的步骤：
字段
对应步骤
不填时
core
版式分配（含大纲生成）
用服务端 .env 默认
design_style_extract
风格提取
复用 core
page_code_gen
页面代码生成
复用 core
vision
图片标注 + 图片筛选
core 支持视觉则复用，否则用 gemini3

批量 — 内联 JSON

curl -s -X POST $SERVER/api/v1/batch \
  -H "Content-Type: application/json" \
  -d '{
    "parallel_jobs": 2,
    "model_config": {"preset": "claude"},
    "reports": [
      {"id": "job-01", "report": "# 报告A\n...", "page_number": "4页"},
      {"id": "job-02", "report": "# 报告B\n...", "page_number": "4页"},
      {"id": "job-03", "report": "# 报告C\n...", "page_number": "4页"}
    ]
  }' | python3 -m json.tool --no-ensure-ascii

parallel_jobs 控制同时处理几条

批量 — 上传 JSONL 文件

# 默认模型
curl -s -X POST $SERVER/api/v1/batch/upload \
  -F "file=@tests/test_data_small.jsonl" \
  -F "parallel_jobs=1" \
  | python3 -m json.tool --no-ensure-ascii

# 手动 Key + 并发
curl -s -X POST $SERVER/api/v1/batch/upload \
  -F "file=@tests/test_data_small.jsonl" \
  -F "parallel_jobs=3" \
  -F 'model_config_json={"core":{"provider":"openai","model":"claude-opus-4-6","api_key":"sk-YOUR_KEY","base_url":"https://your-endpoint/v1"}}' \
  | python3 -m json.tool --no-ensure-ascii

查询状态

curl -s $SERVER/api/v1/jobs/<JOB_ID>/status | python3 -m json.tool --no-ensure-ascii
curl -s $SERVER/api/v1/batch/<BATCH_ID>/status | python3 -m json.tool --no-ensure-ascii
curl -s $SERVER/api/v1/jobs | python3 -m json.tool --no-ensure-ascii
curl -s $SERVER/api/v1/batches | python3 -m json.tool --no-ensure-ascii

状态值：pending 排队 / running 处理中 / cancelling 取消中 / cancelled 已取消 / done 完成 / failed 失败

取消

curl -s -X POST $SERVER/api/v1/jobs/<JOB_ID>/cancel | python3 -m json.tool --no-ensure-ascii
curl -s -X POST $SERVER/api/v1/batch/<BATCH_ID>/cancel | python3 -m json.tool --no-ensure-ascii

下载结果

JOB_ID=your-job-id
curl -s --fail -o result_${JOB_ID}.zip $SERVER/api/v1/jobs/${JOB_ID}/result \
  && echo "下载成功" || echo "下载失败，请先确认任务状态为 done/cancelled"
unzip result_${JOB_ID}.zip -d result_${JOB_ID}/

BATCH_ID=your-batch-id
curl -s --fail -o batch_result_${BATCH_ID}.zip $SERVER/api/v1/batch/${BATCH_ID}/result \
  && echo "下载成功" || echo "下载失败，请先确认批次状态为 done/partial_done"
unzip batch_result_${BATCH_ID}.zip -d batch_result_${BATCH_ID}/

测试模型连通性

curl -s -X POST $SERVER/api/v1/test/model \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model": "claude-opus-4-6",
    "api_key": "sk-YOUR_KEY",
    "base_url": "https://your-endpoint/v1"
  }' | python3 -m json.tool --no-ensure-ascii


---

结果文件结构

ZIP 解压后，用 page_insert_image/ 下的文件（最终结果），每个 HTML 为单页，直接浏览器打开：

result_<job_id>/
├── page_result/          中间产物，可忽略
└── page_insert_image/    最终结果
    └── <job_id>/
        ├── <job_id>_page1.html
        ├── <job_id>_page2.html
        └── ...
一、本周进展
1. PPT 评估 benchmark 跑通并测试

没有太大的变化，主要是固定了这个第一个版本：
若有 report.md / report.json 会先走报告预处理，抽取 key_topics / key_facts，供后续内容类评估使用。
随后 Step 1 单页评估（PageEvaluator）：包含 Hard Check（4 项：边界截断、遮挡重叠、内容完整性、图像质量等）、细粒度美学（6 维）、高层次美学（单页 1～5 分再归一化），按页真实性核查。
Step 2 全套评估（DeckEvaluator）：结构完整性、跨页视觉一致性，以及可选的内容完整性（coverage）；deck 总分由结构、一致性、完整性三部分按文档中的权重（如结构 0.40、一致性 0.35、完整性 0.25）合成。

也就是说，v1 已覆盖「单页硬指标 + 美学 + 可选真实性」与「全套结构 / 一致性 / 可选内容覆盖」两层输出，材料见 [260323]。

第一版测试（[260325] 第一版测试）
在真实样本上跑通上述流程后，已记录一批现象与待改进点，例如：高层次美学 1～5 分在 agent 间区分度偏弱、整体偏高分；Hard Check 与多维美学若简单平均易稀释短板；真实性评估与「输入类型」划分偏粗，对「排版型 vs 数据报告型」、以及「报告未逐字写出但由数据合理推导」的陈述，当前规则不易区分；Deck 侧一致性在「模板统一但插图风格多样」等场景下，分数解释是否与业务预期一致仍需定义；总分采用 page / deck / content 加权组合，该权重尚未与人工偏好对齐验证。

评测团队的评测框架也测试了一下。
这些结论已写入 [260325]，作为后续改指标、改 prompt 或改权重时的依据。


2. 构建评测数据、评测管线这边
目前是提供了一个report到html生成的小浣熊管线的一键生成的服务，
拿这个管线，把基线与 qwen-ppt-gen（SFT） 跑了一下，
效果如下：

已完成：小浣熊生成管线给出了 report2html 外部服务，使用说明见 [260327]；173 条含 query 与附件的数据集已落在 M 集群：/mnt/afs/zhangyingying/ppt/query_dataset。

二、当前问题与风险
API 与任务：外部模型 API 不稳定或额度紧张，导致评测批次难以连续跑完；report2html 等链路单任务耗时长、排队明显，整体测试周期拉长。
指标与平台：第一版测试已暴露当前的一些美观维度的标准制定有问题
同时评测工作汇总要求美观打分 + 盲评、内容评测自动化，与当前内部测试平台的打分标准、字段是否一致，需要专门对齐，否则同一套结果可能出现口径不一致。

三、需要协同事项
平台与标准：若内部测试平台仍沿用旧字段或旧说明，需与负责同学确认同步改版计划或临时对照表，避免与 [260330] 及当前 benchmark 输出不一致。

四、下周计划
[260330] 评测工作汇总 ，做这个的目的是主要是评测能够一件运行，
评测范围包括：小浣熊线上（其中无模板生成为 P0）、agentv3 / agentOS / nanobot / openclaw 等 ppt-superpower 形态、生图编辑管线；
模型侧 P0 含 HTML 生成能力，另有 agent 能力与生图子能力等；竞品与数据源均为 P0。
评测维度上，美观计划为打分加盲评，内容侧依赖自动化管线；美观打分标准已调整而内部测试平台尚未同步，内容自动化管线曾有试验但中断过一段时间。

数据上，我这里也从小浣熊整理了一部分用户真实query，计划之后在 173 条 query_dataset 上扩跑

迭代：根据 [260325] 整理迭代清单。
