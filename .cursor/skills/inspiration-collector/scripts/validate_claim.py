#!/usr/bin/env python3
"""Validate Claim fields (YAML file or stdin JSON). Exit 0=ok, 1=errors, 2=usage."""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

from paths import DATA_2_DB

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

STATUSES = {"pending", "active", "superseded", "rejected"}
CONFIDENCE = {"low", "medium", "high"}
DEIXIS = re.compile(r"(这个|那个|它|他们|上述|前者|后者)")
SOFT = re.compile(r"(更好|应该|大概|可能|或许)")
ID_RE = re.compile(r"^C-\d{8}-\d{3}$")

REQUIRED = {
    "id",
    "version",
    "status",
    "domain",
    "subject",
    "assertion",
    "scope",
    "exclusions",
    "confidence",
    "sources",
    "created_at",
    "updated_at",
}


def load_domains() -> set[str]:
    if not DATA_2_DB.is_file():
        return set()
    conn = sqlite3.connect(DATA_2_DB)
    try:
        rows = conn.execute("SELECT name FROM domains").fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


def _as_list(val: Any) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        s = val.strip()
        if s.startswith("["):
            try:
                return list(json.loads(s))
            except json.JSONDecodeError:
                return [val]
        return [val]
    return [val]


def validate(data: dict, domains: set[str] | None = None) -> list[str]:
    errs: list[str] = []
    domains = domains if domains is not None else load_domains()
    missing = REQUIRED - set(data)
    if missing:
        errs.append(f"missing fields: {sorted(missing)}")

    cid = data.get("id")
    if cid and not ID_RE.match(str(cid)):
        errs.append(f"id must match C-YYYYMMDD-NNN, got {cid!r}")

    if "version" in data and not (isinstance(data["version"], int) and data["version"] >= 1):
        errs.append("version must be int >= 1")

    if data.get("status") not in STATUSES:
        errs.append(f"status must be one of {sorted(STATUSES)}")

    if data.get("confidence") not in CONFIDENCE:
        errs.append(f"confidence must be one of {sorted(CONFIDENCE)}")

    dom = _as_list(data.get("domain"))
    if not dom:
        errs.append("domain must be non-empty list")
    elif domains:
        bad = [d for d in dom if d not in domains]
        if bad:
            errs.append(f"domain not in domains table: {bad}")

    for field in ("subject", "assertion"):
        val = data.get(field) or ""
        if not str(val).strip():
            errs.append(f"{field} empty")
        elif DEIXIS.search(str(val)):
            errs.append(f"{field} contains unresolved deixis")

    scope = str(data.get("scope") or "").strip()
    excl = str(data.get("exclusions") or "").strip()
    if not scope and not excl:
        errs.append("need scope and/or exclusions (boundary required)")

    assertion = str(data.get("assertion") or "")
    oq = _as_list(data.get("open_questions"))
    if SOFT.search(assertion):
        if data.get("confidence") != "low" or not oq:
            errs.append("soft eval in assertion requires confidence=low and open_questions")

    sources = _as_list(data.get("sources"))
    if not sources:
        errs.append("sources must be non-empty (data_1 inspiration ids)")

    if data.get("status") == "active" and oq:
        errs.append("active claim cannot have open_questions")

    return errs


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_claim.py <claim.yaml|claim.json>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        if yaml is None:
            print("error: PyYAML required for .yaml (pip install pyyaml)", file=sys.stderr)
            return 2
        data = yaml.safe_load(text)

    if not isinstance(data, dict):
        print("error: root must be a mapping", file=sys.stderr)
        return 1

    errs = validate(data)
    if errs:
        print(f"FAIL {path}")
        for e in errs:
            print(f"  - {e}")
        return 1
    print(f"OK {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
