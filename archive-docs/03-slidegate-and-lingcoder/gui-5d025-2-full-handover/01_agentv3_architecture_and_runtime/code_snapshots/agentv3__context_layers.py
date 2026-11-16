import os
import re
from copy import deepcopy
from typing import Any, Dict, List, Optional


def normalize_active_editor_file(raw: Any, *, max_chars: int = 6000) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    path = str(raw.get("path") or "").strip()
    if not path:
        return None

    content = raw.get("content")
    summary = None
    if isinstance(content, str) and len(content) > max_chars:
        head = max_chars // 2
        tail = max_chars - head
        content = f"{content[:head]}\n... [truncated] ...\n{content[-tail:]}"
        summary = f"content truncated to {max_chars} chars"

    normalized = {
        "path": path,
        "language": str(raw.get("language") or _guess_language_from_path(path) or "").strip() or None,
        "content": content if isinstance(content, str) else None,
        "selection": raw.get("selection") if isinstance(raw.get("selection"), (dict, list, str)) else None,
        "version": raw.get("version"),
        "dirty": bool(raw.get("dirty", False)),
    }
    if summary:
        normalized["summary"] = summary
    return normalized


def _guess_language_from_path(path: str) -> Optional[str]:
    suffix = os.path.splitext(str(path))[1].lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".md": "markdown",
        ".json": "json",
        ".html": "html",
        ".css": "css",
        ".yaml": "yaml",
        ".yml": "yaml",
    }
    return mapping.get(suffix)


def extract_knowledge_base_refs(
    query: Optional[str],
    explicit_refs: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    seen = set()
    pattern = re.compile(r"@知识库(?P<path>/[^\s,，；;]+)")
    for match in pattern.finditer(str(query or "")):
        path = match.group("path").strip()
        if not path or path in seen:
            continue
        seen.add(path)
        refs.append({"path": path, "type": "file" if os.path.splitext(path)[1] else "dir"})

    for item in explicit_refs or []:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        if not path or path in seen:
            continue
        seen.add(path)
        refs.append(
            {
                "path": path,
                "type": str(item.get("type") or ("file" if os.path.splitext(path)[1] else "dir")).strip(),
            }
        )
    return [deepcopy(item) for item in refs]
