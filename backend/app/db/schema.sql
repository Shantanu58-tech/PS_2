PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS raw_records (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    collector_id TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    payload_canonical TEXT NOT NULL,
    record_hash TEXT NOT NULL,
    entry_hash TEXT NOT NULL,
    prev_entry_hash TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS raw_no_update BEFORE UPDATE ON raw_records
BEGIN SELECT RAISE(ABORT, 'append-only'); END;

CREATE TRIGGER IF NOT EXISTS raw_no_delete BEFORE DELETE ON raw_records
BEGIN SELECT RAISE(ABORT, 'append-only'); END;

CREATE TABLE IF NOT EXISTS ledger_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_seq INTEGER NOT NULL,
    last_seq INTEGER NOT NULL,
    merkle_root TEXT NOT NULL,
    signature TEXT NOT NULL,
    pubkey_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    ots_proof BLOB,
    ots_status TEXT,
    ots_block INTEGER
);

CREATE TABLE IF NOT EXISTS accounts (
    platform TEXT NOT NULL,
    account_id TEXT NOT NULL,
    handle TEXT,
    display_name TEXT,
    bio TEXT,
    location_text TEXT,
    created_at TEXT,
    followers INTEGER,
    following INTEGER,
    verified INTEGER,
    synthetic INTEGER DEFAULT 0,
    PRIMARY KEY (platform, account_id)
);

CREATE TABLE IF NOT EXISTS posts (
    platform TEXT NOT NULL,
    post_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    parent_post_id TEXT,
    root_post_id TEXT,
    origin_post_id TEXT,
    channel TEXT,
    lang TEXT,
    metrics_json TEXT,
    synthetic INTEGER DEFAULT 0,
    ledger_seq INTEGER,
    PRIMARY KEY (platform, post_id)
);

CREATE INDEX IF NOT EXISTS idx_posts_time ON posts(created_at);
CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform);
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author_id);

CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
    text,
    content='posts',
    content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS posts_ai AFTER INSERT ON posts BEGIN
    INSERT INTO posts_fts(rowid, text) VALUES (new.rowid, new.text);
END;

CREATE TABLE IF NOT EXISTS media (
    media_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    url TEXT,
    local_path TEXT,
    sha256 TEXT NOT NULL,
    phash TEXT,
    ocr_text TEXT,
    clip_vec_id INTEGER
);

CREATE TABLE IF NOT EXISTS post_media (
    platform TEXT NOT NULL,
    post_id TEXT NOT NULL,
    media_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS edges (
    src_platform TEXT NOT NULL,
    src_account TEXT NOT NULL,
    dst_platform TEXT NOT NULL,
    dst_account TEXT NOT NULL,
    kind TEXT NOT NULL,
    ts TEXT NOT NULL,
    post_id TEXT,
    weight REAL DEFAULT 1.0
);

CREATE INDEX IF NOT EXISTS idx_edges_ts ON edges(ts);
CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src_account);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst_account);

CREATE TABLE IF NOT EXISTS post_emotions (
    platform TEXT NOT NULL,
    post_id TEXT NOT NULL,
    anxiety REAL,
    excitement REAL,
    supportive REAL,
    against REAL,
    sarcasm REAL,
    neutral REAL,
    sentiment TEXT,
    model_version TEXT,
    PRIMARY KEY (platform, post_id)
);

CREATE TABLE IF NOT EXISTS embeddings_map (
    platform TEXT NOT NULL,
    post_id TEXT NOT NULL,
    faiss_id INTEGER NOT NULL,
    PRIMARY KEY (platform, post_id)
);

CREATE TABLE IF NOT EXISTS topics (
    topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    keywords TEXT NOT NULL,
    centroid BLOB,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    nature TEXT DEFAULT 'organic',
    coordinated_share REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS topic_assign (
    platform TEXT NOT NULL,
    post_id TEXT NOT NULL,
    topic_id INTEGER NOT NULL,
    prob REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS topic_series (
    topic_id INTEGER NOT NULL,
    bucket_start TEXT NOT NULL,
    count_all INTEGER NOT NULL DEFAULT 0,
    count_organic INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS bursts (
    topic_id INTEGER NOT NULL,
    start TEXT NOT NULL,
    end TEXT NOT NULL,
    level INTEGER NOT NULL,
    weight REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS coord_clusters (
    cluster_id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER,
    n_posts INTEGER NOT NULL,
    n_accounts INTEGER NOT NULL,
    hn REAL,
    burstiness REAL,
    sync REAL,
    dup_ratio REAL,
    regular_share REAL,
    score REAL NOT NULL,
    basis TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS coord_accounts (
    platform TEXT NOT NULL,
    account_id TEXT NOT NULL,
    cluster_id INTEGER NOT NULL,
    score REAL NOT NULL,
    reasons_json TEXT,
    PRIMARY KEY (platform, account_id, cluster_id)
);

CREATE TABLE IF NOT EXISTS demo_aggregates (
    scope TEXT NOT NULL,
    scope_id TEXT NOT NULL,
    dimension TEXT NOT NULL,
    bucket TEXT NOT NULL,
    count INTEGER NOT NULL,
    organic_only INTEGER NOT NULL DEFAULT 0,
    computed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    topic_id INTEGER,
    priority REAL NOT NULL,
    headline TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    status TEXT DEFAULT 'new'
);

CREATE TABLE IF NOT EXISTS cases (
    case_id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    brief_path TEXT
);

CREATE TABLE IF NOT EXISTS certificates (
    cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    generated_at TEXT NOT NULL,
    pdf_path TEXT,
    first_seq INTEGER NOT NULL,
    last_seq INTEGER NOT NULL,
    merkle_root TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS forecasts (
    topic_id INTEGER NOT NULL,
    model TEXT NOT NULL,
    bucket_start TEXT NOT NULL,
    predicted REAL NOT NULL,
    lower REAL,
    upper REAL,
    created_at TEXT NOT NULL
);

-- Experimental behaviour likelihood (timing/co-posting features only; never
-- demographic, never labelled "bot" in the UI).
CREATE TABLE IF NOT EXISTS account_behaviour (
    platform TEXT NOT NULL,
    account_id TEXT NOT NULL,
    likelihood REAL NOT NULL,
    features_json TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    PRIMARY KEY (platform, account_id)
);

-- Precomputed KOL / bridge rankings per view (raw | organic); centrality over
-- thousands of accounts is too slow to compute per request on small servers.
CREATE TABLE IF NOT EXISTS influence_cache (
    view TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    computed_at TEXT NOT NULL
);

-- Audience segments (network communities) for "spread between segments" (PS E).
CREATE TABLE IF NOT EXISTS account_segments (
    account_id TEXT PRIMARY KEY,
    segment INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS segment_labels (
    segment INTEGER PRIMARY KEY,
    label TEXT NOT NULL,
    size INTEGER NOT NULL,
    computed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS summaries (
    scope TEXT NOT NULL,
    scope_id TEXT NOT NULL,
    model TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (scope, scope_id)
);

CREATE TABLE IF NOT EXISTS collector_targets (
    collector TEXT NOT NULL,
    target TEXT NOT NULL,
    added_at TEXT NOT NULL,
    PRIMARY KEY (collector, target)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    detail_json TEXT,
    ledger_seq INTEGER
);
