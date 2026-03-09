#!/usr/bin/env python3
"""
install.py — Install one or all skills from this repo into ~/.claude/skills/

Usage:
    python install.py                  # Install all skills
    python install.py reflection       # Install a specific skill
    python install.py --list           # List available skills
    python install.py --dry-run        # Preview without copying
"""

import json
import re
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).parent.resolve()
SKILLS_DEST = Path.home() / ".claude" / "skills"


def parse_frontmatter(skill_md: Path) -> dict:
    """Extract name and description from SKILL.md YAML frontmatter."""
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    block = match.group(1)
    result = {}
    for line in block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip().strip(">").strip()
    return result


def discover_skills() -> list[Path]:
    """Find all skill directories (contain a SKILL.md)."""
    return sorted(
        p.parent for p in REPO_ROOT.rglob("SKILL.md")
        if p.parent != REPO_ROOT
    )


def install_skill(skill_dir: Path, dry_run: bool = False) -> bool:
    """Copy a skill directory to SKILLS_DEST. Returns True on success."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"  [SKIP] No SKILL.md in {skill_dir.name}")
        return False

    meta = parse_frontmatter(skill_md)
    name = meta.get("name") or skill_dir.name
    dest = SKILLS_DEST / name

    already_installed = dest.exists()
    status = "UPDATE" if already_installed else "INSTALL"

    print(f"  [{status}] {name}  ->  {dest}")

    if dry_run:
        print(f"           (dry-run, no files written)")
        return True

    if already_installed:
        # Remove only files managed by this skill (preserve user customizations elsewhere)
        shutil.rmtree(dest)

    shutil.copytree(skill_dir, dest)
    print(f"           Copied {sum(1 for _ in dest.rglob('*') if _.is_file())} files")
    return True


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]

    if "--list" in args:
        skills = discover_skills()
        if not skills:
            print("No skills found in this repo.")
            return
        print("Available skills:")
        for s in skills:
            meta = parse_frontmatter(s / "SKILL.md")
            name = meta.get("name") or s.name
            desc = meta.get("description", "")[:80]
            print(f"  {name:<20} {desc}")
        return

    skills = discover_skills()
    if not skills:
        print("No skills found in this repo.")
        sys.exit(1)

    # Filter to requested skill(s)
    if args:
        requested = set(args)
        selected = [s for s in skills if s.name in requested]
        missing = requested - {s.name for s in selected}
        if missing:
            print(f"Unknown skill(s): {', '.join(sorted(missing))}")
            print(f"Available: {', '.join(s.name for s in skills)}")
            sys.exit(1)
    else:
        selected = skills

    # Already in the right place — no copy needed
    if REPO_ROOT.resolve() == SKILLS_DEST.resolve():
        print(f"Repo is already at {SKILLS_DEST}")
        print("Skills are installed in-place. No copy needed.\n")
        for skill_dir in selected:
            meta = parse_frontmatter(skill_dir / "SKILL.md")
            name = meta.get("name") or skill_dir.name
            print(f"  [OK] {name}")
        return

    if dry_run:
        print("Dry run - no files will be written.\n")

    SKILLS_DEST.mkdir(parents=True, exist_ok=True)
    print(f"Installing to {SKILLS_DEST}\n")

    success = 0
    for skill_dir in selected:
        if install_skill(skill_dir, dry_run=dry_run):
            success += 1

    print(f"\nDone: {success}/{len(selected)} skill(s) installed.")


if __name__ == "__main__":
    main()
