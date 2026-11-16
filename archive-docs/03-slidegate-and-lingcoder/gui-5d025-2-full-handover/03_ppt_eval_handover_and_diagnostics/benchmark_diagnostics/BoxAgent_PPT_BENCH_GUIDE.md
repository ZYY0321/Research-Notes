# PPTBench on AgentCompass

This integration imports the 47-question PPTBench industry set in two modes:
47 original prompts plus the same 47 prompts bound to the supplied templates.
The resulting 94 CustomBenchmark tasks retain Box-Agent's native files but are
scored through PPTBench's original folder pipeline. Artifact discovery first
uses non-empty `htmls/page_*.html`, then accepts Box-Agent's equivalent
`slides/slide_*.html`, final renders, or `present.html` as compatibility
inputs. `task_pack.json` is not an evaluation contract.

## Dataset

Regenerate into a new destination; the importer intentionally never overwrites
an existing dataset:

```bash
python3 scripts/import_ppt_bench.py \
  --source /home/sensebench/code/yyb/ppt-bench \
  --destination /data1/chenyanbing/agentcompass_data/custom/ppt-bench
ln -s /data1/chenyanbing/agentcompass_data/custom/ppt-bench data/custom/ppt-bench
```

`manifest.json` records the source revision and input/attachment hashes.
Attachments are copied once under `assets/` and hard-linked into both mode
workspaces.

## Box-Agent image

The build uses the delivered Box-Agent source pinned to
`2aba016638c6b5c27bf3216383bcb37e54b75bde`, the matching ACP evaluator,
Node 24, the 20 PPTBench templates, and the Playwright Chromium runtime.
Runtime version `0.9.7` is recorded in `docker/box-agent-ppt/VERSION`; the
canonical image tag is `agentcompass-box-agent-ppt:v0.9.7`. The build script
checks the Box-Agent commit and template count before building.

To select another image prepared by the `box-agent-image-manager` skill, set
`PPT_BENCH_BOX_AGENT_IMAGE`. The launcher validates the image and forwards the
selection through AgentCompass environment parameters:

```bash
PPT_BENCH_BOX_AGENT_IMAGE=agentcompass-box-agent-ppt:v0.9.8 \
  scripts/run_ppt_bench.sh qwen3.6-plus
```

```bash
docker/box-agent-ppt/ensure-image.sh
```

`ensure-image.sh` reuses a valid local image and builds it when missing. Override
`BOX_AGENT_SOURCE`, `PPT_TEMPLATES_SOURCE`, or `BOX_NODE_ARCHIVE` when the
delivery bundle is stored elsewhere. A truly source-free setup requires the
versioned image to be published to a registry; this repository does not assume
a registry destination.

## Run

Install AgentCompass, prepare the independent PPT evaluator profile described
in `PPT_AUTO_EVAL_GUIDE.md`, and provide the candidate model through normal
AgentCompass model flags:

```bash
export PPT_EVAL_PROFILE="$PWD/configs/ppt-eval.local.yaml"
export SERPER_API_KEY=...

scripts/run_ppt_bench.sh candidate-model \
  --benchmark-params '{"sample_ids":["ppt-bench-notpl-seq_0007"]}'
```

The launcher runs the image check/build before invoking AgentCompass. To prepare
the image without starting a benchmark, use
`scripts/run_ppt_bench.sh --ensure-image-only`.

The preset writes a private per-case Box-Agent model profile, selects the
`sn-ppt-entry` skill, auto-approves the plan and one-shot tool permissions, and
masks evaluator keys from the candidate process. The upstream PPT evaluator
uses its original `evaluate_one_folder` page/deck/content stages without the
AgentCompass checklist-summary revalidation layer. Candidate task concurrency
is 20 in the preset; Judge execution is independently limited to the original
four-worker pool. Its compatibility wrapper also
continues a bounded number of incomplete ACP turns so an unattended run can use
sensible defaults instead of stopping to ask which authoring mode to use.
