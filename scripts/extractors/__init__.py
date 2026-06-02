"""Chat extractors for chat_to_obsidian.

Each extractor produces markdown files in a staging directory that the
main script then enriches (frontmatter, tags, wikilinks) and copies into
the vault.

To add a new source:
1. Create extractors/<source>.py with an Extractor subclass
2. Register it in EXTRACTORS below
"""

from __future__ import annotations

from .base import ChatItem, Extractor
from .claude_code import ClaudeCodeExtractor
from .claude_web import ClaudeWebExtractor
from .copilot import CopilotExtractor
from .cursor import CursorExtractor

EXTRACTORS: dict[str, type[Extractor]] = {
    "claude-code": ClaudeCodeExtractor,
    "claude-web": ClaudeWebExtractor,
    "cursor": CursorExtractor,
    "copilot": CopilotExtractor,
}

__all__ = ["EXTRACTORS", "Extractor", "ChatItem"]
