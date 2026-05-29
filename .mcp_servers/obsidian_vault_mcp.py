# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp",
# ]
# ///

from __future__ import annotations

import json
import os
import subprocess
from datetime import date
from pathlib import Path

from mcp.server.fastmcp import FastMCP


VAULT_ROOT = Path(os.getenv("OBSIDIAN_VAULT_ROOT", "/root/obsidian-vault")).resolve()
DAILY_DIR = os.getenv("OBSIDIAN_DAILY_DIR", "Daily")
MAX_READ_CHARS = int(os.getenv("OBSIDIAN_MCP_MAX_READ_CHARS", "120000"))
MAX_SEARCH_RESULTS = int(os.getenv("OBSIDIAN_MCP_MAX_SEARCH_RESULTS", "50"))

mcp = FastMCP("obsidian-vault")


def _json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _error(code: str, message: str) -> str:
    return _json({"error": {"code": code, "message": message}})


def _vault_path(path: str) -> Path:
    if not isinstance(path, str):
        raise ValueError("path must be a string")

    normalized = path.strip().lstrip("/")
    if not normalized:
        raise ValueError("path cannot be empty")

    resolved = (VAULT_ROOT / normalized).resolve()
    if resolved != VAULT_ROOT and VAULT_ROOT not in resolved.parents:
        raise ValueError("path escapes vault root")

    return resolved


def _relative(path: Path) -> str:
    return str(path.relative_to(VAULT_ROOT))


def _run_git(args: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        ["git", "-C", str(VAULT_ROOT), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


@mcp.tool()
def vault_info() -> str:
    """Return vault path, git branch, remote, and working tree status."""
    if not VAULT_ROOT.exists():
        return _error("VAULT_NOT_FOUND", f"Vault root does not exist: {VAULT_ROOT}")

    return _json(
        {
            "root": str(VAULT_ROOT),
            "branch": _run_git(["branch", "--show-current"]),
            "remote": _run_git(["remote", "-v"]),
            "status": _run_git(["status", "--short"]),
        }
    )


@mcp.tool()
def git_pull() -> str:
    """Pull latest vault changes from the configured git remote."""
    return _json(_run_git(["pull", "--ff-only"]))


@mcp.tool()
def git_status() -> str:
    """Return the current vault git status."""
    return _json(_run_git(["status", "--short"]))


@mcp.tool()
def git_commit_push(message: str) -> str:
    """Commit all vault changes and push them to the configured git remote."""
    if not message.strip():
        return _error("INVALID_MESSAGE", "Commit message cannot be empty")

    add = _run_git(["add", "."])
    if not add["ok"]:
        return _json({"add": add})

    diff = _run_git(["diff", "--cached", "--quiet"])
    if diff["returncode"] == 0:
        return _json({"committed": False, "message": "No staged changes to commit"})

    commit = _run_git(["commit", "-m", message.strip()])
    if not commit["ok"]:
        return _json({"add": add, "commit": commit})

    push = _run_git(["push"])
    return _json({"add": add, "commit": commit, "push": push})


@mcp.tool()
def list_directory(path: str = ".") -> str:
    """List files and directories under a vault directory."""
    try:
        target = VAULT_ROOT if path.strip() in {"", "."} else _vault_path(path)
        if not target.is_dir():
            return _error("NOT_DIRECTORY", f"Not a directory: {path}")

        dirs: list[str] = []
        files: list[str] = []
        for child in sorted(target.iterdir(), key=lambda item: item.name.lower()):
            if child.name == ".git":
                continue
            if child.is_dir():
                dirs.append(child.name)
            else:
                files.append(child.name)
        return _json({"path": _relative(target), "dirs": dirs, "files": files})
    except ValueError as exc:
        return _error("INVALID_PATH", str(exc))


@mcp.tool()
def read_note(path: str) -> str:
    """Read a note or text file from the vault."""
    try:
        target = _vault_path(path)
        if not target.is_file():
            return _error("NOT_FOUND", f"File not found: {path}")

        content = target.read_text(encoding="utf-8", errors="replace")
        truncated = len(content) > MAX_READ_CHARS
        if truncated:
            content = content[:MAX_READ_CHARS]
        return _json({"path": _relative(target), "truncated": truncated, "content": content})
    except ValueError as exc:
        return _error("INVALID_PATH", str(exc))


@mcp.tool()
def write_note(path: str, content: str, overwrite: bool = False) -> str:
    """Create a note. Set overwrite=true to replace an existing file."""
    try:
        target = _vault_path(path)
        if target.exists() and not overwrite:
            return _error("FILE_EXISTS", "File already exists; pass overwrite=true to replace it")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return _json({"ok": True, "path": _relative(target)})
    except ValueError as exc:
        return _error("INVALID_PATH", str(exc))


@mcp.tool()
def append_note(path: str, content: str) -> str:
    """Append content to a vault file, creating it if needed."""
    try:
        target = _vault_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(content)
        return _json({"ok": True, "path": _relative(target)})
    except ValueError as exc:
        return _error("INVALID_PATH", str(exc))


@mcp.tool()
def daily_append(content: str) -> str:
    """Append content to today's daily note using OBSIDIAN_DAILY_DIR/YYYY-MM-DD.md."""
    daily_path = f"{DAILY_DIR}/{date.today().isoformat()}.md"
    return append_note(daily_path, content)


@mcp.tool()
def search_notes(query: str, limit: int = 20) -> str:
    """Search markdown/text notes by case-insensitive substring."""
    normalized = query.strip().lower()
    if not normalized:
        return _error("INVALID_QUERY", "query cannot be empty")

    safe_limit = max(1, min(limit, MAX_SEARCH_RESULTS))
    matches: list[dict[str, object]] = []
    for root, dirs, files in os.walk(VAULT_ROOT):
        dirs[:] = [directory for directory in dirs if directory != ".git"]
        for name in files:
            if not name.lower().endswith((".md", ".markdown", ".txt", ".base", ".canvas")):
                continue
            file_path = Path(root) / name
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue

            for line_number, line in enumerate(lines, start=1):
                if normalized in line.lower():
                    matches.append(
                        {
                            "path": _relative(file_path),
                            "line": line_number,
                            "excerpt": line[:300],
                        }
                    )
                    break
            if len(matches) >= safe_limit:
                return _json({"query": query, "matches": matches, "truncated": True})

    return _json({"query": query, "matches": matches, "truncated": False})


if __name__ == "__main__":
    mcp.run()
