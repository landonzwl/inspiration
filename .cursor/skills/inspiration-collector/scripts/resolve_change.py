#!/usr/bin/env python3
"""Approve or reject a pending change. Requires write lock."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from paths import CHANGES_DIR, CONTENTS_DB, DATA_3_DIR
from write_lock import WriteLockError, write_lock

TZ = ZoneInfo("Asia/Shanghai")


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def load_body(change_path: Path) -> str:
    text = change_path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].lstrip("\n")
    return text


def resolve(change_id: str, action: str, note: str) -> None:
    conn = sqlite3.connect(CONTENTS_DB)
    conn.row_factory = sqlite3.Row
    try:
        ch = conn.execute(
            "SELECT * FROM change_proposals WHERE id = ?", (change_id,)
        ).fetchone()
        if ch is None:
            raise SystemExit(f"error: unknown change {change_id}")
        if ch["status"] != "pending_review":
            raise SystemExit(f"error: change not pending_review (status={ch['status']})")

        proj = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (ch["project_id"],)
        ).fetchone()
        if proj is None:
            raise SystemExit(f"error: missing project {ch['project_id']}")

        change_file = CHANGES_DIR / ch["path"]
        product_file = DATA_3_DIR / proj["path"]
        ts = now_iso()

        if action == "approve":
            if not change_file.is_file():
                raise SystemExit(f"error: missing change file {change_file}")
            body = load_body(change_file)
            product_file.parent.mkdir(parents=True, exist_ok=True)
            product_file.write_text(body, encoding="utf-8")
            new_ver = int(proj["version"]) + 1
            conn.execute(
                """
                UPDATE change_proposals
                SET status='applied', resolved_at=?, resolution_note=?
                WHERE id=?
                """,
                (ts, note or "approved", change_id),
            )
            conn.execute(
                """
                UPDATE projects
                SET version=?, status='active', pending_change_id=NULL, updated_at=?
                WHERE id=?
                """,
                (new_ver, ts, proj["id"]),
            )
            conn.commit()
            print(f"APPLIED {change_id} -> data_3/{proj['path']} version={new_ver}")
            return

        # reject: delete change file; keep DB row as rejected
        if change_file.is_file():
            change_file.unlink()
        conn.execute(
            """
            UPDATE change_proposals
            SET status='rejected', resolved_at=?, resolution_note=?
            WHERE id=?
            """,
            (ts, note or "rejected", change_id),
        )
        # if product exists keep active; else rejected
        new_status = "active" if product_file.is_file() else "rejected"
        conn.execute(
            """
            UPDATE projects
            SET status=?, pending_change_id=NULL, updated_at=?
            WHERE id=?
            """,
            (new_status, ts, proj["id"]),
        )
        conn.commit()
        print(f"REJECTED {change_id}; project -> {new_status}; change file deleted")
    finally:
        conn.close()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["approve", "reject"])
    p.add_argument("change_id")
    p.add_argument("--note", default="")
    args = p.parse_args()
    if not CONTENTS_DB.is_file():
        print("error: contents DB missing; run init_dbs.py", file=sys.stderr)
        return 2
    try:
        with write_lock(timeout_sec=0):
            resolve(args.change_id, args.action, args.note)
    except WriteLockError as e:
        print(f"BUSY {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
