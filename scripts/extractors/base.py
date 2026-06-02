"""Base protocol for chat extractors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ChatItem:
    """A single chat ready to be written to the vault as markdown."""

    title: str
    markdown: str
    created: datetime
    source_path: Path | None = None


class Extractor:
    """Base class for chat extractors.

    Subclasses must set `name` (used for vault subfolder `chats/<name>/`)
    and implement `discover()`. The default `extract()` runs `discover()`
    and applies the per-source `to_markdown()` if subclasses choose to
    override the two-step flow.
    """

    name: str = "generic"

    def __init__(self, import_dir: Path | None = None) -> None:
        self.import_dir = import_dir

    def discover(self) -> list[ChatItem]:
        """Return all chats found by this extractor."""
        raise NotImplementedError

    def cleanup(self, item: ChatItem) -> None:
        """Optionally delete the original after a successful import.

        Called by chat_to_obsidian when --move is passed. Default: no-op.
        Subclasses that own a stable source file should override.
        """
        if item.source_path and item.source_path.exists():
            item.source_path.unlink()
