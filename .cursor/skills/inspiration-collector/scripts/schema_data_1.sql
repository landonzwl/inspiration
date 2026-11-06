-- data_1: raw inspirations (append-only raw_text)
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS inspirations (
  id TEXT PRIMARY KEY,
  captured_at TEXT NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('chat', 'manual', 'import', 'clarification')),
  raw_text TEXT NOT NULL,
  raw_hash TEXT,
  completeness TEXT NOT NULL DEFAULT 'pending'
    CHECK (completeness IN ('pending', 'complete', 'incomplete', 'mistake')),
  completeness_note TEXT,
  related_inspiration_id TEXT,
  related_claim_id TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_inspirations_captured ON inspirations(captured_at);
CREATE INDEX IF NOT EXISTS idx_inspirations_completeness ON inspirations(completeness);
