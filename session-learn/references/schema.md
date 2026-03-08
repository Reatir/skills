# session-learn — Schema Reference

## index.json

Root structure:
```json
{
  "version": "1",
  "entries": [ ]
}
```

### Entry fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Unique ID: `p001`=pattern, `f001`=failed, `d001`=debug, `r001`=rule |
| `type` | enum | yes | `pattern` \| `failed` \| `debug` \| `rule` |
| `title` | string | yes | Short, searchable title (same as the ## heading in the .md file) |
| `file` | string | yes | Which memory file holds this entry (`patterns.md`, etc.) |
| `scope` | enum | yes | `global` \| `project` |
| `confidence` | enum | yes | `unknown` \| `tentative` \| `confirmed` \| `stable` \| `exception_noted` |
| `count` | int | yes | Times observed or reinforced |
| `added` | date | yes | ISO date YYYY-MM-DD when first created |
| `last_reinforced` | date | yes | Last date count was bumped (same as `added` on creation) |
| `tags` | string[] | no | Optional classification tags |
| `fixes` | string | no | (failed entries only) ID of the pattern that replaces this approach |
| `exception_context` | string | no | (exception_noted only) When the rule has a valid exception |

### Confidence lifecycle

```
unknown       — imported from pre-existing files, not yet evaluated
tentative     — observed once (count=1)
confirmed     — observed 2-3 times
stable        — observed 4+ times
exception_noted — stable rule with a documented valid exception
```

Auto-promotion on DUPLICATE detected:
- count reaches 2 or 3 → `confirmed`
- count reaches 4+ → `stable`

Downgrade: never automatic. Only on explicit user instruction during review.

Exception: when a `stable` rule is violated successfully → set `exception_noted`, fill `exception_context`.

### ID assignment

IDs are sequential per type. To find the next ID:
1. Load `index.json`
2. Filter entries by type
3. Find max numeric suffix
4. Increment by 1, zero-pad to 3 digits

Example: existing patterns p001, p002, p007 → next is p008.

---

## Inline comment format

Every entry in `.md` files carries a metadata comment on the line immediately after the `##` heading:

```markdown
## Title of entry
<!-- id:p042 added:2026-03-07 confidence:tentative count:1 -->
```

For failed entries, add `fixes:` when applicable:
```markdown
## Title of failed entry
<!-- id:f003 added:2026-03-07 confidence:stable count:7 fixes:p001 -->
```

For exception_noted entries:
```markdown
## Title of rule
<!-- id:r005 added:2026-01-15 confidence:exception_noted count:9 exception:"only when X condition" -->
```

The `index.json` is the source of truth. Inline comments are for humans reading the files directly. They must stay in sync — update both when modifying an entry.

---

## Entry format per category

### patterns.md

```markdown
## [Short title]
<!-- id:pNNN added:YYYY-MM-DD confidence:tentative count:1 -->

**When**: [context in which this applies]
**Do**: [what to do — specific enough to act on]
**Why**: [why this is better than the alternative]
**Instead of**: [what not to do]
```

### failed.md

```markdown
## [What was tried]
<!-- id:fNNN added:YYYY-MM-DD confidence:tentative count:1 fixes:pNNN -->

**Tried**: [exact action taken]
**Result**: [what happened]
**Root cause**: [why it failed — not just "it didn't work"]
**Instead**: [what to do — must give the fix or reference the pattern]
```

### debugging.md

```markdown
## [Symptom description]
<!-- id:dNNN added:YYYY-MM-DD confidence:tentative count:1 -->

**Symptom**: [what was observed]
**Root cause**: [actual cause]
**Fix**: [solution applied]
**Example** (optional):
```code
[relevant snippet if helpful]
```
```

### Rule (inline in MEMORY.md or patterns.md)

```markdown
## [Rule title]
<!-- id:rNNN added:YYYY-MM-DD confidence:stable count:N -->

**Rule**: Always [X] | Never [Y]
**Reason**: [why]
**Exception** (if exception_noted): [when the rule does not apply]
```

---

## session-learn-log.md format

Append-only. Each run adds one block at the bottom:

```markdown
## YYYY-MM-DD HH:MM — session-slug (or "conversational")
Type: feature | Outcome: partial
Accepted: 5 (pattern:2 failed:1 debug:1 rule:1) | Skipped: 2 | Filtered: 3 | Conflicts: 1
Modified: patterns.md (+2), failed.md (+1), index.json
---
```

---

## Minimal file templates (first-run)

### MEMORY.md
```markdown
# Memory

> Key rules and pointers. Keep under 180 lines.
> Details live in topic files below.

## Pointers
- Patterns: see `patterns.md`
- Failed approaches: see `failed.md`
- Debug solutions: see `debugging.md`
```

### index.json
```json
{
  "version": "1",
  "entries": []
}
```

### patterns.md / failed.md / debugging.md
```markdown
# [Patterns | Failed approaches | Debug solutions]

<!-- Managed by session-learn. Do not edit IDs or inline comments manually. -->
```

### session-learn-log.md
```markdown
# session-learn audit log

<!-- Append-only. One block per run. -->
```
