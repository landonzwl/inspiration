# 灵感收集器

本地流水线：聊天灵感 → `data_1`（原始 SQLite）→ 语义判定与正则化 → `data_2`（Claim SQLite）→ 宿主确认立项后经 `changes` 审批 → `data_3`（一项目一文件，仅最新版）。目录索引在 `contents`。

- 规格：[SPEC.md](SPEC.md)
- Skill：`.cursor/skills/inspiration-collector/`

## 初始化

```powershell
pip install -r requirements.txt
python .cursor/skills/inspiration-collector/scripts/init_dbs.py
```

## 常用

```powershell
# 会话开始 / 定时：扫待审批（只读）
python .cursor/skills/inspiration-collector/scripts/scan_pending.py

# 审批
python .cursor/skills/inspiration-collector/scripts/resolve_change.py approve CH-YYYYMMDD-NNN
python .cursor/skills/inspiration-collector/scripts/resolve_change.py reject CH-YYYYMMDD-NNN --note "理由"

# 分配当日下一个 id（写入前先拿写锁）
python .cursor/skills/inspiration-collector/scripts/write_lock.py acquire
python .cursor/skills/inspiration-collector/scripts/allocate_id.py R
python .cursor/skills/inspiration-collector/scripts/write_lock.py release
```

对 Agent：`灵感：……` 捕获；需要整理时让它请求立项；有待审时按提示 通过/驳回。

## 布局

| 路径 | 说明 |
|------|------|
| `data_1/data_1.sqlite` | 原始灵感 |
| `data_2/data_2.sqlite` | Claim |
| `contents/contents.sqlite` | 项目目录 + 变更索引 |
| `data_3/` | 成品最新版 |
| `changes/` | 变更提案（通过保留，驳回删文件） |
| `data/write.lock` | 写互斥 |
| `data/_templates/` | 成品模板 |

旧 `data/L0-raw` 等仅为历史样例，新数据走上方路径。
