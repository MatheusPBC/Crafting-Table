#!/usr/bin/env python3
"""Import portable CLI stack package into target workspace with snapshot rollback."""

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


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def copy_path(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def import_stack(package_root: Path, target_root: Path) -> tuple[Path, Path]:
    manifest_path = package_root / "stack_manifest.json"
    payload_root = package_root / "payload"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found in package: {manifest_path}")
    if not payload_root.exists():
        raise FileNotFoundError(
            f"Payload directory not found in package: {payload_root}"
        )

    manifest = load_json(manifest_path)
    timestamp = utc_timestamp()

    snapshots_root = target_root / "platform" / "snapshots"
    snapshots_root.mkdir(parents=True, exist_ok=True)

    snapshot_dir = snapshots_root / f"snapshot_{timestamp}"
    snapshot_payload_dir = snapshot_dir / "payload"
    snapshot_payload_dir.mkdir(parents=True, exist_ok=True)

    snapshot_items: list[dict[str, Any]] = []
    imported_items: list[dict[str, Any]] = []

    for component in manifest["components"]:
        source_rel = Path(component["source"])
        target_rel = Path(component.get("target", component["source"]))
        required = bool(component.get("required", True))

        package_item_path = payload_root / target_rel
        target_path = target_root / target_rel
        snapshot_item_path = snapshot_payload_dir / target_rel

        exists_before = target_path.exists() or target_path.is_symlink()

        snapshot_entry = {
            "name": component.get("name", target_rel.as_posix()),
            "target": target_rel.as_posix(),
            "required": required,
            "existedBefore": exists_before,
        }

        if exists_before:
            copy_path(target_path, snapshot_item_path)

        if package_item_path.exists() or package_item_path.is_symlink():
            remove_path(target_path)
            copy_path(package_item_path, target_path)
            imported_items.append(
                {
                    "name": component.get("name", target_rel.as_posix()),
                    "target": target_rel.as_posix(),
                    "sourceInPackage": target_rel.as_posix(),
                }
            )
        elif required:
            raise FileNotFoundError(
                f"Required payload item not found: {package_item_path}"
            )

        snapshot_items.append(snapshot_entry)

    snapshot_metadata = {
        "timestamp": timestamp,
        "snapshotPath": str(snapshot_dir),
        "targetRoot": str(target_root),
        "sourcePackage": str(package_root),
        "items": snapshot_items,
    }
    snapshot_metadata_path = snapshot_dir / "snapshot_metadata.json"
    snapshot_metadata_path.write_text(
        json.dumps(snapshot_metadata, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    import_metadata = {
        "timestamp": timestamp,
        "targetRoot": str(target_root),
        "sourcePackage": str(package_root),
        "snapshotPath": str(snapshot_dir),
        "stackVersion": manifest.get("stackVersion"),
        "importedItems": imported_items,
    }
    import_metadata_path = snapshots_root / f"import_{timestamp}.json"
    import_metadata_path.write_text(
        json.dumps(import_metadata, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    print(f"Import completed into target: {target_root}")
    print(f"Snapshot created: {snapshot_dir}")
    print(f"Import metadata: {import_metadata_path}")
    return snapshot_dir, import_metadata_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Import portable CLI stack package")
    parser.add_argument(
        "--package", required=True, help="Path to exported package directory"
    )
    parser.add_argument(
        "--target-root",
        default=".",
        help="Target workspace root where package should be applied",
    )
    args = parser.parse_args()

    package_root = Path(args.package).resolve()
    target_root = Path(args.target_root).resolve()

    try:
        import_stack(package_root=package_root, target_root=target_root)
    except Exception as exc:
        print(f"ERROR: import failed: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
