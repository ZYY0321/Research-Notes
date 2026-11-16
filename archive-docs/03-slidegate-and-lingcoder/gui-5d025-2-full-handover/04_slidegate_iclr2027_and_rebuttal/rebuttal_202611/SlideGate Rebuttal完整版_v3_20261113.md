# SlideGate Rebuttal 完整版 v3（2026-11-13）

v2 之后按你的意见改。英文部分可以直接贴到 OpenReview。所有数字都已从原始结果文件重新计算并核对，验算表见 `/home/gui-5d025-2/zyy/benchmark/docs/0906论文迭代/最终正式稿/rebuttal_20261106/rebuttal_数字验算表_20261113.md`，脚本是 `/home/gui-5d025-2/zyy/benchmark/docs/0906论文迭代/最终正式稿/rebuttal_20261106/analysis/verify_rebuttal_numbers.py`。双人阻断审计按你的确认作为最终结果使用；标注网站上如果再有改动，重跑脚本即可更新。

## 〇、这一版改了什么

| 位置 | 改动 |
|---|---|
| 主线 | 不再说「最要命的失败发生在看起来很好的 PPT 里」。改为：决定能不能交付的失败，恰恰不是质量分在量的东西。一类在页面上根本看不到（只有对照请求和材料才存在），一类看得到但被整份平均掉。两类都覆盖 |
| 方法讲解 | 新增「用一个请求走一遍 SlideGate」：seq_1214 的请求如何变成 21 条带原文引用的检查项，Kimi 的 13 页成稿怎样被判出 11 条失败 |
| 案例 | 新增两个「分数第一但不能交付」的例子：seq_1025 在四个现有方案下都排同题第一；seq_1156 都是最高或并列最高 |
| uV2j 问题 1 | 恢复「PPT 是复杂任务」：文本、视觉、内容逻辑、排版美学、附件理解、硬约束 |
| uV2j 问题 3 | 改框架：自动化是设计目标，不辩解「不只用 LM」；讲清楚自动判定为什么可靠，人工研究用来验证 |
| uYyY Q2（κ） | 用户给的「按类型分别算再平均」用现有数据复现不出 .65（结果是 .51）。按你的指示改用后来标注的那版：244/12/14，κ=.61。回复里只写「修订后的表 12 直接由公开的逐条标注文件计算」 |
| uYyY Q1 | 分歧条目按新版是 14 条（不是 15 条），重算结果已用新版核对过 |
| 视觉对比（更正） | v2 写的「对比方案视觉分项 −.71 到 .66、页级区分 41%–73%」作废，那是旧版评委的结果。用论文实际的官方复现版重算后，对比方案在页面层面看得出缺陷（deck 内区分 AUROC .70–.91）。这反而加强了「看到了但被稀释」的主论点，回复里按这个写 |

## 一、ICLR rebuttal 的提交形式

- 在 OpenReview 上以评论形式回复，**截止 11 月 18 日 AoE**（还有 5 天）。之后进入审稿人和 AC 的内部讨论，作者不能再发言。
- 每条评论最多 5,000 字符，可以发多条；支持 Markdown 和 LaTeX 公式。
- 评论里放不了图。图表放进**修订版 PDF**：讨论期正文上限放宽到 10 页，附录不限；OpenReview 会自动生成和原稿的差异对比。审稿人不一定重读全文，所以要在总回复里列出改了哪些地方。
- 不需要图文并茂。回复里用 Markdown 表格放关键数字；方法示例和新实验的图表放修订稿附录，回复里写「见修订稿 Appendix X / Figure Y」。
- 评论对公众可见，不能出现能识别身份的信息。案例里的人名、公司名都要去掉。
- 建议发帖顺序：先发总回复（2 条），再发三位审稿人的回复（6R1G 1 条、uV2j 1 条、uYyY 2 条）。越早发越好，留时间给审稿人追问。

## 二、需要你确认的事

1. **请求来源（uYyY Q5）**。从任务文件核对的实际情况：
   - 有附件的 28 题来自产品里的真实会话。10 题正式请求与用户原话完全相同；其余是用户原话 + 附件名 + `ppt_scene_data` 里的四个选项（场景、受众、页数、角色），措辞稍作规整。已确认这四个选项是用户在产品界面上自己选的，英文稿第 6 条按此写。
   - 无附件的 12 题不是用户原话：参数字段为「随机生成」，主题来自岗位×主题库，原始短句 16–40 字，扩写成 75–503 字的详细要求。扩写在上游数据里完成，执行者不明。英文稿不写执行者，只如实写「在构建测试集时把短句扩写成写明受众、结构、风格和页数的详细要求」。如果审稿人追问是谁扩写的，再如实说明是测试集构建阶段统一处理的。
   - 匿名仓库公开的 `tasks/*/query.json` 带有「随机生成」、原始短句和正式请求，审稿人可以直接看到。所以这 12 题只能如实写成「为覆盖无附件输入形式而构造」，不能写成产品界面选项或真实用户原话。
   - 回复里所有当作「真实用户原话」的案例（seq_1214、1156、1408、1457、1025、1380、1087）都是有附件的题，不受影响。
2. **PresentBench 的区别**：已对照原文（arXiv 2603.07244）核实并写进 6R1G 回复。它的生成指令由专家针对材料手写，检查项人工设计（平均每个实例 54.1 条），逐条判定后汇总成总分。它也给页码证据，所以「定位到页」不作为我们独有的能力来写。

## 三、主线和策略

**主线**：决定一份 PPT 能不能交付的失败，不是质量分在量的东西。有些失败在页面上根本看不到：第 4 版块该不该有、这是不是第二课、给投资人的营收数字是不是附件里那几个，只有对照请求和材料才存在。另一些失败在页面上看得到（公式被截断、图表被遮挡），但被整份 deck 的平均分摊薄了。SlideGate 把请求和附件变成冻结的检查项，逐条对照，把这两类失败都变成定位到条目和页码、不能被其他优点抵消的阻断判定。

**这次补上的「方法讲解」**：用 seq_1214 走一遍：请求 → 21 条带原文引用的检查项 → 输出前冻结 → Kimi 13 页成稿逐条核对 → 11 条失败（第 4 版块整块缺失） → 阻断判定与条目、页码一起报告。这一段放在总回复第一条，比数字更直观。

**落点顺序**：问题和方法（案例） → 最终判定的直接验证 → 控制实验 → 视觉稀释 → 新系统。

**态度**：先澄清，再讲贡献，必要限定一句带过，最后给结果。不道歉，不说「我们弄错了」。

---

## 四、英文全文

### 评论 1：General Response（1/2）What SlideGate measures, in one example

> We sincerely thank all three reviewers for their careful reading and constructive suggestions. We are glad that the reviewers found the evaluation problem practically important, highlighted the difference between a deck that looks organized and one that fulfills the request, and saw value in task-specific diagnosis. Before the individual replies, we would like to briefly restate what SlideGate measures, using one task from the benchmark. All new results are included in the revised PDF.
>
> **The failures that decide whether a deck can be delivered are often not what a quality score measures.** Some are invisible on the slides themselves: whether a requested section exists, whether the deck uses the lesson the user named, or whether an investor deck carries the figures in the attached spreadsheet. They exist only relative to the request or the source material. Others are visible on a page, such as a clipped formula or an occluded chart, but are averaged away across the deck. For example, one investor deck in our set ranks first among the six outputs for its task under SlideAudit, PPTBench, AutoPresent and PPTEval, yet it omits the full-year revenue figures and channel shares given in the attached spreadsheet (Section 6).
>
> **SlideGate on one request** (Appendix I, Table 14). A hospital department head asked for an annual report in four named sections. Section 3 should cover, among others, a lifecycle-management system, on-site repair stations, and quality-control and incentive rules; section 4 lists near-term arrangements such as an inventory check, advance stock of oxygen and consumables, and two-tier on-call shifts.
>
> 1. *Specification.* SlideGate turns the request into 21 hard instruction items, each tied to the request span it comes from (e.g., "Section 4: add near-term arrangements"), and derives 20 required content items from the request and the attached work plan, each tied to its request quotation or source location. Rule checks reject items without a supporting span, and the specification is frozen before any output is seen, so every system answers the same questions.
> 2. *Verification.* Each item is judged pass, partial or fail with supporting pages; page counts are computed by code; every rendered page is checked for cropping and occlusion.
> 3. *Decision.* One system returned 13 well-formatted slides covering three sections. SlideGate records 11 failed instruction items and 5 missing content items, and reports a blocking failure with those item IDs; quality scores are reported separately and cannot offset it. In our blinded audit, both annotators independently mark every item of section 4 as failed.
>
> Nothing on these slides looks wrong; the failure becomes visible only against the request, and it is located precisely enough to fix. This is the capability we aim to add: request- and source-grounded acceptance items, frozen across systems, with non-compensatory decisions located at the item and page level. Across 240 commercial outputs, 124 decks carry at least one such failure.

### 评论 2：General Response（2/2）New evidence and revisions

> **Summary of evidence and revisions** (all in the revised PDF):
>
> | Question | Evidence |
> |---|---|
> | Are the final blocking flags correct? | Blinded audit of 30 decks (15 flagged, 15 not; system identity and SlideGate verdicts hidden): both annotators confirm a blocking failure in **all 15** flagged decks; inter-annotator κ .66–.86 per failure type (Section 5.4, Appendix J). |
> | Do borderline specification items drive the result? | Removing the 12 items both annotators judged unnecessary: 121–123 blocked decks (from 124); also removing the 14 disputed items: 117–122. SlideAudit's FPR stays at 77.1–77.9% (Table 13). |
> | How much does specification construction matter? | Single-candidate instruction specifications change deck-level instruction-failure flags on 6–7 of 72 decks, mostly by missing failures (Appendix C). |
> | Is it the information or the judge? | The same judge (Sonnet 4.6) given the request, the full attachment text and all pages, but no frozen specification, reaches AUROC .765, yet its own flags recover only 69/124 blocked decks and 17/71 content failures. SlideAudit re-run with Sonnet 4.6: AUROC .725, FPR 79.3% at 89.5% recall (Section 5.2, Appendix K). |
> | Do comparison schemes miss visual defects? | They respond to defective pages, and the signal is diluted at deck level (Appendix K). |
> | Is it the renderer? | Keeping only occlusion and out-of-page defects, which are least sensitive to font substitution, 120/124 decks remain flagged (Appendix J). |
> | Does it transfer to other systems? | Codex and NotebookLM on 12 tasks with unchanged specifications: 3/12 and 1/12 decks blocked (Appendix L). |
> | Interventions | Same backbone, workflow changed: instruction-failure decks 15→1, cropping/occlusion decks 11→12 (Section 5.3). Controlled defect injection turns all 10 targeted instruction verdicts from pass to fail, worsens 9 of 10 targeted content verdicts, and lowers 8 of 10 targeted page scores (Appendix H.2). |
>
> **Revisions to the paper:** (1) a walk-through of one task from request to decision (Appendix I); (2) the blinded audit and the specification-exclusion analysis (Section 5.4, Appendix J, Table 13); (3) the single-candidate ablation and a clarified description of how instruction and content specifications are built (Section 4.1, Appendix C); (4) information- and judge-controlled comparisons and the page-level dilution analysis (Section 5.2, Appendix K); (5) the rendering pipeline, the text-overflow analysis and two additional systems (Appendices J and L); (6) Table 12 computed directly from the released item-level annotation file; (7) PPTEval recomputed using content and design only for 39 decks whose coherence response could not be parsed and had been recorded as zero (AUROC .666, p = .031, FPR 73.2%), so four of six schemes now separate the groups, while none screens individual decks at high recall without flagging most of the others; (8) request provenance and the collection protocol (Appendix A).

### 评论 3：Reply to Reviewer 6R1G

> We thank the reviewer for the thoughtful comments and for recognizing that a presentation "can look visually appealing while still missing key information or violating explicit instructions."
>
> **W1. New evaluation capabilities beyond PresentBench, PPTBench and SlideAudit.**
>
> We would like to clarify that our contribution is not the observation that averages can hide errors. The failures that decide delivery are relations between a deck and its request, its source material, or its rendered page; an evaluator that reads only the slides cannot observe the first two, however it aggregates (see the walk-through in the General Response and Appendix I). SlideGate adds three capabilities that, to our knowledge, the cited works do not provide together:
>
> - **Specifications built automatically from the user's own request and attachments, frozen before any output is seen.** PresentBench writes a controlled instruction for each instance and designs its checklist manually. SlideGate derives items from the requests actually given to the systems, which range from one sentence to multi-section briefs, templates and edits of existing decks and mostly originate from practitioners' own work; each item keeps its request quotation or source location.
> - **Non-compensatory decisions.** PresentBench aggregates item verdicts into an overall score. In SlideGate, an unmet hard requirement, a missing required item, or a cropped or occluded page yields a blocking flag with item IDs and page numbers that quality scores cannot offset.
> - **A test of whether existing scores can screen delivery.** With thresholds set for at least 90% recall, the six schemes flag 73–100% of held-out decks without a detected failure.
>
> Our controls separate these capabilities from aggregation and from extra input. Deck-level aggregation dilutes visual signals: SlideAudit's cut-off/occlusion categories fire on 92.0% of the 88 defect pages, yet one hit lowers a 12-page deck's score by about .004. Extra input helps but does not replace item-wise checking: the same judge given the request, the full attachment text and all pages, but no frozen specification, flags 17 of the 71 SlideGate content failures (Section 5.2). Section 6 now also shows an investor deck that ranks first among six under four existing scores while omitting the core figures of its attached data.
>
> **W2. Coverage of systems.**
>
> Thank you for this suggestion. We would first like to explain how the systems were chosen. The paper's claims concern the evaluation instrument rather than a leaderboard: blocking failures fall into three largely separate types, and existing quality scores cannot screen them. We therefore selected the initial systems to represent several deck-generation workflows. They were the publicly available slide generators we could access during collection and span dedicated slide tools (AnyGen, Kimi), a chat assistant's slide entry (Doubao) and multi-step agents (Skywork, MiniMax, Manus) (Table 5). The tasks already cover the workflows you mention, with 17 document-based generation, 6 editing and 5 template tasks. Collection through these commercial interfaces involves manual submission, export and subscription access, which limited the size of the initial collection.
>
> To test whether the findings extend beyond these six, we added Codex (code-generated PPTX) and NotebookLM (source-grounded generation, partly delivered as full-page images) on 12 tasks spanning one-sentence, detailed, document-based, template and editing requests (Appendix L). The frozen specifications apply unchanged: 3/12 Codex and 1/12 NotebookLM decks are blocked. One Codex content failure involves an item whose source name had been replaced by a placeholder in the de-identified attachment; excluding that item leaves two blocked Codex decks among the same 12 outputs. The failures again fall into the paper's categories while taking new forms: a Codex physics deck matches the original lecture page for page, yet all of its roughly 100 formula objects are gone, which only a source-grounded check reveals.
>
> In summary, the frozen specifications apply without modification to workflows outside the original six and identify failures within the same defined categories. As the added outputs were collected later, we report them as a transfer test rather than a ranking.

### 评论 4：Reply to Reviewer uV2j

> We thank the reviewer for the helpful comments and for noting that task-specific diagnosis across generation settings "is helpful for real-world usage."
>
> **W1. Scope of the task.**
>
> We appreciate this point. While a presentation is a single artifact, producing one involves several capabilities at once: understanding the user's constraints, reading heterogeneous attachments, organizing content logic, laying out text and visuals with aesthetic quality, and delivering a file in which every page is readable. In our set, one request asks for a lesson-two deck that follows a separate production guideline; another asks to restyle a deck "without changing the main content or background"; a third asks to keep every formula of a 17-page physics lecture. Covering seven scenarios and five input forms, we hope the benchmark can serve as a demanding testbed for these combined abilities.
>
> **W2. Comparison with more methods; completeness of the metric system.**
>
> Beyond 6 systems, a same-backbone workflow comparison and 6 evaluation frameworks, we now add 2 systems and controls for information and judge (Section 5.2, Appendices K–L). On completeness, the evaluation covers instruction following, content coverage, depth and source faithfulness, four visual-defect checks, six design criteria and three aesthetic criteria with cross-page consistency (Table 2, Appendix B). These are organized by what a deck can be checked against: the request, the supplied materials and its rendered pages. SlideGate defines one delivery condition for each (a failed hard instruction, a missing required-content item, and page-level cropping or occlusion), applies them as non-compensatory gates, and keeps the remaining judgments as separate quality scores. Since 88 of the 124 blocked decks fail exactly one condition, dropping any condition would pass decks that the others reject.
>
> **W3. LM-based evaluation and label noise.**
>
> SlideGate is automated by design, so that it can be re-run on new systems without new annotation, as we did for Codex and NotebookLM. Its judgments are constrained to make them checkable: every item is fixed in advance with its request span or source location, so the judge answers a narrow question such as "does section 4 exist"; page counts are decided by code; and every verdict returns evidence pages. Human studies then validate the design: two blinded annotators confirm a blocking failure in all 15 audited flagged decks (Appendix J), content-item judgments agree with annotators at 80.7% and 85.6%, and controlled defect injection turns all 10 targeted instruction verdicts from pass to fail, worsens 9 of 10 targeted content verdicts and lowers 8 of 10 targeted page scores (Appendix H). Regarding attribution, the commercial results characterize end-to-end outputs rather than isolated backbone abilities, which the same-backbone comparison addresses (W4).
>
> **W4. Intervention analysis by failure type.**
>
> Thank you for this suggestion. The direct-versus-workflow comparison is an intervention on the generator: with the backbone fixed, instruction-failure decks fall from 15 to 1, while cropping/occlusion decks go from 11 to 12 (Section 5.3). We add interventions on the evaluator: using AutoPresent's worst page instead of its mean raises visual-failure AUROC from .66 to .81, and giving a judge full task information without a frozen specification flags 17 of the 71 SlideGate content failures (Appendix K). Different failure types respond to different changes, which we hope helps system builders decide where to improve.

### 评论 5：Reply to Reviewer uYyY（1/2）

> We are grateful for the reviewer's detailed reading and concrete suggestions, and for the note that the design remains valuable even if the claims about existing scores were narrowed. We followed the suggested analyses.
>
> **W1 / Q1 / Q2. Accuracy of the final blocking labels and the effect of specification annotations.**
>
> Following your suggestion, two annotators reviewed 30 decks (15 flagged, 15 not) blind to system identity and to SlideGate's verdicts, checking each against the request, the original attachments and every page. Both confirmed a blocking failure in all 15 flagged decks; inter-annotator κ per failure type is .66–.86. Among the 15 unflagged decks, annotators A and B identified a blocking failure in six and five, three of them in common (Section 5.4, Appendix J). If 3/15 of the 82 screening negatives contained blocking failures and all of them were among SlideAudit's false alarms, its FPR at the same operating point would still be about 71%.
>
> We also recomputed the findings under the specification annotations (Table 13):
>
> | Content items | Content failures | Blocked decks | SlideAudit AUROC | SlideAudit FPR |
> |---|---|---|---|---|
> | All 270 items | 71 | 124 | .672 | 76.8% |
> | Without the 12 items both annotators judged unnecessary | 64–69 | 121–123 | .676–.686 | 77.1–77.6% |
> | Also without the 14 disputed items | 51–67 | 117–122 | .674–.683 | 77.1–77.9% |
>
> Ranges treat decks whose status cannot be determined after removal as failing or as excluded. Thank you also for checking the agreement statistic: the revised Table 12 is computed directly from the released item-level annotation file (244 items required by both annotators, 12 by neither, 14 disputed; Cohen's κ = .61 with 94.8% raw agreement and Gwet's AC1 = .94, as about 90% of items fall in one class), and the analysis above uses exactly these labels. A blocking flag states a failed necessary condition for delivery; partially covered content, which SlideGate scores as partial by design, is reported but not gated.
>
> **W2. Information, judge, and visual defects.**
>
> We agree these factors should be separated. Given the request, the full attachment text and every page, but no frozen specification, the same Sonnet 4.6 judge reaches AUROC .765, yet its own flags recover only 69 of 124 blocked decks and 17 of 71 content failures, while both annotators confirmed a blocking failure in each of the 15 audited flagged decks. Re-running SlideAudit with Sonnet 4.6 raises AUROC from .672 to .725, with FPR still 79.3% at 89.5% recall (Section 5.2, Appendix K).
>
> We also agree that several schemes assess overlap and bounds, and they do respond to defective pages: within the same deck, their page scores rank defect pages below the others with AUROC .70–.91, and SlideAudit's categories fire on 92.0% of the 88 flagged pages. The signal is diluted at deck level: one hit lowers a 12-page deck's SlideAudit score by about .004; AutoPresent's worst page instead of its mean raises visual-failure AUROC from .66 to .81; and alarming on any SlideAudit hit reaches 95% recall but flags 54% of decks without a detected failure. We therefore see detecting a defect on a page and making a delivery decision as related but different capabilities.

### 评论 6：Reply to Reviewer uYyY（2/2）

> **Q3. A single candidate specification versus the full procedure.**
>
> With judge, prompt, requests and sources fixed, we scored 72 decks (12 tasks × 6 systems) with each of three single-candidate instruction specifications and with the final one (Appendix C). On the deck-level 1–5 instruction rating that the judge returns with its item verdicts, a single candidate agrees exactly with the final specification on 71–74% of decks (Spearman .59–.68), and the system ranking changes (Kendall .60–.83): all three single candidates rank Doubao first, while the final specification ranks AnyGen first. Deck-level instruction-failure flags differ on 6–7 of the 72 decks; the final specification flags 15 decks and each single candidate 11–13, so most changes are failures a single candidate misses. For example, on the task "organize the contents and images of the two files", all single candidates give a score of 5 to two decks that use at most one of the attachments' 27 embedded images; only the consolidated specification retains the image requirement as a hard item, and both decks receive 2. In an audit of earlier single-pass labels, an internal page-count estimate was treated as a hard constraint on 19 of 40 tasks, inferred requirements were scored on 17, and optional wording was upgraded to mandatory on 9; consolidation against the request text, critique and rule validation are designed to remove these, and freezing ensures all systems face the same items. We have also clarified in Section 4.1 that the three-candidate procedure applies to instruction specifications, while content specifications use source-constrained extraction, code validation and a critic that may only remove items.
>
> **Q4. Saving and rendering.**
>
> Thank you for raising this. We evaluate the file each system delivers: the exported PPTX for all six systems, including Manus's PPTX export from its web-slide interface. All files go through one pipeline without per-system tuning: LibreOffice 6.4.7 headless to PDF, then pdftoppm at 150 dpi, yielding 3,026 pages (Appendix J). We view defects introduced by a product's own export as part of its delivery quality. Fonts are chosen by the generating system; fonts not installed on the rendering machine are replaced by LibreOffice's fallback fonts, as they would be for a user opening the file in the same environment. Flags are determined on the delivered file rather than on in-app previews, because the file is what users receive. Since text overflow is the defect most sensitive to font substitution, we also keep only defects classified as occlusion or elements beyond the page: 120 of 124 decks remain blocked. In the Codex physics deck, the same pipeline renders all of roughly 100 formula objects in the original lecture, whereas the delivered file contains none of them, so the information is lost before rendering.
>
> **Q5. Requests, selection, and generation protocol.**
>
> We have added these details to Appendix A. We selected the 40 tasks by stratifying over scenario and input form. The 28 tasks with attachments come from real use: we invited practitioners from a range of industries to use an internal presentation-generation system for their own work, and de-identified the content while keeping input forms and scenarios. In that system a user types a message and also selects the scenario, audience, length and role; the formal request merges the message, the selected options and the attachment names into one instruction, and is identical to the message when the message already states them. The 12 text-only tasks cover brief and detailed requests without materials; their topics are drawn from a library of roles and presentation topics with sampled style parameters, and during test-set construction each short topic message was expanded into a detailed request stating audience, structure, style and length, so that the set spans a controlled range of request complexity; their input-form labels follow the original test-set design (six brief, six detailed). The released task files contain both the opening message and the formal request. All formal requests were fixed before any system output was collected. Runs that produced no deliverable were resubmitted; the first delivered deck was kept, without manual edits and without selection among multiple results.

---

## 五、论文修订稿（已完成）

修订稿源文件在 `/home/gui-5d025-2/zyy/benchmark/docs/0906论文迭代/最终正式稿/rebuttal_20261106/paper_revision_20261113/`（`submission.tex` + `sections/`），编译好的 PDF 是 `/home/gui-5d025-2/zyy/benchmark/docs/0906论文迭代/最终正式稿/rebuttal_20261106/paper_revision_20261113/submission_revision_20261113.pdf`。正文 10 页（上限 10 页），全文 28 页，没有未定义引用。

| 位置 | 改动 |
|---|---|
| 摘要、引言 | PPTEval 修正后显著的方案由三个变成四个，FPR 范围改为 73.2%–98.8%；摘要加一句盲审结果 |
| 5.2 节 | 新增一段：信息对齐基线、换评委对照、页面层面看得见但被整份稀释 |
| 5.4 节 | 新增「盲审阻断判定」一段；规格有效性改为 244 条、一致率 94.8%，并给出删条目后的重算结果 |
| 第 6 节 | 新增「排名第一的 deck 也可能交付失败」（seq_1025） |
| 第 7 节 | 加一句两个新增系统的结果 |
| 附录 A | 请求来源与生成协议 |
| 附录 E、F | PPTEval（39 份 coherence 无法解析）和 SlidesGen（两个分量不再用常数回退）的修正；p 值和混淆矩阵更新；筛查相关三张图按修正后的分数重画 |
| 附录 H.2 | 受控缺陷注入的三类结果 |
| 附录 H.4 | 表 12 改为公开逐条标注文件的统计（244/12/14，κ=.61，一致率 94.8%，AC1=.94）；新增表 13（删条目后的重算） |
| 附录 I | 一个任务从请求到判定的完整示例（表 14） |
| 附录 J | 盲审阻断判定（表 15）、88 页二次复核、渲染管线与字体无关下界 |
| 附录 K | 信息对齐基线、换评委、页面层面区分度与整份稀释（表 16、17） |
| 附录 L | Codex 与 NotebookLM（表 18） |

重画图的脚本是 `/home/gui-5d025-2/zyy/benchmark/docs/0906论文迭代/最终正式稿/rebuttal_20261106/paper_revision_20261113/analysis/build_revision_figures.py`。中文对照稿（`sections/chinese.tex`）没有同步修改，它不进投稿版。

## 六、内部备注（不进回复）

- **88 页复核的说法**：这 88 页是我（AI 助手）逐页看图复核的，不是人工标注。论文附录 J 如实写成「由独立于 SlideGate 评委的通用多模态助手复核」，正文和 rebuttal 都不把它当人工证据用。如果标注同学把这 88 页过一遍（约一小时），可以改成人工复核，正文也可以加回这句。
- **字体分类**：65/22/1 的分类是 Claude Sonnet 4.6 做的，附录 J 已写明。
- **设计师对比**：SlideGate 视觉分在同一批设计师数据上与排名系统级 ρ=.943，但对比方案也有 .54–.83，成对层面不占优，回复和论文都不用。
- **seq_1214 示例**：机器记录 11 条指令失败、5 条内容缺失；两位标注者都判第 4 版块全部 8 条失败。回复里两种口径都按这个写。
- **人工审计数字**（15/15、κ .66–.86、放行组 3/15）如果标注网站上再有改动，重跑 `/home/gui-5d025-2/zyy/benchmark/docs/0906论文迭代/最终正式稿/rebuttal_20261106/analysis/verify_rebuttal_numbers.py` 即可更新。
- **格式**：uYyY 的回复按他自己的编号回答，Q2（κ）并入 W1/Q1 那一段，不单列标题。6R1G、uV2j 用中性的小标题概括问题。每条回复开头先致谢，并引用审稿人自己在 Strengths 里的原话。
