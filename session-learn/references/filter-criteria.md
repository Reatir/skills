# Filter Criteria

A learning must pass **all 4 tests** to be captured.
One failure = skip. Log the reason in the audit trail.

---

## Test 1: Repeatable

**Question**: Could this exact situation occur in another session?

PASS:
- "Used Read without offset on a 500-line file and got too much context"
- "Docker containers failed because xUnit parallelizes test classes by default"
- "Bash grep was called instead of the Grep tool — hook blocked it"

FAIL:
- "Skipped documentation for this story because we were pressed for time"
- "Decided to use approach X for this particular feature"
- "Ignored the timeout for this specific test run"

**Fail indicator**: the learning contains "for this story / task / PR / today / this time"

---

## Test 2: Actionable

**Question**: Does this change what Claude does next time?

PASS:
- "Use Grep tool with glob:'*.cs' instead of Bash grep" → changes tool choice
- "Add [Collection] attribute on integration test classes to prevent parallel execution" → changes code written
- "Run transition-story.sh instead of editing sprint-status.yaml directly" → changes workflow

FAIL:
- "The codebase uses the Repository pattern" → descriptive, not prescriptive
- "Story 2.7 was more complex than expected" → observation, no action follows
- "The team prefers small commits" → preference, not a behavioral change for Claude

**Fail indicator**: the learning describes a fact rather than prescribing an action

---

## Test 3: Non-trivial

**Question**: Would Claude get this wrong without the hint?

PASS:
- "Don't edit sprint-status.yaml directly, use transition-story.sh" → non-obvious workflow
- "AMD GPU needs HSA_OVERRIDE_GFX_VERSION=11.0.1 for Ollama on RDNA 3" → environment-specific
- "WithReuse(true) in Testcontainers means two fixtures share the same container" → subtle behavior

FAIL:
- "Read the file before editing it" → Claude does this by default
- "Run tests after making changes" → standard practice
- "Check if the file exists before writing to it" → Claude handles this automatically

**Fail indicator**: the learning states an obvious best practice or something Claude already does

---

## Test 4: Durable

**Question**: Will this still be true in 3 months?

PASS → scope **global**:
- "Use Grep tool, never Bash grep for content search" — true for all Claude Code projects

PASS → scope **project**:
- "Use transition-story.sh for status changes in this project" — true for this project's lifetime
- "HSA_OVERRIDE_GFX_VERSION=11.0.1 for Ollama on this machine" — tied to this dev environment

FAIL:
- "Use the staging URL while prod is down" — temporary state
- "Qdrant API v1.8 has a breaking change in collection creation" — version-pinned, will rot
- "Skip story 2.7 validation for now" — explicitly temporary

**Fail indicator**: the learning references a specific version number, a date, or a known-temporary state

---

## Special case: Failed entries

A Failed entry requires **all four** of these fields. Missing any → defer as a note, don't create the entry yet:

1. **What was tried** — specific enough to recognize the situation next time
2. **What happened** — the failure mode observed
3. **Why it failed** — root cause (not just "it didn't work")
4. **What to do instead** — the fix, or the ID of the pattern that replaces it

If "what to do instead" is not yet known (still investigating) → classify as Debug instead.

---

## Scope decision guide

Apply after a learning passes all 4 tests:

| Signal | Scope |
|---|---|
| References a specific file path in the project | project |
| References a project-specific script or workflow | project |
| References a project-specific convention or naming | project |
| Applies to any Claude Code session anywhere | global |
| References Claude Code tools (Grep, Read, Edit...) generically | global |
| Uncertain | project (safer default) |

Global entries go to `~/.claude/memory/`.
Project entries go to `.claude/memory/` (or the auto-memory path).

---

## Logging skipped items

Each skipped item must appear in the FILTERED section of the review output and in the audit log:

```
SKIP: "skipped docs for story X" — Fail: Repeatable (one-off decision)
SKIP: "Read file before editing" — Fail: Non-trivial (Claude default behavior)
SKIP: "Use staging URL" — Fail: Durable (temporary state)
SKIP: "Grep tool usage" — Duplicate of p001, count bumped to 4, promoted to stable
```
