"""GitHub Copilot extractor.

Copilot doesn't expose a stable filesystem location for chat history, so the
recommended flow is:

    1. In VS Code: "Chat: Export" (Cmd/Ctrl+Shift+P → "Chat: Export")
    2. Save the resulting .json file into ~/copilot-exports/
    3. Run chat_to_obsidian --source copilot

This extractor parses those exported .json files. It accepts a few common
shapes that VS Code has shipped over the past releases.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .base import ChatItem, Extractor


def _safe_filename(text: str) -> str:
    safe = "".join(c if c.isalnum() or c in " -_" else "" for c in text)
    return "-".join(safe.split())[:80] or "untitled"


def _extract_text(value) -> str:
    """Pull plain text from any of VS Code's chat export shapes."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            parts.append(_extract_text(item))
        return "\n\n".join(p for p in parts if p)
    if isinstance(value, dict):
        for key in ("text", "value", "content", "markdown", "message"):
            if key in value:
                return _extract_text(value[key])
    return ""


def _render_turn(turn: dict) -> str:
    role = (
        turn.get("role")
        or turn.get("speaker")
        or ("user" if "request" in turn else "assistant")
    )
    body_source = turn.get("response") or turn.get("request") or turn.get("content") or turn
    body = _extract_text(body_source).strip()
    if not body:
        return ""
    heading = "## 👤 User" if role.lower().startswith("user") else "## 🤖 Copilot"
    return f"{heading}\n\n{body}"


class CopilotExtractor(Extractor):
    name = "copilot"

    def discover(self) -> list[ChatItem]:
        staging = self.import_dir or Path.home() / "copilot-exports"
        if not staging.exists():
            return []

        items: list[ChatItem] = []
        for jf in sorted(staging.rglob("*.json")):
            try:
                data = json.loads(jf.read_text(encoding="utf-8", errors="replace"))
            except (OSError, json.JSONDecodeError):
                continue

            requests = (
                data.get("requests")
                or data.get("turns")
                or data.get("messages")
                or data.get("history")
                or (data if isinstance(data, list) else [])
            )
            if not isinstance(requests, list) or not requests:
                continue

            rendered = [_render_turn(t) for t in requests if isinstance(t, dict)]
            body = "\n\n---\n\n".join(p for p in rendered if p)
            if not body:
                continue

            mtime = datetime.fromtimestamp(jf.stat().st_mtime)
            title_seed = (
                _extract_text(requests[0]).strip().splitlines()[0]
                if requests
                else jf.stem
            )
            title = title_seed[:80] or jf.stem
            date_prefix = mtime.strftime("%Y-%m-%d")
            filename = f"{date_prefix}-copilot-{_safe_filename(title)}"
            markdown = (
                f"# {title}\n\n"
                f"*Source: GitHub Copilot · "
                f"{mtime.strftime('%Y-%m-%d %H:%M')}*\n\n"
                f"{body}\n"
            )
            items.append(
                ChatItem(
                    title=filename,
                    markdown=markdown,
                    created=mtime,
                    source_path=jf,
                )
            )
        return items
