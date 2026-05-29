---
name: opencode-nvim-mcp
description: Use when working in OpenCode terminal sessions that need to open files or candidate lists in the current Neovim through the opencode-nvim MCP server.
tags: [opencode, neovim, mcp, navigation, terminal]
---

# OpenCode Neovim MCP

Use this skill when the user wants the OpenCode terminal to open files, jump to locations, or show candidate pickers in the current Neovim instance.

## When to Use

- Terminal-first OpenCode session, not ask-first flow
- User explicitly asks to open, navigate, jump, or choose files in Neovim
- You need `open_file` or `open_candidates` from the `opencode-nvim` MCP server

Do not use when:

- The user only wants explanation, not navigation
- There is no explicit intention to open or navigate
- A normal text answer is enough

## Core Rules

1. Only use the MCP when the user explicitly asks to open or navigate.
2. Tool names like `opencode-nvim_open_file` and `opencode-nvim_open_candidates` are the MCP tools from the `opencode-nvim` server, namespaced by OpenCode.
3. Prefer `open_file` when there is one clear target.
4. Prefer `open_candidates` when there are multiple reasonable targets.
4. Paths sent to the MCP should be absolute whenever possible.
5. The default editor behavior is `tabedit` in the current Neovim instance.
6. If a namespaced MCP tool returns `Not connected`, treat that as an MCP action failure to diagnose, not as proof that file discovery was wrong.
7. If `opencode mcp list` shows `opencode-nvim` as `connected` but the tool still returns `Not connected`, verify `OPENCODE_NVIM_RPC` and retry once before falling back.

## Preflight Check

Before relying on the tool, verify the MCP is available:

```bash
opencode mcp list
```

Expected:

- `opencode-nvim` appears as `connected`

If it is not connected, do not guess. Follow the diagnostics below.

## Diagnostics

### Case 1: MCP shows `failed`

Check whether the OpenCode session was opened from the plugin terminal.

The expected path is:

1. User opens Neovim
2. User starts OpenCode through `require("opencode").toggle()` or the mapped key
3. Plugin injects `OPENCODE_NVIM_RPC`

If needed, ask the user to verify in Neovim:

```vim
:lua print(require("opencode").rpc_socket())
:lua print(require("opencode").mcp_server_script())
```

### Case 2: `opencode-nvim` is disconnected in a terminal started outside the plugin

The fallback is manual environment export before launching OpenCode:

```bash
export OPENCODE_NVIM_RPC="/run/user/1000/nvim.xxxxx.0"
opencode
```

### Case 3: Tool call succeeds but nothing opens

Treat this as a Neovim-side action problem, not a discovery problem.
Re-check:

- `opencode-nvim` is connected
- path is absolute
- file exists
- target is unambiguous or `open_candidates` was used

### Case 4: `opencode-nvim_open_file` or `opencode-nvim_open_candidates` returns `Not connected`

These names are the MCP tools themselves.

Treat this as:

- MCP action path reached
- Neovim bridge failed for this call
- discovery may still be correct

Do this in order:

1. keep the discovered target or candidate list
2. run `opencode mcp list`
3. if `opencode-nvim` is not connected, report connection failure
4. if it is connected, verify `OPENCODE_NVIM_RPC` is present in the OpenCode terminal environment
5. retry once through the MCP tool
6. if it still fails and the user still wants the file opened, use direct shell fallback with the same socket

Reliable fallback for a single target:

```bash
nvim --server "$OPENCODE_NVIM_RPC" --remote-expr "execute('tabedit +' .. 526 .. ' ' .. fnameescape('/absolute/path/to/file'))"
```

Use `--remote-expr` or RPC-style execution for fallback. Do not use `--remote-send` for reliable automation.

## Tool Selection

### Single target

Use `open_file` with:

- `path`
- `line` optional
- `col` optional

Example mental model:

- user: "Abra README.md na linha 526 no Neovim"
- action: `open_file(path=<absolute>, line=526)`

### Multiple targets

Use `open_candidates` with:

- `prompt` optional
- `candidates[]`

Each candidate should include:

- `path`
- `line` optional
- `col` optional
- `label` optional

Example mental model:

- user: "Mostre as opções de arquivos relacionados a profiles e abra no Neovim"
- action: `open_candidates(candidates=[...])`

## Prompting Guidance

When the user asks in natural language to open something in Neovim:

1. resolve the target first
2. if one target is clear, call `open_file`
3. if more than one target is reasonable, call `open_candidates`
4. after the tool succeeds, confirm the result briefly

Do not stop at "I found the file" when the user explicitly asked to open it.
If the MCP tool fails once with `Not connected`, diagnose and retry. If the user explicitly still wants the file opened and `OPENCODE_NVIM_RPC` is available, use the direct shell fallback with `--remote-expr`.

## Common Mistakes

- Stopping after discovery and forgetting the MCP call
- Trying to use the MCP without explicit open/navigate intent
- Sending relative paths when you already know the absolute path
- Guessing a single file when ambiguity is real instead of using `open_candidates`
- Treating MCP failure as codebase failure instead of connection/setup failure
- Treating `Not connected` from `opencode-nvim_open_file` as if discovery failed
- Using `--remote-send` for fallback automation instead of `--remote-expr`

## Quick Reference

| Situation | Action |
|---|---|
| User wants one clear file opened | `open_file` |
| User wants navigation but there are multiple candidates | `open_candidates` |
| MCP failed to connect | Check `opencode mcp list` and `OPENCODE_NVIM_RPC` |
| OpenCode was started outside plugin | Use manual `OPENCODE_NVIM_RPC` export |
| `opencode-nvim_open_file` says `Not connected`, but server is connected | Verify `OPENCODE_NVIM_RPC`, retry once, then use `--remote-expr` fallback if needed |
