---
name: yuumi-plan
description: Use when creating, converting, or saving implementation plans for the Yuumi Neovim plugin, especially JSON plans with anchors, writeText, .agent/current-plan.json, .agent/*-plan.json, or :YuumiPlans.
---

# Yuumi Plan

## Overview
Create executable guidance plans for the Yuumi Neovim plugin. A Yuumi plan is not a generic task list: it is a JSON file with concrete guided patches, exact text to write, and validation criteria that the developer can consume in Neovim through `:Yuumi`, `:YuumiBoard`, ghost text, and `:YuumiValidate`.

Core principle: research first, plan only, do not edit application code unless the user explicitly asks for implementation.

## When To Use
- User asks to create a plan for Yuumi, Neovim guided coding, `:YuumiPlans`, `.agent/current-plan.json`, `.agent/<slug>-plan.json`, or `writeText`.
- User wants agents to prepare work for manual execution in the Yuumi plugin.
- User asks to convert an implementation plan, diff, issue, or task into a Yuumi-compatible JSON plan.
- User wants a plan allocated to `.agent/` for later use inside Neovim.

## When Not To Use
- User wants normal prose planning only.
- User wants direct code implementation without Yuumi.
- User wants to modify the Yuumi plugin itself, unless the output is a Yuumi plan file.

## Required Workflow
1. Understand the requested change and identify the target project root.
2. Research the codebase enough to identify real files, symbols, and insertion regions.
3. Create `.agent/` if needed.
4. Save the plan as `.agent/<task-slug>-plan.json`.
5. Only overwrite `.agent/current-plan.json` when the user explicitly asks for the plan to become the default.
6. Do not modify application code as part of Yuumi plan creation.
7. Validate the JSON syntax before reporting completion when tools are available.
8. Tell the user to load it with `:Yuumi`, `:YuumiPlans`, or `:YuumiLoad .agent/<task-slug>-plan.json`.

## JSON Contract
Top-level shape:

```json
{
  "version": 2,
  "title": "Short human-readable plan title",
  "patches": [
    {
      "id": "patch-slug",
      "file": "relative/path/to/file.ext",
      "summary": "What this task changes",
      "locator": {
        "afterText": "existing line before insertion",
        "beforeText": "existing line after insertion"
      },
      "insert": ["final line to type"],
      "doneWhen": ["How to know this patch is complete"]
    }
  ]
}
```

Prefer guided patches for edits in existing files:

| Field | Required | Purpose |
|---|---:|---|
| `id` | yes | Stable anchor identifier, lowercase slug. |
| `file` | yes | File path relative to the project root. |
| `summary` | yes | Human-readable patch summary. |
| `locator.afterText` | yes for insert-between | Existing line before the insertion region, trimmed match allowed. |
| `locator.beforeText` | yes for insert-between | Existing line after the insertion region, trimmed match allowed. |
| `reason` | no | Why this edit exists. |
| `guidance` | no | Human instruction shown in `:YuumiBoard`. |
| `insert` | yes | Lines the developer should write; array of strings. |
| `doneWhen` | yes | Checklist that confirms the anchor is complete. |
| `inlineSuggestions` | no | Optional trigger-based deterministic completions. |

Legacy line anchors are still accepted when no reliable context exists. In that case use `line`, optional `endLine`, and top-level `writeText`.

## Anchor Quality Rules
- Prefer 1-5 patches per file. Too many patches make the board noisy.
- Keep each `insert` block small enough to type manually, usually 5-25 lines.
- Use real file paths relative to the project root.
- Use `locator.afterText` and `locator.beforeText` from current code whenever possible; line numbers are fallback only.
- `insert` must be final text, not pseudocode, not comments saying TODO, and not markdown fences.
- `doneWhen` must verify behavior or structure, not repeat vague goals.
- If the task is exploratory or risky, create a planning anchor first instead of pretending exact code is known.

## Output Example
Save as `.agent/add-structured-log-plan.json`:

```json
{
  "version": 2,
  "title": "Add structured log",
  "patches": [
    {
      "id": "log-after-parse-input",
      "file": "src/handlers/example/lambda_function.py",
      "summary": "Add a structured log after input parsing.",
      "locator": {
        "afterText": "device_id, payload = _parse_input(event)",
        "beforeText": "device_lookup_id = device_id"
      },
      "reason": "Captures sanitized command context after parsing.",
      "guidance": "Insert this log between input parsing and device lookup assignment.",
      "insert": [
        "logger.info(",
        "    \"AppSync device command input parsed\",",
        "    extra={\"device_id\": device_id},",
        ")"
      ],
      "doneWhen": [
        "The log is between parse_input and device_lookup_id",
        "The log does not include raw payload data"
      ]
    }
  ]
}
```

## Final Response Contract
After creating the plan, report:
- Plan path, for example `.agent/add-greeting-plan.json`.
- Whether `.agent/current-plan.json` was updated.
- Files the plan targets.
- How to open it in Neovim: `:Yuumi`, `:YuumiPlans`, or `:YuumiLoad <path>`.
- Validation performed, if any.

## Common Mistakes
| Mistake | Fix |
|---|---|
| Creating generic `goal/tasks/title/verify` JSON | Use the required `version/title/patches[]` contract. |
| Saving in the project root | Save in `.agent/<slug>-plan.json`. |
| Depending only on line numbers | Prefer `locator.afterText` and `locator.beforeText`. |
| Omitting `insert` | Every actionable guided patch needs planned lines. |
| Using markdown code fences inside JSON | Store plain strings in `insert`. |
| Editing application code while planning | Create the Yuumi plan only. |
| Overwriting `.agent/current-plan.json` silently | Only do that when the user explicitly asks. |
| Planning against imaginary files | Research actual files first. |

## Quick Checklist
- [ ] Plan saved under `.agent/`.
- [ ] Top-level `version`, `title`, `patches` exist.
- [ ] Every guided patch has `id`, `file`, `summary`, `locator`, `insert`, `doneWhen`.
- [ ] `insert` is final text as an array of strings.
- [ ] No application code was changed unless separately requested.
- [ ] User was told how to load the plan in Yuumi.
