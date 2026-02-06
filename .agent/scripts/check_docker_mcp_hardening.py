#!/usr/bin/env python3
"""Deterministic hardening gate for `.mcp_servers/docker_mcp_server.py`.

Runs static checks only (no Docker daemon dependency) and returns non-zero exit
code when required hardening invariants are missing.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class GateCheck:
    name: str
    passed: bool
    detail: str


def _has_function(module: ast.Module, function_name: str) -> bool:
    return any(isinstance(node, ast.FunctionDef) and node.name == function_name for node in module.body)


def _normalized_source(node: ast.AST) -> str:
    return ast.unparse(node).replace("\n", "").replace(" ", "")


def _contains_all(text: str, snippets: List[str]) -> bool:
    return all(snippet in text for snippet in snippets)


def _find_load_config_limits(module: ast.Module) -> bool:
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "_load_config":
            continue

        normalized = _normalized_source(node)
        required_fragments = [
            "DOCKER_MCP_TIMEOUT_SECONDS",
            "DOCKER_MCP_LIST_LIMIT",
            "DOCKER_MCP_LIST_INCLUDE_STOPPED",
            "DOCKER_MCP_LOG_TAIL_DEFAULT",
            "DOCKER_MCP_LOG_TAIL_MAX",
            "DOCKER_MCP_MAX_LOG_CHARS",
            "DOCKER_MCP_MAX_IMAGE_CHARS",
            "DOCKER_MCP_ALLOWED_CONTAINER_PATTERN",
            "ifconfig.log_tail_default>config.log_tail_max",
        ]
        return all(fragment in normalized for fragment in required_fragments)

    return False


def _find_identifier_validation(module: ast.Module) -> bool:
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "_validate_container_identifier":
            continue

        normalized = _normalized_source(node)
        required_fragments = [
            "isinstance(container_name,str)",
            "normalized=container_name.strip()",
            "len(normalized)>128",
            "_CONTAINER_IDENTIFIER_REGEX.fullmatch(normalized)",
            "_ALLOWED_CONTAINER_REGEX.fullmatch(normalized)",
        ]
        return all(fragment in normalized for fragment in required_fragments)

    return False


def _find_tail_normalization(module: ast.Module) -> bool:
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "_normalize_tail":
            continue

        normalized = _normalized_source(node)
        required_fragments = [
            "isinstance(tail,bool)ornotisinstance(tail,int)",
            "_clamp_int(tail,1,CONFIG.log_tail_max)",
        ]
        return all(fragment in normalized for fragment in required_fragments)

    return False


def _find_list_containers_guards(module: ast.Module) -> bool:
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "list_containers":
            continue

        normalized = _normalized_source(node)
        required_fragments = [
            "client.containers.list(all=CONFIG.list_include_stopped)",
            "len(all_containers)>CONFIG.list_limit",
            "_truncate_text(str(c.image),CONFIG.max_image_chars)",
            "except(APIError,DockerException,OSError,TimeoutError)",
            "_error_payload('DOCKER_UNAVAILABLE'",
            "finally:",
            "client.close()",
        ]
        return all(fragment in normalized for fragment in required_fragments)

    return False


def _find_get_logs_guards(module: ast.Module) -> bool:
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "get_logs":
            continue

        normalized = _normalized_source(node)
        required_fragments = [
            "normalized_container_name=_validate_container_identifier(container_name)",
            "safe_tail=_normalize_tail(tailiftailisnotNoneelseCONFIG.log_tail_default)",
            "container=client.containers.get(normalized_container_name)",
            "iflen(logs_text)>CONFIG.max_log_chars",
            "exceptValueError:",
            "exceptNotFound:",
            "except(APIError,DockerException,OSError,TimeoutError):",
            "_error_payload('INVALID_ARGUMENT'",
            "_error_payload('CONTAINER_NOT_FOUND'",
            "_error_payload('DOCKER_UNAVAILABLE'",
            "finally:",
            "client.close()",
        ]
        return all(fragment in normalized for fragment in required_fragments)

    return False


def evaluate(docker_server_path: Path) -> List[GateCheck]:
    if not docker_server_path.exists() or not docker_server_path.is_file():
        return [
            GateCheck(
                name="docker_mcp_server_exists",
                passed=False,
                detail=f"file not found: {docker_server_path}",
            )
        ]

    raw = docker_server_path.read_text(encoding="utf-8")
    module = ast.parse(raw)

    checks: List[GateCheck] = []

    checks.append(
        GateCheck(
            name="config_and_env_clamps",
            passed=(
                _has_function(module, "_clamp_int")
                and _has_function(module, "_get_env_int")
                and _has_function(module, "_get_env_bool")
                and _find_load_config_limits(module)
            ),
            detail="config loader must enforce env-based clamps and policy pattern",
        )
    )

    checks.append(
        GateCheck(
            name="container_identifier_validation",
            passed=(
                "_CONTAINER_IDENTIFIER_REGEX = re.compile" in raw
                and _find_identifier_validation(module)
            ),
            detail="container_name must be validated by syntax + policy regex",
        )
    )

    checks.append(
        GateCheck(
            name="allowed_pattern_fallback",
            passed=_contains_all(
                raw,
                [
                    "_ALLOWED_CONTAINER_REGEX = re.compile(CONFIG.allowed_container_pattern)",
                    "except re.error:",
                    "falling back to safe default pattern",
                    "_ALLOWED_CONTAINER_REGEX = re.compile(r\"^[a-zA-Z0-9_.-]+$\")",
                ],
            ),
            detail="invalid allowed-container regex must fall back to safe default",
        )
    )

    checks.append(
        GateCheck(
            name="tail_normalization",
            passed=_find_tail_normalization(module),
            detail="tail input must reject non-int/bool and clamp to CONFIG.log_tail_max",
        )
    )

    checks.append(
        GateCheck(
            name="list_containers_resilience",
            passed=_find_list_containers_guards(module),
            detail="list_containers must enforce limits, sanitize output, map daemon errors, and close client",
        )
    )

    checks.append(
        GateCheck(
            name="get_logs_resilience",
            passed=_find_get_logs_guards(module),
            detail="get_logs must validate inputs, cap output, map errors, and close client",
        )
    )

    return checks


def print_human_report(checks: List[GateCheck]) -> int:
    failures = [c for c in checks if not c.passed]

    print("=== Docker MCP Hardening Gate ===")
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
    parser = argparse.ArgumentParser(description="Static gate for Docker MCP hardening invariants")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root path. Default: auto-detect from script location.",
    )
    parser.add_argument("--json", action="store_true", help="Output report in JSON format")
    args = parser.parse_args()

    default_repo_root = Path(__file__).resolve().parents[2]
    repo_root = Path(args.repo_root).resolve() if args.repo_root else default_repo_root
    docker_server_path = repo_root / ".mcp_servers" / "docker_mcp_server.py"

    try:
        checks = evaluate(docker_server_path)
    except Exception as exc:  # pragma: no cover - defensive gate behavior
        print(f"ERROR: gate execution failed: {exc}")
        return 2

    if args.json:
        print(json.dumps(build_json_report(checks), indent=2, ensure_ascii=False, sort_keys=True))
        return 1 if any(not c.passed for c in checks) else 0

    return print_human_report(checks)


if __name__ == "__main__":
    sys.exit(main())

