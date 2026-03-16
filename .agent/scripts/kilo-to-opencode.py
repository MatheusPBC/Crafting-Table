#!/usr/bin/env python3
"""
Kilo CLI -> OpenCode Session Migration Script

Migrates sessions, messages, and parts from Kilo CLI storage format
to OpenCode-compatible storage format (JSON files + SQLite database).

Usage:
    python kilo-to-opencode.py --dry-run                    # Preview migration
    python kilo-to-opencode.py --session ses_XXX            # Migrate single session
    python kilo-to-opencode.py --all                        # Migrate all sessions
    python kilo-to-opencode.py --all --backup               # Migrate with backup
"""

import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


KILO_STORAGE = Path.home() / ".local" / "share" / "kilo" / "storage"
OPENCODE_STORAGE = Path.home() / ".local" / "share" / "opencode" / "storage"
OPENCODE_DB = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
BACKUP_DIR = Path.home() / ".local" / "share" / "opencode" / "backups"


def log(msg: str, level: str = "INFO") -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def read_json_file(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(path: Path, data: Dict[str, Any], dry_run: bool = False) -> bool:
    if dry_run:
        log(f"  [dry-run] Would write: {path}")
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return True


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(OPENCODE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def insert_session_to_db(session_data: Dict[str, Any], dry_run: bool = False) -> bool:
    if dry_run:
        log(f"  [dry-run] Would insert session to DB: {session_data.get('id')}")
        return True

    conn = get_db_connection()
    cur = conn.cursor()

    session_id = session_data.get("id")
    time_data = session_data.get("time", {})

    try:
        cur.execute(
            """
            INSERT OR REPLACE INTO session (
                id, project_id, parent_id, slug, directory, title, version,
                share_url, summary_additions, summary_deletions, summary_files,
                summary_diffs, revert, permission, time_created, time_updated,
                time_compacting, time_archived, workspace_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                session_id,
                session_data.get("projectID", "global"),
                session_data.get("parentID"),
                session_data.get("slug", "migrated-session"),
                session_data.get("directory", "/"),
                session_data.get("title", "Migrated from Kilo"),
                session_data.get("version", "1.0.0"),
                session_data.get("shareUrl"),
                session_data.get("summary", {}).get("additions", 0),
                session_data.get("summary", {}).get("deletions", 0),
                session_data.get("summary", {}).get("files", 0),
                json.dumps(session_data.get("summary", {}).get("diffs", [])),
                session_data.get("revert"),
                json.dumps(session_data.get("permission"))
                if session_data.get("permission")
                else None,
                time_data.get("created", int(datetime.now().timestamp() * 1000)),
                time_data.get("updated", int(datetime.now().timestamp() * 1000)),
                time_data.get("compacting"),
                time_data.get("archived"),
                session_data.get("workspaceId"),
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log(f"  [ERROR] Failed to insert session {session_id}: {e}", "ERROR")
        conn.close()
        return False


def insert_message_to_db(message_data: Dict[str, Any], dry_run: bool = False) -> bool:
    if dry_run:
        return True

    conn = get_db_connection()
    cur = conn.cursor()

    message_id = message_data.get("id")
    time_data = message_data.get("time", {})
    now_ts = int(datetime.now().timestamp() * 1000)

    try:
        cur.execute(
            """
            INSERT OR REPLACE INTO message (
                id, session_id, time_created, time_updated, data
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (
                message_id,
                message_data.get("sessionID"),
                time_data.get("created")
                if time_data and time_data.get("created")
                else now_ts,
                time_data.get("updated")
                if time_data and time_data.get("updated")
                else now_ts,
                json.dumps(message_data),
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log(f"  [ERROR] Failed to insert message {message_id}: {e}", "ERROR")
        conn.close()
        return False


def insert_part_to_db(
    part_data: Dict[str, Any], message_id: str, session_id: str, dry_run: bool = False
) -> bool:
    if dry_run:
        return True

    conn = get_db_connection()
    cur = conn.cursor()

    part_id = part_data.get("id")
    time_data = part_data.get("time", {})

    try:
        now_ts = int(datetime.now().timestamp() * 1000)
        cur.execute(
            """
            INSERT OR REPLACE INTO part (
                id, message_id, session_id, time_created, time_updated, data
            ) VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                part_id,
                message_id,
                session_id,
                time_data.get("created")
                if time_data and time_data.get("created")
                else now_ts,
                time_data.get("updated")
                if time_data and time_data.get("updated")
                else now_ts,
                json.dumps(part_data),
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log(f"  [ERROR] Failed to insert part {part_id}: {e}", "ERROR")
        conn.close()
        return False


def backup_opencode_session(session_id: str) -> bool:
    backup_path = BACKUP_DIR / datetime.now().strftime("%Y%m%d_%H%M%S") / session_id
    backup_path.mkdir(parents=True, exist_ok=True)

    session_file = OPENCODE_STORAGE / "session" / "global" / f"{session_id}.json"
    if session_file.exists():
        shutil.copy2(session_file, backup_path / f"{session_id}.json")

    message_dir = OPENCODE_STORAGE / "message" / session_id
    if message_dir.exists():
        shutil.copytree(message_dir, backup_path / "messages", dirs_exist_ok=True)

    part_dir = OPENCODE_STORAGE / "part"
    if part_dir.exists():
        for part_file in part_dir.rglob("*.json"):
            if session_id in str(part_file):
                rel_path = part_file.relative_to(part_dir)
                dest = backup_path / "parts" / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(part_file, dest)

    log(f"Backed up session {session_id} to {backup_path}")
    return True


def convert_kilo_session_to_opencode(
    session_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    files_to_create = []

    session_file = {
        "id": session_data.get("id"),
        "slug": session_data.get("slug"),
        "version": session_data.get("version"),
        "projectID": session_data.get("projectID", "global"),
        "directory": session_data.get("directory", "/"),
        "title": session_data.get("title", "Migrated from Kilo"),
        "time": session_data.get("time", {}),
        "summary": session_data.get(
            "summary", {"additions": 0, "deletions": 0, "files": 0}
        ),
    }

    if session_data.get("permission"):
        session_file["permission"] = session_data["permission"]

    if session_data.get("parentID"):
        session_file["parentID"] = session_data["parentID"]

    files_to_create.append(
        {
            "path": OPENCODE_STORAGE
            / "session"
            / "global"
            / f"{session_data['id']}.json",
            "data": session_file,
        }
    )

    return files_to_create


def convert_kilo_message_to_opencode(
    message_data: Dict[str, Any], session_id: str
) -> List[Dict[str, Any]]:
    files_to_create = []

    message_file = {
        "id": message_data.get("id"),
        "sessionID": message_data.get("sessionID"),
        "role": message_data.get("role"),
        "time": message_data.get("time"),
        "summary": message_data.get("summary", {"title": "", "diffs": []}),
    }

    if message_data.get("agent"):
        message_file["agent"] = message_data["agent"]

    if message_data.get("model"):
        message_file["model"] = message_data["model"]

    if message_data.get("tools"):
        message_file["tools"] = message_data["tools"]

    files_to_create.append(
        {
            "path": OPENCODE_STORAGE
            / "message"
            / session_id
            / f"{message_data['id']}.json",
            "data": message_file,
        }
    )

    return files_to_create


def convert_kilo_part_to_opencode(
    part_data: Dict[str, Any], message_id: str
) -> List[Dict[str, Any]]:
    files_to_create = []

    part_file = {
        "id": part_data.get("id"),
        "messageID": message_id,
        "type": part_data.get("type"),
        "text": part_data.get("text"),
        "time": part_data.get("time"),
    }

    if part_data.get("toolCall"):
        part_file["toolCall"] = part_data["toolCall"]

    if part_data.get("toolResult"):
        part_file["toolResult"] = part_data["toolResult"]

    files_to_create.append(
        {
            "path": OPENCODE_STORAGE / "part" / message_id / f"{part_data['id']}.json",
            "data": part_file,
        }
    )

    return files_to_create


def get_all_kilo_sessions() -> List[Dict[str, Any]]:
    sessions = []
    kilo_session_dir = KILO_STORAGE / "session" / "global"

    if not kilo_session_dir.exists():
        log("No Kilo sessions found", "WARN")
        return sessions

    for session_file in kilo_session_dir.glob("*.json"):
        session_data = read_json_file(session_file)
        if session_data:
            sessions.append(session_data)

    return sessions


def get_session_messages_and_parts(session_id: str) -> tuple:
    messages = []
    parts = []

    kilo_message_dir = KILO_STORAGE / "message" / session_id
    if not kilo_message_dir.exists():
        return messages, parts

    for message_file in sorted(kilo_message_dir.glob("*.json")):
        message_data = read_json_file(message_file)
        if message_data:
            messages.append(message_data)

            kilo_part_dir = KILO_STORAGE / "part" / message_data["id"]
            if kilo_part_dir.exists():
                for part_file in sorted(kilo_part_dir.glob("*.json")):
                    part_data = read_json_file(part_file)
                    if part_data:
                        parts.append((message_data["id"], part_data))

    return messages, parts


def migrate_session(
    session_id: str, dry_run: bool = False, do_backup: bool = False
) -> bool:
    kilo_session_file = KILO_STORAGE / "session" / "global" / f"{session_id}.json"

    if not kilo_session_file.exists():
        log(f"Session {session_id} not found in Kilo storage", "ERROR")
        return False

    session_data = read_json_file(kilo_session_file)
    if not session_data:
        log(f"Failed to read session {session_id}", "ERROR")
        return False

    log(f"Migrating session: {session_id} ({session_data.get('title', 'Untitled')})")

    if do_backup and not dry_run:
        opencode_session_file = (
            OPENCODE_STORAGE / "session" / "global" / f"{session_id}.json"
        )
        if opencode_session_file.exists():
            backup_opencode_session(session_id)

    all_files = []

    session_files = convert_kilo_session_to_opencode(session_data)
    all_files.extend(session_files)

    messages, parts = get_session_messages_and_parts(session_id)

    for message_data in messages:
        message_files = convert_kilo_message_to_opencode(message_data, session_id)
        all_files.extend(message_files)

    for message_id, part_data in parts:
        part_files = convert_kilo_part_to_opencode(part_data, message_id)
        all_files.extend(part_files)

    for file_info in all_files:
        write_json_file(file_info["path"], file_info["data"], dry_run)

    if not dry_run:
        insert_session_to_db(session_data)
        for message_data in messages:
            insert_message_to_db(message_data)
        for message_id, part_data in parts:
            insert_part_to_db(part_data, message_id, session_id)

    log(f"  Migrated {len(all_files)} files for session {session_id}")
    return True


def ensure_opencode_project() -> bool:
    project_file = OPENCODE_STORAGE / "project" / "global.json"
    if project_file.exists():
        return True

    project_data = {
        "id": "global",
        "worktree": "/",
        "time": {
            "created": int(datetime.now().timestamp() * 1000),
            "updated": int(datetime.now().timestamp() * 1000),
        },
        "sandboxes": [],
    }

    write_json_file(project_file, project_data)
    log("Created global project file")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Kilo CLI sessions to OpenCode"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without making changes",
    )
    parser.add_argument("--session", type=str, help="Migrate a specific session by ID")
    parser.add_argument("--all", action="store_true", help="Migrate all sessions")
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Backup OpenCode sessions before overwriting",
    )
    parser.add_argument(
        "--list", action="store_true", help="List available Kilo sessions"
    )

    args = parser.parse_args()

    if not KILO_STORAGE.exists():
        log(f"Kilo storage not found: {KILO_STORAGE}", "ERROR")
        sys.exit(1)

    if args.list:
        sessions = get_all_kilo_sessions()
        log(f"Found {len(sessions)} sessions in Kilo storage:")
        for s in sessions:
            created = datetime.fromtimestamp(
                s.get("time", {}).get("created", 0) / 1000
            ).strftime("%Y-%m-%d %H:%M")
            title = s.get("title", "Untitled")[:50]
            print(f"  {s['id']} | {created} | {title}")
        sys.exit(0)

    if not args.session and not args.all:
        parser.print_help()
        sys.exit(1)

    if not args.dry_run:
        ensure_opencode_project()

    if args.session:
        migrate_session(args.session, args.dry_run, args.backup)
        log("Migration complete!")
        sys.exit(0)

    if args.all:
        sessions = get_all_kilo_sessions()
        log(f"Found {len(sessions)} sessions to migrate")

        success = 0
        failed = 0

        for session_data in sessions:
            try:
                if migrate_session(session_data["id"], args.dry_run, args.backup):
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                log(f"Failed to migrate {session_data.get('id')}: {e}", "ERROR")
                failed += 1

        log(f"Migration complete! Success: {success}, Failed: {failed}")
        sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
