# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp",
# ]
# ///

from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP


LOGGER = logging.getLogger("cocoindex_vps_mcp_server")
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=getattr(
            logging,
            os.getenv("COCOINDEX_VPS_MCP_LOG_LEVEL", "INFO").upper(),
            logging.INFO,
        ),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


@dataclass(frozen=True)
class Config:
    ssh_target: str
    repo_path: str
    python_path: str
    timeout_seconds: int
    max_limit: int


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


CONFIG = Config(
    ssh_target=os.getenv("COCOINDEX_VPS_SSH_TARGET", "root@100.101.254.17"),
    repo_path=os.getenv("COCOINDEX_VPS_REPO_PATH", "/root/smartly.backend_smartly-dev"),
    python_path=os.getenv(
        "COCOINDEX_VPS_PYTHON_PATH",
        "/root/.local/share/uv/tools/cocoindex-code/bin/python",
    ),
    timeout_seconds=_env_int("COCOINDEX_VPS_TIMEOUT_SECONDS", 180, 5, 900),
    max_limit=_env_int("COCOINDEX_VPS_MAX_LIMIT", 50, 1, 100),
)


REMOTE_SCRIPT = r"""
import json
import sys

from cocoindex_code import client

payload = json.load(sys.stdin)
repo_path = payload["repo_path"]
action = payload["action"]

if action == "refresh_index":
    response = client.index(repo_path)
    print(json.dumps({
        "success": response.success,
        "message": response.message,
    }))
elif action == "search":
    if payload.get("refresh_index"):
        index_response = client.index(repo_path)
        if not index_response.success:
            print(json.dumps({
                "success": False,
                "results": [],
                "total_returned": 0,
                "offset": payload.get("offset", 0),
                "message": index_response.message or "remote index refresh failed",
            }))
            raise SystemExit(0)

    response = client.search(
        repo_path,
        query=payload["query"],
        languages=payload.get("languages"),
        paths=payload.get("paths"),
        limit=payload.get("limit", 5),
        offset=payload.get("offset", 0),
    )
    print(json.dumps({
        "success": response.success,
        "results": [
            {
                "file_path": item.file_path,
                "language": item.language,
                "content": item.content,
                "start_line": item.start_line,
                "end_line": item.end_line,
                "score": item.score,
            }
            for item in response.results
        ],
        "total_returned": response.total_returned,
        "offset": response.offset,
        "message": response.message,
    }))
else:
    print(json.dumps({"success": False, "message": f"unknown action: {action}"}))
"""


def _error_payload(code: str, message: str) -> str:
    return json.dumps(
        {
            "success": False,
            "results": [],
            "total_returned": 0,
            "offset": 0,
            "message": f"{code}: {message}",
        },
        ensure_ascii=False,
    )


def _run_remote(payload: dict[str, Any]) -> dict[str, Any]:
    remote_command = f"{shlex.quote(CONFIG.python_path)} -c {shlex.quote(REMOTE_SCRIPT)}"
    command = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        CONFIG.ssh_target,
        remote_command,
    ]
    full_payload = {"repo_path": CONFIG.repo_path, **payload}

    result = subprocess.run(
        command,
        input=json.dumps(full_payload),
        text=True,
        capture_output=True,
        timeout=CONFIG.timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "remote command failed"
        raise RuntimeError(stderr)

    output = result.stdout.strip()
    if not output:
        raise RuntimeError("remote command returned empty output")
    return json.loads(output)


def _normalize_limit(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("limit must be an integer")
    return max(1, min(limit, CONFIG.max_limit))


def _normalize_offset(offset: int) -> int:
    if isinstance(offset, bool) or not isinstance(offset, int):
        raise ValueError("offset must be an integer")
    return max(0, offset)


mcp = FastMCP("smartly-vps-cocoindex")


@mcp.tool()
def search(
    query: str,
    limit: int = 5,
    offset: int = 0,
    refresh_index: bool = False,
    languages: list[str] | None = None,
    paths: list[str] | None = None,
) -> str:
    """Semantic code search using the CocoIndex index hosted on the Tailscale VPS."""
    try:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")

        payload = _run_remote(
            {
                "action": "search",
                "query": query.strip(),
                "limit": _normalize_limit(limit),
                "offset": _normalize_offset(offset),
                "refresh_index": bool(refresh_index),
                "languages": languages,
                "paths": paths,
            }
        )
        return json.dumps(payload, ensure_ascii=False)
    except (OSError, RuntimeError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        LOGGER.exception("VPS CocoIndex search failed")
        return _error_payload("VPS_COCOINDEX_SEARCH_FAILED", str(exc))


@mcp.tool()
def refresh_index() -> str:
    """Refresh the CocoIndex index on the Tailscale VPS."""
    try:
        payload = _run_remote({"action": "refresh_index"})
        return json.dumps(payload, ensure_ascii=False)
    except (OSError, RuntimeError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        LOGGER.exception("VPS CocoIndex refresh failed")
        return _error_payload("VPS_COCOINDEX_REFRESH_FAILED", str(exc))


if __name__ == "__main__":
    mcp.run()
