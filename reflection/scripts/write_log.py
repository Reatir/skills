#!/usr/bin/env python3
"""
write_log.py — Append a reflection run entry to reflection-log.md.

Usage: python write_log.py <input.json> <log_path>
       python write_log.py - <log_path>   # read JSON from stdin

Input JSON schema:
{
  "date": "2026-03-08",          // optional
  "project": "my-project",       // from CWD basename
  "session": "one sentence",     // what the session was about
  "tool_calls": {                // all tool calls made, grouped by phase
    "phase_1_batch_1": ["Read ~/.claude/CLAUDE.md", ...],
    "phase_1_batch_2": ["Read project/CLAUDE.md", ...],
    "phase_3": ["Edit memory/MEMORY.md", ...]
  },
  "findings": [
    {
      "id": 1,
      "category": "Bloat",
      "file": "memory/MEMORY.md",
      "observed": "exact quote or description",
      "problem": "why this is an issue",
      "action": "APPLIED",       // or "SKIPPED"
      "reason": "",              // reason if SKIPPED
      "before": "exact text",    // verbatim, or "n/a"
      "after": "exact text"      // verbatim, DELETE, or "n/a"
    }
  ]
}
"""

import json
import sys
from pathlib import Path


PHASE_LABELS = {
    "phase_0": "Phase 0",
    "phase_1_batch_1": "Phase 1 Batch 1",
    "phase_1_batch_2": "Phase 1 Batch 2",
    "phase_3": "Phase 3",
    "phase_4": "Phase 4",
}


def format_entry(data: dict) -> str:
    date = data.get("date", "")
    project = data.get("project", "unknown")
    header = f"## {date} — {project}" if date else f"## {project}"

    session = data.get("session", "")
    findings = data.get("findings", [])
    applied = sum(1 for f in findings if f.get("action", "").upper() == "APPLIED")
    skipped = len(findings) - applied

    lines = [
        header,
        "",
        f"**Session:** {session}",
        f"**Stats:** {len(findings)} findings — {applied} applied, {skipped} skipped",
    ]

    # Tool calls block
    tool_calls = data.get("tool_calls", {})
    if tool_calls:
        lines.append("")
        lines.append("**Tool calls:**")
        total = 0
        for key, calls in tool_calls.items():
            if calls:
                label = PHASE_LABELS.get(key, key)
                lines.append(f"- {label}: {', '.join(calls)}")
                total += len(calls)
        lines.append(f"- Total: {total} tool calls")

    # Findings
    for f in findings:
        fid = f.get("id", "?")
        category = f.get("category", "Unknown")
        lines.append("")
        lines.append(f"### Finding {fid} — {category}")
        lines.append(f"- **File:** {f.get('file', 'n/a')}")
        lines.append(f"- **Observed:** {f.get('observed', 'n/a')}")
        lines.append(f"- **Problem:** {f.get('problem', 'n/a')}")
        action = f.get("action", "").upper()
        reason = f.get("reason", "")
        if action == "APPLIED":
            action_str = "APPLIED"
        elif reason:
            action_str = f"SKIPPED — {reason}"
        else:
            action_str = "SKIPPED"
        lines.append(f"- **Action:** {action_str}")
        lines.append(f"- **Before:** {f.get('before', 'n/a')}")
        lines.append(f"- **After:** {f.get('after', 'n/a')}")

    lines.extend(["", "---", ""])
    return "\n".join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: write_log.py <input.json|-> <log_path>", file=sys.stderr)
        sys.exit(1)

    input_arg = sys.argv[1]
    log_path = Path(sys.argv[2])

    if input_arg == "-":
        data = json.load(sys.stdin)
    else:
        data = json.loads(Path(input_arg).read_text(encoding="utf-8"))

    entry = format_entry(data)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(entry)

    print(f"Appended to {log_path}")


if __name__ == "__main__":
    main()
