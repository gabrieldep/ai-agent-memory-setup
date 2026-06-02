"""Claude Code extractor.

Wraps the `claude-conversation-extractor` CLI when available, otherwise
reads markdown files already dropped into the staging directory.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from .base import ChatItem, Extractor


class ClaudeCodeExtractor(Extractor):
    name = "claude-code"

    def __init__(self, import_dir: Path | None = None, run_extract: bool = True) -> None:
        super().__init__(import_dir)
        self.run_extract = run_extract

    def discover(self) -> list[ChatItem]:
        staging = self.import_dir or Path.home() / "claude-exports" / "code"
        staging.mkdir(parents=True, exist_ok=True)

        if self.run_extract and shutil.which("claude-extract"):
            try:
                subprocess.run(
                    ["claude-extract", "--all", "--output", str(staging)],
                    check=False,
                    capture_output=True,
                    timeout=300,
                )
            except subprocess.TimeoutExpired:
                pass

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
