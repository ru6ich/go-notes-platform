CREATE TABLE IF NOT EXISTS notes (
    id BIGSERIAL PRIMARY KEY,
    text TEXT NOT NULL CHECK (length(trim(text)) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_checks (
    id BIGSERIAL PRIMARY KEY,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status_code INT NOT NULL CHECK (status_code >= 100 AND status_code <= 599),
    latency_ms INT NOT NULL CHECK (latency_ms >= 0),
    success BOOLEAN NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notes_created_at
    ON notes (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_api_checks_checked_at
    ON api_checks (checked_at DESC);

CREATE INDEX IF NOT EXISTS idx_api_checks_success
    ON api_checks (success);
