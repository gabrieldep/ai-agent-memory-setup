"""Cursor extractor.

Cursor stores agent transcripts as JSONL files at:
    ~/.cursor/projects/<project-slug>/agent-transcripts/<uuid>/<uuid>.jsonl

Each line is one turn. Shape:
    {"role": "user"|"assistant", "message": {"content": [{"type": "text"|"tool_use"|..., ...}]}}
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .base import ChatItem, Extractor


def _block_to_markdown(block: dict) -> str:
    """Render a single content block to markdown."""
    btype = block.get("type")
    if btype == "text":
        return (block.get("text") or "").strip()
    if btype == "tool_use":
        name = block.get("name", "tool")
        params = block.get("input", {})
        params_pretty = json.dumps(params, indent=2, ensure_ascii=False)[:400]
        return f"<details>\n<summary>🔧 Tool: <code>{name}</code></summary>\n\n```json\n{params_pretty}\n```\n\n</details>"
    if btype == "tool_result":
        return ""  # too noisy for vault notes
    if btype == "thinking":
        return ""  # internal reasoning, skip
    return ""


def _turn_to_markdown(turn: dict) -> str:
    role = turn.get("role", "unknown")
    content = turn.get("message", {}).get("content", [])
    if isinstance(content, str):
        body = content.strip()
    elif isinstance(content, list):
        rendered = [_block_to_markdown(b) for b in content if isinstance(b, dict)]
        body = "\n\n".join(p for p in rendered if p)
    else:
        body = ""
    if not body:
        return ""
    heading = "## 👤 User" if role == "user" else "## 🤖 Assistant"
    return f"{heading}\n\n{body}"


def _derive_title(turns: list[dict], fallback: str) -> str:
    for turn in turns:
        if turn.get("role") != "user":
            continue
        content = turn.get("message", {}).get("content", [])
        if isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "text":
                    text = (b.get("text") or "").strip()
                    if "<user_query>" in text:
                        start = text.find("<user_query>") + len("<user_query>")
                        end = text.find("</user_query>", start)
                        if end != -1:
                            text = text[start:end].strip()
                    text = text.replace("\n", " ").strip()
                    if text:
                        return text[:80]
    return fallback


def _safe_filename(text: str) -> str:
    safe = "".join(c if c.isalnum() or c in " -_" else "" for c in text)
    return "-".join(safe.split())[:80] or "untitled"


class CursorExtractor(Extractor):
    name = "cursor"

    def __init__(self, import_dir: Path | None = None) -> None:
        super().__init__(import_dir)
        self.projects_root = import_dir or Path.home() / ".cursor" / "projects"

    def discover(self) -> list[ChatItem]:
        if not self.projects_root.exists():
            return []

        items: list[ChatItem] = []
        for jsonl in sorted(self.projects_root.glob("*/agent-transcripts/*/*.jsonl")):
            project_slug = jsonl.parents[2].name
            turns: list[dict] = []
            try:
                with jsonl.open(encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            turns.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            except OSError:
                continue

            if not turns:
                continue

            title = _derive_title(turns, fallback=jsonl.stem)
            rendered = [_turn_to_markdown(t) for t in turns]
            body = "\n\n---\n\n".join(p for p in rendered if p)
            mtime = datetime.fromtimestamp(jsonl.stat().st_mtime)
            date_prefix = mtime.strftime("%Y-%m-%d")
            filename_title = f"{date_prefix}-{project_slug}-{_safe_filename(title)}"
            markdown = (
                f"# {title}\n\n"
                f"*Project: `{project_slug}` · Transcript: `{jsonl.stem[:8]}` · "
                f"{mtime.strftime('%Y-%m-%d %H:%M')}*\n\n"
                f"{body}\n"
            )
            items.append(
                ChatItem(
                    title=filename_title,
                    markdown=markdown,
                    created=mtime,
                    source_path=jsonl,
                )
            )
        return items

    def cleanup(self, item: ChatItem) -> None:
        """Cursor manages its own transcript files; never delete them."""
        return
