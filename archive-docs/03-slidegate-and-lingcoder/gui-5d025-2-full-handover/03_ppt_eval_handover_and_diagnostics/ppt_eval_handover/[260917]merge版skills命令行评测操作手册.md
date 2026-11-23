# merge版skills命令行评测操作手册

适用机器：`/home/gui-5d025-2/zyy/xhx_agent_v3` 所在评测机。更新：2026-09-17。

目标：不修改现有 `automation/` 源码、不替换平台默认skills、不重启原平台，单独评测一个固定提交的merge版skills，结果进入现有8770结果看板。

**本文件是操作说明，不表示文中的任务已经启动。先填参数，再按顺序执行。** 示例针对当前 `aipptx-templates/skills/agent-3.0` 的 OpenAI 兼容模型评测；不直接适用于Anthropic协议或任意结构的skills仓库。

<a id="choose-skill-source"></a>

## 先选一种测试方式

第一次使用，先看情况一、二。已经用本手册测过，再根据这次是否更换模型或 skill 版本，选择情况三、四、五。只执行与你目的相符的一种。

### 情况一：使用平台默认 skills（/home/gui-5d025-2/zyy/xhx_agent_v3/skills/ppt-maker），和平时网页测试一样

直接在[平台新建任务页](http://10.151.196.17:8770/automation/new)填写模型等参数并创建任务。**不用执行本手册后面的 merge 测试步骤。**



只需要填写：

1. 【标志 / 任务名】：写要测试的模型名字，比如： SenseNova-Flash-Lite-20260727-v39-fp8-step4k-dpov2-mtp


2. 【served 模型名(/v1/models 里的 id)】写要测试的模型名字，比如： SenseNova-Flash-Lite-20260727-v39-fp8-step4k-dpov2-mtp


3. 【主 LLM 端点】：比如 10.210.9.14:208


4. 【review model（可空）】：留空的时候等于主模型，探活失败可以基于探活失败的报错，修改为报错信息里面显示的api serve的实际model name，比如checkpoint-148这种输出

5. 填完之后点击【探活】，探活成功之后 【直接开始跑批】

---

**评分用的 TokenHub Key 需要重新配置时，见[附录：更换评分 Key，并同步命令行测试](#optional-platform-judge-key)。**

---

### 情况二：第一次使用这份手册测试自己开发的 skills

从[第1节](#section-1)开始：第1.2节选择要测的 skill 版本，第1.3节填写模型信息、创建测试目录，然后按第2节及后续步骤依次操作。

<a id="reuse-skill-new-model"></a>

### 情况三：换模型，skill 版本与上次相同

例如：上次测 SenseNova v1 版本，这次换成v2 版本，但仍用上次的 skill commit。

1. 按[第8.1节](#section-8-restore)选中使用该 skill 版本的旧测试，取回它保存的版本号。当前终端已选中它，就不用重复选择。
2. **跳过第1.2节，直接从[第1.3节](#section-1-3)开始**，填写新模型名和地址、创建新测试目录，再从第2节继续。

不用重新选分支或提交 skill。第1.3节输出后，确认是**新模型、原 skill 版本、新目录**；旧测试结果会保留。

### 情况四：修改了 skill，要测试新版本

从[第1.2节](#section-1-2)开始：已提交的修改走[情况A](#skill-case-a)选择版本，未提交的修改走[情况B](#skill-case-b)检查并提交。然后在[第1.3节](#section-1-3)填写待测模型、创建新测试，继续第2节及后续步骤。模型可以沿用上次的，也可以更换。

<a id="same-model-skill"></a>

### 情况五：模型和 skill commit 都与上次相同

**想用之前的版本重新完整测一次：** 按[第8.1节](#section-8-restore)选回旧测试，再从[第1.3节](#section-1-3)开始，填写相同的模型名和地址、创建新测试目录，之后从第2节继续。跳过第1.2节，不用重新提交或选择 commit；这次结果单独保存，不覆盖上次结果。

**上次运行中断，只想接着完成原测试：** 按[第12节](#section-12)的中断处理步骤操作，保留原目录；不用从第1节重新开始，也不要新建测试。具体选择命令和续跑命令都在第12节说明。

## 常用操作跳转

| 你要做的事 | 去哪里 |
|---|---|
| 换模型，沿用上次的 skill 版本 | 按上面的[情况三](#reuse-skill-new-model)，加载旧版本后从第1.3节创建新测试 |
| 只想查看日志和生成进度 | [第8节](#section-8) |
| 给正式测试的PPT评分、更新看板 | [第9节](#section-9) |
| 需要主动停止正在运行的测试 | [第11节](#section-11)，已有产物保留 |
| 正式生成、评分、上板完成，需要分析Token与耗时 | [第10节](#section-10) |
| 已启动的正式任务中断，需要补跑 | [第12节](#section-12)，保留原测试目录 |

首次测试的顺序是：**选择skill版本 → 填模型信息 → 复制skills → 配置模型调用 → 生成配置 → 检查连接 → 两种模式各试1题 → 正式生成 → 查看进度 → 评分与上板 → Token与耗时分析。** 前4节主要准备文件；第5节开始实际调用服务。

操作时一次只复制一个代码块，保留换行，不复制代码框外的文字。命令中的“填写…”需要替换；`$PPT_ROOT`、`$CTL` 等以 `$` 开头的内容是前面自动保存的变量，不用手工替换。每步看到成功提示才继续；出现错误就先停下。脚本细节放在链接中，正常使用只执行手册里的短命令。

<a id="section-0"></a>

## 0. 先搞清楚本次改动范围

| 内容 | 本流程怎么处理 |
|---|---|
| 主agent实现 | 复用 `xhx_agent_v3/agents/agentv3` 等当前代码；不切主仓分支 |
| skills业务代码 | 从指定Git提交导出，不直接使用还在修改的工作目录 |
| 技能依赖 | 以当前评测底座补齐通用技能，再按目录整体替换merge版技能 |
| 模板素材 | 使用同一个merge提交的 `templates/styles` |
| 模型调用适配 | 只在本批skills副本中接入现有评测transport，保留差异记录 |
| 主agent配置、密钥、状态、日志 | 放在本批 `output/<RUN_ID>_control/` 下 |
| 原 `automation/` | 只读复用模块，不修改源码、不写入它的任务目录 |
| 评分互斥 | 继续使用全机现有全局评分锁，不另开一条绕锁的评分管线 |
| 结果看板 | 登记到 `results_dashboard/runs.json`，在8770结果页查看 |

**命令行任务不会自动出现在 `/automation` 的任务列表中。** 那个页面扫描的是它自己的 `automation/tasks/`；本流程将状态放在外部目录。任务可以显示在同一站点的**结果看板首页** `http://10.151.196.17:8770/`。

本流程隔离的是skills版本。若merge还修改了主agent的Python代码，应另建对应代码的checkout/worktree，不能只改 `skills_dir`。评测期间也不要修改本批skills副本或主agent代码；需要改版时另建RUN_ID。

<a id="section-1"></a>

## 1. 在评测机终端选择 skill 版本、填写模型参数

**从本节开始，所有参数都在评测机的 Bash 终端里填写，不需要打开平台网页或在网页创建任务。**

先看第1.1节了解参数含义，再按[第1.2节](#section-1-2)选择 skill 版本，最后在[第1.3节](#section-1-3)的命令中填写模型名和地址。任务名与 served 模型名相同时只填一次模型名；不同时按第1.3节说明单独设置 served 模型名。

沙盒默认使用腾讯云，review 默认与主模型相同，HTML 生成端点按脚本的默认规则配置，通常无需另外填写。下面的“平台字段”仅用于对照你熟悉的名称，不表示需要去网页操作。

<a id="section-1-1"></a>

### 1.1 平台字段与命令行参数对照

| 平台字段 | 本手册变量 | 填什么 |
|---|---|---|
| 标志 / 任务名 | `TASK_NAME` | 填待测模型名字，使用英文、数字、下划线或短横线，例如 模型名字`SenseNova-Flash-Lite-20260727-v39-fp8-step4k-dpov2-mtp` |
| 主 LLM 端点 | `MODEL_BASE` | 填模型服务地址，例如 `10.210.9.14:208`；和页面一样，可不写 `http://` 和 `/v1` |
| served 模型名 | `MODEL_ID` | 默认填同一个模型名字 |
| 看板显示名 label | `MODEL_DISPLAY` | 不需要另外填，默认用 served 模型名，和平台 label 留空一致 |
| 沙盒地址 | `SANDBOX_BASE` | 不需要填，沿用腾讯云 `http://62.234.119.98:3000` |
| HTML skill 生成端点 / 模型名 | `HTML_BASE` / `MODEL_ID` | 不需要填，复用平台默认及已有中继规则 |
| review 模型 | `REVIEW_MODEL` / `REVIEW_BASE` | 不需要填，复用平台“与主模型相同”规则；不是跟随 HTML 中继地址 |
| 协议 / 并发 / thinking / reasoning_effort / 跳过 review | 后续命令固定沿用 | `openai` / `4` / 开启 / `xhigh` / 不跳过 |

例如：任务名填 `SenseNova-Flash-Lite-20260727-v39-fp8-step4k-dpov2-mtp`、主端点填 `10.210.9.14:208`，served 名也填 `SenseNova-Flash-Lite-20260727-v39-fp8-step4k-dpov2-mtp` 即可。示例地址只说明格式，执行时换成待测服务地址。

<a id="section-1-2"></a>

### 1.2 先确认分支，再选择要测试的 skill 版本

本节要做的是：找到你修改 `ppt-maker` 的仓库，确认分支，然后选定这次要测试的版本。**先完成下面的路径和分支检查，再选择情况 A 或 B。**

#### 第一步：设置技能仓库位置，查看当前分支

如果你的 skills 就放在下面的目录，三行代码直接复制即可；如果放在另一个目录，只改第一行的路径。执行后只会保存路径、显示状态，不会切分支或提交代码。

```bash
export SKILL_REPO='/home/gui-5d025-2/zyy/aipptx-templates'
export SKILL_SUBDIR='skills/agent-3.0'
git -c core.quotePath=false -C "$SKILL_REPO" status --short --branch
```

**成功时会看到：**

```text
## test/ppt-outline-merge
 M skills/agent-3.0/ppt-maker/SKILL.md
```

- `##` 后面是当前分支名。请确认是不是你这次开发的分支；示例分支名不用照抄。
- `M` 表示文件有修改，`??` 表示新增文件尚未被 Git 跟踪，都不是报错。
- 只有分支名、没有文件列表，通常表示没有待提交的改动（Git忽略的文件不会列出）。

如果出现 `cannot change to` 或 `not a git repository`，说明仓库路径不对，修正第一行后再执行。若当前分支不是你想测的分支：测已提交的内容可直接用[情况 A2](#skill-case-a-branch)指定分支；需要提交本地修改时，先按[可选分支操作](#optional-skill-branch)核对并切换，不要直接提交到错误分支。

**第二行为什么是 `skills/agent-3.0`？** 它表示这一套技能在仓库里的位置，完整入口路径是：

```text
仓库：/home/gui-5d025-2/zyy/aipptx-templates
技能目录：skills/agent-3.0
入口文件：skills/agent-3.0/ppt-maker/SKILL.md
```

只换分支、没改目录结构时，第二行不用改。后面会把这份入口和同版本的模板/无模板技能一起复制到本次测试目录，平台默认 skills 不会被替换。

#### 第二步：下面两种情况，只选一种

| 你现在的情况 | 接下来做什么 |
|---|---|
| 要测的修改已经 commit，需要选定这个版本 | 去[情况 A：选择已提交版本](#skill-case-a)，不用重新提交 |
| 要测的修改还没 commit | 去[情况 B：检查并提交修改](#skill-case-b) |

A 或 B 完成后，都进入[第1.3节：填写模型信息](#section-1-3)。不要把 A、B 当作两步连续执行。

<a id="skill-case-a"></a>

#### 情况 A：修改已经提交，选择一个已提交版本测试

**本节用于选择一个已提交的 skill 版本。** 如果只是换模型、沿用某次旧测试的同一版本，按开头的[情况三](#reuse-skill-new-model)操作即可，不用执行本节。需要重新选择版本时，先查看提交记录，再从 A1、A2、A3 中选一种，不要依次全部执行。

先运行下面两行，查看当前分支和它最近5次提交，**第一条提交就是当前分支最新版本**：

```bash
git -C "$SKILL_REPO" branch --show-current
git -C "$SKILL_REPO" --no-pager log -5 --format='%h %s'
```

例如本次仓库显示：

```text
test/ppt-outline-merge
349d5d4 Prepare merged PPT skills for evaluation
fd73ea7 refactor(ppt): make outline.md the sole outline contract
```

第一行是分支名；`349d5d4`、`fd73ea7` 是各次提交的短版本号。本文说的“版本号”就是 Git 的 commit SHA，可理解为每次提交的唯一编号。以你的实际输出为准；下面的脚本会自动获取完整编号并保存，不需要手抄。

<a id="skill-case-a-latest"></a>

**A1．测当前分支最新提交（常规用这个，不需要填写版本号）**

确认上面显示的分支就是你要测的开发分支后，直接执行：

```bash
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_skill_prepare.sh select HEAD || echo '版本选择失败，请查看提示'
```

请保留命令开头的 `source`：它会让选好的版本号留在当前终端，供下一步使用。脚本细节在 [merge_skill_prepare.sh](scripts/merge_skill_prepare.sh)，正常操作无需打开或修改它。

`HEAD` 在你已处于开发分支时，表示这个分支当前最新的已提交版本。这里的 `HEAD` 原样保留，不需要替换成一串 SHA。它不会包含本地尚未提交的修改，也不会自动获取远端更新。如果分支检查没有输出分支名、处于 detached HEAD，则 `HEAD` 只表示当前检出的提交，不代表某个分支最新版本，此时请按 A2 指定分支。

<a id="skill-case-a-branch"></a>

**A2．测指定本地分支的最新提交（当前不在该分支时用）**

先列出本地分支；这一步只查看，不切分支：

```bash
git -C "$SKILL_REPO" branch --list
```

选择要测的分支，把下面示例 `test/ppt-outline-merge` 换成它的名称。若本次就是测这个分支，直接使用示例即可：

```bash
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_skill_prepare.sh select 'test/ppt-outline-merge' || echo '版本选择失败，请查看提示'
```

脚本直接获取该本地分支的最新 commit，不需要先切过去；其他分支不会被修改。

<a id="skill-case-a-specific"></a>

**A3．测指定提交（复测旧版本、保持不同模型的 skill 版本一致时用）**

从上面的提交列表选一个短 SHA，或使用之前记录的完整 SHA，填到 `select` 后。例如，继续使用你已经提交的这一个版本：

```bash
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_skill_prepare.sh select '349d5d41bce11c2e123e011ee9b102941172c459' || echo '版本选择失败，请查看提示'
```

若想查看另一分支的历史记录，可以运行 `git -C "$SKILL_REPO" --no-pager log -5 --oneline '分支名'`，再从中选择 SHA。上面的完整 SHA 是本次已提交版本，不需要重新生成；短 SHA 只要能唯一定位提交也可以使用。

**怎样判断选择成功：** 不论 A1、A2 还是 A3，都会输出完整 SHA、提交说明，以及 `版本选择成功，可以继续第1.3节。`。例如：

```text
349d5d41bce11c2e123e011ee9b102941172c459 Prepare merged PPT skills for evaluation
版本选择成功，可以继续第1.3节。
```

这时 `SKILL_REF` 已自动保存，不需要再手动 export 版本号。想再次确认当前选定的值，只需：

```bash
printf '本次选定的skill版本：%s\n' "$SKILL_REF"
```

然后进入[第1.3节](#section-1-3)，填写这次要测的模型名和地址，创建新的测试目录。此处已选好版本，不要再加载旧测试的参数，以免覆盖刚选定的版本。创建后即使分支有了新提交，本次测试仍使用已选定的版本。

<a id="skill-case-b"></a>

#### 情况 B：要测的修改还没提交，先检查再提交

本流程只测试已经 commit 的内容。如果这次不想提交，可以停在这里，或回[情况 A](#skill-case-a)选以前提交过的版本。

<a id="skill-branch-check"></a>

**B1．确认提交到哪个分支**

运行下面一行，记录当前分支，后面的提交会落在这个分支上：

```bash
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_skill_prepare.sh check || echo '分支检查未完成，请查看提示'
```

**成功时显示：** `分支检查成功：本次将在 test/ppt-outline-merge 上提交修改`。分支名以实际输出为准。确认它就是本次开发分支，再做 B2；如果不是，先看[可选分支操作](#optional-skill-branch)。这一步没有提交代码。

**B2．查看这次改了哪些文件**

```bash
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_skill_prepare.sh diff || echo '查看改动失败，请查看提示'
```

**正常输出：** 文件列表和修改内容。`+` 表示新增内容，`-` 表示删除内容；新增但未跟踪的文件此时可能只显示文件名，下一步会显示其内容。没有改动可查看时，确认是否已提交过，已提交则改走[情况 A](#skill-case-a)。

**B3．把要提交的改动放入暂存区，再审阅一次**

“暂存区”就是准备提交的文件清单。这一步默认加入 `skills/agent-3.0` 和 `templates/styles` 中的改动，但还不创建提交：

```bash
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_skill_prepare.sh stage || echo '准备提交清单失败，请查看提示'
```

**正常输出：** 改动文件统计、具体差异，最后显示 `暂存内容检查结束（尚未提交）`。如果提示 `已有暂存修改，本步骤不再添加文件`，脚本会展示已有清单；它不是提交失败，也不需要反复运行本步骤。

检查展示的文件是否都是本次需要的内容。包含无关改动时，先不要做 B4；缺少本次文件时，先补齐清单。需要改变默认加入的文件范围，可修改 [merge_skill_prepare.sh](scripts/merge_skill_prepare.sh) 中 `stage` 操作的 `git add` 路径。

**B4．确认提交，自动取得版本号**

单独执行下面一行。等确认提示出现后，手动输入小写 `yes` 并按 Enter；不要连同其他命令一起粘贴。

```bash
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_skill_prepare.sh commit || echo '本次未完成提交，请查看提示'
```

**成功输出示例：**

```text
是否提交已审阅的修改并用于测试？输入 yes 提交：yes
[test/ppt-outline-merge 349d5d4] Prepare merged PPT skills for evaluation
...
提交成功，本次测试版本 SKILL_REF=349d5d41bce11c2e123e011ee9b102941172c459
```

看到最后一行就完成了，**不用再自己输入版本号，也不用 push 才能测试**。在同一个终端继续[第1.3节](#section-1-3)。输出中的 SHA 是示例，每次新提交会得到自己的编号。

| 如果看到这些提示 | 下一步 |
|---|---|
| `未提交，输入为…` | 没有识别到 `yes`；改动仍在。需要提交就重新单独执行 B4，等提示后再输入 |
| `没有新的暂存改动` | 检查是否已经提交；若是，去[情况 A](#skill-case-a)选择版本 |
| `请先执行check并确认当前开发分支` | 回 B1 重新核对分支 |
| `Author identity unknown` | Git没有配置提交者身份；先为技能仓库设置自己的 `user.name` 和 `user.email`，再执行 B4 |
| 其他 `fatal` / `error` | 停在当前步骤，保留完整报错，暂不进入评测 |

提交后如果仍列出文件，说明那些文件还有未提交内容，不属于刚生成的版本。不要为了清空列表，把与本次无关的改动也提交进去。

<a id="section-1-3"></a>

### 1.3 填写模型信息，准备本次测试目录

**开始前，完成以下任意一种准备即可：** 第1.2节已选择/提交版本成功；或者按开头的[情况三](#reuse-skill-new-model)加载了旧测试、准备沿用它的 skill 版本。继续在这个终端操作，不用手动重复填写版本号。本节用于创建新测试；仅继续已有测试时不要执行。

#### 第一步：填写模型名和地址

只修改前两行单引号里的内容，填法与平台一致。下面是格式示例，执行前换成这次要测的模型和地址；第三行原样执行：

```bash
export TASK_NAME='SenseNova-Flash-Lite-20260727-v39-fp8-step4k-dpov2-mtp'
export MODEL_BASE='10.210.9.14:208'
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_eval_env.sh || echo '参数准备失败，请查看提示，暂不继续'
```

**成功时显示：** `参数准备成功（尚未启动测试）`，后面列出模型名、主端点、skill版本、看板名称和本次目录。确认模型和版本正确，再做第二步。

脚本会自动设置腾讯云沙盒、与主模型相同的 review，以及平台已有的 HTML 中继规则。此时只是准备参数，还没有调用模型。需要调整更多默认值时，查看 [merge_eval_env.sh](scripts/merge_eval_env.sh)。

如果平台里的 served 模型名与任务名不同，先执行 `export PPT_SERVED_MODEL='实际served模型ID'`，再运行上面的三行；以后改回同名时执行 `unset PPT_SERVED_MODEL`。

**每次执行第三行都会准备一轮新测试。** `RUN_ID` 是自动生成的本次任务标识，`CTL` 是本次配置、日志等文件所在目录。已经开始的任务不要重做本步骤；换终端后继续原任务，按[第8节](#section-8)恢复原来的 `run.env`。如果还没保存 `run.env` 就关闭了终端，需要重新选择版本并准备参数。

#### 第二步：创建本次专用目录

运行下面一行，核对所选版本并创建目录。无需手动填写目录名，不会修改平台默认skills，也不会启动评测。实现见 [01_prepare_directory.sh](scripts/01_prepare_directory.sh)。

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/01_prepare_directory.sh" || echo '目录准备失败，请查看提示，暂不继续'
```

**成功提示二选一：**

- `本次工作目录创建成功：…_control`
- `本次目录已存在且为空，可以继续使用：…_control`

看到其中一个就做第三步。如果目录已有文件，脚本会停止，避免覆盖。先核对之前已完成哪些步骤；目录存在不等于评测已经启动，不要直接删除它重来。

#### 第三步：保存参数和凭据

**默认不用输入任何 Key。** 主模型 API Key 默认留空，review沿用主模型；评分裁判默认复用平台已有的 TokenHub Key。主模型需要鉴权时，见[主模型 Key 附录](#optional-model-api-key)；评分 Key 不可用时，按[更换评分 Key 并同步命令行测试](#optional-platform-judge-key)处理，然后回来保存。

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/merge_eval_save.sh" || echo '保存失败，请查看提示，暂不进入第2节'
```

**成功时显示：** `参数和凭据保存成功（尚未启动测试）`，并显示裁判 Key 的来源。此时第1节完成，继续[第2节：复制所选版本的 skills](#section-2)。

脚本 [merge_eval_save.sh](scripts/merge_eval_save.sh) 会把普通参数写入 `run.env`，把 Key 分别写入私有文件，不在终端显示 Key。已有本批凭据会保留；新指定的值与它不同时会报错，不覆盖运行中的设置。正式评分会使用选定凭据，将页面和所需文本发送到裁判服务。

<a id="section-2"></a>

## 2. 把选定版本的 skills 复制到本次目录

从本节起，长逻辑均已放入 [scripts/](scripts/) 中，正文只需执行对应的一行命令。要看细节或调整实现，打开每步链接的脚本即可。脚本会加载本批 `$CTL/run.env`，保持所选模型、commit 和运行目录一致，不会自动串行执行后续步骤。

**你已完成第1节的话，直接执行下面第2节命令即可，不需要重做前面的提交或参数初始化。** 所有步骤按顺序逐项检查；报错时先停在当前步骤。第5节会实际探活，第6节会运行小样本生成/评分，第7节会登记看板并启动正式测试；这些操作不会因为脚本整理而自动执行。

脚本使用你已选定的 `SKILL_SUBDIR`（当前为 `skills/agent-3.0/`），模板样式取自同一提交的 `templates/styles/`。以下操作只写CTL中的副本。

具体逻辑见 [02_export_skills.sh](scripts/02_export_skills.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/02_export_skills.sh" || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** 成功时显示“本批skills”和“merge技能目录”，并生成 `$CTL/provenance.json`；未启动模型调用。只有这一步成功后才能进入[第3节](#section-3)。

这里按技能目录**整体替换**，不会把旧技能脚本残留在同名merge技能中；merge以外的通用技能来自底座，这一点会记录在provenance中。因此结果应描述为“当前agent＋固定merge技能＋记录中的通用依赖”，不能描述成整个运行环境都是该Git提交。

<a id="section-3"></a>

## 3. 让本批 skills 使用你指定的模型

**前置条件：第2节已成功导出，本批目录中存在 `skills/` 和 `provenance.json`。** 如果缺少 `provenance.json`，说明当前运行目录还没有完成第2节，先返回[第2节](#section-2)执行导出，不要手工创建这个文件。

**这一步做什么：** 把本次模型地址和模型名接入刚复制的skills，确保生成和review用的是本次待测模型。只填写主模型参数还不够，因为skills内部也会发起模型调用。

脚本仅适用于本手册所述、通过 `_tool_call.py` 调用的merge版。若报接口或适配文件缺失，先停止并检查脚本，不要换回平台默认skills后继续测试。

具体逻辑见 [03_adapt_transport.sh](scripts/03_adapt_transport.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/03_adapt_transport.sh" || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** 显示“已适配”及技能列表，然后进入[第4节](#section-4)。若提示“本批已适配，请勿重复执行”，表示这个目录已经完成过第3节，不必重做。

**需要排查实现时再看：**

下面复用本机已有、用于merge评测的 `_eval_model_transport.py`，只在本批副本中替换模型调用出口：

- `html_page_generate`、`outline_md_generate` → 本批HTML模型；
- `html_page_review`、`image_filter` → 本批review模型；
- 渲染等非模型工具 → 原业务工具接口；
- 基准禁用的搜索等工具仍禁止调用。

**适配来源有明确路径，先检查文件存在。不存在或merge版工具接口改变时，不要临时抄回整个旧skill来凑通过。** 应先核对接口并完成适配；后面的doctor会实际调用适配后的脚本。

上述命令在本批 adapter 副本的生成请求中补齐平台默认的 thinking 开启和 `xhigh`；主配置也使用相同设置。主 agent 经 SDK 使用 `extra_body.chat_template_kwargs`，adapter 经 requests 直接发送 JSON，因此请求体使用 `chat_template_kwargs`，不发送顶层 `reasoning_effort`。生成输出预算为128000，视觉 review 保留 adapter 的8192预算。merge 业务脚本与平台旧版脚本仍有实现差异，不能据此声称两者请求完全相同；修改只发生在本批副本。

若你的merge版已经改回 `_html_llm_direct.py`，不要运行这一节的替换代码；应在副本中配置两模式的直连helper并核对实际review出口。新旧transport不能混搭后仍宣称是同一评测条件。

<a id="section-4"></a>

## 4. 生成本次评测配置

**这一步做什么：** 把已选的模型、skills目录和评测设置写成本批专用配置，并准备两种模式的1题试跑输入。运行后还不会开始生成PPT。

具体逻辑见 [04_build_config.sh](scripts/04_build_config.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/04_build_config.sh" || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** 显示 `config.yaml` 和 `state.json` 路径，继续[第5节](#section-5)。

这里的allowlist适用于现有PPT双模式任务。若merge版要求主agent直接发现其他技能，先补齐allowlist再做doctor/smoke。模板和无模板使用同一份配置，仅测试集和输出目录不同。

<a id="section-5"></a>

## 5. 检查模型与沙盒是否能正常调用（Doctor）

**5.1 先检查评测机能否访问主模型与沙盒**

具体逻辑见 [05_check_endpoints.sh](scripts/05_check_endpoints.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/05_check_endpoints.sh" || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** 报告中主模型的 `all_ok` 和沙盒的 `ok` 均为 `true`，并保存 `doctor_endpoints.json`。仅出现这个文件不代表通过，失败时也可能保存报告；有报错就不进入下一步。

**看到 `"severity": "error"` 不代表本次检查失败。** 这是检查项预先设置的“失败时按什么级别报告”，检查通过时也可能保留这个值。本次是否通过，要看主模型的 `all_ok` 和各检查项、沙盒的 `ok`，不要只看 `severity`。

例如，下面表示该检查项已经通过，可以继续；其中的 `severity` 不影响通过结果：

```json
{"ok": true, "detail": "HTTP 200", "severity": "error"}
```

主模型 `all_ok: true`、沙盒 `ok: true`，且执行没有其他报错时，就继续下方 **5.2**。如果 `all_ok` 或 `ok` 是 `false`，则查看对应的 `detail`，先解决问题再继续。


如果这里出现 `curl: (28) Connection timed out after 5000 milliseconds`，表示评测机在5秒内未能与显示的模型地址建立连接，不是 skill 版本或模型输出错误。此时停止在本节，先核对模型地址、端口及服务/网络是否可用，再重试同一步；不要跳过检查继续跑批。如果地址确实填错，不要只改当前终端变量后继续，因为脚本会加载本批已保存的 `run.env`，已有配置也包含原地址，需同步核对本批配置。

`/v1/models`列出的served ID应包含MODEL_ID。仅HTTP200不代表ID正确；部分兼容接口会忽略错误模型名。若端点只认checkpoint别名，核实映射后改MODEL_ID，MODEL_DISPLAY仍保留展示全名。

**5.2 再检查沙盒内部能否生成页面、渲染图片和执行review**

前一步成功后再执行。脚本会生成一张简单测试页，并让review模型检查它，验证真实调用链能工作：

具体逻辑见 [05_check_sandbox.sh](scripts/05_check_sandbox.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/05_check_sandbox.sh" || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** `generation`、`render`、`review` 均为 `true`，并保存 `doctor_runtime.json`，然后进入[第6节](#section-6)。

检查 `doctor_runtime.stderr.log` 的 `eval_model_request/response`：生成与review的model、endpoint应分别对应本批设置。有HTTP错误、空内容、模型名不符或超时就先修复，不能继续正式跑批。该检查验证公共transport；两模式具体skill逻辑由下一节smoke验证。

<a id="section-6"></a>

## 6. 先试跑：模板、无模板各1题（Smoke）

本节分三步：**生成两份样本 → 评分 → 查看产物并确认通过**。这里只是小样本试跑，通过后才开正式任务。

<a id="section-6-generate"></a>

**6.1 先生成两份样本**：模板模式1题、无模板模式1题，分别保存在本批smoke目录。

具体逻辑见 [06_generate_smoke.sh](scripts/06_generate_smoke.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/06_generate_smoke.sh" || echo '本步骤失败，请查看报错，暂不继续'
```

**结束时会显示：** `两种模式的冒烟生成命令均已结束（尚未评分或验收）`，随后回到命令提示符。这只表示生成命令已经结束；两题的最新终态应为 `done`，且真实非空HTML存在，才能继续评分。最终是否通过，还要完成第6.2节评分和第6.3节的页面、review检查。

运行时详细日志写入文件，可能较长时间没有新的终端输出。查看进度或核对结束结果，可以另开终端，按[第8.1节](#section-8-restore)选择本批测试，再查看日志。需要主动中止，见[第11节](#section-stop)。

<a id="section-6-score"></a>

**6.2 给两份样本评分**

下面创建一个**仅调用现有正式评分函数**的命令入口。它放在CTL外部任务目录中，不修改 `automation/`，也不实现另一套评分逻辑。两种模式以及smoke/正式任务使用不同VERSION；全局评分锁仍与原平台共享。

具体逻辑见 [06_score_smoke.sh](scripts/06_score_smoke.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/06_score_smoke.sh" || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** 成功时两模式都输出coverage_ok为true，生成对应score_ok.json。

有其他任务正在评分时，本批会排队等待，不需要重复启动。查看评分日志，可以另开终端，按[第8.1节](#section-8-restore)选择本批测试，再按[第8.4节](#section-8-scoring)查看。

**6.3 检查样本，记录验收通过**

打开两份smoke产物，检查内容、模式及资源加载无异常后，执行验收记录。这个命令会核对配置、skills没有在smoke中途被改动：

具体逻辑见 [06_accept_smoke.sh](scripts/06_accept_smoke.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/06_accept_smoke.sh" || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** 显示“Smoke通过，可以启动正式双模式”，再进入[第7节](#section-7)。

<a id="section-7"></a>

## 7. 启动正式47×2题，并登记结果看板

这一步继续使用本批已有配置，不经过网页的 `start_task()`，否则网页会重新复制默认skills底座。

**7.1 先在看板登记本次测试**。会创建模板、无模板两条记录；此时还没有正式生成结果或分数：

具体逻辑见 [07_register_dashboard.sh](scripts/07_register_dashboard.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/07_register_dashboard.sh" || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** 成功时显示“看板登记步骤完成”，尚未启动正式生成。此时刷新[结果看板首页](http://10.151.196.17:8770/)可以核对本次测试名称；命令行测试不显示在 `/automation` 平台任务列表中。

登记成功并核对名称后，继续执行[第 7.2 节：启动正式生成](#section-7-2)。不要停留在本节等待生成结果；本步骤只负责登记两条看板记录，正式生成需要由第 7.2 节单独启动。

**上板后如何区分 skill 版本：** 本流程登记到同一个8770结果看板，但每次运行使用独立 ID、产物目录和评分文件。看板显示名会自动包含 skill commit 的前12位及制作模式。例如本次版本的两条结果显示为：

```text
sensenova-flash-284b-vision-v16-20260914-sft | skills merge@349d5d41bce1 | 无模板模式
sensenova-flash-284b-vision-v16-20260914-sft | skills merge@349d5d41bce1 | 模板模式
```

完整 commit SHA 同时保存在登记记录的 `skill_commit`、备注及本批 `provenance.json` 中。模型 API 请求仍使用原始 served 模型名，不会把 skill 后缀传给模型。平台已有记录不改名、不覆盖；同一 skill 版本重复测试也有不同的运行 ID（带时间），可在看板表格的 ID 中区分。新脚本生成的运行 ID 还带 commit 短号。

**登记成功后，你会在[结果看板](http://10.151.196.17:8770/)看到本次测试的入口，名称会自动带上所测的 skill 版本，不需要手动填写。** 此时尚未产生本次正式测试的分数；完成[第9节](#section-9)评分后，分数才会更新。

查看本次命令行测试的结果，请打开上面的“结果看板”；平台 `/automation` 的“任务列表”不显示这类命令行任务。

<a id="section-7-2"></a>

**7.2 再启动正式生成**。以下并发为两模式各4，总计最多8题；若端点容量不足，两模式错峰，或统一降低CONCURRENCY并记录。

具体逻辑见 [07_launch_formal.sh](scripts/07_launch_formal.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/07_launch_formal.sh" || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** 显示已提交启动请求后，按[第8节](#section-8)看日志和进度；日志应出现 `batch_start`、`case_start`。启动命令返回不代表生成已完成。

PID文件记录的是启动owner，不能只凭PID存在判断生成正常。验收启动至少要看到原OUT的新 `batch_start`、`case_start`，以及日志中的真实 `[llm-response]` 和后续有效工具结果。

### 生成过程中如何选择后续流程

正式生成启动后，先按[第 8.3 节](#section-8-formal)查看两种模式的实际进度，再根据是否要等待整批生成结束选择后续步骤：

| 你的目的 | 后续跳转 | 说明 |
|---|---|---|
| 生成还在进行，想先评测已经完成的一部分 | [第 9.2 节：生成过程中提前评分](#section-9-early) | 先确认对应模式已有至少 20 套有效生成结果，再只评分该模式；这属于阶段性结果，不能当作整批最终结果 |
| 生成过程中决定结束本轮，只保留当前已完成的结果 | [第 11 节：停止任务](#section-stop)，然后回到[第 9.1 节：本轮生成结束后评分](#section-9-final) | 先停止任务，再核对有效产物和失败情况，随后对已有结果评分，并记录实际有效数量 |
| 等两种模式全部生成结束后一次性评分 | 先按[第 8.3 节](#section-8-formal)确认生成结束，再跳转[第 9.1 节：本轮生成结束后评分](#section-9-final) | 依次执行无模板和模板两种模式的正式评分，得到本轮完整结果 |

这里的“生成结束”不要求 47 题全部成功；允许少量题失败或未完成，但必须记录失败题，并在最终结果中注明计划数、有效生成数和已评分数。只完成少量题时不能直接作为整批结论，应按[第 12 节](#section-12)续跑。

<a id="section-8"></a>

## 8. 只查看日志和进度

本节用于查看任务执行到哪里、成功生成了多少题，不会启动评分。冒烟样本查看[第8.2节](#section-8-smoke)，正式测试查看[第8.3节](#section-8-formal)，评分日志查看[第8.4节](#section-8-scoring)。冒烟生成完成后回到[第6.2节](#section-6-score)评分；正式测试评分与上板见[第9节](#section-9)。

<a id="section-8-restore"></a>

### 8.1 另开终端，选择本批测试

保持运行测试的终端不动，另开一个终端用于查看日志。在新终端单独执行下面这一行，不需要修改命令或查找目录：

```bash
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_eval_restore.sh || echo '参数未加载，请查看提示，暂不继续'
```

脚本会列出已保存的测试。根据模型名、skill版本和创建时间找到本次测试，输入前面的序号并回车。看到 `参数加载成功：` 和正确的本批目录，才继续下面的命令；直接回车表示取消，输错序号则重新执行选择。

选择成功后，查看冒烟日志就继续[第8.2节](#section-8-smoke)，查看正式测试日志就继续[第8.3节](#section-8-formal)，查看评分日志就继续[第8.4节](#section-8-scoring)。这一步读取本批保存的参数，让新终端知道要查看哪一批测试，不会重新启动测试。

<a id="section-8-smoke"></a>

### 8.2 查看冒烟样本的日志（对应第6.1节）

**先查看当前日志末尾。** 命令执行后会返回提示符，不会重新生成：

```bash
tail -n 30 "$CTL/smoke_notpl.batch.log" "$CTL/smoke_tpl.batch.log"
```

**生成结束的判断：** 两份日志分别出现 `[batch_done]`，并显示 `本趟 1 个: done=1`，表示两题均已生成结束。仍需检查真实HTML、页面是否可打开及review情况，不能仅凭进度条的 `ok=1` 判定冒烟验收通过。确认生成结果后，回到[第6.2节](#section-6-score)评分。

若需要核对每题的终态，执行下面一行查看事件记录；对应题的最新 `case_done` 应为 `terminal_class: "done"`、`success: true`，随后有 `batch_done`：

```bash
tail -n 5 "$CTL/smoke_notpl/events.jsonl" "$CTL/smoke_tpl/events.jsonl"
```

**持续查看日志：** 在刚才用于查看日志的新终端执行：

```bash
tail -F "$CTL/smoke_notpl.batch.log" "$CTL/smoke_tpl.batch.log"
```

脚本先生成无模板，再生成有模板。模板尚未开始时，提示模板日志不存在是正常的；如果两份日志都不存在，先核对是否选中了正在测试的批次、是否已执行第6.1节。

批次进度可能长时间停在 `0/1`，完成整套PPT后才更新。需要看内部具体进展时，日志开头的“实时 tail”会列出详细 agent 日志的查看命令，复制其中的 `tail -F …agentv3_concurrent_….log` 单独执行即可。

详细日志里的新模型响应或工具调用说明有进展；长时间没有新输出时，要结合进程、最近调用及报错判断，不能单凭安静认定卡住。在看日志的终端按 Ctrl+C 只会退出 `tail`，不会停止另一终端的生成任务。

<a id="section-8-formal"></a>

### 8.3 查看正式测试的日志和生成进度（对应第7节）

只有启动了第7节正式测试，才执行本小节。冒烟阶段不需要执行这里的命令。

**查看正式日志：** 在第8.1节已选好本批测试的新终端执行。脚本会先打印当前日志末尾，然后持续跟踪两种模式的正式 batch 日志：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/08_logs.sh" || echo '日志尚不存在或读取失败，请核对任务状态'
```

命令会保持运行并持续输出新日志，不会立即返回命令提示符。按 `Ctrl+C` 只退出日志查看，不会停止正式生成任务；如果只想打印一次当前日志，可先执行 `export PPT_LOG_ONCE=1`，再运行上面的命令。

按每题最新start/终态关系查看真实成功数，不看tqdm的ok数量：

具体逻辑见 [08_progress.sh](scripts/08_progress.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/08_progress.sh" || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** 输出两模式有效HTML数量及终态统计；不会启动任务。

<a id="section-8-scoring"></a>

### 8.4 查看评分日志（对应第6.2节或第9节）

先按[第8.1节](#section-8-restore)在新终端选择本批测试，再根据正在进行的评分选择下面一条命令。命令只查看日志，不会启动评分。

下面两条命令都会持续跟踪日志文件的新内容，不是一次性打印。按 `Ctrl+C` 只退出日志查看，不会停止评分任务；评分是否完成仍以执行评分命令的原终端输出为准。

**查看冒烟样本评分（第6.2节）：**

```bash
tail -F "$CTL/smoke_notpl.score.log" "$CTL/smoke_tpl.score.log"
```

**查看正式测试评分（第9节）：**

```bash
tail -F "$CTL/formal_notpl.score.log" "$CTL/formal_tpl.score.log"
```

出现评分日志内容，表示已经打开对应日志；后续新内容会自动显示。在这个查看日志的终端按 Ctrl+C 可退出查看，不会停止另一终端的评分。

**原评分终端显示“等待全局评分锁”时，意思是正在排队等其他任务评分结束。** 此时评分日志可能还没有创建，`tail` 提示文件不存在是正常的，会继续等待文件出现。冒烟先评无模板、再评有模板；尚未开始的模式也可能没有日志。如果原评分终端已经报错退出，就先处理报错，不要一直等日志。

**评分是否成功，以执行评分命令的原终端为准：** 对应模式输出 `coverage_ok: True`，且没有失败提示。第6.2节需要两种模式都通过；正式测试还需按[第9节](#section-9)核对最终评分覆盖情况。日志暂时没有新内容不等于评分已经完成。

<a id="section-9"></a>

## 9. 给已生成的 PPT 评分，并更新结果看板

本节用于**第7节正式测试的评分**；第6节的两份冒烟样本仍按[第6.2节](#section-6-score)评分。

根据你的需求选择下面一种方式，不需要按顺序执行两种方式：

| 你想怎么评 | 去哪里操作 |
|---|---|
| 本轮生成结束后，对已有有效产物统一评分（常规方式） | [9.1 本轮生成结束后评分](#section-9-final) |
| 生成还在继续，先看部分已完成PPT的分数（可选） | [9.2 生成过程中提前评分](#section-9-early)；全部生成结束后仍需回9.1补齐 |

执行评分前，确认当前终端选中的是本批测试；新终端先按[第8.1节](#section-8-restore)选择。评分时有其他任务占用裁判服务，本批会排队等待，不需要重复启动。查看评分日志统一见[第8.4节](#section-8-scoring)。

<a id="section-9-final"></a>

### 9.1 方式一：本轮生成结束后评分（允许少量生成失败）

**“本轮生成结束”不要求47题全部成功。** 大部分题已完成，只有少量题失败或没有产物时，可以先不补这几题，对已有有效产物评分、查看整体结果，不必一直重试到47/47。

确认正式生成已结束，或决定不再等待剩余题目后，分别执行下面两条评分命令。评分过程中如需查看进度，另开终端（新终端先按[第8.1节](#section-8-restore)选择。），再按[第 8.4 节](#section-8-scoring)持续跟踪评分日志。

| 当前情况（每种模式计划47题） | 接下来怎么做 |
|---|---|
| 47题全部成功，本轮已结束 | 执行下面的评分命令 |
| 例如46题成功、1题失败或未完成，决定本轮不再补这1题 | 记录这道题及失败或未完成原因，再对已有46题评分；展示结果时注明46/47 |
| 只完成1～2题就中断，大部分题还没测 | 先按[第12节](#section-12)续跑，不能把这几题的分数当作整批结果 |
| 生成仍在运行，想先看已有结果 | 按[第9.2节](#section-9-early)提前评分；若决定结束本轮，先按[第11节](#section-stop)停止本批，再核对产物和评分 |

**评分脚本没有要求必须47题全部成功，也没有自动判断“样本数足够”的门槛。** 它对已有有效产物评分；是否已经测了足够多的题，需要按上面的情况判断。允许少量生成失败，不等于可以忽略已经生成产物的评分缺失。

**第一步：给无模板结果评分。** 运行下面这一行，等待命令结束：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/08_score_formal.sh" notpl || echo '无模板评分失败，请查看第8.4节日志，暂不继续'
```

**成功判断：** 输出 `coverage_ok: True`（即为真），且没有失败提示，表示本次检查的有效无模板产物已被评分覆盖，再执行第二步。这里的覆盖是“已有有效产物都已评分”，不是“47题全部生成成功”。

**第二步：给有模板结果评分。** 运行下面这一行，等待命令结束：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/08_score_formal.sh" tpl || echo '模板评分失败，请查看第8.4节日志，暂不继续'
```

**成功判断：** 同样输出 `coverage_ok: True`，且没有失败提示。两种模式均成功后，进入[第9.3节](#section-9-board)查看并核对看板。

如果之前做过提前评分，仍执行上面两步：脚本会跳过已有成功评分，补评新增的产物。无需更换任务名或重新生成PPT。两种方式都使用 [08_score_formal.sh](scripts/08_score_formal.sh)，区别只是执行时机。

<a id="section-9-early"></a>

### 9.2 方式二：生成过程中提前评分（可选）

**什么时候执行：** 正式生成尚未全部结束，但某一模式已有效生成至少20套PPT，你想先查看这部分结果的分数。按[第8.3节](#section-8-formal)确认该模式的有效生成数量，再执行对应命令。

**无模板已达到20套，想先评无模板时，执行：**

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/08_score_formal.sh" notpl || echo '无模板评分失败，请查看第8.4节日志'
```

**有模板已达到20套，想先评有模板时，执行：**

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/08_score_formal.sh" tpl || echo '模板评分失败，请查看第8.4节日志'
```

只执行满足条件、且你想评分的模式；不需要两条一起执行。如果两种模式都要提前评分，先等第一条结束再执行第二条。

**成功判断：** 对应模式输出 `coverage_ok: True`，且没有失败提示，表示这次检查的已生成产物已被评分覆盖。可以按[第9.3节](#section-9-board)查看阶段性分数；这些分数不能作为整批最终结果。

**后面还要做什么：** 新生成一批PPT后，可以再次执行对应模式的同一条命令，已有成功评分会跳过。等两种模式的生成全部结束，必须回到[第9.1节](#section-9-final)，依次执行两种模式的评分命令，补齐最终评分。脚本不会自动定时补评分。

<a id="section-9-board"></a>

### 9.3 刷新页面入口，查看并核对看板

生成侧页面索引可按需刷新：

具体逻辑见 [08_refresh_pages.sh](scripts/08_refresh_pages.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/08_refresh_pages.sh" || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** 成功时显示“页面索引刷新完成”；不会重新生成PPT。

在 `http://10.151.196.17:8770/` 查看正式两模式。应能打开真实页面，评分覆盖数与文件唯一query数一致。smoke分数不登记为正式结果、不计入全量均分。

评分入口会尝试更新本地模型卡及交接包总表等材料；核对 `$CTL/tasks/$RUN_ID/deliverables_status.json`，存在 `deliverables_error.json` 就先处理错误，不能称为材料齐套。另按 `[260709]跑完模型的后置产出清单-给agent读.md` 核对A/F/B/C：机器汇总不替代逐例失败归因，也不会自动完成飞书同步。

本轮结果核对：两种模式已有的有效产物都应有完整评分，`content=None`/`dyn=0`等评分异常需处理。允许少量题生成失败或未完成，不强制反复补跑到47/47；展示分数时同时写明有效生成数、已评分数和未成功题，例如“计划47题，有效生成46题，已评分46题，1题生成失败”。只完成1～2题就中断的情况应先续跑，不能以少量样本代表整批结果。

<a id="section-8-costs"></a>
<a id="section-10"></a>

## 10. 上板后，生成 Token 与耗时分析附件

**执行时机：** 两种模式的正式生成和评分均已结束、结果已上板，产物不再写入。若还在补跑，先完成[第12节](#section-12)相关处理，再回到这里分析。

本步骤接入已写好的[《评测上板后 Token 与耗时分析操作手册》](./[260916]评测上板后Token与耗时分析操作手册.md)，调用其中的 [analyze_completed_run.py](../automation/analyze_completed_run.py)。它读取本次正式生成、主轨迹和全部子任务轨迹，输出 Token、时间和分数汇总，**不调用模型、不重新生成、评分或上板**。

**第一步：执行一行分析命令**

仍在原终端就直接执行；换了终端则先按[第8节开头](#section-8)恢复参数。脚本会自动找到本次 `notpl`、`tpl` 正式目录及对应评分文件，不需要你再填写两套路径。实现见 [08_analyze_costs.sh](scripts/08_analyze_costs.sh)。

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/08_analyze_costs.sh" || echo '分析未完成，请查看提示；不要把未完成报告作为最终附件'
```

**成功时显示：** `Token与耗时分析完成`，以及“附件目录”和 `逐case与分阶段对账：passed`。每次分析都会在 `$CTL/analysis_delivery_…/` 创建新目录，不覆盖之前的报告；最新成功目录保存在 `$CTL/analysis_latest.txt`。报告另外记录本次 RUN_ID 和完整 skill commit，便于区分不同模型及skill版本。

脚本会检查生成/评分进程与锁、两模式汇总和评分文件。若提示仍在运行，就等对应任务结束；若 `batch_summary.json` 缺失或只剩补跑切片，先核对原始完整汇总，不能手工编造耗时。尤其在[第12.2节](#section-12-2)归档过汇总时，需核对保留下来的原始记录，不要直接把切片耗时当成全量耗时。

**第二步：查看校验结果和汇总**

下面第一行只读取刚打印的附件目录，无需手填。后两行显示校验与汇总：

```bash
ANALYSIS_OUTPUT="$(cat "$CTL/analysis_latest.txt")"
python3 -m json.tool "$ANALYSIS_OUTPUT/validation.json"
python3 -m json.tool "$ANALYSIS_OUTPUT/summary.json"
```

先确认刚才分析成功再运行这里；分析失败不会更新 `analysis_latest.txt`，否则你可能打开上次的报告。

| 查看什么 | 怎么判断 |
|---|---|
| `case_stage_reconciliation` | 应为 `passed`：逐case和分阶段的统计加和一致 |
| `generated_cases` / `cases` | 完整47×2测试通常分别为每模式47、合计94；以本次正式输入为准，不把smoke算进去 |
| `scored_cases` | 与本次有效评分覆盖数核对；缺失评分保持空值，不按0分处理 |
| `cases_with_coverage_flags` / `issue_count` | 不为0不代表分析程序失败，但说明存在缺记录或覆盖疑点，应查看 `issues.json` 并在交付时说明 |

**第三步：打开并交付报告**

到上面打印的附件目录查看以下文件；Markdown可直接阅读，CSV可用Excel打开，JSONL用于程序处理：

| 文件 | 用途 |
|---|---|
| `report.md` / `summary.json` | 本批总体分数、Token、耗时、各阶段汇总 |
| `case_tokens.md` / `.csv` / `.jsonl` | 附件一：逐case输入、输出、总Token及覆盖提示 |
| `case_times.md` / `.csv` / `.jsonl` | 附件二：逐case实际耗时和已观测模型请求耗时 |
| `case_stage_token_time.csv` / `.jsonl` | 每个case各阶段的详细统计 |
| `request_usage_time.csv` / `.jsonl` | 请求级明细和轨迹来源 |
| `validation.json` / `issues.json` | 统计对账结果、缺失或可疑记录定位 |
| `source_manifest.json` / `run_identity.json` | 原文件指纹、本次运行与skill版本，供追溯 |

**阅读结果时注意：**

- Token只统计已保存的 `eval_model_response` 中的 `usage`，包括主轨迹和子任务轨迹；未记录的agent推理、截断日志、失败请求及评分调用不在总量中，不能称为完整账单。
- 时间单位是秒。`wall_duration_s` 是单case实际生成耗时；`batch_wall_s` 是整批实际生成耗时；`sum_s` 是观测到的模型请求耗时之和。并发时三者不同，不能互相替代；前两者也不含评分和上板时间。
- 空值表示未获取到数据，不是零成本。`passed` 表示统计对账通过，不代表日志完整。更详细的字段解释见[原分析手册第7节](./[260916]评测上板后Token与耗时分析操作手册.md#7-token-和时间的统计含义)；原手册的历史数量和总Token不是本批预期值。

完成本节后，本批交付应包含：**带skill版本的看板结果、质量评分、Token附件、耗时附件，以及缺失数据说明**。分析附件保存在本批目录，不会自动增加看板上的Token/耗时栏目。

<a id="section-stop"></a>
<a id="section-11"></a>

## 11. 随时停止本批测试（可选）

**本节是随时可用的可选操作，不必等前面的步骤完成。** 冒烟、正式生成、补跑或评分期间需要停止，都可以使用本节。选择列表列出的是已保存参数的历史测试，**出现目录不表示任务正在运行**；探活失败、尚未开始生成的批次通常没有需要停止的生成进程。

**第一步：另开终端，选择要停止的测试。** 单独执行下面一行，等列表出现后输入序号并回车。按模型名、skill版本及创建时间确认，不要选错批次：

```bash
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_eval_restore.sh || echo '参数未加载，请查看提示，暂不继续'
```

看到 `参数加载成功`，且显示的确实是要停止的测试，才继续。取消或加载失败时不要执行后面的命令。

**第二步：检查是否还在生成或评分。** 此命令只检查，不会停止：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/stop_merge_run.sh" --check || echo '检查失败，请查看报错'
```

显示 `未发现本批运行中的本地生成或评分进程，无需停止`，说明这批当前没有检测到的生成或评分进程，可以到此结束。若列出 PID，则表示仍有进程，可执行下一步。

**第三步：停止选中的这批生成和评分。** 会停止本批两个模式的本地生成、评分及其子进程，不删除已生成的PPT、日志、参数或评分文件。实现见 [stop_merge_run.sh](scripts/stop_merge_run.sh) 和 [stop_merge_run.py](scripts/stop_merge_run.py)。

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/stop_merge_run.sh" --stop || echo '停止未完成，请查看提示'
```

**成功判断：** 显示 `本批本地生成和评分进程已停止`，或提示没有需要停止的进程。原来执行生成/评分命令的终端可能显示中断、Terminated 或步骤失败，这是手动停止后的正常现象。若提示仍有进程未退出，不算停止成功。

停止后目录仍会出现在选择列表中，这是为了保留结果供查看或续跑；不需要删除目录。此命令只处理本手册启动的本地生成和评分，不是平台网页任务的停止按钮，也不会终止正在查看日志的 `tail`。已发送到远端模型或沙盒的请求可能仍会继续，不能据此认为远端请求也已取消。探活命令可在执行它的原终端按 Ctrl+C 中断。

重新开始正式生成时按[第12节](#section-12)核对并续跑，不要重新初始化目录；冒烟中断后可重试[第6节](#section-6)生成命令，评分中断后按原模式重新执行评分命令。停止过程中未完成的题不能当作成功题，仍需按对应章节验收。停止命令保留已有看板记录，不会替你把整批标成评测成功。

<a id="section-12"></a>

## 12. 断点续跑：不要重跑成功题

**第一步：选回原测试。** 按[第8.1节](#section-8-restore)运行选择脚本，选中要继续的测试。看到“参数加载成功”后，再按下面实际中断的阶段操作。终端断开不一定意味着任务停止；若原任务仍在运行或排队，查看日志即可，不要重复启动。

**第二步：按中断的阶段继续。**

| 中断的位置 | 接下来执行什么 |
|---|---|
| 第6.1节冒烟生成 | 确认旧冒烟进程退出、故障解决后，重新执行[第6.1节](#section-6-generate)的生成命令，再核对结果 |
| 第7节正式生成，因服务故障或手动停止而中断 | 按下面[第12.1节](#section-12-1)执行对应模式的续跑命令 |
| 正式生成有内容错误、渲染异常等失败题，需要重试 | 按[第12.2节](#section-12-2)先核对原因，再准备补跑清单 |
| 第6.2节冒烟评分 | 确认旧评分进程已退出、报错已处理，再执行[第6.2节](#section-6-score)的评分命令 |
| 第9节正式评分 | 确认旧评分进程已退出、报错已处理，再执行[第9.1节](#section-9-final)中尚未完成模式的评分命令 |


<a id="section-12-1"></a>

### 12.1 只有基础设施失败或中断

先确认该模式旧owner及其子进程已退出。端点、沙盒仍不可用时先恢复doctor，禁止不断启动新批空转。

复用原任务参数，只恢复需要续跑的模式。例如无模板：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/07_launch_formal.sh" notpl || echo '续跑启动失败，请检查报错'
```

模板模式将 `notpl` 改成 `tpl`。脚本保持**原INPUT、原OUT、原配置、`--resume`一致**。`flock`拒绝启动说明旧owner可能仍持锁，不要删除锁文件来绕过。

<a id="section-12-2"></a>

### 12.2 other_error / render_suspect / done_no_html等

`--resume`默认会跳过这些终态。先查对应 `result.jsonl` 和原始agent日志；只有确认错误已经修复、确需再跑时，才建立显式remain清单。质量问题也要如实保留首轮结论，不因低分而无限重跑挑最好结果。

以下脚本只准备清单，**不会启动、不会改events、不会删除产物**：

具体逻辑见 [09_prepare_remain.sh](scripts/09_prepare_remain.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/09_prepare_remain.sh" notpl || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** 显示成功保留数及待归因数；不会启动补跑。 模板模式将命令末尾的 `notpl` 改为 `tpl`。

记录每个待重跑case的原终态、原因和时间后，保留确需补跑的行。对这些原本会被resume跳过的题，使用 `--input "$CTL/remain_${MODE}.jsonl"`、**同一个原OUT**，此轮不加 `--resume`；因为输入已明确排除了成功题。仍使用相同生成锁，日志追加而不覆盖。

使用下面的命令执行已审核的remain清单。启动前再次校验它不包含已成功题：

具体逻辑见 [09_launch_remain.sh](scripts/09_launch_remain.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/09_launch_remain.sh" notpl || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** 先校验清单不含成功题；提交启动请求后继续检查日志。 模板模式将命令末尾的 `notpl` 改为 `tpl`。

remain输入必须在每趟补跑前重新盘点生成；不能在部分题已成功后再次无条件重用旧remain清单。

remain完成可能把 `batch_summary.json` 的 `case_total`写成切片题数。此时不要只看summary宣称全量完成。确认该模式生成和评分进程均已退出后，以下命令保留原汇总备份，让现有转换器从完整events读取最新终态，并另存一份审计快照；不改events、不伪造 `batch_done`：

具体逻辑见 [09_audit_events.sh](scripts/09_audit_events.sh)。运行下面一行完成本步骤：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/09_audit_events.sh" notpl || echo '本步骤失败，请查看报错，暂不继续'
```

**成功判断：** 输出进度和真实有效case，并保留原汇总备份与审计快照。 模板模式将命令末尾的 `notpl` 改为 `tpl`。

这份审计快照不是“47题全部成功”的证明；仍要逐题核对完整测试集及缺失终态。随后按[第9节](#section-9)重新执行对应模式的评分命令，补评分及刷新看板，无需重新生成。下一趟生成若再次写入切片汇总，结束后重复此核对步骤。

<a id="section-13"></a>

## 13. 文件在哪里、怎样确认真测了merge版

| 要找的东西 | 位置 |
|---|---|
| 非敏感参数 | `$CTL/run.env` |
| 来源提交、通用底座和agent工作区状态 | `$CTL/provenance.json` |
| 实际使用的skills | `$CTL/skills/` |
| transport接入来源与预算 | `$CTL/transport_adaptation.json` |
| 主agent配置 | `$CTL/config.yaml` |
| 独立状态与交付清单 | `$CTL/tasks/$RUN_ID/` |
| smoke生成、评分日志 | `$CTL/smoke_*.batch.log`、`$CTL/smoke_*.score.log` |
| 正式生成日志 | `$CTL/formal_*.batch.log`，其中包含原始agent日志路径 |
| 正式产物 | `$PPT_ROOT/output/${RUN_ID}_{notpl,tpl}/` |
| 正式评分 | `../benchmark/results/industry_v2_${RUN_ID}_{notpl,tpl}.jsonl` |
| 已评分后的结果入口 | `http://10.151.196.17:8770/` |

确认顺序：固定提交 → 检查config的绝对skills_dir → 对照skills文件哈希 → 在原始日志确认“压缩/上传skills目录” → 核对沙盒模型请求model/endpoint → 打开真实产物 → 核对评分case覆盖。

**常见误操作：** 回到旧网页点击“新建任务”不会继承这里的config；修改宿主环境变量不保证沙盒脚本收到；仅保存新skill但未进入allowlist不等于主agent会发现；只把任务登记到runs.json不等于已有分数；score.log显示等待锁不等于正在打分。

本机适配器属于现有实验产物依赖，跨机器复现时需连同来源、哈希一起迁移或正式整理为可复用资源；不要只复制这份文档就假设其他机器也有该文件。文中未提交任何运行产物或凭据，也不要求修改原平台代码。


<a id="optional-skill-branch"></a>

## 附录：可选操作——新建或切换 skills 开发分支

> **本附录不属于按顺序执行的评测步骤。已经在目标开发分支上，请跳过整节。**
>
> **下面两种操作最多选一种，不要连续执行。** 它们会改变当前分支；代码增加了确认提示，只有输入 `yes` 才执行。

如果修改是在另一个 worktree 目录中完成的，应先把 `SKILL_REPO` 改成那个工作区路径，再返回[分支检查](#skill-branch-check)，不必在这里切分支。未提交修改属于工作区，切换分支时可能一起带过去，也可能因冲突被 Git 拒绝；执行前先确认这些修改应保留在哪个分支。本手册不强制切换、不自动 stash。

### 可选一：还没创建本次开发分支，确实需要新建

仅当你准备把当前工作区的修改放到一个**尚不存在的新分支**时，运行下面代码。把占位文字改成新分支名。此操作从当前 HEAD 创建分支，并切到新分支；不会创建 commit。

```bash
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_skill_prepare.sh create-branch '填写本次新分支名' || echo '分支操作未完成，请查看提示'
```


成功时 Git 通常显示 `Switched to a new branch '你的分支名'`（中文环境可能显示中文）。随后返回[分支检查](#skill-branch-check)，以它输出的新分支名为准，再继续检查改动、提交。若提示分支已存在，本次新建失败，不要直接换个名字重试；先确认是否应使用下面的“可选二”。

### 可选二：目标分支已经存在，确实需要切过去

仅当你确认要切到一个**已经存在的本地分支**，且已经核对当前工作区的未提交修改应如何处理时，运行下面代码。把占位文字改成已有目标分支名。

```bash
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_skill_prepare.sh switch-branch '填写已有目标分支名' || echo '分支操作未完成，请查看提示'
```


成功时 Git 通常显示 `Switched to branch '你的分支名'`；`Already on '你的分支名'` 表示本来就在该分支。随后返回[分支检查](#skill-branch-check)，重新保存 `SKILL_BRANCH` 后再继续提交。若提示本地修改会被覆盖，Git 会拒绝切换；先处理这些修改，不要加 `--force` 或 `--discard-changes` 重试。

<a id="optional-model-api-key"></a>

## 附录：填写主模型 API Key（可选）

**默认不填，跳过本节。** 如果模型提供方给了 API Key，且你本次需要使用它，请在[第1.3节](#section-1-3)“保存本次参数和凭据”之前，单独执行下面这一行。提示出现后输入 Key 并按 Enter；不需要填写就直接按 Enter。这里填的是模型提供方给你的 Key，不是模型名、地址、版本号，也不是评分裁判的 TokenHub Key。

```bash
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_model_key.sh || echo '输入未完成，请查看提示'
```

输入的字符不会显示在屏幕上，这是正常现象。看到 `已接收主模型 Key（不显示内容）` 或 `未填写主模型 Key，将使用默认占位值`，表示输入步骤完成；返回[第1.3节](#section-1-3)继续保存参数和凭据。Key 是否有效在[第5节](#section-5)实际检查。

此步骤只设置当前终端变量；如果本批 `model.key` 已保存，后续保存代码会保留该文件，不会因为重新输入而覆盖它。需要更换已有任务的 Key 时，先确认任务状态，再单独处理凭据文件，不要重复初始化。换回默认不填的设置、准备新任务时，可执行 `unset PPT_MODEL_API_KEY` 清除当前终端中先前输入的值。

<a id="optional-platform-judge-key"></a>
<a id="optional-judge-key"></a>

## 附录：更换评分 Key，并同步命令行测试

平台评分的 TokenHub Key 不可用时，按下面顺序完成一次更换，让平台和命令行测试使用同一个新 Key。

**开始前：** 等平台生成、评分和自动续跑任务停止后再操作；需要同步的命令行测试也先停止评分，包括正在排队的评分。重启会短暂中断平台页面，不能代替停止旧任务。停止命令行测试的方法见[第11节](#section-11)。

### 第一步：填写新 Key，保存配置

在评测机终端逐行执行下面三行。只替换第一行单引号里的内容；第二行清除以前单独指定给命令行测试的 Key 设置，后续统一使用平台配置。

```bash
export PPT_PLATFORM_JUDGE_API_KEY='在这里粘贴新的TokenHub Key'
unset PPT_JUDGE_API_KEY PPT_JUDGE_KEY_FILE
bash /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/platform_judge_key.sh || echo '保存失败，请查看提示，暂不继续'
```

**成功判断：** 显示 `平台裁判 Key 配置已保存`，再执行第二步。实现见 [platform_judge_key.sh](scripts/platform_judge_key.sh)。

### 第二步：重启平台，让新 Key 生效

确认前面的任务已停止、第一步保存成功，再执行：

```bash
systemctl --user daemon-reload && systemctl --user restart ppt-automation-8877.service
systemctl --user is-active ppt-automation-8877.service
```

**成功判断：** 第一行没有报错，第二行显示 `active`。这表示平台已重新运行；新 Key 是否有效，还需后续实际评分确认。

<a id="sync-existing-judge-key"></a>

### 第三步：把同一个新 Key 同步到已有命令行测试

先执行下面一行，输入要继续评分的旧测试序号，按回车：

```bash
source /home/gui-5d025-2/zyy/xhx_agent_v3/ppt-eval-handover/scripts/merge_eval_restore.sh || echo '参数未加载，请查看提示，暂不继续'
```

看到 `参数加载成功`，确认选对测试后，执行同步命令：

```bash
bash "$PPT_ROOT/ppt-eval-handover/scripts/sync_judge_key.sh" || echo '同步失败，请查看提示，暂不启动评分'
```

**成功判断：** 显示 `本批裁判 Key 已同步`，或 `本批裁判 Key 已与平台配置一致，无需更新`。如果提示评分仍在运行或排队，先停止本批评分再同步。实现见 [sync_judge_key.sh](scripts/sync_judge_key.sh)。

有多个旧测试要继续评分，就逐个选择并同步。之后新建的命令行测试会在首次保存参数时读取新 Key，不需要做这一步。

### 第四步：继续评分

同步完成后，冒烟样本执行[第6.2节](#section-6-score)的评分命令；正式测试执行[第9.1节](#section-9-final)对应模式的评分命令。**不需要重新生成PPT，已有结果保留。**

更换的是评分裁判 Key，主模型和 review 的 Key 不变。“等待全局评分锁”表示排队，换 Key 不会跳过排队。粘贴 Key 的命令可能留在终端历史中，请勿分享。
