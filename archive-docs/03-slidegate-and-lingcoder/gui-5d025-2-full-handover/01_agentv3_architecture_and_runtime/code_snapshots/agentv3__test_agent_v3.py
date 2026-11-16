#!/usr/bin/env python3
"""
交互式 Agent 运行脚本
提供命令行交互环境，用户可以输入 query 和文件路径，执行一次 agent 并将结果保存到结果目录
"""
import argparse
import json
import logging
import os
import re
import sys
import io
import zipfile
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

# 添加项目根目录到 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.base_llm import BaseLLM
from src.utils import load_yaml_config
from src.utils.streamer import Streamer
from src.utils.tool_utils import load_tools
from src.base_agent import BaseAgent, BaseNode

from tools.sandbox.sandbox_manager import LLMSandbox
from agents.agentv3.system_prompt_utils import render_system_prompt, resolve_system_prompt_path
from agents.agentv3.agent_v3 import MainAgent, SubtaskAgent, ReflectionAgent, AgentV3, init_ctx
from agents.agentv3.system_prompt_utils import render_system_prompt, build_system_prompt_with_memory
from agents.agentv3.agent_v3 import init_ctx
# from agents.agentv3.ppt_artifact_verifier import resolve_local_workspace_dir, verify_workspace
from memory.config_resolver import resolve_memory_user_id
from memory.config_resolver import get_jobs_config
from memory.job_queue import JOB_TYPE_SUMMARY, get_job_by_key
from agents.agentv3 import run_agent as _run_agent
import uuid

# 设置日志
def setup_logger(log_dir: Path) -> logging.Logger:
    """设置日志记录器."""
    if isinstance(log_dir, str):
        log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_filename = log_dir / f"react_agent_concurrent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)

logger = setup_logger("logs/demo")
logger.setLevel(logging.DEBUG)

def sanitize_filename(text: str, max_length: int = 50) -> str:
    """清理文本，使其适合作为文件名"""
    # 移除或替换不安全的字符
    text = re.sub(r'[<>:"/\\|?*]', '_', text)
    # 移除多余的空格
    text = re.sub(r'\s+', '_', text.strip())
    # 限制长度
    if len(text) > max_length:
        text = text[:max_length]
    return text

summarize_prompt_template = """
请将以下用户问题压缩为一个简洁的摘要（不超过{max_length}个字符），用于文件命名。

用户问题：
{query}

要求：
1. 提取问题的核心关键词
2. 使用简洁的中文或英文
3. 不超过{max_length}个字符
4. 只返回摘要内容，不要包含其他说明文字

摘要："""

def summarize_query(query: str, llm: BaseLLM, max_length: int = 15) -> str:
    """使用 LLM 总结用户问题，生成压缩版本"""
    logger.info(f"start summarize_query")
    try:
        
        prompt = summarize_prompt_template.format(query=query, max_length=max_length)
        response = llm.completion(
            messages=[{"role": "user", "content": prompt}]
        )
        summary = response.get("content", "").strip()
        
        # 清理摘要，移除可能的引号或说明文字
        summary = re.sub(r'^["\']|["\']$', '', summary)
        summary = re.sub(r'^摘要[：:]\s*', '', summary, flags=re.IGNORECASE)
        summary = summary.strip()
        
        if not summary or len(summary) > 50:
            # 如果总结失败或太长，使用原始问题的简化版本
            summary = query[:30] if len(query) > 30 else query
            summary = sanitize_filename(summary, max_length=30)
        
        logger.info(f"end summarize_query: {summary}")
        return sanitize_filename(summary, max_length=30)
    except Exception as e:
        logger.warning(f"LLM 总结失败: {e}，使用原始问题简化版本")
        # 失败时使用原始问题的简化版本
        summary = query[:30] if len(query) > 30 else query
        logger.info(f"end summarize_query: {summary}")
        return sanitize_filename(summary, max_length=30)


def _load_skill_assets(conf: Dict[str, Any]) -> Dict[str, Any]:
    tool_conf = conf.get("tools", {}).get("skill_tool", {}) or {}
    enabled = bool(tool_conf.get("enabled"))
    tool_cfg = tool_conf.get("config", {}) or {}

    skills_local_dir = tool_cfg.get("skills_local_dir", "skills")
    skills_sandbox_dir = tool_cfg.get("skills_sandbox_dir", "/mnt/data/skill")
    skills_allowlist = tool_cfg.get("skills_allowlist") or []

    return {
        "enabled": enabled,
        "skills_local_dir": skills_local_dir,
        "skills_sandbox_dir": skills_sandbox_dir,
        "skills_allowlist": skills_allowlist,
    }


def _compress_skills_folder(skills_dir: str, allowlist: Optional[List[str]] = None) -> Optional[bytes]:
    """动态压缩 skills 文件夹为 zip 格式并返回字节数据."""
    skills_path = Path(skills_dir)
    if not skills_path.exists() or not skills_path.is_dir():
        logger.warning(f"Skills 目录不存在或不是文件夹: {skills_path}")
        return None

    allow = {item.strip().lower() for item in (allowlist or []) if isinstance(item, str)}

    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(skills_path):
                root_path = Path(root)
                for file in files:
                    file_path = root_path / file
                    rel_path = file_path.relative_to(skills_path)
                    if allow and rel_path.parts and rel_path.parts[0].lower() not in allow:
                        continue
                    zipf.write(file_path, rel_path.as_posix())
        data = buf.getvalue()
        logger.info(f"成功压缩 skills 文件夹: {skills_path}, 大小: {len(data)} bytes")
        return data
    except Exception as exc:
        logger.error(f"压缩 skills 文件夹失败: {exc}", exc_info=True)
        return None


def create_result_directory(query: str, llm: BaseLLM, base_dir: Path = Path("results")) -> Path:
    """创建结果目录，格式：时间戳_压缩后的用户问题"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    query_summary = summarize_query(query, llm, max_length=15)
    dir_name = f"{timestamp}_{query_summary}"
    result_dir = base_dir / dir_name
    result_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"结果目录已创建: {result_dir}")
    return result_dir


def save_result(result_dir: Path, case: Dict[str, Any], result: Dict[str, Any]):
    """保存结果到结果目录"""
    # 保存完整结果
    result_file = result_dir / "result.json"
    output = {
        "case": case,
        "result": result,
        "timestamp": datetime.now().isoformat(),
    }
    with result_file.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    logger.info(f"结果已保存到: {result_file}")
    
    # 保存简化的响应文本
    if result.get("success") and result.get("response"):
        response_file = result_dir / "response.txt"
        with response_file.open("w", encoding="utf-8") as f:
            f.write(result["response"])
        logger.info(f"响应文本已保存到: {response_file}")


def verify_ppt_artifacts(
    *,
    result_dir: Path,
    case: Dict[str, Any],
    components: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    session_id = str(case.get("session_id") or "").strip()
    if not session_id:
        return None

    workspace_dir = resolve_local_workspace_dir(session_id, components.get("sandbox_conf", {}) or {})
    if workspace_dir is None or not workspace_dir.exists():
        logger.warning("PPT verifier 跳过：未找到本地 sandbox 工作区。session_id=%s", session_id)
        return None

    report = verify_workspace(workspace_dir)
    report_file = result_dir / "ppt_verification.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("PPT verifier 报告已写入: %s", report_file)

    if report.get("status") == "failed":
        logger.warning("PPT verifier 检测到 %s 个问题。", report.get("issue_count"))
        for deck in report.get("decks", []):
            for issue in deck.get("issues", [])[:20]:
                logger.warning("PPT verifier issue [%s]: %s", issue.get("code"), issue.get("message"))
    elif report.get("status") == "passed":
        logger.info("PPT verifier 通过：未发现结构或引用问题。")
    else:
        logger.info("PPT verifier 跳过：工作区中未发现 deck 目录。")

    return report

def parse_args() -> argparse.Namespace:
    """解析命令行参数。

    当提供 --query 时，脚本将不再进入交互式输入模式（也不再询问文件路径）。
    可选提供 --file/-f 指定本地文件路径（可多次传入多个文件）。
    """
    parser = argparse.ArgumentParser(description="交互式/非交互式运行 Agent 的脚本")
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="直接从命令行指定用户query；提供后将跳过交互式输入",
    )
    parser.add_argument(
        "--file",
        "-f",
        action="append",
        default=None,
        help="指定本地文件路径（可多次使用，例如 -f a.pdf -f b.png）；提供后将跳过交互式文件路径输入",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Agent 配置文件路径；未提供时优先使用 conf_v3_zh.yaml",
    )
    return parser.parse_args()



def build_agent_components(conf_path: Path, conversation_id: str) -> Dict[str, Any]:
    """初始化 LLM/VLM 与工具等共用组件."""
    conf = load_yaml_config(str(conf_path))
    skill_assets = _load_skill_assets(conf)

    llm_conf = conf.get("llm", {})
    vlm_conf = conf.get("vlm", {})
    audio_basellm_conf = conf.get("audio_basellm", {})

    logger.info(f"初始化 LLM，模型: {llm_conf.get('model')}")
    llm = BaseLLM(
        model=llm_conf.get("model"),
        api_key=llm_conf.get("api_key"),
        base_url=llm_conf.get("base_url"),
        provider=llm_conf.get("provider"),
        max_tokens=llm_conf.get("max_tokens", 4096),
        temperature=llm_conf.get("temperature", 0.7),
    )

    logger.info(f"初始化 VLM，模型: {vlm_conf.get('model')}")
    vlm = BaseLLM(
        model=vlm_conf.get("model"),
        api_key=vlm_conf.get("api_key"),
        base_url=vlm_conf.get("base_url"),
        provider=vlm_conf.get("provider"),
    )

    logger.info(f"初始化 Audio LLM，模型: {audio_basellm_conf.get('model')}")
    audio_basellm = BaseLLM(
        model=audio_basellm_conf.get("model"),
        api_key=audio_basellm_conf.get("api_key"),
        base_url=audio_basellm_conf.get("base_url"),
        provider=audio_basellm_conf.get("provider"),
        temperature=audio_basellm_conf.get("temperature", 0.7),
    )
    # 从配置文件中读取系统提示路径
    runtime_conf = conf.get("runtime", {})
    runtime_lang = runtime_conf.get("language")
    system_prompt_path = resolve_system_prompt_path(
        runtime_conf,
        default_zh="agents/agentv3/system_prompt_zh.md",
        default_en="agents/agentv3/system_prompt_en.md",
    )
    system_prompt = render_system_prompt(config_path=str(conf_path), template_path=str(system_prompt_path))
    tools = load_tools(config=conf['tools'], language=runtime_lang)

    logger.debug(f"start create sandbox_manager")
    sandbox_conf = conf.get("sandbox", {}) or conf.get("sandbox_conf", {})
    sandbox_manager = LLMSandbox(
        base_url=sandbox_conf.get("sandbox_base_url"),
        timeout=sandbox_conf.get("sandbox_timeout"),
        absolute_sandbox_path=sandbox_conf.get("sandbox_absolute_path"),
        retrieve_path=sandbox_conf.get("sandbox_retrieve_path"),
        retrieve_subdirs=sandbox_conf.get("sandbox_retrieve_subdirs"),
        retrieve_use_session_subdir=sandbox_conf.get("sandbox_retrieve_use_session_subdir", True),
    )

    logger.debug(f"start create_workspace")
    sandbox_manager.create_workspace(session_id=conversation_id)
    # print('warning: sandbox_manager.create_workspace is not implemented')
    session_id = conversation_id
    # 动态压缩并上传 skills 文件夹到沙盒
    if skill_assets.get("enabled"):
        skills_local_dir = skill_assets.get("skills_local_dir", "skills")
        skills_sandbox_dir = skill_assets.get("skills_sandbox_dir", "/mnt/data/skill")
        skills_allowlist = skill_assets.get("skills_allowlist") or []
        try:
            logger.info(f"[{session_id}] 开始压缩 skills 文件夹: {skills_local_dir}")
            skills_zip_data = _compress_skills_folder(skills_local_dir, allowlist=skills_allowlist)

            if skills_zip_data:
                logger.info(f"[{session_id}] 开始上传 skills.zip 到沙盒...")
                sandbox_manager.put_file(session_id=session_id, filename="skills.zip", data=skills_zip_data)
                logger.info(f"[{session_id}] skills.zip 上传成功，开始解压...")

                # 在沙盒中解压 skills.zip
                unzip_cmd = (
                    f"mkdir -p {skills_sandbox_dir} && "
                    f"unzip -q -o {sandbox_manager.absolute_sandbox_path}/skills.zip -d {skills_sandbox_dir} && "
                    f"rm -f {sandbox_manager.absolute_sandbox_path}/skills.zip"
                )
                unzip_result = sandbox_manager.client.execute_command(
                    session_id=session_id,
                    command=unzip_cmd
                )
                if getattr(unzip_result, "return_code", 1) == 0:
                    logger.info(f"[{session_id}] skills.zip 解压成功 -> {skills_sandbox_dir}")
                else:
                    logger.warning(f"[{session_id}] skills.zip 解压失败: {getattr(unzip_result, 'stderr', '')}")
            else:
                logger.warning(f"[{session_id}] 压缩 skills 文件夹失败，跳过上传")
        except Exception as exc:
            logger.warning(f"[{session_id}] 压缩/上传/解压 skills 失败: {exc}")
    

    # create main_agent
    # main_agent 内部处理 loops、tool_calls、extra_loops_for_final、收尾模式
    main_node = BaseNode(
        name="main",
        llm=llm,
        tools=tools,
        message_key="messages",
    )
    main_agent = MainAgent(
        name="main_agent", nodes=[main_node], entry_point="main",
        max_loops=conf['runtime'].get('max_loops', 20))

    # create subtask_agent
    # subtask_agent 使用 subtask_max_loops 控制，每个子任务独立，不需要收尾余量
    subtask_tools = []
    for tool in tools:
        if tool['schema']['function']['name'] not in ['create_subtask', 'display_result', 'reflection']:
            subtask_tools.append(tool)
    subtask_node = BaseNode(
        name="main",
        llm=llm,
        tools=subtask_tools,
        message_key="messages",
    )
    subtask_agent = SubtaskAgent(
        name="subtask_agent", nodes=[subtask_node], entry_point="main",
        max_loops=conf['runtime'].get('subtask_max_loops', 5))

    # create reflection_agent (reuse subtask tools, exclude reflection)
    reflection_node = BaseNode(
        name="main",
        llm=llm,
        tools=subtask_tools,
        message_key="messages",
    )
    reflection_agent = ReflectionAgent(
        name="reflection_agent", nodes=[reflection_node], entry_point="main",
        max_loops=conf['runtime'].get('subtask_max_loops', 5))

    # AgentV3 只负责调度，循环控制由 MainAgent/SubtaskAgent/ReflectionAgent 自行处理
    agent = AgentV3(
        name="agent",
        main_agent=main_agent,
        subtask_agent=subtask_agent,
        reflection_agent=reflection_agent,
        entry_point="main_agent",
    )

    return {
        "conf": conf,
        "config_path": conf_path,
        "agent": agent,
        "sandbox_manager": sandbox_manager,
        "sandbox_conf": sandbox_conf,
        "system_prompt": system_prompt,
        "tools": tools,
        "llm": llm,
        "vlm": vlm,
        "audio_basellm": audio_basellm,
        "skill_assets": skill_assets,
    }

def get_user_input() -> tuple[str, Optional[list[str]]]:
    """获取用户输入：query 和可选的文件路径（支持多个文件）"""
    print("\n" + "="*60)
    print("Agent 交互式运行")
    print("="*60)
    
    # 获取 query
    print("\n请输入您的问题（query）：")
    print("（支持多行输入，输入完成后按 Enter（空行）结束）")
    query_lines = []
    while True:
        line = input()
        if not line.strip():
            if query_lines:
                # 如果已有输入，空行表示结束
                break
            # 如果还没有输入，继续等待
            continue
        query_lines.append(line)
    query = "\n".join(query_lines).strip()
    
    if not query:
        print("错误：问题不能为空")
        sys.exit(1)
    
    # 获取文件路径（可选，支持多个文件）
    print("\n请输入文件路径（可选，支持多个文件，每行一个，直接按 Enter 跳过）：")
    file_paths = []
    while True:
        line = input().strip()
        if not line:
            if file_paths:
                # 如果已有输入，空行表示结束
                break
            # 如果还没有输入，空行表示跳过
            return query, None
        if not os.path.exists(line):
            print(f"警告：文件不存在: {line}")
            response = input("是否继续？(y/n): ").strip().lower()
            if response != 'y':
                sys.exit(1)
        file_paths.append(line)
    
    return query, file_paths if file_paths else None

def run_single_case(
    case: Dict[str, Any],
    components: Dict[str, Any],
    conversation_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """与 run_agent 保持同步：复用其单轮执行逻辑。"""
    conf = components.get("conf", {}) or {}
    case = dict(case or {})
    if session_id is None:
        session_id = str(case.get("session_id") or uuid.uuid4())
    if conversation_id is None:
        conversation_id = str(case.get("conversation_id") or session_id)

    case.setdefault("session_id", str(session_id))
    case.setdefault("conversation_id", str(conversation_id))
    case.setdefault(
        "memory_user_id",
        resolve_memory_user_id(
            conf,
            explicit_user_id=case.get("user_id") or conf.get("user_id"),
        ),
    )

    return _run_agent.run_single_case(
        case=case,
        components=components,
        conversation_id=str(conversation_id),
    )


def _wait_for_summary_job_terminal(
    *,
    conversation_id: str,
    session_id: str,
    timeout_sec: float,
    poll_sec: float,
) -> Optional[Dict[str, Any]]:
    deadline = time.time() + max(float(timeout_sec), 0.5)
    poll = max(float(poll_sec), 0.1)
    last_job: Optional[Dict[str, Any]] = None
    while time.time() < deadline:
        job = get_job_by_key(
            job_type=JOB_TYPE_SUMMARY,
            conversation_id=str(conversation_id),
            session_id=str(session_id),
        )
        if job:
            last_job = job
            status = str(job.get("status") or "")
            if status in {"succeeded", "failed", "dead"}:
                return job
        time.sleep(poll)
    return last_job


def main():
    """主函数"""
    args = parse_args()
    # 检查配置文件
    config_path = "/home/wangbo4/Workspace/Prjs/xhx_agent_v3/conf_v3_zh.yaml"
    
    if not os.path.exists(config_path):
        logger.error(f"配置文件不存在: {config_path}")
        sys.exit(1)
    
    logger.info(f"使用配置文件: {config_path}")
    
    conversation_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    session_id = str(uuid.uuid4())
    try:
        # 初始化 agent 组件
        logger.info("正在初始化 Agent 组件...")
        components = build_agent_components(config_path, conversation_id)
        logger.info("Agent 组件初始化完成")
        config = components.get("conf", {}) or load_yaml_config(str(config_path))
        
        # 获取用户输入：提供 --query 时跳过交互式输入
        if args.query is not None:
            query = args.query.strip()
            if not query:
                logger.error("--query 不能为空")
                sys.exit(1)
            file_paths = args.file
        else:
            query, file_paths = get_user_input()
        
        # 创建结果目录（需要 LLM 来总结问题）
        logger.info("正在创建结果目录...")
        result_dir = create_result_directory(query, components["llm"])
        
        # 构建 case 字典
        case = {
            "query": query,
            "local_file_path": file_paths,
            "conversation_id": conversation_id,
            "session_id": session_id,
            "user_id": str(config.get("user_id") or "default_user"),
        }
        case["memory_user_id"] = resolve_memory_user_id(
            config,
            explicit_user_id=case.get("user_id"),
        )
        
        # 执行 agent
        logger.info("正在执行 Agent...")
        logger.info(f"问题: {query}")
        if file_paths:
            if isinstance(file_paths, list):
                logger.info(f"文件数量: {len(file_paths)}")
                for i, fp in enumerate(file_paths, 1):
                    logger.info(f"  文件 {i}: {fp}")
            else:
                logger.info(f"文件: {file_paths}")
        
        logger.debug(f"start run_single_case")
        result = run_single_case(
            case=case,
            components=components,
            conversation_id=conversation_id,
        )
        logger.debug(f"end run_single_case")

        # ppt_verification = verify_ppt_artifacts(
        #     result_dir=result_dir,
        #     case=case,
        #     components=components,
        # )
        # if ppt_verification is not None:
        #     result["ppt_verification"] = ppt_verification

        # 保存结果
        save_result(result_dir, case, result)

        jobs_cfg = get_jobs_config(config)
        jobs_enabled = bool(jobs_cfg.get("enabled", False))

        # jobs 模式下，默认等待当前 session 的 summary job 收敛，避免进程退出导致 md 未落盘
        if jobs_enabled:
            wait_timeout = float(jobs_cfg.get("wait_summary_timeout_sec", 30))
            wait_poll = float(jobs_cfg.get("wait_summary_poll_sec", 0.5))
            summary_job = _wait_for_summary_job_terminal(
                conversation_id=str(case.get("conversation_id") or session_id),
                session_id=str(case.get("session_id") or session_id),
                timeout_sec=wait_timeout,
                poll_sec=wait_poll,
            )
            if not summary_job:
                logger.warning(
                    "等待 summary job 超时（timeout=%ss），摘要可能稍后由后台worker完成。",
                    wait_timeout,
                )
            else:
                status = str(summary_job.get("status") or "")
                if status != "succeeded":
                    logger.warning(
                        "summary job 未成功完成: status=%s, last_error=%s",
                        status,
                        summary_job.get("last_error"),
                    )

        # 可选：执行完成后触发离线 summary（仅在 jobs 关闭时启用，避免重复写入）
        if args.summary_after_run and not jobs_enabled:
            try:
                from memory.summarize_sessions import summarize_user_sessions
                processed, skipped = summarize_user_sessions(
                    cfg=config,
                    user_id=str(case.get("memory_user_id") or config.get("user_id") or "default_user"),
                    since_date=None,
                    limit=None,
                )
                logger.info(f"summary-after-run 完成: processed={processed}, skipped={skipped}")
            except Exception as exc:
                logger.warning(f"summary-after-run 失败: {exc}")
        elif args.summary_after_run and jobs_enabled:
            logger.info("summary-after-run 已跳过：memory.jobs.enabled=true，避免与异步summary重复写入。")
        
        # 显示结果
        print("\n" + "="*60)
        print("执行完成")
        print("="*60)
        if result.get("success"):
            print(f"\n✅ 执行成功")
            print(f"\n响应:\n{result.get('response', '无响应')}")
        else:
            print(f"\n❌ 执行失败")
            print(f"错误: {result.get('error', '未知错误')}")
        print(f"\n结果目录: {result_dir}")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        logger.info("\n用户中断执行")
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行出错: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
