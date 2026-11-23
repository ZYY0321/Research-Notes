import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.agentv3.core.batch_runner import (
    append_result,
    load_cases,
    load_existing_results,
    run_concurrent,
    save_results,
)
from agents.agentv3.core.postprocess import (
    _build_latest_response_meta,
    _generate_conversation_title,
    _generate_next_questions,
)
from agents.agentv3.core.runtime_components import build_agent_components
from agents.agentv3.core.session_runner import run_single_case


def setup_logger(log_dir: Path) -> logging.Logger:
    """设置日志记录器."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_filename = log_dir / f"agentv3_concurrent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


logger: logging.Logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="并发执行 AgentV3 测试集（支持断点续跑）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dataset",
        required=True,
        type=Path,
        help="测试集路径 (json/jsonl)",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default=None,
        help="数据集名称，用于日志目录命名 (如 gaia/drb/hle)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("conf_v3.yaml"),
        help="Agent 配置文件路径",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=max(os.cpu_count() or 4, 4),
        help="并发线程数",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="仅运行前 N 条数据，调试用",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="结果保存路径 (jsonl)",
    )
    parser.add_argument(
        "--file-dir",
        type=Path,
        default=None,
        help="数据集中相对文件路径的基础目录",
    )
    return parser.parse_args()


def main() -> None:
    global logger
    args = parse_args()

    dataset_name = args.dataset_name
    if not dataset_name:
        for part in args.dataset.parts:
            if part.upper() in ["GAIA", "DRB", "HLE"]:
                dataset_name = part.lower()
                break
        if not dataset_name:
            dataset_name = args.dataset.stem

    log_dir = Path("logs") / dataset_name
    logger = setup_logger(log_dir)

    logger.info("========== AgentV3 并发测试 ==========")
    logger.info("数据集: %s", args.dataset)
    logger.info("配置文件: %s", args.config)
    logger.info("并发数: %s", args.max_workers)
    logger.info("限制条数: %s", args.limit or "无限制")
    logger.info("输出路径: %s", args.output)

    try:
        result_path = run_concurrent(
            args.dataset,
            args.config,
            args.max_workers,
            args.limit,
            args.output,
            args.file_dir,
        )
        logger.info("测试完成，结果保存在: %s", result_path)
    except Exception as exc:
        logger.error("程序执行出错: %s", exc, exc_info=True)
        raise


__all__ = [
    "append_result",
    "build_agent_components",
    "load_cases",
    "load_existing_results",
    "logger",
    "main",
    "parse_args",
    "run_concurrent",
    "run_single_case",
    "save_results",
    "setup_logger",
    "_build_latest_response_meta",
    "_generate_conversation_title",
    "_generate_next_questions",
]


if __name__ == "__main__":
    main()
