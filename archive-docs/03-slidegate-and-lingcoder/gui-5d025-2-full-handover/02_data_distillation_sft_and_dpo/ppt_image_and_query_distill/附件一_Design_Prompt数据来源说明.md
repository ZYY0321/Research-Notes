# 附件一：Design Prompt 数据来源与爬取情况说明

**整理时间**：2026-06-12  **负责人**：孙继业（数据收集主导）/ 张荧滢（GitHub 爬取 + 管线对接）

---

## 一、背景与整体规模

生图管线需要高质量的「design prompt」作为视觉风格指导。目前形成**三层数据体系**：

| 层级 | 数据集 | 规模 | 用途 |
|------|--------|------|------|
| L1 广泛池 | `image_prompt_collection_all.json` | **34,595 条** | 原始/半结构化收集，覆盖面最广 |
| L2 候选池 | `professional_design_prompt_candidates.jsonl` | **19,150 条** | 从 L1 筛出专业设计相关条目 |
| L3 精拆版 | `manual_content_design_handwritten_current.jsonl` | **300 条** | 人工精拆 content+design，可直接入管线 |

此外归档了 **84 个候选来源**的元数据（P0 优先级 27 个，P1 候选 39 个），用于后续系统扩量。

**详细分析见**：`/home/gui-5d025-2/zyy/data/prompt_sources/handoff_public_machine_2026-06-11/04_meeting_report/data_collection_meeting_report_2026-06-11.md`

---

## 二、L1 广泛池：34,595 条主要来源（Top 10）

| 来源 | 数量 | 说明 |
|------|------|------|
| YouMind/youmarketing-api（nano-banana-pro） | 14,217 | 商业 prompt 为主 |
| YouMind/youmarketing-api | 9,445 | 综合 prompt |
| github.com/Jermic/awesome-aiart-pics-prompts | 4,854 | 开源 AI 图 prompt |
| songguoxs/gpt4o-image-prompts | 1,040 | GPT-4o 图像 prompt |
| gpt-image2.canghe.ai | 334 | PPT/信息图专项 |
| nanoprompts.org | 240 | 设计 prompt 社区 |
| pixps.com | 178 | 视觉/摄影风格 |
| ZeroLu/awesome-gpt-image | 515 | 综合 |
| imgedify/Awesome-GPT4o-Image-Prompts | 398 | GPT-4o 专项 |
| 其他 20+ 来源 | ~3,374 | 含 Adobe、Reddit、Dribbble 等 |

---

## 三、L2 专业候选池：19,150 条来源分布（Top 10）

| 来源/域名 | 候选数量 | 说明 |
|---------|---------|------|
| x.com | 15,461 | X/Twitter 上的生图 prompt |
| aiart.pics | 1,994 | AI 艺术图 prompt |
| raw.githubusercontent.com | 590 | GitHub 开源 prompt |
| youmind.com | 203 | 商业模板 |
| gpt-image2.canghe.ai | 170 | PPT/信息图专项 |
| nanoprompts.org | 131 | 设计 prompt |
| www.pixps.com | 87 | 视觉构图 |
| docs.2sj.ai | 79 | 文档化 prompt |
| 其他 | ~1,435 | 含 myprompt/fotor/reddit 等 |

---

## 四、L3 精拆版：300 条正式语料

由孙继业从 L2 候选池逐条阅读、人工整理，拆分为 `content`（内容主题）+ `design`（纯设计要求）二元结构。

### 4.1 来源分布

| 来源 | 数量 | 特点 |
|------|------|------|
| gpt-image2.canghe.ai | 128 | 主力，信息图/报告页/商业图表，设计字段可直接用 |
| nanoprompts.org | 28 | 设计+摄影混合 |
| 2slides.com | 17 | PPT 专项，质量高 |
| slidesgo.com | 15 | PPT/Google Slides 模板描述 |
| slidescarnival.com | 15 | 信息图、层级图、流程图 |
| pitch.com | 13 | Startup/VC/Sales deck |
| 其他 7 个来源 | 84 | aiart/zcool/cyberbara 等 |

### 4.2 asset_type 分布（主要类型）

| asset_type | 数量 |
|-----------|------|
| infographic | 32 |
| poster | 30 |
| advertisement | 21 |
| ppt_slide | 10 |
| 其他（brand_board/report/storyboard 等） | 207 |

### 4.3 质量说明
- content 平均 ~182 字符，design 平均 ~216 字符
- 全 300 条无 JSON 错误、无缺失字段、无重复 ID
- **主要不足**：canghe 来源占 43%，风格偏向同一套柔和信息图色调，多样性待扩充

---

## 五、各来源可爬性评估

### 5.1 已确认可自动爬取

| 来源 | 爬取方式 | 数量 | 说明 |
|------|---------|------|------|
| GitHub 各仓库（awesome-gpt-image-2 等） | 静态 JSON/MD/HTML | ~669 条（ZYY 爬取） | 静态文件，直接 HTTP 下载 |
| YouMind/youmarketing-api | 公开 API 接口 | ~9,445 条（Codex 爬取） | 有公开分页 API |
| songguoxs/gpt4o-image-prompts 等其他 GitHub | 静态文件 | ~1,600 条（Codex 爬取） | 同上 |
| **L1 广泛池合计** | | **34,595 条** | 全部来自 GitHub + YouMind API，无一条来自 canghe/2slides 等 |

### 5.2 确认无法静态爬取（JS 动态渲染）

这些网站是当前**质量最高的 PPT 专项来源**，但页面内容由 JS 动态加载，静态 HTTP 请求只能拿到空 HTML，需要 Playwright 或人工操作：

| 网站 | 已有数据量 | 质量评估 | 爬取方案 |
|------|---------|---------|---------|
| gpt-image2.canghe.ai | 128 条（人工精拆） | ⭐⭐⭐⭐ PPT/信息图专项，设计细节丰富 | Playwright 自动化（优先） |
| 2slides.com | 17 条（人工精拆） | ⭐⭐⭐⭐⭐ 与 PPT 生成高度相关 | Playwright 自动化（优先） |
| slidesgo.com | 15 条（人工精拆） | ⭐⭐⭐⭐ PPT/Google Slides 模板描述 | Playwright（P0） |
| generatepromptai.com | 0 条 | 未评估 | Playwright（P1） |
| nanoprompts.org | 28 条（人工精拆） | ⭐⭐⭐ 设计+摄影混合 | Playwright（P1） |

### 5.3 未探测（仅有元数据，可爬性未知）

51 个候选来源仅收录了网址和优先级，尚未做可爬性探测，P0 优先级建议：

| 来源 | 类型 | 优先级 |
|------|------|-------|
| deck.gallery | 专业 deck 作品集 | P0 |
| pitch.com/templates | Startup/VC deck 模板 | P0 |
| beautiful.ai | AI 演示模板 | P0 |
| figma.com/community（presentation 类） | 现代设计语言 | P0 |
| visme.co / venngage.com | 信息图模板 | P0 |
| slidemodel.com / slideteam.net | 商业图表/流程模板 | P1 |
| behance.net / dribbble.com（deck 筛选） | 高质量设计案例 | P1 |

> **当前状态**：L3 精拆 300 条均为人工从 JS 动态渲染网站手动整理，非自动爬取。自动化爬取方案（Playwright）尚未落地，下周排期。

---

## 六、技法库（techniques.jsonl）

从爬取数据中提炼的可复用设计技法片段，**49 条**，覆盖：

| 类别 | 数量 | 示例 |
|------|------|------|
| quality（质量词） | 12 | "ultra-high resolution, 300dpi" |
| layout（布局） | 11 | "golden ratio composition, Z-pattern reading flow" |
| style（风格） | 10 | "Swiss International Typographic Style" |
| color（配色） | 9 | "analogous color scheme with 60-30-10 rule" |
| typography（排版） | 7 | "hierarchical type scale: 48/32/16pt" |

---

## 七、数据文件清单

```
data/prompt_library/
├── content_design_queries_crawled.jsonl   # 669条 全量爬取
├── content_design_queries_ready.jsonl     # 265条 过滤后可用
├── techniques.jsonl                       # 49条 设计技法片段
└── crawled_gallery.html                   # A(极简) vs B(原文) 对比画廊

/home/gui-5d025-2/zyy/data/prompt_sources/
└── handoff_public_machine_2026-06-11/01_final_formal_split/
    └── manual_content_design_handwritten_current.jsonl   # 300条 L3精拆版
```

---

## 八、下一步

1. **Playwright 爬取**：优先 2slides.com + canghe.ai（PPT 专项，质量高，估计可新增 500-1000 条）
2. **多样性补充**：当前 L3 中 canghe 占 43%，建议从 slidesgo、beautiful.ai、pitch.com 等渠道补充
3. **L3 扩量**：人工精拆效率约 5-10 条/小时，如需快速扩量可考虑 LLM 辅助拆分
