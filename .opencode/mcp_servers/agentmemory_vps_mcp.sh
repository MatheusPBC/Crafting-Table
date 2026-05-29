#!/usr/bin/env bash
set -euo pipefail

VPS_TARGET="${AGENTMEMORY_VPS_SSH_TARGET:-root@100.101.254.17}"
LOCAL_PORT="${AGENTMEMORY_LOCAL_PORT:-43111}"
REMOTE_PORT="${AGENTMEMORY_REMOTE_PORT:-3111}"
SECRET_FILE="${AGENTMEMORY_SECRET_FILE:-$HOME/.agentmemory/agentmemory_secret}"

if [ ! -r "$SECRET_FILE" ]; then
  printf 'AgentMemory secret file not readable: %s\n' "$SECRET_FILE" >&2
  exit 1
fi

if ! curl -fsS "http://127.0.0.1:${LOCAL_PORT}/agentmemory/livez" >/dev/null 2>&1; then
  ssh \
    -f \
    -N \
    -L "127.0.0.1:${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT}" \
    -o ExitOnForwardFailure=yes \
    "$VPS_TARGET"
fi

export AGENTMEMORY_URL="http://127.0.0.1:${LOCAL_PORT}"
export AGENTMEMORY_SECRET="$(cat "$SECRET_FILE")"
export AGENTMEMORY_TOOLS="${AGENTMEMORY_TOOLS:-all}"

MCP_BIN="$(find "$HOME/.npm/_npx" -path '*/node_modules/@agentmemory/mcp/bin.mjs' -print -quit 2>/dev/null || true)"

if [ -z "$MCP_BIN" ]; then
  npx -y @agentmemory/mcp >/dev/null 2>&1 || true
  MCP_BIN="$(find "$HOME/.npm/_npx" -path '*/node_modules/@agentmemory/mcp/bin.mjs' -print -quit 2>/dev/null || true)"
fi

if [ -z "$MCP_BIN" ]; then
  printf 'AgentMemory MCP package not found after npx bootstrap\n' >&2
  exit 1
fi

exec node "$MCP_BIN"
