---
name: session-learn
description: Extract learnings from a work session and write them to memory files. Use whenever the user says "session-learn", "learn from this session", "capture what we learned", "update my memory", "qu'est-ce qu'on a appris", "remember this for next time", or after completing a story, debug session, code review, or any significant task. Trigger even on vague phrasing like "let's capture that" or "save what we learned". Also trigger for "session-learn review" to prune stale memory.
---

# session-learn

Turns session experience into durable, structured memory. Works on any project — no framework required.

## Two commands

- `session-learn` — extract learnings from a session, write to memory files
- `session-learn review` — audit and prune stale memory entries

---

## Command: `session-learn`

### Step 1 — ORIENT

Ask two questions unless context makes the answers obvious:

**Q1 — Outcome**: Did the session achieve its goal?
- `yes` → extract patterns from what worked + failed approaches from abandoned branches
- `no` → extract blockers, what to try next time
- `partial` → both

**Q2 — Type**: `debug` | `feature` | `refactor` | `exploration` | `review`
Drives which extraction heuristics apply in Step 2.

If a `.jsonl` path was provided, infer type from session metadata (slug, gitBranch, tool call patterns).

---

### Step 2 — EXTRACT

#### Find memory files

Search in order, use first match:
1. `~/.claude/projects/<project>/memory/` — derive `<project>` from cwd: replace `\`, `/`, `:` with `-`, strip leading `-`
2. `.claude/memory/` in current working directory
3. Neither found → **first-run mode** (see end of file)

Expected files: `MEMORY.md`, `patterns.md`, `failed.md`, `debugging.md`, `index.json`, `session-learn-log.md`

#### Select input mode

| Condition | Mode |
|---|---|
| Path provided: `session-learn <path.jsonl>` | Transcript |
| No file provided | Conversational |
| session-audit report path given | Import |

**Transcript mode**: Always analyze the **previous** session file, never the current one (the current .jsonl is incomplete and contains session-learn's own calls). For files > 300 lines, detect Python first: `python3 --version 2>/dev/null || python --version 2>/dev/null`. If available, run `scripts/extract.py <path>` and work from its JSON output. If unavailable, read the first 150 and last 150 lines directly.

**Conversational mode** — ask 3-4 focused questions based on session type:
- *debug*: "What was the symptom? What was the real cause? What did you try first that failed?"
- *feature*: "What approach worked well? Any tool sequences you'd reuse? Anything abandoned?"
- *refactor / exploration*: "What did you learn? Any dead ends worth noting?"
- *review*: "Any patterns or anti-patterns to remember?"

**Import mode**: Read the session-audit report. Treat each finding as a candidate learning.

#### Detect patterns from transcript (automated)

When a transcript is available, scan for these signals:
- **Hook violations**: `"data":{"type":"hook_progress"}` entries with non-zero exit → rule violated, count occurrences per hook name
- **Retry storms**: same tool name + similar path/pattern within 5 consecutive turns → failed approach candidate
- **Error chains**: tool_result error → subsequent retry → success → debug insight candidate
- **Read without offset**: `Read` call with no `offset`/`limit` on a file > 200 lines → inefficiency
- **Sequential independent calls**: 3+ Glob/Grep/Read calls that could have been parallel → pattern candidate

#### Classify — 4 categories

| Category | Required fields |
|---|---|
| ✅ **Pattern** | what to do + when to use it + why better than alternative |
| ❌ **Failed** | what was tried + what happened + why it failed + what to do instead (all 4 required) |
| 🔧 **Debug** | symptom + root cause + fix (all 3 required) |
| ⚠️ **Rule** | must be expressible as "always X" or "never Y" with no nuance |

If a Failed entry is missing "what to do instead" → defer or reclassify as Debug.

#### Filter — 4 binary tests

Read `references/filter-criteria.md` for concrete pass/fail examples.
A learning must pass **all 4** to be captured:

1. **Repeatable** — could this happen in another session?
2. **Actionable** — does this change behavior next time?
3. **Non-trivial** — would Claude get it wrong without the hint?
4. **Durable** — true beyond today's specific context?

Fail any test → skip. Log the skip with which test failed.

#### Scope decision

- References a project-specific path, script, or convention → **project** (`./memory/`)
- Applies to any Claude Code project → **global** (`~/.claude/memory/`)
- Uncertain → **project** (safer default)
- CLAUDE.md: **never auto-write**. If a rule is critical enough: output the exact text, say "Add this manually to CLAUDE.md."

#### Diff against index.json

Load `index.json`. For each candidate:
- Title similarity > 80% to existing entry → **DUPLICATE** → bump `count` + `last_reinforced`, skip add, auto-promote confidence (2-3 → `confirmed`, 4+ → `stable`)
- Logical contradiction with existing Rule entry → **CONFLICT** → flag for Step 3 arbitration
- Otherwise → **NEW**, assign next sequential ID (`p`=pattern, `f`=failed, `d`=debug, `r`=rule, zero-padded 3 digits)

#### MEMORY.md size guard

Count lines. If > 175: identify sections with > 5 detail lines and propose moving them to a topic file, keeping a 1-line pointer in MEMORY.md.

---

### Step 3 — REVIEW

Present in this exact structure — no more:

```
--- TOP PRIORITY (max 3) -------------------------------------------
[1] ✅ Pattern — "Short title"
    Scope: global | New | ID: p042
    ---
    [exact text that will be written to the file]
    ---
    [a]ccept  [s]kip  [e]dit

[2] ...

--- BATCH (N items) ------------------------------------------------
• Pattern: title  • Failed: title  • Debug: title  • Rule: title

[A]ccept all  [S]kip all  [R]eview individually

--- FILTERED (N items) ---------------------------------------------
• "..." — Fail: Repeatable (one-off decision)
• "..." — Duplicate of p017, count bumped to 3

--- CONFLICTS (N items) --------------------------------------------
⚠️  Rule r005 "always X" vs new: "Y also works in context Z"
    [keep r005]  [replace]  [add exception note]  [ignore]
```

Top Priority = items that most change future behavior. Max 3.
Batch = everything else, titled only. Show full text only if user asks.

---

### Step 4 — APPLY

For each file to be modified:

```bash
# Dated backup — keep last 5, delete older
cp MEMORY.md "MEMORY.md.bak-$(date +%Y%m%d-%H%M%S)"
ls MEMORY.md.bak-* 2>/dev/null | sort | head -n -5 | xargs rm -f 2>/dev/null
```

Write entries to the appropriate `.md` file with inline metadata comment (see `references/schema.md` for exact format).

Update `index.json` with all new/modified entries.

Append to `session-learn-log.md`:
```
## YYYY-MM-DD HH:MM — <session-slug or "conversational">
Type: feature | Outcome: partial
Accepted: 5 (pattern:2 failed:1 debug:1 rule:1) | Skipped: 2 | Filtered: 3 | Conflicts: 1
Modified: patterns.md (+2), failed.md (+1), index.json
---
```

---

## Command: `session-learn review`

Triggered by `session-learn review` or "review my memory".

Read `index.json`. Present:

1. **Stale tentative** — `confidence:tentative` + `added` > 30 days + never reinforced → confirm / delete
2. **Orphaned refs** — failed entries with `fixes:` pointing to a deleted ID → fix or delete
3. **Internal contradictions** — two Rule entries that conflict → arbitrate
4. **MEMORY.md size** — current line count, action if > 175
5. **Consolidated proposal** → apply with confirmation

---

## First-run mode

Triggered when no `memory/` directory or `index.json` found.

1. Scan for existing memory files in both candidate locations
2. If found: build `index.json` from existing content — create entries with `confidence:unknown`, infer type from filename/content
3. Create any missing files from minimal templates (see `references/schema.md`)
4. Confirm structure with user, then run normal session-learn

If no existing files: create the full structure from scratch with empty files.

---

## Reference files

- `references/schema.md` — index.json spec, entry format per category, inline comment format, log format
- `references/filter-criteria.md` — 4 filter tests with concrete pass/fail examples
- `scripts/extract.py` — transcript parser, optional, large files only
