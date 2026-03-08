#!/usr/bin/env python3
"""
session-learn: transcript extractor

Parses a Claude Code .jsonl session file and outputs a condensed JSON summary.
Called by the session-learn skill for transcript files > 300 lines.

Usage: python extract.py <path-to-session.jsonl>
Output: JSON to stdout (condensed, ~50 lines — not raw events)
Errors: JSON to stdout with "error" key, exit code 1
"""

import json
import sys
import os
from collections import defaultdict


def parse_transcript(path):
    events = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except (IOError, OSError) as e:
        return None, str(e)
    return events, None


def extract_metadata(events):
    meta = {"session_id": "", "cwd": "", "git_branch": "", "slug": "",
            "start_time": "", "end_time": "", "version": ""}
    for e in events:
        if e.get("type") == "user" and e.get("parentUuid") is None:
            meta["session_id"] = e.get("sessionId", "")
            meta["cwd"] = e.get("cwd", "")
            meta["git_branch"] = e.get("gitBranch", "")
            meta["version"] = e.get("version", "")
            meta["start_time"] = e.get("timestamp", "")
        if e.get("slug") and not meta["slug"]:
            meta["slug"] = e["slug"]

    timestamps = [e["timestamp"] for e in events if e.get("timestamp")]
    if timestamps:
        meta["end_time"] = timestamps[-1]
    return meta


def extract_tool_calls(events):
    """Return ordered list of tool calls with their results."""
    call_map = {}
    call_order = []

    for e in events:
        msg = e.get("message", {})
        content = msg.get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                tid = block.get("id", "")
                call_map[tid] = {
                    "id": tid,
                    "name": block.get("name", ""),
                    "input": block.get("input", {}),
                    "timestamp": e.get("timestamp", ""),
                    "error": False,
                    "result_preview": "",
                }
                call_order.append(tid)
            elif block.get("type") == "tool_result":
                tid = block.get("tool_use_id", "")
                if tid in call_map:
                    call_map[tid]["error"] = bool(block.get("is_error", False))
                    raw = block.get("content", "")
                    if isinstance(raw, list):
                        for c in raw:
                            if isinstance(c, dict) and c.get("type") == "text":
                                call_map[tid]["result_preview"] = c.get("text", "")[:150]
                                break
                    elif isinstance(raw, str):
                        call_map[tid]["result_preview"] = raw[:150]

    return [call_map[tid] for tid in call_order if tid in call_map]


def detect_hook_violations(events):
    """Find hook blocks (progress events from hooks that fired)."""
    violations = []
    for e in events:
        data = e.get("data", {})
        if isinstance(data, dict) and data.get("type") == "hook_progress":
            violations.append({
                "hook": data.get("hookName", "unknown"),
                "event": data.get("hookEvent", ""),
                "timestamp": e.get("timestamp", ""),
            })
    # Deduplicate by hook name, keep count
    counts = defaultdict(int)
    for v in violations:
        counts[v["hook"]] += 1
    return [{"hook": h, "count": c} for h, c in counts.items()]


def detect_retry_storms(tool_calls):
    """Same tool + similar path within 5 consecutive turns after an error."""
    retries = []
    seen = set()
    for i, call in enumerate(tool_calls):
        if call.get("error") and i not in seen:
            window = tool_calls[i + 1: i + 6]
            same = [c for c in window if c["name"] == call["name"]]
            if same:
                key = f"{call['name']}:{i}"
                if key not in seen:
                    seen.add(key)
                    # Extract a simple path/pattern identifier
                    inp = call.get("input", {})
                    context = inp.get("file_path") or inp.get("path") or inp.get("pattern") or str(inp)[:80]
                    retries.append({
                        "tool": call["name"],
                        "context": context,
                        "retry_count": len(same),
                        "timestamp": call.get("timestamp", ""),
                    })
    return retries


def detect_error_chains(tool_calls):
    """Error followed by success within 4 turns — debug insight candidates."""
    chains = []
    for i, call in enumerate(tool_calls):
        if call.get("error"):
            window = tool_calls[i + 1: i + 5]
            for j, c in enumerate(window):
                if not c.get("error"):
                    chains.append({
                        "failed_tool": call["name"],
                        "failed_input": str(call.get("input", ""))[:80],
                        "success_tool": c["name"],
                        "success_input": str(c.get("input", ""))[:80],
                        "attempts_before_success": j + 1,
                    })
                    break
    return chains


def detect_inefficiencies(tool_calls):
    """Reads without offset/limit — potential large-file inefficiencies."""
    results = []
    for call in tool_calls:
        if call["name"] == "Read":
            inp = call.get("input", {})
            if not inp.get("offset") and not inp.get("limit"):
                path = inp.get("file_path", "")
                results.append({
                    "type": "read_without_offset",
                    "file": path,
                    "timestamp": call.get("timestamp", ""),
                })
    return results


def tool_summary(tool_calls):
    counts = defaultdict(int)
    errors = defaultdict(int)
    for c in tool_calls:
        counts[c["name"]] += 1
        if c.get("error"):
            errors[c["name"]] += 1
    return {
        "counts": dict(counts),
        "errors": dict(errors),
        "total": len(tool_calls),
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: extract.py <path.jsonl>"}))
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(json.dumps({"error": f"File not found: {path}"}))
        sys.exit(1)

    events, err = parse_transcript(path)
    if err:
        print(json.dumps({"error": err}))
        sys.exit(1)

    tool_calls = extract_tool_calls(events)

    result = {
        "metadata": extract_metadata(events),
        "tool_summary": tool_summary(tool_calls),
        "hook_violations": detect_hook_violations(events),
        "retry_storms": detect_retry_storms(tool_calls),
        "error_chains": detect_error_chains(tool_calls),
        "inefficiencies": detect_inefficiencies(tool_calls),
        "total_events": len(events),
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
