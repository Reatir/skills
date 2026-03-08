---
name: reflection
description: >
  Reviews the current conversation session to surface improvements across three areas:
  (1) Claude config files — CLAUDE.md, .claude/settings.json, .claude/commands/;
  (2) project auto-memory — MEMORY.md and linked topic files;
  (3) new slash commands worth creating.
  Use this skill at the end of a session, after resolving a tricky bug, completing a story,
  or any time you want to lock in learnings before context is lost. Invoke it with
  /reflection or "run reflection" or "let's do a reflection". Always use this skill rather
  than trying to do the analysis ad hoc — it ensures nothing gets missed.
---

# Reflection Skill

The goal is to turn ephemeral session knowledge into durable improvements. Patterns were
confirmed, mistakes were corrected, preferences were revealed — capture what's worth keeping
before the context disappears.

## Phase 0 — Zero-cost analysis (no tool calls)

Everything here runs on data already in context. Do this first, before any tool calls.

**Session analysis** (from conversation history):
- Did Claude misunderstand a request that a rule could prevent next time?
- Were there repeated corrections or clarifications?
- Did Claude **violate an existing rule**? → needs strengthening
- Did the user type the same prompt more than once? → candidate for a new slash command
- Did a tool or permission get approved that should be persisted in settings?
- Was a pattern confirmed, a memory entry contradicted, or a problem solved in a reusable way?

**MEMORY.md analysis** (content already in context via auto-memory):
- **Duplication** — same fact in two bullets or sections
- **Vagueness** — rule with no clear trigger or action ("be careful with X")
- **Bloat** — block >5 lines or 3+ bullets sharing a theme; flag if MEMORY.md >160 lines
- **Skills staleness** — skill names referenced in MEMORY.md that don't appear in the `system-reminder` list
- **Oversize document** — scan session history for Read calls on files ≥150 lines without `offset`/`limit`
- **Skill description quality** — for each skill invoked this session, is its `system-reminder` description specific enough to trigger reliably?

Hold all findings, then proceed to Phase 1.

## Phase 1 — Fetch files

**Step 1 — Run the gather script (1 tool call):**
```
python ~/.claude/skills/reflection/scripts/gather.py
```

Returns a JSON manifest: every relevant path, whether it exists, and its line count:
- `global_claude_md` — `~/.claude/CLAUDE.md`
- `project_claude_mds` — all `**/CLAUDE.md` under CWD
- `settings` — `.claude/settings.json` and `.claude/settings.local.json`
- `commands` — `.claude/commands/*.md`
- `memory_files` — all files in the memory directory
- `slug` and `memory_dir` — pre-computed

**Step 2 — Read files in one parallel batch:**
Use `lines` from the manifest to set limits — never load more than needed:
- `global_claude_md` and `project_claude_mds`: `lines ≤ 150` → read in full; `> 150` → `limit=150`
- `settings` files: read in full
- Command files: `lines ≤ 40` → read in full; `> 40` → Grep for stale references only
- Memory files linked in the in-context MEMORY.md: read with `limit=80`
- Memory files **not** linked in MEMORY.md: note as orphan candidates, no read yet

Two tool calls total for Phase 1: gather script + one parallel read batch.

## Phase 2 — Analysis on fetched files

### Pass 1 — Staleness & cross-reference

- Does MEMORY.md reference skills, files, or tools absent from the gather output? → stale reference
- Are there `memory_files` not linked from MEMORY.md? → orphan candidate. `Read limit=50` to summarize before proposing deletion.
- Do CLAUDE.md entries reference completed work, resolved bugs, or outdated versions? → freshness candidate

### Pass 2 — Document sharpening

Apply to all newly loaded files (CLAUDE.md, command files, topic files):

**Duplication** — same rule in CLAUDE.md and MEMORY.md, or repeated within a single file.

**Vagueness** — rule with no clear trigger or no specific action.

**Contradiction** — two rules prescribing opposite behaviors. Propose a single source of truth.

**Global vs project scope** — rules in `~/.claude/CLAUDE.md` that are project-specific, or vice versa.

**Oversize document** — extend the Phase 0 scan with large files now loaded. Propose: split via `bmad-shard-doc` (check `system-reminder` if installed), prepend a compact index block (10–20 lines, topic → line range), or delete stale sections.

### Pass 3 — Net-new additions

Separate from finding problems — ask: *what from this session is worth adding fresh?*

- Was a technique, workaround, or debugging approach used that worked well and isn't in memory yet?
- Was a tool combination, workflow, or sequence discovered that would help future sessions?
- Was a user preference expressed (style, tone, tooling, decision) that wasn't already captured?
- Was a project-specific fact learned (architecture, key file, naming convention) that belongs in memory?

For each candidate, draft the **exact text** to add — not a vague description of it. If nothing new was learned, say so explicitly rather than skipping silently.

These become **Addition** findings (lowest priority, but never omitted).

---

**What NOT to save** (applies across all passes):
- Session-specific context (current task, temp state, in-progress work)
- Speculative conclusions from a single observation
- Anything already covered in existing CLAUDE.md rules or memory entries

## Phase 3 — Interactive Review

**Gap check first:** If `memory_dir_exists: false` or `memory_files: []` in the gather output, always propose creating MEMORY.md with key session facts — even if no other issues found.

If no findings: say so briefly and stop.

Otherwise, present all findings at once **sorted by priority** before implementing anything:

1. **Contradiction** — two rules prescribe opposite behaviors
2. **Oversize** — large file read in full (burns tokens every session)
3. **Rule violated** — existing rule broken in this session (needs strengthening)
4. **Duplication** — same rule in two places
5. **Staleness** — stale references, completed work, old versions
6. **Scope misplacement** — rule in wrong CLAUDE.md (global vs project)
7. **Bloat** — section too long for active memory
8. **Vagueness** — rule not actionable
9. **Orphan / stale command / skill description** — cleanup, low urgency
10. **Addition** — net-new memory entry or rule worth adding
11. **Gap** — missing MEMORY.md

Each finding uses this format:

```
### [Category]

**Observed**: [What was found — quote or describe, with file + location]
**Problem**: [One line: why this is an issue — omit for Addition findings]
**Before**: [Current text, verbatim — omit for new additions]
**After**: [Exact replacement text, or DELETE, or new text to add]
**Action**: [APPLIED / SKIPPED — filled in after user decision]
**File**: [exact path(s)]
```

Wait for the user to approve individually, say "all", or ask to modify.

## Phase 4 — Implementation

For each approved change:

1. **CLAUDE.md edits**: Use `Edit`. Place in the most logical existing section; add a section only if nothing fits. Keep rules concise and actionable.

2. **Memory updates**:
   - Stable patterns → relevant topic file (`debugging.md`, `patterns.md`, etc.)
   - Short cross-session facts → `MEMORY.md`
   - Remove or correct stale entries — never leave contradictions
   - Keep `MEMORY.md` under ~180 lines

3. **New commands**: Create `.claude/commands/<name>.md` with description and exact prompt text.

4. **Settings**: Add tool permissions or MCP entries to `settings.local.json` (not `settings.json`).

5. **Oversize document**:
   - `bmad-shard-doc` in `system-reminder` → tell the user they can run `/bmad-shard-doc` on the file
   - Flat list (no H2 sections) → prepend a compact index block so future sessions can Grep it
   - Stale sections only → delete them directly

After all changes, confirm what was modified in one short list.

## Phase 5 — Write log entry

Compose a JSON object and run:
```
python ~/.claude/skills/reflection/scripts/write_log.py - <memory_dir>/reflection-log.md
```
Use `memory_dir` from the gather output. Pass JSON via stdin (`-`). Script creates the file if absent and always appends.

```json
{
  "date": "YYYY-MM-DD",
  "project": "<CWD basename>",
  "session": "<one sentence: what this session was about>",
  "tool_calls": {
    "phase_1_step_1": ["python gather.py"],
    "phase_1_step_2": ["Read ~/.claude/CLAUDE.md", "Read .claude/settings.json", "..."],
    "phase_4": ["Edit memory/MEMORY.md", "..."]
  },
  "findings": [
    {
      "id": 1,
      "category": "Bloat",
      "file": "exact/path",
      "observed": "verbatim quote or precise description",
      "problem": "why this is an issue",
      "action": "APPLIED",
      "reason": "",
      "before": "exact original text, or n/a for new additions",
      "after": "exact replacement text, DELETE, or n/a if skipped"
    }
  ]
}
```

Rules:
- Use today's date from `currentDate` context if available.
- Every finding gets an entry — nothing omitted, even if skipped.
- `before`/`after` must be verbatim for applied changes — this is the audit trail.
- List every tool call made during this run, grouped by phase.
