---
name: inspiration-collector
description: >-
  Captures chat inspirations (prefix 灵感：) into data_1 SQLite, semantically
  checks completeness, normalizes into data_2 Claims with clarification gate and
  source links, indexes products in contents SQLite, writes one-file projects
  under data_3 via changes approval. Use when the user captures灵感, clarifies
  Claims, scans待审批, approves/rejects changes, requests立项/整理, or searches
  the local store.
---

# Inspiration Collector

Spec: [SPEC.md](../../../SPEC.md).

| Store | Path |
|-------|------|
| Raw | `data_1/data_1.sqlite` |
| Claims | `data_2/data_2.sqlite` |
| Product files | `data_3/` (latest only, one file per project) |
| Catalog | `contents/contents.sqlite` |
| Change history | `changes/` (keep on approve; delete file on reject) |

Scripts: `.cursor/skills/inspiration-collector/scripts/`.

## Principles

1. **data_1 append-only** — never UPDATE `raw_text`.
2. **data_2 active = schema-valid** — pending on ambiguity gate (2.5).
3. **4.5 link** — every Claim has `claim_sources` → data_1 ids; every change lists `claim_ids`.
4. **Writes need lock** — `write_lock.py`; reads (incl. `scan_pending.py`) do not.
5. **No auto-final** — data_3 updates only via approve; 立项 only after host agrees.

## Chat routing

| Input | Action |
|-------|--------|
| `灵感：…` / `灵感:…` | → **Capture** |
| 扫描待审 / 会话开始检查 | → **Scan pending** |
| 通过 / 驳回 + change id | → **Resolve** |
| 整理 / 同意立项 | → **Project propose** then draft change |
| 澄清答案 | → **Clarify** |
| 其它交流命令 | 不入库；可检索只读 |

## Capture

1. Acquire write lock.
2. **Semantic completeness** (not length-only): `complete` | `incomplete` | `mistake`.
3. Insert data_1 (`allocate_id.py R`). Mistakes still stored; stop if not complete.
4. Normalize → Claim slots ([claim-schema.md](claim-schema.md)).
5. Gate fail → insert Claim `status=pending` + ≤2 option questions; do **not** set `active`.
6. Gate pass → validate → insert `active` + `claim_sources`.
7. Release lock.

## Clarify

1. New data_1 row `source=clarification` linked to prior R/C.
2. Update Claim (version++) or supersede; only then maybe `active`.

## Scan pending

```bash
python .cursor/skills/inspiration-collector/scripts/scan_pending.py
```

If not `NO_PENDING`, ask host per item: 通过 / 驳回（可附理由）.

## Resolve

```bash
python .cursor/skills/inspiration-collector/scripts/resolve_change.py approve CH-…
python .cursor/skills/inspiration-collector/scripts/resolve_change.py reject CH-… --note "…"
```

- Approve: overwrite `data_3` file; keep changes file; version++; status `active`.
- Reject: delete that changes file; DB row `rejected`; project `active` if file exists else `rejected`.

## Project / 整理

1. When host wants整理, **ask to 立项** (do not invent projects silently).
2. On同意: write-lock → insert `projects` (`proposed`/`drafting`) + optional empty/template file plan.
3. Draft full body → write `changes/CH-….md` + `change_proposals` + set `pending_review`.
4. One pending change per project; block new writes until resolved.

Details: [workflows.md](workflows.md).

## Setup

```bash
pip install -r requirements.txt
python .cursor/skills/inspiration-collector/scripts/init_dbs.py
```

## Ambiguity gate

- Deixis in subject/assertion: 这个|那个|它|他们|上述|前者|后者
- Soft eval without low+open_questions: 更好|应该|大概|可能|或许
- Missing both scope and exclusions
- Conflict with active Claim; domain not in data_2.domains
