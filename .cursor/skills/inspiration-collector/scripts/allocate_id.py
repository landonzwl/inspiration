#!/usr/bin/env python3
"""Allocate next R-|C-|P-|CH- id for today. Must run under write lock for commits."""

from __future__ import annotations

import re
import sqlite3
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from paths import CONTENTS_DB, DATA_1_DB, DATA_2_DB

TZ = ZoneInfo("Asia/Shanghai")
PREFIX = {
    "R": (DATA_1_DB, "inspirations", "id"),
    "C": (DATA_2_DB, "claims", "id"),
    "P": (CONTENTS_DB, "projects", "id"),
    "CH": (CONTENTS_DB, "change_proposals", "id"),
}


def today() -> str:
    return datetime.now(TZ).strftime("%Y%m%d")


def next_id(kind: str, day: str | None = None) -> str:
    kind = kind.upper()
    if kind not in PREFIX:
        raise ValueError(f"kind must be one of {sorted(PREFIX)}")
    day = day or today()
    prefix = f"{kind}-{day}-"
    db, table, col = PREFIX[kind]
    n = 0
    if db.is_file():
        conn = sqlite3.connect(db)
        try:
            rows = conn.execute(
                f"SELECT {col} FROM {table} WHERE {col} LIKE ?",
                (prefix + "%",),
            ).fetchall()
        finally:
            conn.close()
        pat = re.compile(rf"^{re.escape(kind)}-{day}-(\d{{3}})$")
        for (oid,) in rows:
            m = pat.match(str(oid))
            if m:
                n = max(n, int(m.group(1)))
    return f"{prefix}{n + 1:03d}"


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: allocate_id.py R|C|P|CH [YYYYMMDD]", file=sys.stderr)
        return 2
    kind = sys.argv[1]
    day = sys.argv[2] if len(sys.argv) == 3 else None
    try:
        print(next_id(kind, day))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
