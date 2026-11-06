# 灵感收集器 — 规格

## 目标

聊天捕获灵感 → 语义完整性判定 → data_1 → 语言正则化（澄清门）→ data_2 →（宿主请求整理时）请求立项 → data_3 成品；变更经 changes 审批后才覆盖 data_3。

## 聊天分类

| 类型 | 识别 | 行为 |
|------|------|------|
| 灵感 | 默认前缀 `灵感：`（或 `灵感:`） | 走灵感流水线 |
| 交流命令 | 无此前缀的正常指令 | 审批 / 检索 / 立项请求 / 其它对话，不入库为灵感 |

非前缀但语义极像灵感时：询问是否补前缀，不擅自入库。

## 存储布局

| 名称 | 形态 | 职责 |
|------|------|------|
| `data_1/data_1.sqlite` | SQLite | 原始灵感，**只追加**，不改写 `raw_text` |
| `data_2/data_2.sqlite` | SQLite | 正则化后的 Claim；`active` 须过校验 |
| `data_3/` | 文件夹 | 成品 Markdown，**一项目一文件，只保留最新版** |
| `contents/contents.sqlite` | SQLite | 成品目录索引（含状态、路径、版本、待审变更） |
| `changes/` | 文件夹 | 变更提案与历史正文；**通过则保留，驳回则删除该文件** |
| `data/_templates/` | 文件夹 | memo / spec / article 模板 |
| `data/write.lock` | 锁文件 | 写互斥（读不挡） |

旧路径 `data/L0-raw` 等仅作历史样例，新写入一律走本规格。

## 库表设计

### data_1 — `inspirations`

| 列 | 类型 | 说明 |
|----|------|------|
| `id` | TEXT PK | `R-YYYYMMDD-NNN` |
| `captured_at` | TEXT | ISO-8601 |
| `source` | TEXT | `chat` \| `manual` \| `import` \| `clarification` |
| `raw_text` | TEXT | 宿主原文，永不 UPDATE |
| `raw_hash` | TEXT | 可选，原文 hash |
| `completeness` | TEXT | `pending` \| `complete` \| `incomplete` \| `mistake`（**语义判定**） |
| `completeness_note` | TEXT | 判定理由摘要 |
| `related_inspiration_id` | TEXT | 澄清时指向原 R- |
| `related_claim_id` | TEXT | 澄清时指向 C- |
| `created_at` | TEXT | |

失误/不完整：**仍插入 data_1**（`completeness=mistake|incomplete`），不进入正则化写 active。

### data_2 — `claims` + `claim_sources` + `domains`

**claims**

| 列 | 类型 | 说明 |
|----|------|------|
| `id` | TEXT PK | `C-YYYYMMDD-NNN` |
| `version` | INTEGER | 语义修订 +1 |
| `status` | TEXT | `pending` \| `active` \| `superseded` \| `rejected` |
| `domain` | TEXT | JSON 数组， ⊆ `domains` |
| `subject` | TEXT | 禁止未解析指代 |
| `assertion` | TEXT | 可检验断言 |
| `scope` | TEXT | 与 exclusions 至少一非空 |
| `exclusions` | TEXT | |
| `confidence` | TEXT | `low` \| `medium` \| `high` |
| `open_questions` | TEXT | JSON 数组 |
| `depends_on` | TEXT | JSON 数组（Claim id） |
| `supersedes` | TEXT | 旧 Claim id |
| `created_at` | TEXT | |
| `updated_at` | TEXT | |

**claim_sources**：`(claim_id, inspiration_id)` — **4.5 链接**：每条 Claim 至少一条 data_1 id。

**domains**：受控词表；扩表须宿主确认。

**澄清门 2.5**：不完整/有歧义 → 可写 `status=pending`，**禁止** `active`；须宿主澄清后再升 `active`。

### contents — `projects` + `project_claims` + `change_proposals`

**projects**（目录索引）

| 列 | 类型 | 说明 |
|----|------|------|
| `id` | TEXT PK | `P-YYYYMMDD-NNN` |
| `title` | TEXT | |
| `path` | TEXT | 相对 `data_3/`，一项目一文件 |
| `status` | TEXT | 见状态机 |
| `template` | TEXT | `memo` \| `spec` \| `article` \| `custom` |
| `version` | INTEGER | 每次**审批通过**写回 data_3 后 +1 |
| `pending_change_id` | TEXT | 当前待审 `CH-…`，无则 NULL |
| `created_at` | TEXT | |
| `updated_at` | TEXT | |
| `notes` | TEXT | BRIEF 摘要等 |

**project_claims**：项目引用的 data_2 Claim id。

**change_proposals**（索引；正文在 `changes/` 文件）

| 列 | 类型 | 说明 |
|----|------|------|
| `id` | TEXT PK | `CH-YYYYMMDD-NNN` |
| `project_id` | TEXT | |
| `path` | TEXT | 相对 `changes/` |
| `status` | TEXT | `pending_review` \| `applied` \| `rejected` |
| `based_on_version` | INTEGER | 基于的 projects.version |
| `claim_ids` | TEXT | JSON，**必须引用 data_2 id** |
| `summary` | TEXT | 本次更改点 |
| `created_at` | TEXT | |
| `resolved_at` | TEXT | |
| `resolution_note` | TEXT | 宿主意见 |

## 项目状态机（contents.projects.status）

```
proposed → drafting → pending_review → active
                   ↘ rejected
        任意非终态 → parked
```

| 状态 | 含义 |
|------|------|
| `proposed` | 已请求/已建项，尚无稳定正文 |
| `drafting` | 正在起草或整理中 |
| `pending_review` | changes 中有待审提案（`pending_change_id` 非空） |
| `active` | data_3 为当前已通过版本 |
| `rejected` | 立项或末次变更被驳回且流程结束 |
| `parked` | 搁置 |

**立项时机**：宿主说要整理 / 同意 Agent「是否立项」请求时创建；**不**因阈值自动建项（Agent 可提议，宿主确认）。

## 灵感流水线

1. **语义完整性**：模型判定是否完整灵感 vs 失误/残缺（非纯长度规则）。  
   - `mistake` / `incomplete` → 写入 data_1 后停止，可短问是否重说。  
   - `complete` → 继续。
2. **写入 data_1**（持写锁）。
3. **语言正则化** → Claim 槽位（subject / assertion / scope / exclusions / domain）。
4. **澄清门 2.5**：触闸 → `claims.status=pending` + 提问（≤2 选项）；过闸 → `active`。
5. **写入 data_2** + **claim_sources 挂 data_1 id**（4.5）。

## 变更与审批

### 写出 changes（整理 / 改版时）

1. 持写锁；若该项目已有 `pending_review` → **拒绝新变更**（先审完）。
2. 基于 data_2（及现有 data_3）生成提案文件 `changes/CH-….md`：

```markdown
---
id: CH-YYYYMMDD-NNN
project_id: P-…
based_on_version: N
claim_ids: [C-…]
summary: |
  - 更改点 1
  - 更改点 2
status: pending_review
---

（完整正文，将作为 data_3 最新版）
```

3. `change_proposals` 插入；`projects.status=pending_review`，`pending_change_id=CH-…`。

### 扫描待审批（替代「每天第一句」硬编码）

脚本：`python .cursor/skills/inspiration-collector/scripts/scan_pending.py`  

列出 `projects.status=pending_review`（及对应 change）。Agent 在会话开始或宿主要求时运行；若有待审 → **询问审批意见**（通过 / 驳回 + 可选理由）。

### 通过

1. 写锁下：用 changes 正文**覆盖** `data_3/{path}`（只留最新）。
2. `change_proposals.status=applied`；**保留**该 changes 文件（历史）。
3. `projects.version+=1`，`status=active`，`pending_change_id=NULL`，更新 `updated_at`。

### 驳回

1. 写锁下：`change_proposals.status=rejected`，记 `resolution_note`。
2. **删除**该次 `changes/` 文件（不保留驳回正文）。
3. `projects.pending_change_id=NULL`；`status=rejected`（若尚无已通过正文）或退回 `active`（若 data_3 已有旧版）。  
   （语义：审批流程已结束；库内状态用 `rejected` / `active`，避免「已审批」与「已通过」混淆。）

## 并发

- **写**（插入灵感、写 Claim、立项、写/应用/驳回 change）：必须获取 `data/write.lock`；获取失败则告知「有写入进行中，可先检索只读」。
- **读**（检索、scan_pending、打开 data_3）：不获取写锁。

## Claim 校验闸（机器可检，写入 active 前）

- 必填槽位齐全；`claim_sources` 非空。
- `subject` / `assertion` 无未解析指代：`这个|那个|它|他们|上述|前者|后者`
- 软评价词须 `confidence=low` 且 `open_questions` 非空
- `scope` 与 `exclusions` 至少一非空
- `domain` ⊆ domains 表
- `active` 时 `open_questions` 必须为空

无歧义来自 **schema + 校验 + 语义澄清**，不发明自然语言方言。

## ID 方案

- 灵感 `R-YYYYMMDD-NNN` · Claim `C-YYYYMMDD-NNN` · 项目 `P-YYYYMMDD-NNN` · 变更 `CH-YYYYMMDD-NNN`
- 序号：当日同前缀 max+1（在写锁内分配）

## Skill

`.cursor/skills/inspiration-collector/` — 捕获 / 澄清 / 扫描待审 / 审批 / 检索 / 请求立项 / 写变更提案。
