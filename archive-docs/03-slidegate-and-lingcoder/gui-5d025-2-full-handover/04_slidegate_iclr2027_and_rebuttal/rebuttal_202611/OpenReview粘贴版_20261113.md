# OpenReview 粘贴版（2026-11-13）

每条评论分两栏：Title 填标题，Comment 粘贴正文。正文是 Markdown，OpenReview 会直接渲染表格和加粗。

建议顺序：先发 1、2，再发 3、4、5、6。修订稿 PDF 先上传（Add revision），再发评论，因为正文引用了修订稿的章节和附录。

## 01. General Response (1/2): What SlideGate measures, in one example

- 发在：论文页面下发表新评论（Official Comment），读者选 Everyone
- Title：`General Response (1/2): What SlideGate Measures, Illustrated with One Task`
- 字符数：3034（上限 5,000）

```markdown
We sincerely thank all three reviewers for their careful reading and constructive suggestions. We are glad that the reviewers found the evaluation problem practically important, highlighted the difference between a deck that looks organized and one that fulfills the request, and saw value in task-specific diagnosis. Before the individual replies, we would like to briefly restate what SlideGate measures, using one task from the benchmark. All new results are included in the revised PDF.

**The failures that decide whether a deck can be delivered are often not what a quality score measures.** Some are invisible on the slides themselves: whether a requested section exists, whether the deck uses the lesson the user named, or whether an investor deck carries the figures in the attached spreadsheet. They exist only relative to the request or the source material. Others are visible on a page, such as a clipped formula or an occluded chart, but are averaged away across the deck. For example, one investor deck in our set ranks first among the six outputs for its task under SlideAudit, PPTBench, AutoPresent and PPTEval, yet it omits the full-year revenue figures and channel shares given in the attached spreadsheet (Section 6).

**SlideGate on one request** (Appendix I, Table 14). A hospital department head asked for an annual report in four named sections. Section 3 should cover, among others, a lifecycle-management system, on-site repair stations, and quality-control and incentive rules; section 4 lists near-term arrangements such as an inventory check, advance stock of oxygen and consumables, and two-tier on-call shifts.

1. *Specification.* SlideGate turns the request into 21 hard instruction items, each tied to the request span it comes from (e.g., "Section 4: add near-term arrangements"), and derives 20 required content items from the request and the attached work plan, each tied to its request quotation or source location. Rule checks reject items without a supporting span, and the specification is frozen before any output is seen, so every system answers the same questions.
2. *Verification.* Each item is judged pass, partial or fail with supporting pages; page counts are computed by code; every rendered page is checked for cropping and occlusion.
3. *Decision.* One system returned 13 well-formatted slides covering three sections. SlideGate records 11 failed instruction items and 5 missing content items, and reports a blocking failure with those item IDs; quality scores are reported separately and cannot offset it. In our blinded audit, both annotators independently mark every item of section 4 as failed.

Nothing on these slides looks wrong; the failure becomes visible only against the request, and it is located precisely enough to fix. This is the capability we aim to add: request- and source-grounded acceptance items, frozen across systems, with non-compensatory decisions located at the item and page level. Across 240 commercial outputs, 124 decks carry at least one such failure.
```

## 02. General Response (2/2): Summary of evidence and revisions

- 发在：回复第 1 条（General Response 1/2）
- Title：`General Response (2/2): Summary of Evidence and Revisions`
- 字符数：2970（上限 5,000）

```markdown
**Summary of evidence and revisions** (all in the revised PDF):

| Question | Evidence |
|---|---|
| Are the final blocking flags correct? | Blinded audit of 30 decks (15 flagged, 15 not; system identity and SlideGate verdicts hidden): both annotators confirm a blocking failure in **all 15** flagged decks; inter-annotator κ .66–.86 per failure type (Section 5.4, Appendix J). |
| Do borderline specification items drive the result? | Removing the 12 items both annotators judged unnecessary: 121–123 blocked decks (from 124); also removing the 14 disputed items: 117–122. SlideAudit's FPR stays at 77.1–77.9% (Table 13). |
| How much does specification construction matter? | Single-candidate instruction specifications change deck-level instruction-failure flags on 6–7 of 72 decks, mostly by missing failures (Appendix C). |
| Is it the information or the judge? | The same judge (Sonnet 4.6) given the request, the full attachment text and all pages, but no frozen specification, reaches AUROC .765, yet its own flags recover only 69/124 blocked decks and 17/71 content failures. SlideAudit re-run with Sonnet 4.6: AUROC .725, FPR 79.3% at 89.5% recall (Section 5.2, Appendix K). |
| Do comparison schemes miss visual defects? | They respond to defective pages, and the signal is diluted at deck level (Appendix K). |
| Is it the renderer? | Keeping only occlusion and out-of-page defects, which are least sensitive to font substitution, 120/124 decks remain flagged (Appendix J). |
| Does it transfer to other systems? | Codex and NotebookLM on 12 tasks with unchanged specifications: 3/12 and 1/12 decks blocked (Appendix L). |
| Interventions | Same backbone, workflow changed: instruction-failure decks 15→1, cropping/occlusion decks 11→12 (Section 5.3). Controlled defect injection turns all 10 targeted instruction verdicts from pass to fail, worsens 9 of 10 targeted content verdicts, and lowers 8 of 10 targeted page scores (Appendix H.2). |

**Revisions to the paper:** (1) a walk-through of one task from request to decision (Appendix I); (2) the blinded audit and the specification-exclusion analysis (Section 5.4, Appendix J, Table 13); (3) the single-candidate ablation and a clarified description of how instruction and content specifications are built (Section 4.1, Appendix C); (4) information- and judge-controlled comparisons and the page-level dilution analysis (Section 5.2, Appendix K); (5) the rendering pipeline, the text-overflow analysis and two additional systems (Appendices J and L); (6) Table 12 computed directly from the released item-level annotation file; (7) PPTEval recomputed using content and design only for 39 decks whose coherence response could not be parsed and had been recorded as zero (AUROC .666, p = .031, FPR 73.2%), so four of six schemes now separate the groups, while none screens individual decks at high recall without flagging most of the others; (8) request provenance and the collection protocol (Appendix A).
```

## 03. Response to Reviewer 6R1G

- 发在：回复 Reviewer 6R1G 的审稿意见
- Title：`Response to Reviewer 6R1G: New Evaluation Capabilities and System Coverage`
- 字符数：4329（上限 5,000）

```markdown
We thank the reviewer for the thoughtful comments and for recognizing that a presentation "can look visually appealing while still missing key information or violating explicit instructions."

**W1. New evaluation capabilities beyond PresentBench, PPTBench and SlideAudit.**

We would like to clarify that our contribution is not the observation that averages can hide errors. The failures that decide delivery are relations between a deck and its request, its source material, or its rendered page; an evaluator that reads only the slides cannot observe the first two, however it aggregates (see the walk-through in the General Response and Appendix I). SlideGate adds three capabilities that, to our knowledge, the cited works do not provide together:

- **Specifications built automatically from the user's own request and attachments, frozen before any output is seen.** PresentBench writes a controlled instruction for each instance and designs its checklist manually. SlideGate derives items from the requests actually given to the systems, which range from one sentence to multi-section briefs, templates and edits of existing decks and mostly originate from practitioners' own work; each item keeps its request quotation or source location.
- **Non-compensatory decisions.** PresentBench aggregates item verdicts into an overall score. In SlideGate, an unmet hard requirement, a missing required item, or a cropped or occluded page yields a blocking flag with item IDs and page numbers that quality scores cannot offset.
- **A test of whether existing scores can screen delivery.** With thresholds set for at least 90% recall, the six schemes flag 73–100% of held-out decks without a detected failure.

Our controls separate these capabilities from aggregation and from extra input. Deck-level aggregation dilutes visual signals: SlideAudit's cut-off/occlusion categories fire on 92.0% of the 88 defect pages, yet one hit lowers a 12-page deck's score by about .004. Extra input helps but does not replace item-wise checking: the same judge given the request, the full attachment text and all pages, but no frozen specification, flags 17 of the 71 SlideGate content failures (Section 5.2). Section 6 now also shows an investor deck that ranks first among six under four existing scores while omitting the core figures of its attached data.

**W2. Coverage of systems.**

Thank you for this suggestion. We would first like to explain how the systems were chosen. The paper's claims concern the evaluation instrument rather than a leaderboard: blocking failures fall into three largely separate types, and existing quality scores cannot screen them. We therefore selected the initial systems to represent several deck-generation workflows. They were the publicly available slide generators we could access during collection and span dedicated slide tools (AnyGen, Kimi), a chat assistant's slide entry (Doubao) and multi-step agents (Skywork, MiniMax, Manus) (Table 5). The tasks already cover the workflows you mention, with 17 document-based generation, 6 editing and 5 template tasks. Collection through these commercial interfaces involves manual submission, export and subscription access, which limited the size of the initial collection.

To test whether the findings extend beyond these six, we added Codex (code-generated PPTX) and NotebookLM (source-grounded generation, partly delivered as full-page images) on 12 tasks spanning one-sentence, detailed, document-based, template and editing requests (Appendix L). The frozen specifications apply unchanged: 3/12 Codex and 1/12 NotebookLM decks are blocked. One Codex content failure involves an item whose source name had been replaced by a placeholder in the de-identified attachment; excluding that item leaves two blocked Codex decks among the same 12 outputs. The failures again fall into the paper's categories while taking new forms: a Codex physics deck matches the original lecture page for page, yet all of its roughly 100 formula objects are gone, which only a source-grounded check reveals.

In summary, the frozen specifications apply without modification to workflows outside the original six and identify failures within the same defined categories. As the added outputs were collected later, we report them as a transfer test rather than a ranking.
```

## 04. Response to Reviewer uV2j

- 发在：回复 Reviewer uV2j 的审稿意见
- Title：`Response to Reviewer uV2j: Task Scope, Evaluation Coverage, Label Reliability, and Interventions`
- 字符数：3554（上限 5,000）

```markdown
We thank the reviewer for the helpful comments and for noting that task-specific diagnosis across generation settings "is helpful for real-world usage."

**W1. Scope of the task.**

We appreciate this point. While a presentation is a single artifact, producing one involves several capabilities at once: understanding the user's constraints, reading heterogeneous attachments, organizing content logic, laying out text and visuals with aesthetic quality, and delivering a file in which every page is readable. In our set, one request asks for a lesson-two deck that follows a separate production guideline; another asks to restyle a deck "without changing the main content or background"; a third asks to keep every formula of a 17-page physics lecture. Covering seven scenarios and five input forms, we hope the benchmark can serve as a demanding testbed for these combined abilities.

**W2. Comparison with more methods; completeness of the metric system.**

Beyond 6 systems, a same-backbone workflow comparison and 6 evaluation frameworks, we now add 2 systems and controls for information and judge (Section 5.2, Appendices K–L). On completeness, the evaluation covers instruction following, content coverage, depth and source faithfulness, four visual-defect checks, six design criteria and three aesthetic criteria with cross-page consistency (Table 2, Appendix B). These are organized by what a deck can be checked against: the request, the supplied materials and its rendered pages. SlideGate defines one delivery condition for each (a failed hard instruction, a missing required-content item, and page-level cropping or occlusion), applies them as non-compensatory gates, and keeps the remaining judgments as separate quality scores. Since 88 of the 124 blocked decks fail exactly one condition, dropping any condition would pass decks that the others reject.

**W3. LM-based evaluation and label noise.**

SlideGate is automated by design, so that it can be re-run on new systems without new annotation, as we did for Codex and NotebookLM. Its judgments are constrained to make them checkable: every item is fixed in advance with its request span or source location, so the judge answers a narrow question such as "does section 4 exist"; page counts are decided by code; and every verdict returns evidence pages. Human studies then validate the design: two blinded annotators confirm a blocking failure in all 15 audited flagged decks (Appendix J), content-item judgments agree with annotators at 80.7% and 85.6%, and controlled defect injection turns all 10 targeted instruction verdicts from pass to fail, worsens 9 of 10 targeted content verdicts and lowers 8 of 10 targeted page scores (Appendix H). Regarding attribution, the commercial results characterize end-to-end outputs rather than isolated backbone abilities, which the same-backbone comparison addresses (W4).

**W4. Intervention analysis by failure type.**

Thank you for this suggestion. The direct-versus-workflow comparison is an intervention on the generator: with the backbone fixed, instruction-failure decks fall from 15 to 1, while cropping/occlusion decks go from 11 to 12 (Section 5.3). We add interventions on the evaluator: using AutoPresent's worst page instead of its mean raises visual-failure AUROC from .66 to .81, and giving a judge full task information without a frozen specification flags 17 of the 71 SlideGate content failures (Appendix K). Different failure types respond to different changes, which we hope helps system builders decide where to improve.
```

## 05. Response to Reviewer uYyY (1/2)

- 发在：回复 Reviewer uYyY 的审稿意见
- Title：`Response to Reviewer uYyY (1/2): Blocking-Label Audit, Specification Annotations, and Controlled Comparisons`
- 字符数：3231（上限 5,000）

```markdown
We are grateful for the reviewer's detailed reading and concrete suggestions, and for the note that the design remains valuable even if the claims about existing scores were narrowed. We followed the suggested analyses.

**W1 / Q1 / Q2. Accuracy of the final blocking labels and the effect of specification annotations.**

Following your suggestion, two annotators reviewed 30 decks (15 flagged, 15 not) blind to system identity and to SlideGate's verdicts, checking each against the request, the original attachments and every page. Both confirmed a blocking failure in all 15 flagged decks; inter-annotator κ per failure type is .66–.86. Among the 15 unflagged decks, annotators A and B identified a blocking failure in six and five, three of them in common (Section 5.4, Appendix J). If 3/15 of the 82 screening negatives contained blocking failures and all of them were among SlideAudit's false alarms, its FPR at the same operating point would still be about 71%.

We also recomputed the findings under the specification annotations (Table 13):

| Content items | Content failures | Blocked decks | SlideAudit AUROC | SlideAudit FPR |
|---|---|---|---|---|
| All 270 items | 71 | 124 | .672 | 76.8% |
| Without the 12 items both annotators judged unnecessary | 64–69 | 121–123 | .676–.686 | 77.1–77.6% |
| Also without the 14 disputed items | 51–67 | 117–122 | .674–.683 | 77.1–77.9% |

Ranges treat decks whose status cannot be determined after removal as failing or as excluded. Thank you also for checking the agreement statistic: the revised Table 12 is computed directly from the released item-level annotation file (244 items required by both annotators, 12 by neither, 14 disputed; Cohen's κ = .61 with 94.8% raw agreement and Gwet's AC1 = .94, as about 90% of items fall in one class), and the analysis above uses exactly these labels. A blocking flag states a failed necessary condition for delivery; partially covered content, which SlideGate scores as partial by design, is reported but not gated.

**W2. Information, judge, and visual defects.**

We agree these factors should be separated. Given the request, the full attachment text and every page, but no frozen specification, the same Sonnet 4.6 judge reaches AUROC .765, yet its own flags recover only 69 of 124 blocked decks and 17 of 71 content failures, while both annotators confirmed a blocking failure in each of the 15 audited flagged decks. Re-running SlideAudit with Sonnet 4.6 raises AUROC from .672 to .725, with FPR still 79.3% at 89.5% recall (Section 5.2, Appendix K).

We also agree that several schemes assess overlap and bounds, and they do respond to defective pages: within the same deck, their page scores rank defect pages below the others with AUROC .70–.91, and SlideAudit's categories fire on 92.0% of the 88 flagged pages. The signal is diluted at deck level: one hit lowers a 12-page deck's SlideAudit score by about .004; AutoPresent's worst page instead of its mean raises visual-failure AUROC from .66 to .81; and alarming on any SlideAudit hit reaches 95% recall but flags 54% of decks without a detected failure. We therefore see detecting a defect on a page and making a delivery decision as related but different capabilities.
```

## 06. Response to Reviewer uYyY (2/2)

- 发在：回复第 5 条（Response to Reviewer uYyY 1/2）
- Title：`Response to Reviewer uYyY (2/2): Specification Construction, Rendering, and Request Provenance`
- 字符数：4320（上限 5,000）

```markdown
**Q3. A single candidate specification versus the full procedure.**

With judge, prompt, requests and sources fixed, we scored 72 decks (12 tasks × 6 systems) with each of three single-candidate instruction specifications and with the final one (Appendix C). On the deck-level 1–5 instruction rating that the judge returns with its item verdicts, a single candidate agrees exactly with the final specification on 71–74% of decks (Spearman .59–.68), and the system ranking changes (Kendall .60–.83): all three single candidates rank Doubao first, while the final specification ranks AnyGen first. Deck-level instruction-failure flags differ on 6–7 of the 72 decks; the final specification flags 15 decks and each single candidate 11–13, so most changes are failures a single candidate misses. For example, on the task "organize the contents and images of the two files", all single candidates give a score of 5 to two decks that use at most one of the attachments' 27 embedded images; only the consolidated specification retains the image requirement as a hard item, and both decks receive 2. In an audit of earlier single-pass labels, an internal page-count estimate was treated as a hard constraint on 19 of 40 tasks, inferred requirements were scored on 17, and optional wording was upgraded to mandatory on 9; consolidation against the request text, critique and rule validation are designed to remove these, and freezing ensures all systems face the same items. We have also clarified in Section 4.1 that the three-candidate procedure applies to instruction specifications, while content specifications use source-constrained extraction, code validation and a critic that may only remove items.

**Q4. Saving and rendering.**

Thank you for raising this. We evaluate the file each system delivers: the exported PPTX for all six systems, including Manus's PPTX export from its web-slide interface. All files go through one pipeline without per-system tuning: LibreOffice 6.4.7 headless to PDF, then pdftoppm at 150 dpi, yielding 3,026 pages (Appendix J). We view defects introduced by a product's own export as part of its delivery quality. Fonts are chosen by the generating system; fonts not installed on the rendering machine are replaced by LibreOffice's fallback fonts, as they would be for a user opening the file in the same environment. Flags are determined on the delivered file rather than on in-app previews, because the file is what users receive. Since text overflow is the defect most sensitive to font substitution, we also keep only defects classified as occlusion or elements beyond the page: 120 of 124 decks remain blocked. In the Codex physics deck, the same pipeline renders all of roughly 100 formula objects in the original lecture, whereas the delivered file contains none of them, so the information is lost before rendering.

**Q5. Requests, selection, and generation protocol.**

We have added these details to Appendix A. We selected the 40 tasks by stratifying over scenario and input form. The 28 tasks with attachments come from real use: we invited practitioners from a range of industries to use an internal presentation-generation system for their own work, and de-identified the content while keeping input forms and scenarios. In that system a user types a message and also selects the scenario, audience, length and role; the formal request merges the message, the selected options and the attachment names into one instruction, and is identical to the message when the message already states them. The 12 text-only tasks cover brief and detailed requests without materials; their topics are drawn from a library of roles and presentation topics with sampled style parameters, and during test-set construction each short topic message was expanded into a detailed request stating audience, structure, style and length, so that the set spans a controlled range of request complexity; their input-form labels follow the original test-set design (six brief, six detailed). The released task files contain both the opening message and the formal request. All formal requests were fixed before any system output was collected. Runs that produced no deliverable were resubmitted; the first delivered deck was kept, without manual edits and without selection among multiple results.

---
```
