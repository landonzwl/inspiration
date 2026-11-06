#!/usr/bin/env python3
"""List projects pending approval. Safe to run without write lock (read-only)."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from paths import CHANGES_DIR, CONTENTS_DB, DATA_3_DIR, REPO_ROOT


def main() -> int:
    if not CONTENTS_DB.is_file():
        print("error: contents DB missing; run init_dbs.py", file=sys.stderr)
        return 2

    conn = sqlite3.connect(CONTENTS_DB)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT p.id AS project_id, p.title, p.path AS product_path, p.version,
                   p.pending_change_id, c.id AS change_id, c.path AS change_path,
                   c.summary, c.claim_ids, c.based_on_version, c.created_at
            FROM projects p
            LEFT JOIN change_proposals c
              ON c.id = p.pending_change_id AND c.status = 'pending_review'
            WHERE p.status = 'pending_review'
            ORDER BY (c.created_at IS NULL), c.created_at ASC, p.updated_at ASC
            """
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        print("NO_PENDING")
        return 0

    print(f"PENDING_COUNT {len(rows)}")
    print()
    print("请宿主审批（对每条回复：通过 / 驳回，可附理由）：")
    print()
    for i, r in enumerate(rows, 1):
        change_file = CHANGES_DIR / (r["change_path"] or "")
        product_file = DATA_3_DIR / r["product_path"]
        claims = r["claim_ids"] or "[]"
        try:
            claim_list = json.loads(claims)
        except json.JSONDecodeError:
            claim_list = [claims]
        print(f"### {i}. {r['project_id']} — {r['title']}")
        print(f"- change: {r['change_id']} (based_on_version={r['based_on_version']})")
        print(f"- product: data_3/{r['product_path']} (current version={r['version']})")
        print(f"- change file: {change_file.relative_to(REPO_ROOT) if change_file.parts else '(missing)'}")
        print(f"- exists change file: {change_file.is_file()}")
        print(f"- exists product file: {product_file.is_file()}")
        print(f"- claim_ids: {claim_list}")
        summary = (r["summary"] or "").strip() or "(无 summary)"
        print("- 更改点:")
        for line in summary.splitlines():
            print(f"  {line}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
