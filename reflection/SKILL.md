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

The goal is to turn ephemeral session knowledge into durable improvements. You've just helped
the user through a session — patterns were confirmed, mistakes were corrected, preferences
were revealed. Capture what's worth keeping before the context disappears.

## Phase 1 — Load files (single parallel batch)

**Config files:**
- `~/.claude/CLAUDE.md` — global user-level config (applies to ALL projects)
- Project CLAUDE.md files: `Glob pattern="**/CLAUDE.md"` from the project root, then read each result
- `.claude/settings.json` and `.claude/settings.local.json`
- Command files: `Glob pattern=".claude/commands/*.md"`, then for each file:
  - If ≤40 lines: read in full
  - If >40 lines: `Grep pattern="workflow|command|run|invoke"` to check for stale references only

**Memory files:**
- `~/.claude/projects/<project-slug>/memory/MEMORY.md`
- Topic files linked from MEMORY.md: read each with `limit=80` — enough to assess content without loading everything
- `Glob` the full memory directory to detect files not linked from MEMORY.md (orphan candidates)

**Skills:**
- `Glob pattern="~/.claude/skills/*"` to list installed skills
- Descriptions are already in the `system-reminder` skills list — no file reads needed

## Phase 1 — Analysis passes (run in this order)

### Pass 1 — Staleness & cross-reference

Merge of cross-reference and freshness detection — both look for references that no longer hold:

- Does MEMORY.md reference skills, files, or tools that don't exist? (Check against the skills glob and memory dir glob.) → stale reference
- Are there memory directory files not linked from MEMORY.md? → orphan candidate. Before proposing deletion, `Read limit=50` to summarize content for the user.
- Do MEMORY.md or CLAUDE.md entries reference completed epics/stories by name, resolved bugs, specific package versions that changed, or workarounds for problems that no longer exist? → freshness candidate for archiving or deletion

### Pass 2 — Document sharpening scan

Detects gradual degradation across all documents read in Phase 1.

**Duplication** — same rule or fact in two places (CLAUDE.md + MEMORY.md, or two bullets in the same section). Propose merging into the canonical location.

**Vagueness** — rule with no clear trigger or no specific action ("be careful with X", "consider Y"). A sharp rule names *when* it applies and *exactly* what to do. Propose a rewrite or deletion.

**Bloat** — MEMORY.md block >5 lines, or 3+ bullets sharing a theme. Propose moving to a topic file + one-line summary + link. Also flag if MEMORY.md >160 lines (truncation limit is 200).

**Contradiction** — two rules prescribing opposite behaviors, especially between CLAUDE.md and MEMORY.md. Propose a single source of truth.

**Oversize document** — scan session history for Read calls on files ≥150 lines loaded in full (no `offset`/`limit`), or multiple sequential paginated passes on the same file. For each: note path, line count, fraction of content actually used. Propose one of: split via `bmad-shard-doc` (reuse Phase 1 skills listing to check if installed), prepend a compact index block (10–20 lines mapping topic → line range), or delete stale sections. Highest-value signal — costs tokens every session.

**Global vs project scope** — rules in `~/.claude/CLAUDE.md` that are project-specific, or rules in the project CLAUDE.md that should apply globally. Misplacement means they don't fire in the right context.

**Skill description quality** — for each skill invoked or referenced in this session, check its description from the `system-reminder` (already in context). Is it specific enough to trigger reliably?

### Pass 3 — Session analysis

**For CLAUDE.md / config:**
- Did Claude misunderstand a request that a rule could prevent next time?
- Were there repeated corrections or clarifications?
- Did Claude **violate an existing rule**? The rule needs strengthening: sharper trigger, harder verb ("never" vs "avoid"), or more prominent placement.
- Did the user type the same prompt **more than once**? → direct signal for a new slash command.
- Did a tool, permission, or MCP get approved that should be persisted in settings?

**For memory files:**
- Was a pattern confirmed across multiple moments in this session (→ worth saving)?
- Was an existing memory entry contradicted or shown to be wrong (→ update/remove)?
- Was a problem solved in a way that would help future sessions (→ debugging.md, patterns.md)?
- Was a preference expressed that should survive across conversations?

**What NOT to save:**
- Session-specific context (current task, temp state, in-progress work)
- Speculative conclusions from a single observation
- Anything already covered in existing CLAUDE.md rules or memory entries

## Phase 2 — Interactive Review

If no findings: say so briefly and stop.

Otherwise, present all findings at once **sorted by priority** before implementing anything:

1. **Contradiction** — two rules prescribe opposite behaviors
2. **Oversize** — full read forced on large file (burns tokens every session)
3. **Rule violated** — existing rule broken in this session (needs strengthening)
4. **Duplication** — same rule in two places
5. **Staleness** — stale references, completed work, old versions
6. **Scope misplacement** — rule in wrong CLAUDE.md (global vs project)
7. **Bloat** — section too long for active memory
8. **Vagueness** — rule not actionable
9. **Orphan / stale command / skill description** — cleanup, low urgency

Each finding uses this format:

```
### [Category — subcategory if applicable]

**Observed**: [What was found — quote or describe, with file + location]
**Problem**: [One line: why this is an issue]
**Before**: [Current text, verbatim or summarized — omit if it's a new addition]
**After**: [Exact replacement text — or DELETE]
**File**: [exact path(s)]
```

Wait for the user to approve individually, say "all", or ask to modify.

## Phase 3 — Implementation

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
   - If `bmad-shard-doc` is installed (reuse Phase 1 skills listing — no re-read): tell the user they can run `/bmad-shard-doc` on the file to split by H2.
   - If the file is a flat list (not H2-sectioned): draft a compact index block (10–20 lines, topic → line range) and propose prepending it so future sessions can Grep the index.
   - If the issue is stale sections: delete them directly.

After all changes, confirm what was modified in one short list.
