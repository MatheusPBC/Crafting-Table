#!/usr/bin/env python3
"""Deterministic gate for portable CLI stack structure."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_doctor(repo_root: Path) -> tuple[int, str, str]:
    doctor_script = repo_root / "platform" / "scripts" / "doctor_stack.py"

    if not doctor_script.exists():
        return 1, "", f"doctor script not found: {doctor_script}"

    cmd = [
        sys.executable,
        str(doctor_script),
        "--repo-root",
        str(repo_root),
        "--json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.returncode, result.stdout, result.stderr


def parse_doctor_stdout(stdout: str) -> dict[str, Any]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return {
            "checks": [],
            "summary": {
                "checked": 0,
                "failed": 1,
                "result": "FAIL",
            },
            "error": "invalid_json_output_from_doctor",
        }
    return payload


def print_human_report(payload: dict[str, Any]) -> int:
    checks = payload.get("checks", [])
    summary = payload.get("summary", {})

    print("=== Portable Stack Gate ===")
    for check in checks:
        status = "PASS" if check.get("passed") else "FAIL"
        print(f"{status} | {check.get('name')} | {check.get('detail')}")

    print("\n[Summary]")
    print(f"checked={summary.get('checked', 0)}")
    print(f"failed={summary.get('failed', 0)}")
    print(f"RESULT={summary.get('result', 'FAIL')}")
    return 0 if summary.get("result") == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Portable stack validation gate")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root path. Default: auto-detect from script location.",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    default_repo_root = Path(__file__).resolve().parents[2]
    repo_root = Path(args.repo_root).resolve() if args.repo_root else default_repo_root

    try:
        return_code, stdout, stderr = run_doctor(repo_root)
    except Exception as exc:  # pragma: no cover - defensive execution path
        print(f"ERROR: portable stack gate failed: {exc}")
        return 2

    payload = parse_doctor_stdout(stdout)

    if stderr:
        payload["doctor_stderr"] = stderr.strip()

    if return_code != 0:
        summary = payload.setdefault("summary", {})
        summary["result"] = "FAIL"

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True))
        return 0 if payload.get("summary", {}).get("result") == "PASS" else 1

    return print_human_report(payload)


if __name__ == "__main__":
    sys.exit(main())
