#!/usr/bin/env python3
"""Baseline anti-drift checker between `.agent/` and `.kilocode/`.

Compares an explicit set of mirrored critical files using SHA-256 hashes,
reports missing/divergent files, and returns non-zero exit code on
critical drift.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal


Severity = Literal["critical", "optional"]

FAIL_STATUSES = {"MISSING", "DIFF"}


@dataclass(frozen=True)
class MirrorPath:
    relative_path: str
    diff_severity: Severity = "critical"
    missing_severity: Severity = "critical"


MIRROR_PATHS: List[MirrorPath] = [
    MirrorPath(
        "ARCHITECTURE.md",
        diff_severity="critical",
        missing_severity="critical",
    ),
    MirrorPath(
        "rules/GEMINI.md",
        diff_severity="critical",
        missing_severity="optional",
    ),
    MirrorPath(
        "skills/intelligent-routing/SKILL.md",
        diff_severity="critical",
        missing_severity="optional",
    ),
    MirrorPath(
        "skills/parallel-agents/SKILL.md",
        diff_severity="critical",
        missing_severity="optional",
    ),
    MirrorPath(
        "skills/plan-writing/SKILL.md",
        diff_severity="critical",
        missing_severity="optional",
    ),
]

EXTRA_SCOPES = [
    "rules",
    "skills/intelligent-routing",
    "skills/parallel-agents",
    "skills/plan-writing",
]


@dataclass
class CheckResult:
    relative_path: str
    status: str
    severity: Severity
    detail: str

    @property
    def critical(self) -> bool:
        return self.severity == "critical"


def sha256_file(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def collect_scope_files(base_dir: Path, scope: str) -> List[str]:
    scope_path = base_dir / scope

    if not scope_path.exists():
        return []

    if scope_path.is_file():
        return [scope]

    files = [
        str(path.relative_to(base_dir)).replace("\\", "/")
        for path in scope_path.rglob("*")
        if path.is_file()
    ]
    return sorted(files)


def compare_mirror_paths(agent_root: Path, kilocode_root: Path) -> List[CheckResult]:
    results: List[CheckResult] = []

    for target in MIRROR_PATHS:
        rel = target.relative_path
        agent_file = agent_root / rel
        kilo_file = kilocode_root / rel

        in_agent = agent_file.exists()
        in_kilo = kilo_file.exists()

        if not in_agent or not in_kilo:
            missing_side = []
            if not in_agent:
                missing_side.append(".agent")
            if not in_kilo:
                missing_side.append(".kilocode")

            results.append(
                CheckResult(
                    relative_path=rel,
                    status="MISSING",
                    severity=target.missing_severity,
                    detail=f"missing in {', '.join(missing_side)}",
                )
            )
            continue

        agent_hash = sha256_file(agent_file)
        kilo_hash = sha256_file(kilo_file)

        if agent_hash == kilo_hash:
            results.append(
                CheckResult(
                    relative_path=rel,
                    status="OK",
                    severity=target.diff_severity,
                    detail=f"sha256={agent_hash}",
                )
            )
        else:
            results.append(
                CheckResult(
                    relative_path=rel,
                    status="DIFF",
                    severity=target.diff_severity,
                    detail=f".agent={agent_hash} .kilocode={kilo_hash}",
                )
            )

    return results


def collect_optional_extras(agent_root: Path, kilocode_root: Path) -> Dict[str, List[str]]:
    explicit_paths = {target.relative_path for target in MIRROR_PATHS}

    only_in_agent: List[str] = []
    only_in_kilocode: List[str] = []

    for scope in EXTRA_SCOPES:
        agent_files = set(collect_scope_files(agent_root, scope))
        kilo_files = set(collect_scope_files(kilocode_root, scope))

        for rel_path in sorted(agent_files - kilo_files):
            if rel_path not in explicit_paths:
                only_in_agent.append(rel_path)

        for rel_path in sorted(kilo_files - agent_files):
            if rel_path not in explicit_paths:
                only_in_kilocode.append(rel_path)

    return {
        "only_in_agent": sorted(set(only_in_agent)),
        "only_in_kilocode": sorted(set(only_in_kilocode)),
    }


def summarize_results(results: List[CheckResult], extras: Dict[str, List[str]]) -> Dict[str, object]:
    checked_by_severity = {
        "critical": len([r for r in results if r.severity == "critical"]),
        "optional": len([r for r in results if r.severity == "optional"]),
    }
    failures_by_severity = {
        "critical": len([r for r in results if r.severity == "critical" and r.status in FAIL_STATUSES]),
        "optional": len([r for r in results if r.severity == "optional" and r.status in FAIL_STATUSES]),
    }
    optional_extras = len(extras["only_in_agent"]) + len(extras["only_in_kilocode"])
    result = "FAIL" if failures_by_severity["critical"] else "PASS"

    return {
        "checked": len(results),
        "checked_by_severity": checked_by_severity,
        "failures_by_severity": failures_by_severity,
        "critical_failures": failures_by_severity["critical"],
        "optional_missing_or_diff": failures_by_severity["optional"],
        "optional_extras": optional_extras,
        "optional_findings_total": failures_by_severity["optional"] + optional_extras,
        "result": result,
    }


def print_human_report(results: List[CheckResult], extras: Dict[str, List[str]]) -> int:
    summary = summarize_results(results, extras)

    print("=== Anti-Drift Baseline Check (.agent ↔ .kilocode) ===")
    print("\n[Mirrored rules]")

    for result in results:
        level = result.severity.upper()

        if result.status == "OK":
            print(f"PASS  | {result.relative_path} | {level} | {result.status}")
            continue

        print(f"FAIL  | {result.relative_path} | {level} | {result.status} | {result.detail}")

    print("\n[Optional extras in monitored scopes]")

    if extras["only_in_agent"]:
        print("ONLY .agent:")
        for rel_path in extras["only_in_agent"]:
            print(f"  - {rel_path}")
    else:
        print("ONLY .agent: none")

    if extras["only_in_kilocode"]:
        print("ONLY .kilocode:")
        for rel_path in extras["only_in_kilocode"]:
            print(f"  - {rel_path}")
    else:
        print("ONLY .kilocode: none")

    print("\n[Summary]")
    print(f"checked={summary['checked']}")
    print(
        "checked_by_severity="
        f"critical:{summary['checked_by_severity']['critical']} "
        f"optional:{summary['checked_by_severity']['optional']}"
    )
    print(
        "failures_by_severity="
        f"critical:{summary['failures_by_severity']['critical']} "
        f"optional:{summary['failures_by_severity']['optional']}"
    )
    print(f"critical_failures={summary['critical_failures']}")
    print(f"optional_missing_or_diff={summary['optional_missing_or_diff']}")
    print(f"optional_extras={summary['optional_extras']}")
    print(f"optional_findings_total={summary['optional_findings_total']}")

    print(f"RESULT={summary['result']}")
    return 1 if summary["result"] == "FAIL" else 0


def build_json_report(results: List[CheckResult], extras: Dict[str, List[str]]) -> Dict[str, object]:
    summary = summarize_results(results, extras)

    return {
        "results": [
            {
                "relative_path": r.relative_path,
                "status": r.status,
                "severity": r.severity,
                "critical": r.critical,
                "detail": r.detail,
            }
            for r in results
        ],
        "extras": extras,
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect anti-drift baseline between .agent and .kilocode")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root path. Default: auto-detect from script location.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report in JSON format.",
    )

    args = parser.parse_args()

    default_repo_root = Path(__file__).resolve().parents[2]
    repo_root = Path(args.repo_root).resolve() if args.repo_root else default_repo_root

    agent_root = repo_root / ".agent"
    kilocode_root = repo_root / ".kilocode"

    if not agent_root.exists() or not kilocode_root.exists():
        missing = []
        if not agent_root.exists():
            missing.append(str(agent_root))
        if not kilocode_root.exists():
            missing.append(str(kilocode_root))
        print(f"ERROR: base directories not found: {', '.join(missing)}")
        return 2

    results = compare_mirror_paths(agent_root, kilocode_root)
    extras = collect_optional_extras(agent_root, kilocode_root)

    if args.json:
        report = build_json_report(results, extras)
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
        return 1 if report["summary"]["result"] == "FAIL" else 0

    return print_human_report(results, extras)


if __name__ == "__main__":
    sys.exit(main())
