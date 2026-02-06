#!/usr/bin/env python3
"""Deterministic hardening gate for `.mcp_servers/mysql_mcp_server.py`.

Runs static checks only (no DB/network dependency) and returns non-zero exit
code when required hardening invariants are missing.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class GateCheck:
    name: str
    passed: bool
    detail: str


def _has_function(module: ast.Module, function_name: str) -> bool:
    return any(isinstance(node, ast.FunctionDef) and node.name == function_name for node in module.body)


def _find_run_query_select_guard(module: ast.Module) -> bool:
    """Require guard equivalent to: if not query.strip().upper().startswith('SELECT')."""
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "run_query":
            continue

        for child in ast.walk(node):
            if not isinstance(child, ast.If):
                continue

            source = ast.unparse(child.test).replace('"', "'")
            normalized = source.replace(" ", "")
            if "notquery.strip().upper().startswith('SELECT')" in normalized:
                return True

    return False


def _find_describe_allowlist(module: ast.Module) -> bool:
    """Require dynamic allowlist in describe_table using SHOW TABLES + membership check."""
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "describe_table":
            continue

        has_show_tables = False
        has_membership_check = False

        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                if child.func.attr == "execute" and child.args:
                    arg0 = child.args[0]
                    if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                        if arg0.value.strip().upper() == "SHOW TABLES":
                            has_show_tables = True

            if isinstance(child, ast.Compare):
                if any(isinstance(op, (ast.NotIn, ast.In)) for op in child.ops):
                    left = ast.unparse(child.left) if hasattr(ast, "unparse") else ""
                    comparators = [ast.unparse(comp) if hasattr(ast, "unparse") else "" for comp in child.comparators]
                    joined = f"{left} {' '.join(comparators)}"
                    if "table_name" in joined and "allowed_tables" in joined:
                        has_membership_check = True

        return has_show_tables and has_membership_check

    return False


def _contains_all(text: str, snippets: Iterable[str]) -> bool:
    return all(snippet in text for snippet in snippets)


def evaluate(mysql_server_path: Path) -> List[GateCheck]:
    if not mysql_server_path.exists() or not mysql_server_path.is_file():
        return [
            GateCheck(
                name="mysql_mcp_server_exists",
                passed=False,
                detail=f"file not found: {mysql_server_path}",
            )
        ]

    raw = mysql_server_path.read_text(encoding="utf-8")
    module = ast.parse(raw)

    checks: List[GateCheck] = []

    checks.append(
        GateCheck(
            name="env_password_required",
            passed="_require_env(\"MYSQL_PASSWORD\")" in raw,
            detail="MYSQL_PASSWORD must be required from environment",
        )
    )

    checks.append(
        GateCheck(
            name="identifier_safety_helpers",
            passed=_has_function(module, "_is_safe_identifier") and _has_function(module, "_quote_identifier"),
            detail="identifier validation and quoting helpers must exist",
        )
    )

    checks.append(
        GateCheck(
            name="describe_table_allowlist",
            passed=_find_describe_allowlist(module),
            detail="describe_table must validate table_name against SHOW TABLES allowlist",
        )
    )

    checks.append(
        GateCheck(
            name="run_query_select_only",
            passed=_find_run_query_select_guard(module),
            detail="run_query must enforce SELECT-only guard",
        )
    )

    checks.append(
        GateCheck(
            name="sanitized_error_messages",
            passed=_contains_all(raw, ["def _sanitize_error_message", "Erro operacional no banco de dados"]),
            detail="sanitized operational error path must exist",
        )
    )

    return checks


def print_human_report(checks: List[GateCheck]) -> int:
    failures = [c for c in checks if not c.passed]

    print("=== MySQL MCP Hardening Gate ===")
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"{status} | {check.name} | {check.detail}")

    print("\n[Summary]")
    print(f"checked={len(checks)}")
    print(f"failed={len(failures)}")

    if failures:
        print("RESULT=FAIL")
        return 1

    print("RESULT=PASS")
    return 0


def build_json_report(checks: List[GateCheck]) -> dict:
    failures = [c for c in checks if not c.passed]
    return {
        "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in checks],
        "summary": {
            "checked": len(checks),
            "failed": len(failures),
            "result": "FAIL" if failures else "PASS",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Static gate for MySQL MCP hardening invariants")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root path. Default: auto-detect from script location.",
    )
    parser.add_argument("--json", action="store_true", help="Output report in JSON format")
    args = parser.parse_args()

    default_repo_root = Path(__file__).resolve().parents[2]
    repo_root = Path(args.repo_root).resolve() if args.repo_root else default_repo_root
    mysql_server_path = repo_root / ".mcp_servers" / "mysql_mcp_server.py"

    try:
        checks = evaluate(mysql_server_path)
    except Exception as exc:  # pragma: no cover - defensive gate behavior
        print(f"ERROR: gate execution failed: {exc}")
        return 2

    if args.json:
        print(json.dumps(build_json_report(checks), indent=2, ensure_ascii=False, sort_keys=True))
        return 1 if any(not c.passed for c in checks) else 0

    return print_human_report(checks)


if __name__ == "__main__":
    sys.exit(main())
