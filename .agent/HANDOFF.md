# 🔄 HANDOFF — Agent Context Transfer Protocol

> **Purpose:** Maintain continuity between AI agents (CLI switches, rate limits, second opinions).
> **Rule:** Every agent MUST read this file at session start. Update before closing.

---

## 📌 Current State

- **Active Task:** _None_
- **Last Agent:** _None_
- **Timestamp:** _Not set_
- **Status:** `idle` <!-- idle | in-progress | blocked | review-needed -->

---

## 🎯 Active Task Summary

<!-- What is being worked on RIGHT NOW. Keep to 3-5 lines max. -->

_No active task._

---

## ✅ What Was Done (Last Session)

<!-- Bullet list of completed actions. Be specific: file names, functions, decisions. -->

- _Nothing yet_

---

## 🔜 What Needs To Be Done Next

<!-- Clear, actionable next steps. Numbered for priority. -->

1. _Nothing pending_

---

## 🧠 Key Decisions Made

<!-- Architecture choices, trade-offs, patterns selected. Critical for context. -->

| Decision | Rationale | Files Affected |
|----------|-----------|----------------|
| _None_   | _N/A_     | _N/A_          |

---

## ⚠️ Blockers & Open Questions

<!-- Anything that stopped progress or needs user input. -->

- _None_

---

## 📁 Modified Files (Last Session)

<!-- Quick reference for the next agent to know what changed. -->

```
(no files modified)
```

---

## 🔗 Relevant Context

<!-- Links to task plans, PRs, issues, or documentation the next agent should read. -->

- Task plan: _None_
- Related PR: _None_
- Docs: `.agent/ARCHITECTURE.md`

---

## 📋 Usage Protocol

### When Switching Agents (Rate Limit / Second Opinion)

#### Before Closing Current Agent

1. Ask: _"Update HANDOFF.md with current state before I close"_
2. Agent fills: Active Task, What Was Done, Next Steps, Modified Files
3. Agent sets Status to `in-progress` or `blocked`

#### When Opening New Agent

1. Say: _"Read .agent/HANDOFF.md and continue from where the last agent left off"_
2. New agent picks up context without re-analyzing entire codebase

### For Second Opinion

1. Set Status to `review-needed`
2. Fill "What Was Done" with the approach taken
3. Add specific question to "Blockers & Open Questions"
4. Tell second agent: _"Read .agent/HANDOFF.md — I need a second opinion on the approach described"_
