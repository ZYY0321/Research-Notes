import json
import logging
import os
import shlex
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.agentv3.agent_v3 import (
    AgentV3,
    MainAgent,
    ReflectionAgent,
    SubtaskAgent,
    build_delegate_tools,
    init_ctx,
)
from agents.agentv3.core.runtime_components import (
    _compress_skills_folder,
    _load_skill_assets,
    resolve_locale_resources,
)
from backend.sandbox_storage import (
    PERSISTED_SANDBOX_EXCLUDE_SUBDIRS,
    get_conversation_persisted_root,
    iter_conversation_persisted_files,
    resolve_configured_retrieve_base,
)
from backend.replay_runtime import restore_workspace_snapshot
from src.base_agent import BaseNode
from src.conversation_state_v3 import detect_locale
from src.utils import ctx
from src.utils.cancellation import ensure_not_cancelled
from src.utils.streamer import Streamer
from tools.sandbox.sandbox_manager import LLMSandbox


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TENANT_ID = "default"


def _normalize_locale_hint(locale: Optional[str]) -> Optional[str]:
    if not locale:
        return None
    value = str(locale).strip()
    if not value:
        return None
    lower = value.lower()
    if lower.startswith("zh"):
        return "zh-CN"
    if lower.startswith("en"):
        return "en-US"
    return value


def _inject_case_identity_into_config(conf: Dict[str, Any], case: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(conf, dict):
        return conf
    case = case or {}
    user_id = case.get("user_id")
    tenant_id = case.get("tenant_id") or DEFAULT_TENANT_ID
    if user_id not in (None, ""):
        conf["user_id"] = str(user_id)
    if tenant_id not in (None, ""):
        conf["tenant_id"] = str(tenant_id)
    return conf


def _extract_state_locale_hint(state: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(state, dict):
        return None
    preferred_locale = _normalize_locale_hint((state.get("session_metadata") or {}).get("preferred_locale"))
    runtime_locale = _normalize_locale_hint((state.get("runtime_control") or {}).get("current_prompt_locale"))
    return preferred_locale or runtime_locale


def _resolve_runtime_locale_inputs(
    *,
    case: Dict[str, Any],
    raw_query: str,
    runtime_default_locale: Optional[str],
) -> tuple[str, str]:
    locale_hint = _extract_state_locale_hint(case.get("agent_state"))
    resume_answers = case.get("resume_answers")
    locale_seed = str(raw_query or "")

    if locale_hint and bool(case.get("suppress_user_query_message") or resume_answers):
        return locale_hint, locale_seed

    if not locale_seed and resume_answers:
        locale_seed = json.dumps(resume_answers, ensure_ascii=False)
    detected_locale = detect_locale(
        locale_seed,
        default_locale=runtime_default_locale or locale_hint,
    )
    return detected_locale, locale_seed


def _resolve_disabled_tools_for_case(case: Dict[str, Any]) -> set[str]:
    disabled: set[str] = set()

    if case.get("supports_ask_user") is False:
        disabled.add("ask_user")

    raw_extra = case.get("disable_tools")
    if isinstance(raw_extra, (list, tuple, set)):
        for item in raw_extra:
            name = str(item or "").strip()
            if name:
                disabled.add(name)

    return disabled


def _collect_conversation_persisted_workspace_files(
    conversation_id: str,
    *,
    sandbox_conf: Optional[Dict[str, Any]] = None,
    config_path: Optional[str | Path] = None,
) -> List[Dict[str, str]]:
    """Collect previously persisted sandbox workspace files for a conversation."""
    cid = str(conversation_id or "").strip()
    if not cid:
        return []

    files = iter_conversation_persisted_files(
        PROJECT_ROOT,
        cid,
        sandbox_conf=sandbox_conf,
        config_path=config_path,
    )
    return [
        {
            "relative_path": rel_path,
            "local_path": os.path.abspath(str(local_path)),
        }
        for rel_path, local_path in files
    ]


def _restore_persisted_workspace_files_to_sandbox(
    *,
    sandbox_manager: LLMSandbox,
    session_id: str,
    conversation_id: str,
    persisted_files: List[Dict[str, str]],
) -> int:
    if not persisted_files:
        return 0

    mkdir_targets = set()
    sandbox_root = str(sandbox_manager.absolute_sandbox_path or "/mnt/data").rstrip("/")
    for item in persisted_files:
        rel_path = str(item.get("relative_path") or "").strip().lstrip("/")
        parent = os.path.dirname(rel_path)
        if parent:
            mkdir_targets.add(f"{sandbox_root}/{parent}")

    if mkdir_targets:
        mkdir_cmd = " && ".join(f"mkdir -p {shlex.quote(path)}" for path in sorted(mkdir_targets))
        sandbox_manager.client.execute_command(session_id=session_id, command=mkdir_cmd)

    restored_count = 0
    for item in persisted_files:
        rel_path = str(item.get("relative_path") or "").strip().lstrip("/")
        local_path = str(item.get("local_path") or "").strip()
        if not rel_path or not local_path or not os.path.exists(local_path):
            continue
        with open(local_path, "rb") as file_obj:
            data = file_obj.read()
        sandbox_manager.put_file(session_id=session_id, filename=rel_path, data=data)
        restored_count += 1

    logger.info(
        "[%s] 已回填会话持久化文件: %s个（排除目录: %s）",
        conversation_id,
        restored_count,
        ",".join(PERSISTED_SANDBOX_EXCLUDE_SUBDIRS),
    )
    return restored_count


def _build_sandbox_manager(
    *,
    case: Dict[str, Any],
    components: Dict[str, Any],
    conversation_id: str,
) -> LLMSandbox:
    conf = components["conf"]
    sandbox_conf = components["sandbox_conf"]
    skill_assets = components.get("skill_assets", {})
    config_path = components.get("config_path")
    persist_workspace_state = bool(case.get("persist_sandbox_state")) and bool(conversation_id)

    retrieve_path = sandbox_conf.get("sandbox_retrieve_path")
    retrieve_subdirs = sandbox_conf.get("sandbox_retrieve_subdirs")
    retrieve_exclude_subdirs = sandbox_conf.get("sandbox_retrieve_exclude_subdirs") or []
    use_conversation_subdir = sandbox_conf.get("sandbox_retrieve_use_session_subdir", True)
    sandbox_root = str(sandbox_conf.get("sandbox_absolute_path") or "/mnt/data").rstrip("/")
    configured_retrieve_base = resolve_configured_retrieve_base(
        PROJECT_ROOT,
        sandbox_conf=sandbox_conf,
        config_path=config_path,
    )
    configured_conversation_root = (
        get_conversation_persisted_root(
            PROJECT_ROOT,
            conversation_id,
            sandbox_conf=sandbox_conf,
            config_path=config_path,
        )
        if configured_retrieve_base is not None
        else None
    )

    def _to_relative_under_sandbox(path_value: str) -> str:
        path = str(path_value or "").strip()
        if not path:
            return ""
        if path.startswith(sandbox_root + "/"):
            return path[len(sandbox_root) + 1:].strip("/")
        if path == "/mnt/data/history":
            return "history"
        if path == "/mnt/data/skill":
            return "skill"
        return ""

    # 后端多轮会话优先复用 conversation 级持久化目录，这样同一会话的工作区能连续恢复。
    if configured_conversation_root is not None:
        retrieve_path = str(configured_conversation_root)
        use_conversation_subdir = False
        if persist_workspace_state:
            retrieve_subdirs = None
            retrieve_exclude_subdirs = list(PERSISTED_SANDBOX_EXCLUDE_SUBDIRS)
        else:
            skills_dir = str(skill_assets.get("skills_sandbox_dir") or f"{sandbox_root}/skill")
            excluded = _to_relative_under_sandbox(skills_dir)
            if excluded and excluded not in retrieve_exclude_subdirs:
                retrieve_exclude_subdirs.append(excluded)
    elif persist_workspace_state:
        # 兼容旧模式：即使没有显式配置 retrieve root，也把整轮工作区持久化到默认会话目录。
        retrieve_path = str(get_conversation_persisted_root(PROJECT_ROOT, conversation_id))
        retrieve_subdirs = None
        retrieve_exclude_subdirs = list(PERSISTED_SANDBOX_EXCLUDE_SUBDIRS)
        use_conversation_subdir = False
    else:
        skills_dir = str(skill_assets.get("skills_sandbox_dir") or f"{sandbox_root}/skill")
        excluded = _to_relative_under_sandbox(skills_dir)
        if excluded and excluded not in retrieve_exclude_subdirs:
            retrieve_exclude_subdirs.append(excluded)

        if getattr(ctx, "result_dir", None):
            retrieve_path = str(ctx.result_dir)
            use_conversation_subdir = False

    return LLMSandbox(
        base_url=sandbox_conf.get("sandbox_base_url"),
        timeout=sandbox_conf.get("sandbox_timeout"),
        absolute_sandbox_path=sandbox_conf.get("sandbox_absolute_path"),
        retrieve_path=retrieve_path,
        retrieve_subdirs=retrieve_subdirs,
        retrieve_exclude_subdirs=retrieve_exclude_subdirs,
        retrieve_use_session_subdir=use_conversation_subdir,
    )


def _create_agent(localized_tools: List[Dict[str, Any]], llm: Any, conf: Dict[str, Any]) -> AgentV3:
    # 主/子任务/反思三套 agent 的构造逻辑保持集中，避免入口层再重新拼一遍。
    main_node = BaseNode(
        name="main",
        llm=llm,
        tools=localized_tools,
    )
    main_agent = MainAgent(
        name="main_agent",
        nodes=[main_node],
        entry_point="main",
        max_loops=conf.get("runtime", {}).get("max_loops", 20),
    )

    subtask_tools = build_delegate_tools(localized_tools)
    subtask_node = BaseNode(
        name="main",
        llm=llm,
        tools=subtask_tools,
    )
    subtask_agent = SubtaskAgent(
        name="subtask_agent",
        nodes=[subtask_node],
        entry_point="main",
        max_loops=conf.get("runtime", {}).get("subtask_max_loops", 5),
    )

    reflection_node = BaseNode(
        name="main",
        llm=llm,
        tools=subtask_tools,
    )
    reflection_agent = ReflectionAgent(
        name="reflection_agent",
        nodes=[reflection_node],
        entry_point="main",
        max_loops=conf.get("runtime", {}).get("subtask_max_loops", 5),
    )

    delegate_parallelism = conf.get("runtime", {}).get("delegate_parallelism", 4)

    return AgentV3(
        name="agent",
        main_agent=main_agent,
        subtask_agent=subtask_agent,
        reflection_agent=reflection_agent,
        entry_point="main_agent",
        delegate_parallelism=delegate_parallelism,
    )


def prepare_session(
    case: Dict[str, Any],
    components: Dict[str, Any],
    conversation_id: Optional[str] = None,
) -> Dict[str, Any]:
    log = logging.getLogger(__name__)
    legacy_session_id = str(case.get("session_id") or "").strip()
    # conversation_id 保持线程级稳定；session_id 允许每次运行重新生成。
    resolved_conversation_id = str(
        case.get("conversation_id") or conversation_id or legacy_session_id or ""
    ).strip()
    if not resolved_conversation_id:
        resolved_conversation_id = str(uuid.uuid4())
    runtime_session_id = str(case.get("session_id") or "").strip() or str(uuid.uuid4())
    case["conversation_id"] = resolved_conversation_id
    case["session_id"] = runtime_session_id

    effective_components = dict(components)
    conf = deepcopy(components["conf"])
    effective_components["conf"] = conf
    effective_components["skill_assets"] = _load_skill_assets(conf)
    _inject_case_identity_into_config(conf, case)
    memory_user_id = None
    sandbox_manager = _build_sandbox_manager(
        case=case,
        components=effective_components,
        conversation_id=resolved_conversation_id,
    )
    sandbox_manager.create_workspace(session_id=runtime_session_id)
    ensure_not_cancelled()

    skill_assets = effective_components.get("skill_assets", {})
    if skill_assets.get("enabled"):
        skills_local_dir = skill_assets.get("skills_local_dir", "skills")
        skills_sandbox_dir = skill_assets.get("skills_sandbox_dir", "/mnt/data/skill")
        skills_allowlist = skill_assets.get("skills_allowlist") or []
        skills_extra_dirs = skill_assets.get("skills_extra_dirs") or []
        try:
            ensure_not_cancelled()
            log.info("[%s] 开始压缩 skills 文件夹: %s", resolved_conversation_id, skills_local_dir)
            skills_zip_data = _compress_skills_folder(
                skills_local_dir,
                allowlist=skills_allowlist,
                extra_dirs=skills_extra_dirs,
            )
            if skills_zip_data:
                # skills 作为运行时依赖放进 sandbox，和本地工作区解耦。
                log.info("[%s] 开始上传 skills.zip 到沙盒...", resolved_conversation_id)
                sandbox_manager.put_file(session_id=runtime_session_id, filename="skills.zip", data=skills_zip_data)
                unzip_cmd = (
                    f"mkdir -p {skills_sandbox_dir} && "
                    f"unzip -q -o {sandbox_manager.absolute_sandbox_path}/skills.zip -d {skills_sandbox_dir} && "
                    f"rm -f {sandbox_manager.absolute_sandbox_path}/skills.zip"
                )
                unzip_result = sandbox_manager.client.execute_command(
                    session_id=runtime_session_id,
                    command=unzip_cmd,
                )
                if getattr(unzip_result, "return_code", 1) == 0:
                    log.info("[%s] skills.zip 解压成功 -> %s", resolved_conversation_id, skills_sandbox_dir)
                else:
                    log.warning(
                        "[%s] skills.zip 解压失败: %s",
                        resolved_conversation_id,
                        getattr(unzip_result, "stderr", ""),
                    )
            else:
                log.warning("[%s] 压缩 skills 文件夹失败，跳过上传", resolved_conversation_id)
        except Exception as exc:
            log.warning("[%s] 压缩/上传/解压 skills 失败: %s", resolved_conversation_id, exc)

    restore_workspace_snapshot_id = str(case.get("restore_workspace_snapshot_id") or "").strip()
    if restore_workspace_snapshot_id:
        try:
            ensure_not_cancelled()
            restore_workspace_snapshot(
                conversation_id=resolved_conversation_id,
                snapshot_id=restore_workspace_snapshot_id,
                sandbox_manager=sandbox_manager,
                session_id=runtime_session_id,
                user_id=int(case["user_id"]) if case.get("user_id") not in (None, "") else None,
            )
            log.info("[%s] 已恢复 replay workspace snapshot: %s", resolved_conversation_id, restore_workspace_snapshot_id)
        except Exception as exc:
            log.warning("[%s] 恢复 replay workspace snapshot 失败，降级继续: %s", resolved_conversation_id, exc)
    elif bool(case.get("persist_sandbox_state")) and resolved_conversation_id:
        try:
            ensure_not_cancelled()
            persisted_workspace_files = _collect_conversation_persisted_workspace_files(
                resolved_conversation_id,
                sandbox_conf=effective_components["sandbox_conf"],
                config_path=effective_components.get("config_path"),
            )
            _restore_persisted_workspace_files_to_sandbox(
                sandbox_manager=sandbox_manager,
                session_id=runtime_session_id,
                conversation_id=resolved_conversation_id,
                persisted_files=persisted_workspace_files,
            )
        except Exception as exc:
            log.warning("[%s] 回填会话持久化文件失败，降级继续: %s", resolved_conversation_id, exc)

    raw_query = case.get("query", "")
    runtime_conf = conf.get("runtime", {}) or {}
    detected_locale, locale_seed = _resolve_runtime_locale_inputs(
        case=case,
        raw_query=raw_query,
        runtime_default_locale=runtime_conf.get("language"),
    )
    disabled_tools = _resolve_disabled_tools_for_case(case)
    system_prompt_template, localized_tools, runtime_lang = resolve_locale_resources(
        effective_components,
        detected_locale,
        disabled_tools=disabled_tools,
    )
    agent = _create_agent(localized_tools, effective_components["llm"], conf)

    active_streamer = getattr(ctx, "streamer", None) or Streamer()
    init_ctx(
        runtime_session_id,
        str(effective_components["config_path"]),
        conf,
        effective_components["llm"],
        effective_components["vlm"],
        effective_components["audio_basellm"],
        active_streamer,
        memory_user_id=memory_user_id,
        conversation_id=resolved_conversation_id,
        user_id=int(case["user_id"]) if case.get("user_id") not in (None, "") else None,
        sandbox_manager=sandbox_manager,
        stop_event=getattr(ctx, "stop_event", None),
    )

    main_tool_schemas = [
        deepcopy(tool["schema"])
        for tool in localized_tools
        if isinstance(tool, dict) and isinstance(tool.get("schema"), dict)
    ]
    delegate_tool_schemas = [
        deepcopy(tool["schema"])
        for tool in build_delegate_tools(localized_tools)
        if isinstance(tool, dict) and isinstance(tool.get("schema"), dict)
    ]

    return {
        "agent": agent,
        "conf": conf,
        "conversation_id": resolved_conversation_id,
        "detected_locale": detected_locale,
        "locale_seed": locale_seed,
        "log": log,
        "memory_user_id": memory_user_id,
        "raw_query": raw_query,
        "runtime_conf": runtime_conf,
        "runtime_lang": runtime_lang,
        "runtime_session_id": runtime_session_id,
        "sandbox_manager": sandbox_manager,
        "system_prompt_template": system_prompt_template,
        "main_tool_schemas": main_tool_schemas,
        "delegate_tool_schemas": delegate_tool_schemas,
    }
