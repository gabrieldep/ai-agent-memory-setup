"""Claude.ai (web) extractor.

The browser extension 'Export Claude Chat to Markdown' drops .md files
into a staging directory. This extractor just reads them.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .base import ChatItem, Extractor


class ClaudeWebExtractor(Extractor):
    name = "claude-web"

    def discover(self) -> list[ChatItem]:
        staging = self.import_dir or Path.home() / "claude-exports" / "web"
        if not staging.exists():
            return []

        items: list[ChatItem] = []
        for md in sorted(staging.rglob("*.md")):
            try:
                content = md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            items.append(
                ChatItem(
                    title=md.stem,
                    markdown=content,
                    created=datetime.fromtimestamp(md.stat().st_mtime),
                    source_path=md,
                )
            )
        return items
