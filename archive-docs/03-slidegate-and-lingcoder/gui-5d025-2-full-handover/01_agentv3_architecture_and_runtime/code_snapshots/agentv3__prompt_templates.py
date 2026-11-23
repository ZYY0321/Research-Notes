"""
Prompt templates used by AgentV3 for runtime instruction injection.
"""

from typing import Dict, Any, Optional, List

from src.utils import ctx


def _normalize_language(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    lang = str(value).strip().lower()
    if lang.startswith("zh"):
        return "zh"
    if lang.startswith("en"):
        return "en"
    return lang


def _infer_language_from_system_prompt(runtime_conf: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Infer language from runtime.system_prompt path when runtime.language is missing.
    Expected convention: path contains "_zh" or "_en".
    """
    runtime_conf = runtime_conf or {}
    prompt_value = runtime_conf.get("system_prompt")

    candidates = []
    if isinstance(prompt_value, str):
        candidates.append(prompt_value)
    elif isinstance(prompt_value, dict):
        # Prefer default-like keys first, then inspect any remaining values.
        for key in ("default", "zh", "zh-CN", "en", "en-US"):
            value = prompt_value.get(key)
            if isinstance(value, str):
                candidates.append(value)
        for value in prompt_value.values():
            if isinstance(value, str):
                candidates.append(value)

    for item in candidates:
        path = item.strip().lower()
        if "_zh" in path:
            return "zh"
        if "_en" in path:
            return "en"
    return None


def _resolve_runtime_language(state: Optional[Dict[str, Any]] = None) -> str:
    """Resolve runtime language from state or ctx config."""
    lang = None
    if isinstance(state, dict):
        lang = state.get("language")
    lang = _normalize_language(lang)
    if lang:
        return lang

    runtime_conf: Dict[str, Any] = {}
    if hasattr(ctx, "config") and ctx.config:
        runtime_conf = ctx.config.get("runtime", {}) or {}
        lang = _normalize_language(runtime_conf.get("language"))
        if lang:
            return lang

    inferred = _infer_language_from_system_prompt(runtime_conf)
    if inferred:
        return inferred
    return "en"


def extract_original_task(messages: List[Dict[str, Any]], system_markers: Optional[List[str]] = None) -> str:
    """
    从消息历史中提取原始任务（第一条非系统注入 user 消息）
    """
    if system_markers is None:
        system_markers = ["[系统提示", "[FINALIZE", "[Finalize"]

    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = str(msg.get("content", "") or "")
        if any(marker in content for marker in system_markers):
            continue
        return content
    return "未知任务"


def build_sub_finalize_prompt(original_task: str, state: Dict[str, Any], agent_name: str) -> str:
    """
    构建子任务 finalize prompt。
    """
    lang = _resolve_runtime_language(state)
    if lang == "zh":
        return f"""作为子任务 Agent，请基于已有执行记录输出最终总结。

## 子任务
{original_task}

## 要求
1. 总结你在该子任务中完成的工作
2. 列出关键发现（具体事实/数字/引用）
3. 若完成任务，给出完整结论
4. 若未完成，说明已尝试内容和部分结果
5. 只基于已有上下文，不要新增工具调用或外部检索
6. 主产物必须完整写在 <result> 中；不要把主要结论、分析、表格或草稿只留在文件里
7. 如果执行过程中创建了文件，也必须在 <result> 中返回可读结论，让主线程无需读取文件也能汇总

## 输出格式
硬性规则：你的整个输出必须以 <subtask_result> 开头、以 </subtask_result> 结尾。五个子标签必须放在这两个标签之间。不要在标签外输出任何文字。
主线程只会读取 <subtask_result> 标签内部的内容，标签外的任何文字都会被丢弃。

<subtask_result>
<original_task>回显被委派的任务内容</original_task>
<findings>关键发现：具体事实、数字、引用、证据。引用来源时使用 `<cite index="N" title="标题" url="链接">[N]</cite>` 或 `<cite index="N" title="文件名" path="/mnt/data/路径">[文件名](/mnt/data/路径)</cite>` 格式。若无则写"无"</findings>
<result>最终结论/答案。这一部分会展示给用户，请用面向用户的语言撰写，不要包含工具名、内部文件路径、函数名等实现细节</result>
<cite_files>执行过程中引用、创建或修改的文件。每行格式：文件路径 简要描述。若输入包含“引用文件 /mnt/data/download/... 描述”这类条目，必须逐条列出对应文件路径与说明。若无则留空</cite_files>
<todo>剩余工作、阻塞点、或给主线程的后续建议。若任务已完成则写"无"</todo>
</subtask_result>
"""

    return f"""As a sub-agent, summarize your execution results for the assigned subtask.

## Subtask
{original_task}

## Instructions
1. Summarize what you accomplished during this subtask
2. List key findings with concrete facts/numbers/quotes
3. If completed, provide the complete answer
4. If incomplete, explain what was tried and what partial results were obtained
5. Use only existing context; do not call new tools or perform new searches
6. The primary deliverable MUST be written completely inside <result>; do not leave the main conclusions, analysis, tables, or draft only in a file
7. If files were created during execution, still return a readable conclusion in <result> so the main thread can synthesize without reading the file

## Output Format
Hard rule: Your entire output MUST start with <subtask_result> and end with </subtask_result>. All five sub-tags go between them. Do not output any text outside these tags.
The main thread only reads the content inside <subtask_result>. Anything outside the tag will be discarded.

<subtask_result>
<original_task>Echo back the assigned task content</original_task>
<findings>Key findings: concrete facts, numbers, quotes, evidence. When citing sources, use `<cite index="N" title="title" url="link">[N]</cite>` or `<cite index="N" title="filename" path="/mnt/data/path">[filename](/mnt/data/path)</cite>` format. Write "none" if empty</findings>
<result>Final conclusion/answer. This section will be shown to the user — write in user-facing language, do not mention tool names, internal file paths, function names, or implementation details</result>
<cite_files>Files referenced, created, or modified. Format per line: file_path brief description. If the input contains entries like "引用文件 /mnt/data/download/... description", list each corresponding file path and description. Leave empty if none</cite_files>
<todo>Remaining work, blockers, or suggestions for the main thread. Write "none" if the task is complete</todo>
</subtask_result>
"""


def build_subtask_instruction(subtask_content: str) -> str:
    """
    构建子任务执行指令（按 runtime language 注入输出格式要求）
    """
    lang = _resolve_runtime_language()
    if lang == "zh":
        return f"""[子任务执行模式]

## 被委派任务
{subtask_content}

## 执行边界
- 你正在执行主线程已经定义好的一个工作包；只负责这一段，不负责全局规划。
- 不要创建、修改、重建或接管全局 `todolist`。
- 你不是最终交付的总撰写者。除非指令明确要求你只产出某个局部草稿/局部章节，否则不要代替主线程写整份最终方案、最终报告、最终文章、最终建议或最终答复。
- 如果系统提示中出现 skill registry，先查看注册表；若任务匹配某个 skill，则按其 `location` 读取对应 `SKILL.md`。
- 如果你发现范围不清、输入不足、依赖缺失或任务过大，不要改写计划；直接在最终结果里说明阻塞点、已尝试内容以及建议主线程如何调整。
- 输出应围绕"这个被委派的工作包是否完成"来组织，而不是泛泛总结整个任务。
- 主产物必须完整写在 <result> 中：包括主要结论、分析、表格、局部草稿或可交付内容。
- 不要把主要结论、分析、表格或草稿只写入文件，然后在 <result> 中只给文件路径或一句说明。
- 只有当被委派任务明确要求创建/修改文件，或工具链硬性依赖文件时，才写文件；文件只能作为副产物。
- 即使按明确要求创建了文件，也必须在 <result> 中返回可读结论，让主线程无需读取文件也能汇总。

## 输出格式
硬性规则：你的整个输出必须以 <subtask_result> 开头、以 </subtask_result> 结尾。五个子标签必须放在这两个标签之间。不要在标签外输出任何文字。
主线程只会读取 <subtask_result> 标签内部的内容，标签外的任何文字都会被丢弃。

<subtask_result>
<original_task>回显被委派的任务内容</original_task>
<findings>关键发现：具体事实、数字、引用、证据。引用来源时使用 `<cite index="N" title="标题" url="链接">[N]</cite>` 或 `<cite index="N" title="文件名" path="/mnt/data/路径">[文件名](/mnt/data/路径)</cite>` 格式。若无则写"无"</findings>
<result>最终结论/答案。这一部分会展示给用户，请用面向用户的语言撰写，不要包含工具名、内部文件路径、函数名等实现细节</result>
<cite_files>执行过程中引用、创建或修改的文件。每行格式：文件路径 简要描述。若输入包含“引用文件 /mnt/data/download/... 描述”这类条目，必须逐条列出对应文件路径与说明。若无则留空</cite_files>
<todo>剩余工作、阻塞点、或给主线程的后续建议。若任务已完成则写"无"</todo>
</subtask_result>

IMPORTANT:
- <result> 是唯一会展示给用户的字段，必须用自然语言、面向用户撰写
- <findings> 中列出具体事实、数字、来源，使用 `<cite>` 标签引用来源，支撑 <result> 中的结论
- 引用的文件路径同时在 <cite_files> 中列出，便于主线程统一整理引用体系
- 内容要具体、客观，包含可验证的细节"""

    return f"""[Subtask Execution Mode]

## Assigned Work Package
{subtask_content}

## Execution Boundary
- You are executing a work package already defined by the main thread. Complete this slice only; do not take over global planning.
- Do not create, modify, rebuild, or take over the global `todolist`.
- You are not the author of the final deliverable. Unless the instruction explicitly asks for only a local draft or local section, do not replace the main thread in writing the full final plan, final report, final article, final recommendation, or final answer.
- If the system prompt contains a skill registry, inspect it first. When the task matches a skill, read the corresponding `SKILL.md` at its `location`.
- If scope is unclear, inputs are missing, dependencies are unavailable, or the task is too large, do not rewrite the plan. Report blockers, attempts, and adjustment suggestions in the final result.
- Organize your output around whether the assigned work package is complete.
- The primary deliverable MUST be written completely inside <result>: main conclusions, analysis, tables, local drafts, or deliverable content.
- Do not put the main conclusions, analysis, tables, or draft only in a file and leave only a file path or one-line note in <result>.
- Only create or modify files when the delegated task explicitly asks for it, or when a toolchain strictly depends on a file; files are only side artifacts.
- Even if you explicitly need to create a file, still return a readable conclusion in <result> so the main thread can synthesize without reading the file.

## Output Format
Hard rule: Your entire output MUST start with <subtask_result> and end with </subtask_result>. All five sub-tags go between them. Do not output any text outside these tags.
The main thread only reads the content inside <subtask_result>. Anything outside the tag will be discarded.

<subtask_result>
<original_task>Echo back the assigned task content</original_task>
<findings>Key findings: concrete facts, numbers, quotes, evidence. When citing sources, use `<cite index="N" title="title" url="link">[N]</cite>` or `<cite index="N" title="filename" path="/mnt/data/path">[filename](/mnt/data/path)</cite>` format. Write "none" if empty</findings>
<result>Final conclusion/answer. This section will be shown to the user — write in user-facing language, do not mention tool names, internal file paths, function names, or implementation details</result>
<cite_files>Files referenced, created, or modified. Format per line: file_path brief description. If the input contains entries like "引用文件 /mnt/data/download/... description", list each corresponding file path and description. Leave empty if none</cite_files>
<todo>Remaining work, blockers, or suggestions for the main thread. Write "none" if the task is complete</todo>
</subtask_result>

IMPORTANT:
- <result> is the only field shown to the user — use natural, user-facing language
- <findings> should list concrete facts, numbers, and sources using `<cite>` tags that support the <result>
- List all referenced file paths in <cite_files> as well, so the main thread can unify the citation system
- Be specific and objective; include verifiable details"""


def build_reject_subtask_prompt(remaining_loops: int, required_loops: int, rejected_count: int) -> str:
    """
    构建子任务拒绝提示（全局 loops 余量不足）
    """
    lang = _resolve_runtime_language()
    if lang == "zh":
        return (
            f"[系统提示] 无法执行子任务：全局 loops 余量不足。\n"
            f"- 当前剩余 loops: {remaining_loops}\n"
            f"- 子任务所需最小 loops: {required_loops}\n"
            f"- 被拒绝的子任务数量: {rejected_count}\n\n"
            f"请直接在当前上下文中完成任务，或给出当前进度的总结。"
        )

    return (
        f"[System Notice] Cannot execute subtask: insufficient remaining global loops.\n"
        f"- Remaining loops: {remaining_loops}\n"
        f"- Minimum loops required by subtask: {required_loops}\n"
        f"- Rejected subtask count: {rejected_count}\n\n"
        f"Please continue in the current context, or provide a progress summary."
    )


def build_reflection_instruction(focus: str) -> str:
    """
    构建反思指令（由 reflection 工具触发，按 runtime language 注入输出格式）
    """
    focus = (focus or "").strip()
    lang = _resolve_runtime_language()

    if lang == "zh":
        if focus:
            focus_block = f"反思焦点：{focus}"
        else:
            focus_block = "反思焦点：通用质量检查与证据完整性审视"

        return f"""{focus_block}

请基于已有上下文进行反思与自检，必要时可调用工具补充证据。
目标：发现遗漏、矛盾或证据不足的部分，并提出改进建议。

若系统提示中出现 skill registry，先查看注册表；如果反思任务匹配某个 skill，则按其 `location` 读取对应 `SKILL.md`。

## 输出格式
硬性规则：你的整个输出必须以 <reflection> 开头、以 </reflection> 结尾。五个子标签必须放在这两个标签之间。不要在标签外输出任何文字。
主线程只会读取 <reflection> 标签内部的内容，标签外的任何文字都会被丢弃。

<reflection>
<original_task>回显反思焦点</original_task>
<findings>发现的问题、遗漏、矛盾或确认项。每项必须使用 XML 结构：<item><category>类别</category><finding>具体发现；如需引用外部证据，在这里使用 `<cite index="N" title="标题" url="链接">[N]</cite>` 或 `<cite index="N" title="文件名" path="/mnt/data/路径">[文件名](/mnt/data/路径)</cite>`</finding><source>来源类型或来源描述，例如：用户需求、上下文、工具结果、外部资料</source></item>。若无则写"无"</findings>
<result>综合判断/反思结论。这一部分会展示给用户，请用面向用户的语言撰写，不要包含工具名、内部文件路径、函数名等实现细节</result>
<cite_files>反思过程中引用的文件或来源。每行使用 Markdown 链接格式：[显示文本](路径或URL)。例如：[欧盟委员会关于 AI Act 监管框架及适用时间表的官方页面](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)。若无则留空</cite_files>
<todo>改进建议或建议主线程采取的下一步行动。若无则写"无"</todo>
</reflection>

IMPORTANT:
- <result> 是唯一会展示给用户的字段，必须用自然语言、面向用户撰写
- <findings> 每项使用 `<item>`，内部包含 `<category>`、`<finding>`、`<source>`；外部证据引用放在 `<finding>` 中
- 内容客观具体，避免空话"""

    if focus:
        focus_block = f"Reflection focus: {focus}"
    else:
        focus_block = "Reflection focus: general quality checks and evidence completeness"

    return f"""{focus_block}

Reflect on the current execution context and self-check the quality.
Use tools when needed to add supporting evidence.

If the system prompt contains a skill registry, inspect it first. When the reflection task matches a skill, read the corresponding `SKILL.md` at its `location`.

## Output Format
Hard rule: Your entire output MUST start with <reflection> and end with </reflection>. All five sub-tags go between them. Do not output any text outside these tags.
The main thread only reads the content inside <reflection>. Anything outside the tag will be discarded.

<reflection>
<original_task>Echo back the reflection focus</original_task>
<findings>Issues, gaps, contradictions, or confirmations found. Each item MUST use this XML structure: <item><category>category</category><finding>specific finding; when citing external evidence, include `<cite index="N" title="title" url="link">[N]</cite>` or `<cite index="N" title="filename" path="/mnt/data/path">[filename](/mnt/data/path)</cite>` here</finding><source>source type or source description, such as user requirement, context, tool result, or external material</source></item>. Write "none" if empty</findings>
<result>Overall assessment/reflection conclusion. This section will be shown to the user — write in user-facing language, do not mention tool names, internal file paths, function names, or implementation details</result>
<cite_files>Files or sources referenced during reflection. Use Markdown link format on each line: [display text](path or URL). Example: [European Commission official page on the AI Act regulatory framework and timeline](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai). Leave empty if none</cite_files>
<todo>Improvement suggestions or recommended next steps for the main thread. Write "none" if empty</todo>
</reflection>

IMPORTANT:
- <result> is the only field shown to the user — use natural, user-facing language
- <findings> items should use `<item>` with `<category>`, `<finding>`, and `<source>`; put external evidence citations inside `<finding>`
- Be concrete and objective"""


def build_reflection_finalize_prompt(original_task: str, state: Dict[str, Any], agent_name: str) -> str:
    """
    构建反思 finalize prompt：在反思被 stop 中断时产出结构化 <reflection>。
    """
    lang = _resolve_runtime_language(state)
    if lang == "zh":
        return f"""你是反思 Agent。请基于已有上下文输出最终反思结果，不要新增工具调用或外部检索。

## 原始反思任务
{original_task}

## 输出格式
用 <reflection> 标签包裹，内部使用子标签结构化输出：
主线程只会读取 <reflection> 标签内部的内容。标签外的任何文字都会被丢弃，因此不要在标签前后输出额外说明。

<reflection>
<original_task>回显反思焦点</original_task>
<findings>发现的问题、遗漏、矛盾或确认项。每项必须使用 XML 结构：<item><category>类别</category><finding>具体发现；如需引用外部证据，在这里使用 `<cite index="N" title="标题" url="链接">[N]</cite>` 或 `<cite index="N" title="文件名" path="/mnt/data/路径">[文件名](/mnt/data/路径)</cite>`</finding><source>来源类型或来源描述，例如：用户需求、上下文、工具结果、外部资料</source></item>。若无则写"无"</findings>
<result>综合判断/反思结论。这一部分会展示给用户，请用面向用户的语言撰写，不要包含工具名、内部文件路径、函数名等实现细节</result>
<cite_files>反思过程中引用的文件或来源。每行使用 Markdown 链接格式：[显示文本](路径或URL)。例如：[欧盟委员会关于 AI Act 监管框架及适用时间表的官方页面](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)。若无则留空</cite_files>
<todo>改进建议或建议主线程采取的下一步行动。若无则写"无"</todo>
</reflection>

要求：
- <result> 用自然语言，面向用户
- <findings> 每项使用 `<item>`，内部包含 `<category>`、`<finding>`、`<source>`；外部证据引用放在 `<finding>` 中
- 内容客观具体，避免空话
"""

    return f"""You are the reflection agent. Produce a final reflection from existing context only.
Do not call new tools or perform new external searches.

## Original Reflection Task
{original_task}

## Output Format
Wrap output in <reflection> tags with structured sub-tags:
The main thread only reads the content inside <reflection>. Anything outside the tag will be discarded, so do not add extra prose before or after it.

<reflection>
<original_task>Echo back the reflection focus</original_task>
<findings>Issues, gaps, contradictions, or confirmations found. Each item MUST use this XML structure: <item><category>category</category><finding>specific finding; when citing external evidence, include `<cite index="N" title="title" url="link">[N]</cite>` or `<cite index="N" title="filename" path="/mnt/data/path">[filename](/mnt/data/path)</cite>` here</finding><source>source type or source description, such as user requirement, context, tool result, or external material</source></item>. Write "none" if empty</findings>
<result>Overall assessment/reflection conclusion. This section will be shown to the user — write in user-facing language, do not mention tool names, internal file paths, function names, or implementation details</result>
<cite_files>Files or sources referenced during reflection. Use Markdown link format on each line: [display text](path or URL). Example: [European Commission official page on the AI Act regulatory framework and timeline](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai). Leave empty if none</cite_files>
<todo>Improvement suggestions or recommended next steps for the main thread. Write "none" if empty</todo>
</reflection>

Requirements:
- <result> should be user-facing natural language
- <findings> items should use `<item>` with `<category>`, `<finding>`, and `<source>`; put external evidence citations inside `<finding>`
- Be concrete and objective"""
