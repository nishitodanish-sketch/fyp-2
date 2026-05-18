CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    file_path TEXT,
    timestamp REAL,
    is_directory INTEGER
);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    file_path TEXT,
    timestamp REAL,
    file_size INTEGER,
    entropy REAL,
    mime_type TEXT,
    extension TEXT,
    permissions TEXT,
    sha256_hash TEXT,
    features_json TEXT,
    is_training_sample INTEGER DEFAULT 0,
    FOREIGN KEY(event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    anomaly_score REAL,
    verdict INTEGER,
    timestamp REAL,
    details TEXT,
    FOREIGN KEY(event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS quarantine_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_path TEXT,
    quarantine_path TEXT,
    timestamp REAL,
    reason TEXT,
    restored INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS known_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT,
    sha256_hash TEXT,
    timestamp REAL,
    UNIQUE(file_path, sha256_hash)
);
