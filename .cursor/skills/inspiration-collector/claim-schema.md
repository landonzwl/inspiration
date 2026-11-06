# Claim schema (data_2.claims)

## Fields

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | `C-YYYYMMDD-NNN` |
| `version` | int ≥ 1 | Bump on semantic edit |
| `status` | enum | `pending` \| `active` \| `superseded` \| `rejected` |
| `domain` | string[] | ⊆ `domains` table (JSON in SQLite) |
| `subject` | string | No bare deixis |
| `assertion` | string | Testable |
| `scope` / `exclusions` | string | At least one non-empty |
| `confidence` | enum | `low` \| `medium` \| `high` |
| `open_questions` | string[] | Required path when soft-eval kept; must be empty if `active` |
| `depends_on` | string[] | Claim ids |
| `supersedes` | string? | Prior Claim id |
| `sources` | string[] | **data_1 inspiration ids** via `claim_sources` |
| `created_at` / `updated_at` | ISO-8601 | |

## Gate → pending (not active)

Incomplete semantics, unresolved deixis, soft eval without low+questions, missing boundary, domain unknown, or conflict → `status=pending` until Clarify.

## Absolute-expression rules

- Bad: `这个应该更好一点`
- Good: `subject: 日更任务` / `assertion: 审批通过前不得覆盖 data_3` / explicit scope/exclusions

Validate:

```bash
python .cursor/skills/inspiration-collector/scripts/validate_claim.py path/to/claim.yaml
```
