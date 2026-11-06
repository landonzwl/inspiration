-- contents: project catalog + change proposal index
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  path TEXT NOT NULL UNIQUE,   -- relative to data_3/
  status TEXT NOT NULL
    CHECK (status IN ('proposed', 'drafting', 'pending_review', 'active', 'rejected', 'parked')),
  template TEXT NOT NULL DEFAULT 'memo'
    CHECK (template IN ('memo', 'spec', 'article', 'custom')),
  version INTEGER NOT NULL DEFAULT 0 CHECK (version >= 0),
  pending_change_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS project_claims (
  project_id TEXT NOT NULL REFERENCES projects(id),
  claim_id TEXT NOT NULL,
  PRIMARY KEY (project_id, claim_id)
);

CREATE TABLE IF NOT EXISTS change_proposals (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id),
  path TEXT NOT NULL,          -- relative to changes/
  status TEXT NOT NULL
    CHECK (status IN ('pending_review', 'applied', 'rejected')),
  based_on_version INTEGER NOT NULL DEFAULT 0,
  claim_ids TEXT NOT NULL DEFAULT '[]',  -- JSON; must reference data_2 ids
  summary TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  resolved_at TEXT,
  resolution_note TEXT
);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_changes_status ON change_proposals(status);
CREATE INDEX IF NOT EXISTS idx_changes_project ON change_proposals(project_id);
