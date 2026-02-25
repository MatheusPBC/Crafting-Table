#!/usr/bin/env python3
"""Export portable CLI stack package from manifest-defined components."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def copy_path(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def export_stack(repo_root: Path, manifest_path: Path, output_dir: Path) -> Path:
    manifest = load_manifest(manifest_path)
    stack_version = str(manifest["stackVersion"])
    timestamp = utc_timestamp()

    package_name = f"stack_v{stack_version}_{timestamp}"
    package_root = output_dir / package_name
    payload_root = package_root / "payload"

    output_dir.mkdir(parents=True, exist_ok=True)
    payload_root.mkdir(parents=True, exist_ok=True)

    items: list[dict[str, Any]] = []
    copied_count = 0

    for component in manifest["components"]:
        source_rel = Path(component["source"])
        target_rel = Path(component.get("target", component["source"]))
        required = bool(component.get("required", True))

        source_abs = repo_root / source_rel
        payload_target = payload_root / target_rel

        item = {
            "name": component.get("name", source_rel.as_posix()),
            "source": source_rel.as_posix(),
            "target": target_rel.as_posix(),
            "required": required,
            "exists": source_abs.exists(),
        }

        if source_abs.exists():
            copy_path(source_abs, payload_target)
            copied_count += 1
        elif required:
            raise FileNotFoundError(f"Required component not found: {source_abs}")

        items.append(item)

    manifest_copy_path = package_root / "stack_manifest.json"
    shutil.copy2(manifest_path, manifest_copy_path)

    metadata = {
        "timestamp": timestamp,
        "stackVersion": stack_version,
        "sourceRepoRoot": str(repo_root),
        "manifestPath": str(manifest_path),
        "packagePath": str(package_root),
        "includesCredentialsByDefault": True,
        "items": items,
    }

    metadata_path = package_root / "package_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    print(f"Export package created: {package_root}")
    print(f"Components copied: {copied_count}")
    print(f"Metadata: {metadata_path}")
    return package_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Export portable CLI stack package")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root path. Default: auto-detect from script location.",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Manifest path. Default: <repo-root>/platform/manifests/stack_manifest.json",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory. Default: <repo-root>/platform/exports",
    )
    args = parser.parse_args()

    default_repo_root = Path(__file__).resolve().parents[2]
    repo_root = Path(args.repo_root).resolve() if args.repo_root else default_repo_root
    manifest_path = (
        Path(args.manifest).resolve()
        if args.manifest
        else repo_root / "platform" / "manifests" / "stack_manifest.json"
    )
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else repo_root / "platform" / "exports"
    )

    try:
        export_stack(
            repo_root=repo_root, manifest_path=manifest_path, output_dir=output_dir
        )
    except Exception as exc:
        print(f"ERROR: export failed: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
