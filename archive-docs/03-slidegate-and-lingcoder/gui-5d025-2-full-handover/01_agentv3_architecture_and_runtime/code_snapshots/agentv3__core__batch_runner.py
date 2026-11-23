import json
import logging
import os
import re
import unicodedata
import uuid
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

from agents.agentv3.core.runtime_components import build_agent_components
from agents.agentv3.core.session_runner import run_single_case
from src.conversation_state_v3 import rebuild_compiled_messages


logger = logging.getLogger(__name__)


def load_existing_results(output_path: Path) -> tuple[List[Dict[str, Any]], Set[Any], Set[str]]:
    existing_results: List[Dict[str, Any]] = []
    completed_ids: Set[Any] = set()
    completed_queries: Set[str] = set()

    def _normalize_query(query: Optional[str]) -> Optional[str]:
        if query is None:
            return None
        cleaned = str(query).strip().replace("\r", " ").replace("\n", " ")
        cleaned = cleaned.replace("\ufeff", "").replace("\u200b", "")
        cleaned = re.sub(r"\s+", " ", cleaned)
        return unicodedata.normalize("NFC", cleaned)

    if output_path.exists() and output_path.stat().st_size > 0:
        try:
            with output_path.open("r", encoding="utf-8") as file_obj:
                for line in file_obj:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    existing_results.append(data)
                    case_id = data.get("id")
                    if case_id is None:
                        # 兼容老结果：没有显式 id 时，用规范化 query 生成稳定 hash。
                        query_for_hash = _normalize_query(data.get("query"))
                        if query_for_hash:
                            import hashlib

                            case_id = hashlib.md5(query_for_hash.encode("utf-8")).hexdigest()[:16]
                    if case_id is not None:
                        completed_ids.add(case_id)
                    query = _normalize_query(data.get("query"))
                    if query:
                        completed_queries.add(query)
            logger.info(
                "发现已有结果文件，已完成 %s 条用例 (by id: %s; by query: %s)",
                len(existing_results),
                len(completed_ids),
                len(completed_queries),
            )
        except Exception as exc:
            logger.warning("读取已有结果文件失败: %s，将重新开始", exc)
            existing_results = []
            completed_ids = set()
            completed_queries = set()

    return existing_results, completed_ids, completed_queries


def load_cases(
    dataset_path: Path,
    limit: Optional[int] = None,
    skip_ids: Optional[Set[Any]] = None,
    skip_queries: Optional[Set[str]] = None,
    file_dir: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    skip_ids = skip_ids or set()
    skip_queries = skip_queries or set()
    total_loaded = 0
    skipped = 0

    def _normalize_query(query: Optional[str]) -> Optional[str]:
        if query is None:
            return None
        cleaned = str(query).strip().replace("\r", " ").replace("\n", " ")
        cleaned = cleaned.replace("\ufeff", "").replace("\u200b", "")
        cleaned = re.sub(r"\s+", " ", cleaned)
        return unicodedata.normalize("NFC", cleaned)

    def _sanitize_path(path: str) -> str:
        cleaned = path.strip().replace("\r", "").replace("\n", "")
        cleaned = cleaned.replace("\ufeff", "").replace("\u200b", "")
        return unicodedata.normalize("NFC", cleaned)

    def _normalize_file_paths(raw_paths: Optional[Any]) -> List[str]:
        if not raw_paths:
            return []
        if isinstance(raw_paths, list):
            items = raw_paths
        else:
            raw_str = str(raw_paths)
            if ";" in raw_str:
                items = [path.strip() for path in raw_str.split(";") if path.strip()]
            elif "\n" in raw_str:
                items = [path.strip() for path in raw_str.split("\n") if path.strip()]
            else:
                items = [raw_str.strip()]

        normalized = []
        for path in items:
            path = _sanitize_path(path)
            if path.startswith("./") and file_dir:
                normalized.append(os.path.join(str(file_dir), path[2:]))
            elif file_dir and not os.path.isabs(path):
                if os.path.normpath(path).startswith(os.path.normpath(str(file_dir))):
                    normalized.append(path)
                else:
                    normalized.append(os.path.join(str(file_dir), path))
            else:
                normalized.append(path)
        return normalized

    def parse_item(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        import hashlib

        query = data.get("prompt") or data.get("Question") or data.get("question")
        query = query or data.get("问题") or data.get("question_text")
        case_id = data.get("id") or data.get("task_id") or data.get("question_id")
        answer = data.get("Final answer") or data.get("answer") or data.get("参考答案")

        if query:
            query = _normalize_query(query)

        local_file_path = data.get("file_path") or data.get("input_path")
        if case_id is None and query:
            case_id = hashlib.md5(query.encode("utf-8")).hexdigest()[:16]

        if not local_file_path:
            # 兼容 file_path1/file_path2/... 这种展开列的老数据格式。
            file_path_keys = [key for key in data.keys() if isinstance(key, str) and key.startswith("file_path")]
            file_paths = [data.get(key) for key in file_path_keys if data.get(key)]
            if file_paths:
                local_file_path = file_paths
        local_file_path_list = _normalize_file_paths(local_file_path)

        if query:
            return {
                "id": case_id,
                "query": query,
                "answer": answer,
                "raw_data": data,
                "local_file_path": local_file_path_list,
            }
        return None

    def process_item(data: Dict[str, Any]) -> bool:
        nonlocal total_loaded, skipped

        case = parse_item(data)
        if not case:
            return True

        total_loaded += 1
        if case["id"] is not None and case["id"] in skip_ids:
            skipped += 1
            return not (limit and total_loaded >= limit)
        if case["id"] is None and case["query"] in skip_queries:
            skipped += 1
            return not (limit and total_loaded >= limit)

        cases.append(case)
        return not (limit and total_loaded >= limit)

    if dataset_path.suffix == ".jsonl":
        with dataset_path.open("r", encoding="utf-8") as file_obj:
            for line in file_obj:
                if not line.strip():
                    continue
                if not process_item(json.loads(line)):
                    break
    elif dataset_path.suffix == ".json":
        for item in json.loads(dataset_path.read_text(encoding="utf-8")):
            if not process_item(item):
                break
    elif dataset_path.suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(dataset_path)
        for item in df.where(pd.notna(df), None).to_dict(orient="records"):
            if not process_item(item):
                break
    else:
        raise ValueError(f"不支持的数据集格式: {dataset_path}")

    if skipped > 0:
        logger.info("跳过 %s 条已完成的用例", skipped)
    logger.info("待运行 %s 条用例", len(cases))
    return cases


def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file_obj:
        for item in results:
            file_obj.write(json.dumps(item, ensure_ascii=False) + "\n")
    logger.info("结果已写入: %s，共 %s 条", output_path, len(results))


def append_result(result: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as file_obj:
        file_obj.write(json.dumps(result, ensure_ascii=False) + "\n")


def _prepare_messages_export(result: Dict[str, Any]) -> Dict[str, Any]:
    state = result.get("state")
    if not isinstance(state, dict):
        return {}

    exported_state = deepcopy(state)
    target_state = exported_state.get("main_state") if isinstance(exported_state.get("main_state"), dict) else exported_state
    if isinstance(target_state, dict) and isinstance(target_state.get("message_records"), list):
        rebuild_compiled_messages(target_state)

    state_messages = []
    message_records = []
    prompt_template = None
    subtasks = []
    if isinstance(target_state, dict):
        state_messages = target_state.get("messages") or []
        message_records = target_state.get("message_records") or []
        session_meta = target_state.get("session_metadata") or {}
        prompt_template = session_meta.get("prompt_template") or session_meta.get("system_prompt_template")
        subtasks = target_state.get("subtasks") or []

    export = {
        "state": exported_state,
        "messages": state_messages,
        "message_records": message_records,
        "template": prompt_template,
    }
    if subtasks:
        export["subtasks"] = subtasks
    return export


def run_concurrent(
    dataset_path: Path,
    conf_path: Path,
    max_workers: int,
    limit: Optional[int],
    output: Path,
    file_dir: Optional[Path],
) -> Path:
    existing_results, completed_ids, completed_queries = load_existing_results(output)
    cases = load_cases(
        dataset_path,
        limit,
        skip_ids=completed_ids,
        skip_queries=completed_queries,
        file_dir=file_dir,
    )
    if not cases:
        logger.info("没有需要运行的用例")
        return output

    components = build_agent_components(conf_path)
    components["file_dir"] = str(file_dir) if file_dir else None
    for case in cases:
        case.setdefault("supports_ask_user", False)

    completed = 0
    total = len(cases)
    # 批跑共享同一份 components，单 case 的可变状态都在 run_single_case 内部生成。
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_case = {
            executor.submit(run_single_case, case, components, f"case_{case.get('id', uuid.uuid4())}"): case
            for case in cases
        }
        for future in as_completed(future_to_case):
            case = future_to_case[future]
            try:
                res = future.result()
            except Exception as exc:
                logger.error("用例 %s 处理失败: %s", case.get("id"), exc, exc_info=True)
                res = {"success": False, "error": str(exc)}

            completed += 1
            result = {
                "id": case.get("id"),
                "query": case.get("query"),
                "answer": case.get("answer"),
                **res,
            }
            result.update(_prepare_messages_export(result))
            append_result(result, output)
            logger.info("[%s/%s] 用例 %s 完成，success=%s", completed, total, case.get("id"), res.get("success"))

    logger.info("本次运行完成 %s 条，累计完成 %s 条", completed, len(existing_results) + completed)
    return output
