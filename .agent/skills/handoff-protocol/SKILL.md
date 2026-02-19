---
name: handoff-protocol
description: Multi-agent context transfer protocol. Ensures consistent HANDOFF.md updates when switching CLIs, hitting rate limits, or requesting second opinions.
allowed-tools: Read, Write, Edit
version: 1.0
priority: HIGH
---

# Handoff Protocol — Multi-Agent Context Transfer

> **Purpose:** Ensure seamless context transfer between AI agents via `.agent/HANDOFF.md`.

---

## When To Activate

| Trigger | Action |
|---------|--------|
| User says "handoff", "atualize handoff", "prepare handoff" | Write mode: update HANDOFF.md |
| User says "continue", "continue from handoff", "leia handoff" | Read mode: resume from HANDOFF.md |
| User says "second opinion", "review this approach" | Review mode: read HANDOFF.md, analyze approach |
| Session ending (rate limit, user closing) | Auto-suggest: "Should I update HANDOFF.md before closing?" |

---

## File Location

**Always:** `.agent/HANDOFF.md` (project root, never create copies)

---

## Write Mode (Updating HANDOFF.md)

### 🔴 Rules (MANDATORY)

| Rule | Description |
|------|-------------|
| **Preserve structure** | NEVER delete headers (`##`), tables structure, or the `📋 Usage Protocol` section |
| **Replace content only** | Replace placeholder text (`_None_`, `_No active task_`) with real content |
| **Keep it current** | Each update OVERWRITES previous content (not append) |
| **Be specific** | File names, function names, line numbers — not vague descriptions |
| **Timestamp it** | Always update the `Timestamp` field with current datetime |

### What To Fill

| Section | What To Write |
|---------|---------------|
| **Current State** | Active Task name, your agent name, timestamp, status |
| **Active Task Summary** | 3-5 line summary of current work (what + why + where) |
| **What Was Done** | Bullet list with specific files/functions modified |
| **What Needs To Be Done Next** | Numbered actionable steps, priority order |
| **Key Decisions** | Table: decision → rationale → affected files |
| **Blockers & Open Questions** | Anything that stopped progress or needs user input |
| **Modified Files** | Code block listing every file touched this session |
| **Relevant Context** | Links to task plans, PRs, docs |

### Status Values

| Status | Meaning |
|--------|---------|
| `idle` | No active work |
| `in-progress` | Task underway, can be continued |
| `blocked` | Cannot proceed without user/external input |
| `review-needed` | Second opinion requested |

### Example Update

```markdown
## 📌 Current State

- **Active Task:** Refactoring geofence handlers
- **Last Agent:** Claude Code
- **Timestamp:** 2026-02-19T09:24:00-03:00
- **Status:** `in-progress`

## 🎯 Active Task Summary

Refatorando handlers de geofence para usar @db_handler wrapper.
Completei smartly_create_geofence. Falta smartly_update_geofence e smartly_delete_geofence.
Seguindo padrão definido em implementation_plan.md.

## ✅ What Was Done (Last Session)

- Refactored `smartly_create_geofence/lambda_function.py` — added @db_handler, removed try-catch
- Updated `src/layers/shared/db_utils.py` — new connection pool parameter
- Ran lint check — 0 errors

## 🔜 What Needs To Be Done Next

1. Refactor `smartly_update_geofence/lambda_function.py` (same pattern)
2. Refactor `smartly_delete_geofence/lambda_function.py`
3. Run test suite for geofence handlers
```

---

## Read Mode (Resuming from HANDOFF.md)

### Protocol

1. **Read** `.agent/HANDOFF.md`
2. **Summarize** to user: _"Last session [Agent] was working on [Task]. Status: [status]. Next steps: [1, 2, 3]."_
3. **Ask**: _"Should I continue from step 1?"_
4. **Load context**: Read any files listed in `Modified Files` and `Relevant Context`

### 🔴 Rules

| Rule | Description |
|------|-------------|
| **Don't re-analyze** | Trust the handoff. Don't re-read entire codebase |
| **Verify first** | Quick check that modified files match described state |
| **Ask before changing direction** | If handoff says X, don't do Y without asking |

---

## Review Mode (Second Opinion)

### Protocol

1. **Read** HANDOFF.md — focus on `Active Task Summary` and `Key Decisions`
2. **Analyze** the approach described, not just the code
3. **Respond** with:
   - Agreement or disagreement (with rationale)
   - Alternative approaches (if any)
   - Risks or edge cases the previous agent may have missed
4. **Do NOT modify** HANDOFF.md in review mode (unless user asks)

---

## Edge Cases

| Situation | Action |
|-----------|--------|
| HANDOFF.md doesn't exist | Create it from template (see `.agent/HANDOFF.md`) |
| HANDOFF.md is empty/corrupted | Recreate structure, fill with current session info |
| Multiple tasks in progress | Use the most recent `Timestamp` as current |
| User didn't ask for handoff but session is ending | Suggest: "Want me to update HANDOFF.md before we close?" |
