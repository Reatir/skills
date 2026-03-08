#!/usr/bin/env python3
"""
gather.py — Discover all files relevant to a reflection run.

Usage: python gather.py [cwd]
       If cwd is omitted, uses the current working directory.

Output: JSON manifest of all relevant files with paths, existence, and line counts.
"""

import json
import os
import sys
from pathlib import Path


def count_lines(path: Path) -> int:
    try:
        return sum(1 for _ in path.open(encoding="utf-8", errors="replace"))
    except Exception:
        return 0


def file_info(path: Path) -> dict:
    exists = path.exists() and path.is_file()
    return {
        "path": str(path),
        "exists": exists,
        "lines": count_lines(path) if exists else 0,
    }


def derive_slug(cwd: Path) -> str:
    s = str(cwd).replace("\\", "-").replace("/", "-").replace(":", "-")
    return s.lstrip("-")


def main():
    cwd = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()

    home = Path.home()
    claude_dir = home / ".claude"
    slug = derive_slug(cwd)
    memory_dir = claude_dir / "projects" / slug / "memory"

    # Global CLAUDE.md
    global_claude_md = file_info(claude_dir / "CLAUDE.md")

    # Project CLAUDE.md files (all **/CLAUDE.md under cwd)
    project_claude_mds = [
        file_info(p) for p in sorted(cwd.rglob("CLAUDE.md"))
    ]

    # Settings
    settings = [
        file_info(cwd / ".claude" / "settings.json"),
        file_info(cwd / ".claude" / "settings.local.json"),
    ]

    # Command files
    commands_dir = cwd / ".claude" / "commands"
    commands = []
    if commands_dir.exists():
        commands = [file_info(p) for p in sorted(commands_dir.glob("*.md"))]

    # Memory directory files
    memory_files = []
    if memory_dir.exists():
        memory_files = [
            file_info(p) for p in sorted(memory_dir.iterdir()) if p.is_file()
        ]

    result = {
        "cwd": str(cwd),
        "slug": slug,
        "memory_dir": str(memory_dir),
        "memory_dir_exists": memory_dir.exists(),
        "global_claude_md": global_claude_md,
        "project_claude_mds": project_claude_mds,
        "settings": settings,
        "commands": commands,
        "memory_files": memory_files,
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
