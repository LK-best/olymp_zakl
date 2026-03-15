DROP TABLE IF EXISTS test_predictions;
DROP TABLE IF EXISTS training_history;
DROP TABLE IF EXISTS class_distribution;
DROP TABLE IF EXISTS datasets;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    login       TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,
    role        TEXT    NOT NULL DEFAULT 'user' CHECK(role IN ('admin', 'user')),
    first_name  TEXT    NOT NULL,
    last_name   TEXT    NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    login_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS training_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    epoch           INTEGER NOT NULL,
    train_accuracy  REAL    NOT NULL,
    val_accuracy    REAL    NOT NULL,
    train_loss      REAL    NOT NULL,
    val_loss        REAL    NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS class_distribution (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_type    TEXT    NOT NULL CHECK(dataset_type IN ('train', 'valid', 'test')),
    class_id        INTEGER NOT NULL,
    class_label     TEXT,
    record_count    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS datasets (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL,
    file_name        TEXT    NOT NULL,
    file_path        TEXT    NOT NULL,
    total_records    INTEGER DEFAULT 0,
    overall_accuracy REAL    DEFAULT 0.0,
    overall_loss     REAL    DEFAULT 0.0,
    uploaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS test_predictions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id      INTEGER NOT NULL,
    record_index    INTEGER NOT NULL,
    true_class      INTEGER NOT NULL,
    predicted_class INTEGER NOT NULL,
    confidence      REAL    NOT NULL DEFAULT 0.0,
    is_correct      BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_dataset ON test_predictions(dataset_id);
CREATE INDEX IF NOT EXISTS idx_class_dist_type ON class_distribution(dataset_type);

INSERT OR IGNORE INTO users (login, password, role, first_name, last_name)
VALUES ('admin', 'admin', 'admin', 'Михаил', 'Администратор');