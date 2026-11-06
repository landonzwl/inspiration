"""Repo data paths for inspiration-collector."""

from __future__ import annotations

from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parents[3]  # .../灵感收集

DATA_1_DB = REPO_ROOT / "data_1" / "data_1.sqlite"
DATA_2_DB = REPO_ROOT / "data_2" / "data_2.sqlite"
CONTENTS_DB = REPO_ROOT / "contents" / "contents.sqlite"
DATA_3_DIR = REPO_ROOT / "data_3"
CHANGES_DIR = REPO_ROOT / "changes"
TEMPLATES_DIR = REPO_ROOT / "data" / "_templates"
WRITE_LOCK = REPO_ROOT / "data" / "write.lock"

SCHEMA_1 = SCRIPTS_DIR / "schema_data_1.sql"
SCHEMA_2 = SCRIPTS_DIR / "schema_data_2.sql"
SCHEMA_CONTENTS = SCRIPTS_DIR / "schema_contents.sql"
