#!/usr/bin/env python3
"""Rollback target workspace to previous state using stack snapshots."""

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


def select_snapshot(snapshots_root: Path, snapshot_arg: str | None) -> Path:
    if snapshot_arg:
        candidate = Path(snapshot_arg)
        if candidate.is_absolute():
            return candidate
        return snapshots_root / candidate

    candidates = sorted(
        [path for path in snapshots_root.glob("snapshot_*") if path.is_dir()],
        key=lambda path: path.name,
    )
    if not candidates:
        raise FileNotFoundError(f"No snapshots found in: {snapshots_root}")
    return candidates[-1]


def rollback_stack(target_root: Path, snapshot_arg: str | None) -> Path:
    snapshots_root = target_root / "platform" / "snapshots"
    if not snapshots_root.exists():
        raise FileNotFoundError(f"Snapshots directory not found: {snapshots_root}")

    snapshot_dir = select_snapshot(snapshots_root, snapshot_arg)
    metadata_path = snapshot_dir / "snapshot_metadata.json"
    payload_root = snapshot_dir / "payload"

    if not metadata_path.exists():
        raise FileNotFoundError(f"Snapshot metadata not found: {metadata_path}")
    if not payload_root.exists():
        raise FileNotFoundError(f"Snapshot payload not found: {payload_root}")

    metadata = load_json(metadata_path)

    for item in metadata.get("items", []):
        target_rel = Path(item["target"])
        existed_before = bool(item.get("existedBefore", False))

        target_path = target_root / target_rel
        snapshot_item_path = payload_root / target_rel

        remove_path(target_path)

        if existed_before:
            if not snapshot_item_path.exists() and not snapshot_item_path.is_symlink():
                raise FileNotFoundError(f"Snapshot payload missing for {target_rel}")
            copy_path(snapshot_item_path, target_path)

    rollback_record = {
        "timestamp": utc_timestamp(),
        "targetRoot": str(target_root),
        "restoredFromSnapshot": str(snapshot_dir),
    }
    rollback_record_path = (
        snapshots_root / f"rollback_{rollback_record['timestamp']}.json"
    )
    rollback_record_path.write_text(
        json.dumps(rollback_record, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    print(f"Rollback completed from snapshot: {snapshot_dir}")
    print(f"Rollback metadata: {rollback_record_path}")
    return snapshot_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Rollback portable CLI stack import")
    parser.add_argument(
        "--target-root",
        default=".",
        help="Target workspace root where rollback is applied",
    )
    parser.add_argument(
        "--snapshot",
        default=None,
        help="Snapshot directory name or absolute path. Default: latest snapshot",
    )
    args = parser.parse_args()

    target_root = Path(args.target_root).resolve()

    try:
        rollback_stack(target_root=target_root, snapshot_arg=args.snapshot)
    except Exception as exc:
        print(f"ERROR: rollback failed: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
