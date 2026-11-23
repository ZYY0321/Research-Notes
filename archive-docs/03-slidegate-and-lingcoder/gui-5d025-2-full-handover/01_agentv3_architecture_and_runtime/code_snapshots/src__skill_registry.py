import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def get_skill_registry_settings(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    cfg = config or {}
    runtime_cfg = cfg.get("runtime", {}) or {}
    registry_cfg = runtime_cfg.get("skill_registry", {}) or {}
    if not isinstance(registry_cfg, dict):
        registry_cfg = {}

    return {
        "enabled": bool(runtime_cfg.get("enable_skill_registry", False)),
        "skills_dir": str(registry_cfg.get("skills_dir") or "skills"),
        "skills_sandbox_dir": str(registry_cfg.get("skills_sandbox_dir") or "/mnt/data/skill").rstrip("/"),
        "allowlist": [
            str(item).strip()
            for item in (registry_cfg.get("allowlist") or [])
            if str(item).strip()
        ],
        "extra_dirs": [
            str(item).strip()
            for item in (registry_cfg.get("extra_dirs") or [])
            if str(item).strip()
        ],
    }


def _parse_frontmatter(markdown: str) -> Dict[str, Any]:
    if not isinstance(markdown, str) or not markdown.startswith("---"):
        return {}
    parts = markdown.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except Exception:
        return {}


def _normalize_tags(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize_skill_names(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_items = [str(item or "") for item in value]
    else:
        raw_items = re.split(r"[\n,]+", str(value or ""))

    names: List[str] = []
    seen: set[str] = set()
    for item in raw_items:
        text = str(item or "").strip().strip("'\"`")
        text = re.sub(r"^[-*]\s+", "", text).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        names.append(text)
    return names


def build_skill_registry_from_names(
    config: Optional[Dict[str, Any]],
    skill_names: Any,
) -> List[Dict[str, Any]]:
    requested_names = normalize_skill_names(skill_names)
    if not requested_names:
        return []

    registry_by_name = {
        str(item.get("name") or "").strip(): item
        for item in build_skill_registry(config, use_sandbox_location=True)
        if str(item.get("name") or "").strip()
    }
    return [registry_by_name[name] for name in requested_names if name in registry_by_name]


def build_skill_registry(
    config: Optional[Dict[str, Any]],
    *,
    use_sandbox_location: bool = True,
) -> List[Dict[str, Any]]:
    settings = get_skill_registry_settings(config)
    skills_dir = settings["skills_dir"]
    skills_sandbox_dir = settings["skills_sandbox_dir"]
    allowlist = {
        str(item).strip()
        for item in settings["allowlist"]
        if str(item).strip()
    }

    if not os.path.isabs(skills_dir):
        skills_dir = os.path.abspath(skills_dir)
    base = Path(skills_dir)
    if not base.exists() or not base.is_dir():
        return []

    items: List[Dict[str, Any]] = []
    for skill_path in sorted(base.rglob("SKILL.md")):
        try:
            markdown = skill_path.read_text(encoding="utf-8")
        except Exception:
            continue
        meta = _parse_frontmatter(markdown)
        name = str(meta.get("name") or skill_path.parent.name).strip()
        if allowlist and name not in allowlist:
            continue

        relative_dir = skill_path.parent.relative_to(base).as_posix()
        location = (
            f"{skills_sandbox_dir}/{relative_dir}/SKILL.md"
            if use_sandbox_location
            else str(skill_path.resolve())
        )
        items.append(
            {
                "name": name,
                "metadata": {
                    "description": str(meta.get("description") or "").strip(),
                    "source_type": str(
                        meta.get("source_type")
                        or ("sandbox_synced" if use_sandbox_location else "local_only")
                    ).strip(),
                    "source_label": str(
                        meta.get("source_label")
                        or ("sandbox" if use_sandbox_location else "local")
                    ).strip(),
                    "active": bool(meta.get("active", True)),
                    "tags": _normalize_tags(meta.get("tags")),
                },
                "location": location,
            }
        )

    return items
