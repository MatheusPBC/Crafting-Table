#!/usr/bin/env python3
"""Validate portable stack manifest and required stack infrastructure."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SEMVER_REGEX = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
EXPECTED_PRECEDENCE = ["base", "overlay", "local"]


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def is_safe_relative_path(value: str) -> bool:
    path = Path(value)
    if path.is_absolute():
        return False
    for part in path.parts:
        if part in {"", ".", ".."}:
            return False
    return True


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(repo_root: Path, manifest_path: Path) -> list[CheckResult]:
    results: list[CheckResult] = []

    if not manifest_path.exists():
        return [
            CheckResult(
                "manifest_exists", False, f"Manifest not found: {manifest_path}"
            )
        ]

    try:
        manifest = load_manifest(manifest_path)
    except Exception as exc:
        return [
            CheckResult("manifest_valid_json", False, f"Invalid manifest JSON: {exc}")
        ]

    required_fields = [
        "manifestVersion",
        "stackVersion",
        "components",
        "precedencePolicy",
        "credentialsPolicy",
    ]

    for field in required_fields:
        results.append(
            CheckResult(
                name=f"manifest_field_{field}",
                passed=field in manifest,
                detail=f"Field '{field}' must exist",
            )
        )

    stack_version = str(manifest.get("stackVersion", ""))
    results.append(
        CheckResult(
            name="manifest_stack_semver",
            passed=bool(SEMVER_REGEX.match(stack_version)),
            detail="stackVersion must match basic semver",
        )
    )

    precedence_policy = manifest.get("precedencePolicy")
    results.append(
        CheckResult(
            name="manifest_precedence_policy",
            passed=precedence_policy == EXPECTED_PRECEDENCE,
            detail="precedencePolicy must be ['base', 'overlay', 'local']",
        )
    )

    credentials_policy = manifest.get("credentialsPolicy", {})
    credentials_ok = (
        isinstance(credentials_policy, dict)
        and credentials_policy.get("repositoryVisibility") == "private"
        and credentials_policy.get("versionedCredentials") is True
        and credentials_policy.get("exportIncludesCredentialsByDefault") is True
    )
    results.append(
        CheckResult(
            name="manifest_credentials_policy",
            passed=credentials_ok,
            detail="credentialsPolicy must indicate private repo + versioned credentials",
        )
    )

    components = manifest.get("components", [])
    results.append(
        CheckResult(
            name="manifest_components_non_empty",
            passed=isinstance(components, list) and len(components) > 0,
            detail="components must be a non-empty list",
        )
    )

    if isinstance(components, list):
        for index, component in enumerate(components):
            if not isinstance(component, dict):
                results.append(
                    CheckResult(
                        name=f"component_{index}_shape",
                        passed=False,
                        detail="Component must be an object",
                    )
                )
                continue

            source = str(component.get("source", ""))
            target = str(component.get("target", source))
            required = bool(component.get("required", True))

            results.append(
                CheckResult(
                    name=f"component_{index}_safe_source",
                    passed=is_safe_relative_path(source),
                    detail=f"Component source must be safe relative path: {source}",
                )
            )
            results.append(
                CheckResult(
                    name=f"component_{index}_safe_target",
                    passed=is_safe_relative_path(target),
                    detail=f"Component target must be safe relative path: {target}",
                )
            )

            source_path = repo_root / source
            exists = source_path.exists()
            if required:
                results.append(
                    CheckResult(
                        name=f"component_{index}_exists_required",
                        passed=exists,
                        detail=f"Required component must exist: {source}",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        name=f"component_{index}_exists_optional",
                        passed=True,
                        detail=(
                            f"Optional component {'exists' if exists else 'missing'}: {source}"
                        ),
                    )
                )

    return results


def validate_structure(repo_root: Path) -> list[CheckResult]:
    required_paths = {
        "script_export_stack": repo_root / "platform" / "scripts" / "export_stack.py",
        "script_import_stack": repo_root / "platform" / "scripts" / "import_stack.py",
        "script_doctor_stack": repo_root / "platform" / "scripts" / "doctor_stack.py",
        "script_rollback_stack": repo_root
        / "platform"
        / "scripts"
        / "rollback_stack.py",
        "directory_exports": repo_root / "platform" / "exports",
        "directory_snapshots": repo_root / "platform" / "snapshots",
    }

    results: list[CheckResult] = []
    for name, path in required_paths.items():
        results.append(
            CheckResult(
                name=name,
                passed=path.exists(),
                detail=f"Path must exist: {path}",
            )
        )

    return results


def print_human(results: list[CheckResult]) -> int:
    failures = [item for item in results if not item.passed]

    print("=== Portable Stack Doctor ===")
    for item in results:
        status = "PASS" if item.passed else "FAIL"
        print(f"{status} | {item.name} | {item.detail}")

    print("\n[Summary]")
    print(f"checked={len(results)}")
    print(f"failed={len(failures)}")
    print(f"RESULT={'PASS' if not failures else 'FAIL'}")
    return 0 if not failures else 1


def build_json_report(results: list[CheckResult]) -> dict[str, Any]:
    failures = [item for item in results if not item.passed]
    return {
        "checks": [
            {"name": item.name, "passed": item.passed, "detail": item.detail}
            for item in results
        ],
        "summary": {
            "checked": len(results),
            "failed": len(failures),
            "result": "PASS" if not failures else "FAIL",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate portable CLI stack structure"
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root path. Default: auto-detect from script location.",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    default_repo_root = Path(__file__).resolve().parents[2]
    repo_root = Path(args.repo_root).resolve() if args.repo_root else default_repo_root
    manifest_path = repo_root / "platform" / "manifests" / "stack_manifest.json"

    results = []
    results.extend(validate_manifest(repo_root=repo_root, manifest_path=manifest_path))
    results.extend(validate_structure(repo_root=repo_root))

    if args.json:
        print(
            json.dumps(
                build_json_report(results), indent=2, ensure_ascii=True, sort_keys=True
            )
        )
        return 0 if all(item.passed for item in results) else 1

    return print_human(results)


if __name__ == "__main__":
    sys.exit(main())
