# SlideGate — ICLR 2027 English + Chinese reading copy

Upload the accompanying ZIP with Overleaf → New Project → Upload Project, or replace the matching files in your existing project.

- `main.tex`: English paper first, Chinese reading copy afterward. Use **XeLaTeX**.
- `submission.tex`: English-only anonymous submission. Use **pdfLaTeX** or **XeLaTeX**. Select this main document before exporting a submission PDF.
- The English abstract is the confirmed archived version; the original title is retained.
- Both introductions restore the pre-supplement version after the author's correction. No new 206-output/AUROC paragraph is inserted into the introduction.
- Chinese source/output screenshots remain as evidence in the English paper.

## Sources

- Original confirmed title: `SlideGate: Benchmarking Presentation Generation with Dimension-Specific Verification`.
- Abstract: exact wording from `../摘要英文_用户确认留档_20260918.md`; only Markdown bold and percent-sign escaping were adapted for LaTeX.
- Introduction: restored from `../补充分析_失败筛查/SlideGate_补充筛查前快照.md`, verified against the original pasted manuscript. The later 206-output/AUROC introduction was an assistant edit and has been removed. Body: the combined `../SlideGate_最终正式稿.md`.
- Tables 1–7: the combined manuscript. The initial 235-output grouping p-values come from `../补充分析_失败筛查/metrics.json`.
- Supplementary penalty and weight-grid analyses: `../../overleaf_v20/en.tex`, explicitly labeled as historical snapshots.
- Four existing figures: the v20 figure directory. The coverage figure is in the main text; task examples, ranking conflicts, and source evidence are in the appendix. English labels accompany original-language slide screenshots.

## Official format

Official download, retrieved 2026-09-18:
https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip

The `.sty`, `.bst`, `natbib.sty`, and `fancyhdr.sty` are unmodified official files. All four also match the files in the old v20 project byte for byte: that project used an authentic template but was a bilingual mentor draft, not a finished submission.

AI use statement is required; ethics and reproducibility statements are recommended. They have been added after the conclusion and before references, outside the main-text page budget. Requirements:
https://iclr.cc/Conferences/2027/AuthorGuidelines
https://iclr.cc/Conferences/2027/AIPolicyForAuthors

## Editorial changes

- Preserved the confirmed abstract and original title.
- Removed claims that tasks are verified real-user or real-business submissions, following the author's correction.
- Translated and tightened the latest text; retained all seven result tables and their values. Repetitive explanatory sentences were consolidated; detailed visual criteria and three figures are in the appendix.
- Kept the 240 collected / 235 commonly scored / 206 determinate-union / 186 complete-case cohorts distinct. The abstract's initial five nonsignificant schemes refer to the 235-output grouping; the 78.0% FPR refers to held-out screening on 206 outputs.
- Replaced placeholder bibliography records with verified publication metadata. PPTEval is cited through PPTAgent. Corrected AutoPresent's venue to CVPR 2025 and PresentBench's year to 2026; removed the incorrect assertion that PresentBench evaluates only one system.
- Added an AI-use disclosure based on the assistance actually used in this workflow. It does not invent ethics approval, participant consent, or a claim that all AI outputs have already been manually validated.

## Author checks still needed before the full-paper deadline

These are unresolved research/reporting details inherited from the source, not LaTeX errors:

1. Check the draft AI/ethics/reproducibility disclosures against all authors' actual practices. In particular, disclose any additional AI task-data or figure generation and document participant procedures and applicable permissions. Do not infer consent or institutional approval from the supplied wording.
2. Confirm model identifiers, evaluator prompts/versions, service access dates, the paired baseline's backbone, paired sample counts, and statistical test names. The source manuscript does not provide a complete methods manifest; none has been invented here.
3. Confirm the visual penalty denominator/normalization, the ten-system human-ranking membership, and why the historical .829 and main .855 correlations use different references/snapshots.
4. Independently review the AnyGen zero-coverage case and any product/author affiliation disclosure. The source marks these as awaiting confirmation.
5. The initial five nonsignificant comparisons include 29 outputs with incomplete failure judgments. This is explicitly disclosed in the main text and appendix; it is not a five-method equivalence claim on the 206-output cohort.
6. Finalize data/material release permissions and the empirical checklist-completeness and source-faithfulness limitations. Formatting the paper does not resolve those validation questions.

The old v20 is preserved as history. The prior modified introduction was backed up before restoration. Chinese prose is included in the default reading copy; submission.tex excludes it.

## Build verification

Both entry points compiled locally using Tectonic/XeTeX. English main text ends on page 9 in both versions. The English-only PDF has 14 pages including statements, references, and appendix. The bilingual PDF has 24 pages; Chinese starts on page 15. No overfull boxes, missing glyphs, or undefined references remain.
