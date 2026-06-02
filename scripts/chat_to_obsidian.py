#!/usr/bin/env python3
"""
Pipeline: AI assistant chats → Obsidian vault.

Generalized successor to claude_to_obsidian.py. Supports multiple sources via
per-source extractors in scripts/extractors/.

Usage:
    python3 chat_to_obsidian.py \\
        --source cursor \\
        --vault-dir ~/vault

    python3 chat_to_obsidian.py --source claude-code --vault-dir ~/vault --move
    python3 chat_to_obsidian.py --source copilot     --vault-dir ~/vault --import-dir ~/copilot-exports
    python3 chat_to_obsidian.py --source claude-web  --vault-dir ~/vault --import-dir ~/claude-exports/web

Sources:
    claude-code  Claude Code (wraps `claude-extract`)
    claude-web   Claude.ai browser-exported markdown
    cursor       Cursor agent transcripts (~/.cursor/projects/.../*.jsonl)
    copilot      GitHub Copilot exported chats (VS Code "Chat: Export")

The KEYWORD_TAG_MAP below is the same one from claude_to_obsidian.py — adapt
it to your stack and projects.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extractors import EXTRACTORS, ChatItem  # noqa: E402

# ============================================================================
# CONFIGURATION — adapt KEYWORD_TAG_MAP to your stack and projects
# ============================================================================

KEYWORD_TAG_MAP = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "react": "react",
    "vue": "vue",
    "angular": "angular",
    "fastapi": "fastapi",
    "django": "django",
    "flask": "flask",
    "nodejs": "nodejs",
    "rust": "rust",
    "go ": "golang",
    "golang": "golang",
    "sql": "sql",
    "machine learning": "machine-learning",
    "deep learning": "deep-learning",
    "neural network": "neural-network",
    "transformer": "transformers",
    "llm": "llm",
    "gpt": "llm",
    "claude": "llm",
    "copilot": "llm",
    "cursor": "llm",
    "langchain": "langchain",
    "embedding": "embeddings",
    "fine-tun": "fine-tuning",
    "rag": "rag",
    "prompt": "prompt-engineering",
    "computer vision": "computer-vision",
    "nlp": "nlp",
    "pytorch": "pytorch",
    "tensorflow": "tensorflow",
    "hugging face": "huggingface",
    "huggingface": "huggingface",
    "automation": "automation",
    "selenium": "automation",
    "scrapy": "web-scraping",
    "scraping": "web-scraping",
    "cron": "automation",
    "pipeline": "pipeline",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "aws": "aws",
    "gcp": "gcp",
    "azure": "azure",
    "linux": "linux",
    "git": "git",
    "api": "api",
    "rest": "api",
    "graphql": "graphql",
    "supabase": "supabase",
    "firebase": "firebase",
    "postgres": "database",
    "mongodb": "database",
    "redis": "redis",
    "database": "database",
    "obsidian": "obsidian",
    "vault": "obsidian",
    "zettelkasten": "pkm",
    "graphify": "graphify",
    "debug": "debugging",
    "error": "debugging",
    "refactor": "refactoring",
    "test": "testing",
    "deploy": "deploy",
}

SHORT_KEYWORDS = {"sql", "llm", "gpt", "rag", "nlp", "git", "api", "rest", "aws", "gcp"}

# ============================================================================
# Post-processing — frontmatter, tags, wikilinks (lifted from the original
# claude_to_obsidian.py, made source-agnostic)
# ============================================================================


def extract_tags(content: str) -> list[str]:
    content_lower = content.lower()
    found: set[str] = set()

    for keyword, tag in KEYWORD_TAG_MAP.items():
        if keyword in SHORT_KEYWORDS:
            if re.search(rf"\b{re.escape(keyword)}\b", content_lower):
                found.add(tag)
        else:
            if keyword in content_lower:
                found.add(tag)

    return sorted(found)


def strip_existing_frontmatter(content: str) -> tuple[dict[str, str], str]:
    existing: dict[str, str] = {}
    body = content

    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end != -1:
            fm_block = content[4:end]
            body = content[end + 5:]
            for line in fm_block.split("\n"):
                if ":" in line and not line.startswith("  ") and not line.startswith("-"):
                    key, _, val = line.partition(":")
                    existing[key.strip()] = val.strip()

    return existing, body


def build_frontmatter(
    title: str,
    tags: list[str],
    source: str,
    created: str,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    all_tags = ["chat-import"] + [t for t in tags if t != "chat-import"]
    tags_yaml = "\n".join(f"  - {t}" for t in all_tags)

    return f"""---
title: "{title}"
tags:
{tags_yaml}
source: {source}
created: {created}
processed: {now}
status: imported
type: chat
---

"""


def collect_vault_notes(vault_dir: Path) -> list[str]:
    notes: list[str] = []
    for md in vault_dir.rglob("*.md"):
        rel = md.relative_to(vault_dir)
        if any(p.startswith(".") for p in rel.parts):
            continue
        if rel.parts and rel.parts[0] == "chats":
            # don't link to imported chats — too noisy
            continue
        name = md.stem
        if len(name) >= 4:
            notes.append(name)

    notes.sort(key=lambda n: -len(n))
    return notes


def insert_wikilinks(body: str, vault_notes: list[str]) -> str:
    parts = re.split(r"(```[\s\S]*?```|`[^`\n]+`)", body)
    linked: set[str] = set()

    for i, part in enumerate(parts):
        if part.startswith("`"):
            continue

        for note in vault_notes:
            if note in linked:
                continue
            pattern = rf"(?<!\[\[)\b({re.escape(note)})\b(?!\]\])"
            match = re.search(pattern, part, re.IGNORECASE)
            if match:
                parts[i] = (
                    part[: match.start()]
                    + f"[[{note}]]"
                    + part[match.end():]
                )
                part = parts[i]
                linked.add(note)

    return "".join(parts)


def process_item(
    item: ChatItem,
    source: str,
    vault_dir: Path,
    vault_notes: list[str],
    no_wikilinks: bool,
    dry_run: bool,
) -> dict:
    _, body = strip_existing_frontmatter(item.markdown)

    tags = extract_tags(item.markdown)

    if not no_wikilinks:
        body = insert_wikilinks(body, vault_notes)

    created_str = item.created.strftime("%Y-%m-%d")
    frontmatter = build_frontmatter(item.title, tags, source, created_str)
    output = frontmatter + body

    dest_dir = vault_dir / "chats" / source
    dest = dest_dir / f"{item.title}.md"

    result = {
        "title": item.title,
        "source": source,
        "tags": tags,
        "dest": str(dest),
        "source_path": str(item.source_path) if item.source_path else None,
    }

    if dry_run:
        return result

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest.write_text(output, encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Import AI assistant chats into an Obsidian vault"
    )
    parser.add_argument(
        "--source", required=True, choices=sorted(EXTRACTORS),
        help="Which AI assistant to import from"
    )
    parser.add_argument(
        "--vault-dir", required=True, type=Path,
        help="Path to the Obsidian vault"
    )
    parser.add_argument(
        "--import-dir", type=Path, default=None,
        help="Override staging directory (defaults are extractor-specific)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would happen without modifying anything"
    )
    parser.add_argument(
        "--move", action="store_true",
        help="Delete originals after import (extractors that own files only)"
    )
    parser.add_argument(
        "--no-wikilinks", action="store_true",
        help="Disable wikilink insertion"
    )

    args = parser.parse_args()

    if not args.vault_dir.exists():
        print(f"ERROR: Vault not found: {args.vault_dir}", file=sys.stderr)
        sys.exit(1)

    extractor_cls = EXTRACTORS[args.source]
    extractor = extractor_cls(import_dir=args.import_dir)

    print(f"Source: {args.source}")
    print(f"Vault:  {args.vault_dir}")
    print()

    items = extractor.discover()
    print(f"Discovered {len(items)} chats")
    if not items:
        return

    vault_notes = collect_vault_notes(args.vault_dir)
    print(f"Vault notes available for wikilinks: {len(vault_notes)}")

    if args.dry_run:
        print("=== DRY RUN — nothing will be written ===\n")

    results = []
    for item in items:
        result = process_item(
            item, args.source, args.vault_dir, vault_notes,
            args.no_wikilinks, args.dry_run,
        )
        results.append(result)

        tags_str = ", ".join(result["tags"]) if result["tags"] else "(no tags)"
        prefix = "[DRY] " if args.dry_run else ""
        print(f'{prefix}✓ {result["title"]}')
        print(f'  Tags: {tags_str}')
        print(f'  → {result["dest"]}')

        if args.move and not args.dry_run:
            try:
                extractor.cleanup(item)
            except OSError as exc:
                print(f'  WARN: cleanup failed: {exc}', file=sys.stderr)

    all_tags: set[str] = set()
    for r in results:
        all_tags.update(r["tags"])

    print(f"\n{'═' * 50}")
    print("SUMMARY")
    print(f"{'═' * 50}")
    print(f"Source:        {args.source}")
    print(f"Processed:     {len(results)}")
    print(f"Unique tags:   {len(all_tags)}")
    if all_tags:
        print(f"  {', '.join(sorted(all_tags))}")
    if args.dry_run:
        print("\n⚠ Dry run — no files were modified.")


if __name__ == "__main__":
    main()
