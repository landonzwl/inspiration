-- data_2: normalized claims
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS domains (
  name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS claims (
  id TEXT PRIMARY KEY,
  version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
  status TEXT NOT NULL
    CHECK (status IN ('pending', 'active', 'superseded', 'rejected')),
  domain TEXT NOT NULL,          -- JSON array
  subject TEXT NOT NULL,
  assertion TEXT NOT NULL,
  scope TEXT NOT NULL DEFAULT '',
  exclusions TEXT NOT NULL DEFAULT '',
  confidence TEXT NOT NULL CHECK (confidence IN ('low', 'medium', 'high')),
  open_questions TEXT NOT NULL DEFAULT '[]',  -- JSON array
  depends_on TEXT NOT NULL DEFAULT '[]',      -- JSON array
  supersedes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claim_sources (
  claim_id TEXT NOT NULL REFERENCES claims(id),
  inspiration_id TEXT NOT NULL,
  PRIMARY KEY (claim_id, inspiration_id)
);

CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
CREATE INDEX IF NOT EXISTS idx_claims_subject ON claims(subject);
CREATE INDEX IF NOT EXISTS idx_claim_sources_insp ON claim_sources(inspiration_id);

INSERT OR IGNORE INTO domains(name) VALUES
  ('产品'), ('方法论'), ('技术'), ('个人系统'), ('写作'), ('未分类');
