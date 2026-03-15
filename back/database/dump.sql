BEGIN TRANSACTION;
CREATE TABLE class_distribution (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_type    TEXT    NOT NULL CHECK(dataset_type IN ('train', 'valid', 'test')),
    class_id        INTEGER NOT NULL,
    class_label     TEXT,
    record_count    INTEGER NOT NULL DEFAULT 0
);
INSERT INTO "class_distribution" VALUES(1,'train',0,NULL,50);
INSERT INTO "class_distribution" VALUES(2,'train',1,NULL,80);
INSERT INTO "class_distribution" VALUES(3,'train',2,NULL,110);
INSERT INTO "class_distribution" VALUES(4,'train',3,NULL,50);
INSERT INTO "class_distribution" VALUES(5,'train',4,NULL,80);
INSERT INTO "class_distribution" VALUES(6,'train',5,NULL,110);
INSERT INTO "class_distribution" VALUES(7,'train',6,NULL,50);
INSERT INTO "class_distribution" VALUES(8,'train',7,NULL,80);
INSERT INTO "class_distribution" VALUES(9,'train',8,NULL,110);
INSERT INTO "class_distribution" VALUES(10,'train',9,NULL,50);
INSERT INTO "class_distribution" VALUES(11,'valid',0,NULL,20);
INSERT INTO "class_distribution" VALUES(12,'valid',1,NULL,30);
INSERT INTO "class_distribution" VALUES(13,'valid',2,NULL,40);
INSERT INTO "class_distribution" VALUES(14,'valid',3,NULL,50);
INSERT INTO "class_distribution" VALUES(15,'valid',4,NULL,20);
INSERT INTO "class_distribution" VALUES(16,'valid',5,NULL,30);
INSERT INTO "class_distribution" VALUES(17,'valid',6,NULL,40);
INSERT INTO "class_distribution" VALUES(18,'valid',7,NULL,50);
INSERT INTO "class_distribution" VALUES(19,'valid',8,NULL,20);
INSERT INTO "class_distribution" VALUES(20,'valid',9,NULL,30);
CREATE TABLE datasets (
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
CREATE TABLE sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    login_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
INSERT INTO "sessions" VALUES(1,1,'2026-03-15 09:33:44');
INSERT INTO "sessions" VALUES(2,2,'2026-03-15 09:33:44');
CREATE TABLE test_predictions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id      INTEGER NOT NULL,
    record_index    INTEGER NOT NULL,
    true_class      INTEGER NOT NULL,
    predicted_class INTEGER NOT NULL,
    confidence      REAL    NOT NULL DEFAULT 0.0,
    is_correct      BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);
CREATE TABLE training_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    epoch           INTEGER NOT NULL,
    train_accuracy  REAL    NOT NULL,
    val_accuracy    REAL    NOT NULL,
    train_loss      REAL    NOT NULL,
    val_loss        REAL    NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO "training_history" VALUES(1,1,3.349999999999999644e-01,0.28,1.92,2.130000000000000337e+00,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(2,2,0.37,0.31,1.84,2.06,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(3,3,0.405,3.399999999999999689e-01,1.76,1.990000000000000214e+00,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(4,4,0.44,0.37,1.68,1.920000000000000151e+00,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(5,5,0.475,0.4,1.6,1.85,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(6,6,0.51,0.43,1.52,1.780000000000000249e+00,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(7,7,0.545,4.599999999999999644e-01,1.44,1.710000000000000187e+00,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(8,8,5.800000000000000711e-01,0.49,1.359999999999999876e+00,1.640000000000000124e+00,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(9,9,0.615,0.52,1.28,1.57,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(10,10,0.65,0.55,1.2,1.5,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(11,11,0.685,0.58,1.12,1.43000000000000016e+00,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(12,12,0.72,0.61,1.04,1.36,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(13,13,7.550000000000001154e-01,0.64,0.96,1.29,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(14,14,0.79,6.699999999999999289e-01,8.799999999999998935e-01,1.220000000000000196e+00,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(15,15,0.825,0.7,0.8,1.150000000000000133e+00,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(16,16,8.600000000000000977e-01,0.73,0.72,1.08,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(17,17,0.895,0.76,6.399999999999999023e-01,1.01,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(18,18,9.30000000000000159e-01,0.79,0.56,0.94,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(19,19,9.6500000000000008e-01,0.82,0.48,8.700000000000001065e-01,'2026-03-15 09:33:44');
INSERT INTO "training_history" VALUES(20,20,0.99,0.85,3.999999999999999111e-01,0.8,'2026-03-15 09:33:44');
CREATE TABLE users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    login       TEXT    NOT NULL UNIQUE,
    password    TEXT    NOT NULL,
    role        TEXT    NOT NULL DEFAULT 'user' CHECK(role IN ('admin', 'user')),
    first_name  TEXT    NOT NULL,
    last_name   TEXT    NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO "users" VALUES(1,'admin','admin','admin','Михаил','Администратор','2026-03-15 09:33:44');
INSERT INTO "users" VALUES(2,'user1','pass123','user','Иван','Петров','2026-03-15 09:33:44');
CREATE INDEX idx_users_login ON users(login);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_predictions_dataset ON test_predictions(dataset_id);
CREATE INDEX idx_class_dist_type ON class_distribution(dataset_type);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('users',2);
INSERT INTO "sqlite_sequence" VALUES('sessions',2);
INSERT INTO "sqlite_sequence" VALUES('training_history',20);
INSERT INTO "sqlite_sequence" VALUES('class_distribution',20);
COMMIT;
