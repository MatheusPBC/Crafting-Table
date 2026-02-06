#!/usr/bin/env python3
"""Deterministic hardening gate for `.mcp_servers/aws_mcp_server.py`.

Runs static checks only (no AWS/network dependency) and returns non-zero exit
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


def _normalized_source(node: ast.AST) -> str:
    return ast.unparse(node).replace("\n", "").replace(" ", "")


def _get_top_level_constant(module: ast.Module, constant_name: str) -> int | None:
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == constant_name:
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
                        return node.value.value
    return None


def _find_set_members(module: ast.Module, constant_name: str) -> set[str] | None:
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if constant_name not in targets:
            continue

        if isinstance(node.value, ast.Set):
            values: set[str] = set()
            for element in node.value.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    values.add(element.value)
            return values
    return None


def _find_client_guards(module: ast.Module) -> bool:
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "_client":
            continue

        normalized = _normalized_source(node)
        has_allowlist_guard = "service_namenotinALLOWED_SERVICES" in normalized
        has_session_error_guard = "SESSION_INIT_ERRORisnotNone" in normalized
        has_session_none_guard = "SESSIONisNone" in normalized
        has_client_config = "SESSION.client(service_name,config=BOTO_CLIENT_CONFIG)" in normalized

        return has_allowlist_guard and has_session_error_guard and has_session_none_guard and has_client_config

    return False


def _find_exception_sanitizer_branches(module: ast.Module) -> bool:
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "_sanitize_exception":
            continue

        normalized = _normalized_source(node)
        required_fragments = [
            "isinstance(exc,(NoCredentialsError,PartialCredentialsError))",
            "isinstance(exc,ProfileNotFound)",
            "isinstance(exc,ClientError)",
            "isinstance(exc,BotoCoreError)",
            "logger.exception",
        ]
        return all(fragment in normalized for fragment in required_fragments)

    return False


def _find_validate_function_name_logic(module: ast.Module) -> bool:
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "_validate_function_name":
            continue

        normalized = _normalized_source(node)
        required_fragments = [
            "isinstance(function_name,str)",
            "normalized=function_name.strip()",
            "FUNCTION_NAME_REGEX.fullmatch(normalized)",
        ]
        return all(fragment in normalized for fragment in required_fragments)

    return False


def _find_lambda_get_function_validation(module: ast.Module) -> bool:
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "lambda_get_function":
            continue

        normalized = _normalized_source(node)
        return "validated_name=_validate_function_name(function_name)" in normalized

    return False


def _find_lambda_pagination_caps(module: ast.Module) -> bool:
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "lambda_list_functions":
            continue

        normalized = _normalized_source(node)
        return "pages_seen>SETTINGS.max_pages" in normalized and "len(all_funcs)>=SETTINGS.max_items" in normalized

    return False


def _find_dynamodb_pagination_caps(module: ast.Module) -> bool:
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "dynamodb_list_tables":
            continue

        normalized = _normalized_source(node)
        required_fragments = [
            "whilepages_seen<SETTINGS.max_pagesandlen(table_names)<SETTINGS.max_items",
            "request={'Limit':SETTINGS.page_size}",
        ]
        return all(fragment in normalized for fragment in required_fragments)

    return False


def _contains_all(text: str, snippets: Iterable[str]) -> bool:
    return all(snippet in text for snippet in snippets)


def evaluate(aws_server_path: Path) -> List[GateCheck]:
    if not aws_server_path.exists() or not aws_server_path.is_file():
        return [
            GateCheck(
                name="aws_mcp_server_exists",
                passed=False,
                detail=f"file not found: {aws_server_path}",
            )
        ]

    raw = aws_server_path.read_text(encoding="utf-8")
    module = ast.parse(raw)

    checks: List[GateCheck] = []

    checks.append(
        GateCheck(
            name="hard_caps_constants",
            passed=(
                _get_top_level_constant(module, "MAX_ITEMS_HARD_CAP") == 500
                and _get_top_level_constant(module, "MAX_PAGES_HARD_CAP") == 50
            ),
            detail="MAX_ITEMS_HARD_CAP=500 and MAX_PAGES_HARD_CAP=50 must be present",
        )
    )

    checks.append(
        GateCheck(
            name="validated_settings_loader",
            passed=(
                _has_function(module, "_load_settings")
                and _contains_all(
                    raw,
                    [
                        "AWS_REGION_REGEX",
                        "AWS_PROFILE_REGEX",
                        "AWS_MCP_MAX_ITEMS",
                        "AWS_MCP_MAX_PAGES",
                        "AWS_MCP_PAGE_SIZE",
                    ],
                )
            ),
            detail="settings loader must validate region/profile and clamp env limits",
        )
    )

    checks.append(
        GateCheck(
            name="allowed_services_whitelist",
            passed=_find_set_members(module, "ALLOWED_SERVICES") == {"s3", "lambda", "dynamodb"},
            detail="ALLOWED_SERVICES must restrict clients to s3/lambda/dynamodb",
        )
    )

    checks.append(
        GateCheck(
            name="client_guards_and_timeouts",
            passed=(
                _find_client_guards(module)
                and _contains_all(
                    raw,
                    [
                        "BOTO_CLIENT_CONFIG = BotoConfig(",
                        "connect_timeout=3",
                        "read_timeout=8",
                        'retries={"max_attempts": 3, "mode": "standard"}',
                    ],
                )
            ),
            detail="_client must enforce allowlist/session guards and use bounded BotoConfig",
        )
    )

    checks.append(
        GateCheck(
            name="sanitized_exception_paths",
            passed=_find_exception_sanitizer_branches(module),
            detail="_sanitize_exception must map credential/profile/client/botocore errors",
        )
    )

    checks.append(
        GateCheck(
            name="function_name_validation",
            passed=(
                "FUNCTION_NAME_REGEX = re.compile" in raw
                and _find_validate_function_name_logic(module)
                and _find_lambda_get_function_validation(module)
            ),
            detail="lambda_get_function must validate function_name via regex-backed helper",
        )
    )

    checks.append(
        GateCheck(
            name="pagination_caps_enforced",
            passed=_find_lambda_pagination_caps(module) and _find_dynamodb_pagination_caps(module),
            detail="lambda/dynamodb listing flows must enforce SETTINGS.max_pages/max_items caps",
        )
    )

    return checks


def print_human_report(checks: List[GateCheck]) -> int:
    failures = [c for c in checks if not c.passed]

    print("=== AWS MCP Hardening Gate ===")
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
    parser = argparse.ArgumentParser(description="Static gate for AWS MCP hardening invariants")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root path. Default: auto-detect from script location.",
    )
    parser.add_argument("--json", action="store_true", help="Output report in JSON format")
    args = parser.parse_args()

    default_repo_root = Path(__file__).resolve().parents[2]
    repo_root = Path(args.repo_root).resolve() if args.repo_root else default_repo_root
    aws_server_path = repo_root / ".mcp_servers" / "aws_mcp_server.py"

    try:
        checks = evaluate(aws_server_path)
    except Exception as exc:  # pragma: no cover - defensive gate behavior
        print(f"ERROR: gate execution failed: {exc}")
        return 2

    if args.json:
        print(json.dumps(build_json_report(checks), indent=2, ensure_ascii=False, sort_keys=True))
        return 1 if any(not c.passed for c in checks) else 0

    return print_human_report(checks)


if __name__ == "__main__":
    sys.exit(main())

