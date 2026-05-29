---
description: "Question-first mode for analysis, clarification, and decision support without implementation."
agent: ask
subtask: false
---

OpenCode command notes:
- Use this command when the user wants understanding, analysis, clarification, or planning input without code changes.
- Prefer concise answers and only ask targeted follow-up questions when they materially change the outcome.
- Runs through the `ask` agent, configured to use `openai/gpt-5.3-codex` for cheaper analysis.

# /ask - Ask Mode

$ARGUMENTS

---

## Goal

Handle the user request in ask mode:

- understand first
- inspect relevant context if needed
- answer directly when possible
- ask only the minimum clarifying questions
- do not implement or modify files

## Behavior

1. If this is a direct question, answer it clearly.
2. If this is a vague request, ask focused questions that clarify scope, purpose, or constraints.
3. If repository context matters, inspect before answering.
4. If library or API docs matter, use `context7`.
5. If code discovery matters, prefer `smartly-vps-cocoindex` for semantic search, then confirm with file reads.
6. If prior session context, preferences, or decisions matter, consult `agentmemory`; do not treat memory as authoritative for code without local confirmation.

## Output

- concise answer
- short options/trade-offs when relevant
- one next question only if needed
