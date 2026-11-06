# Workflows

## Capture (灵感：)

1. Write-lock on.
2. Semantic completeness → set `completeness` + note; always INSERT data_1.
3. If not `complete` → unlock, optional short re-ask; stop.
4. Fill Claim micro-template from raw text (do not invent boundaries).
5. Validate; if fail → `pending` Claim + ≤2 MC questions.
6. If pass → `active` Claim + `claim_sources`.
7. Unlock.

```
subject:
assertion:
scope:
exclusions:
domain: []
confidence:
open_questions: []
sources: [R-…]
```

## Request 立项

Host says 整理 / agrees to Agent ask:

1. Confirm title, template (memo|spec|article), claim_ids.
2. Lock → `allocate_id.py P` → INSERT projects (`drafting`), `project_claims`.
3. Generate body → `allocate_id.py CH` → write `changes/CH-….md` → INSERT change_proposals → `pending_review`.
4. Unlock; tell host to approve (or run scan_pending).

## Session / 定时检查待审

```bash
python .cursor/skills/inspiration-collector/scripts/scan_pending.py
```

If pending → ask 通过/驳回 → `resolve_change.py`.

## Reject vs approve

| | changes 文件 | data_3 | contents |
|--|-------------|--------|----------|
| 通过 | 保留（历史） | 覆盖为正文 | version+1, active, clear pending |
| 驳回 | 删除 | 不动 | change=rejected; project active 或 rejected |

## Concurrency

- Any mutate: `write_lock.py acquire` (or resolve_change which locks itself).
- Concurrent writers → busy error; reads OK.
