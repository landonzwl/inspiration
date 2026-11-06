#!/usr/bin/env python3
"""Create data_1 / data_2 / contents SQLite databases and folders."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from paths import (
    CHANGES_DIR,
    CONTENTS_DB,
    DATA_1_DB,
    DATA_2_DB,
    DATA_3_DIR,
    SCHEMA_1,
    SCHEMA_2,
    SCHEMA_CONTENTS,
    TEMPLATES_DIR,
)


def apply_schema(db_path: Path, schema_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    sql = schema_path.read_text(encoding="utf-8")
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def main() -> int:
    apply_schema(DATA_1_DB, SCHEMA_1)
    apply_schema(DATA_2_DB, SCHEMA_2)
    apply_schema(CONTENTS_DB, SCHEMA_CONTENTS)
    DATA_3_DIR.mkdir(parents=True, exist_ok=True)
    CHANGES_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"OK {DATA_1_DB}")
    print(f"OK {DATA_2_DB}")
    print(f"OK {CONTENTS_DB}")
    print(f"OK dirs {DATA_3_DIR} {CHANGES_DIR} {TEMPLATES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
