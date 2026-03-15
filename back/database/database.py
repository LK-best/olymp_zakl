import sqlite3
import os

DB_NAME = "back//database//database.db"
SCHEMA_FILE = "back//database//database.sql"


class Database:

    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_name)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    # Инициализация БД из SQL-файла
    def init_db(self):
        conn = self.connect()
        cursor = conn.cursor()

        with open(SCHEMA_FILE, 'r', encoding='utf-8') as file:
            sql_schema = file.read()

        cursor.executescript(sql_schema)
        conn.commit()
        self.close()
        print(f"[DB] База данных '{self.db_name}' инициализирована из '{SCHEMA_FILE}'")

    # Пользователи
    def authenticate(self, login: str, password: str) -> dict | None:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, role, first_name, last_name FROM users WHERE login=? AND password=?",
            (login, password)
        )
        row = cursor.fetchone()
        self.close()

        if row:
            self.log_session(row["id"])
            return {
                "id": row["id"],
                "role": row["role"],
                "first_name": row["first_name"],
                "last_name": row["last_name"]
            }
        return None

    def create_user(self, login: str, password: str, role: str,
                    first_name: str, last_name: str) -> bool:
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (login, password, role, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                (login, password, role, first_name, last_name)
            )
            conn.commit()
            self.close()
            return True
        except sqlite3.IntegrityError:
            self.close()
            return False

    def get_all_users(self) -> list:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, login, role, first_name, last_name, created_at FROM users")
        rows = cursor.fetchall()
        self.close()
        return [dict(row) for row in rows]

    # Сессии
    def log_session(self, user_id: int):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (user_id) VALUES (?)", (user_id,))
        conn.commit()
        self.close()

    def get_sessions(self, user_id: int = None) -> list:
        conn = self.connect()
        cursor = conn.cursor()
        if user_id:
            cursor.execute(
                "SELECT s.id, u.login, u.first_name, u.last_name, s.login_time "
                "FROM sessions s JOIN users u ON s.user_id = u.id "
                "WHERE s.user_id = ? ORDER BY s.login_time DESC",
                (user_id,)
            )
        else:
            cursor.execute(
                "SELECT s.id, u.login, u.first_name, u.last_name, s.login_time "
                "FROM sessions s JOIN users u ON s.user_id = u.id "
                "ORDER BY s.login_time DESC"
            )
        rows = cursor.fetchall()
        self.close()
        return [dict(row) for row in rows]

    # История обучения
    def save_training_history(self, history: list[dict]):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM training_history")
        for entry in history:
            cursor.execute(
                "INSERT INTO training_history (epoch, train_accuracy, val_accuracy, train_loss, val_loss) "
                "VALUES (?, ?, ?, ?, ?)",
                (entry["epoch"], entry["train_accuracy"], entry["val_accuracy"],
                 entry["train_loss"], entry["val_loss"])
            )
        conn.commit()
        self.close()

    def get_training_history(self) -> list:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM training_history ORDER BY epoch")
        rows = cursor.fetchall()
        self.close()
        return [dict(row) for row in rows]

    # Распределение классов
    def save_class_distribution(self, dataset_type: str, distribution: dict):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM class_distribution WHERE dataset_type = ?", (dataset_type,))
        for class_id, count in distribution.items():
            cursor.execute(
                "INSERT INTO class_distribution (dataset_type, class_id, record_count) VALUES (?, ?, ?)",
                (dataset_type, int(class_id), int(count))
            )
        conn.commit()
        self.close()

    def get_class_distribution(self, dataset_type: str) -> list:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT class_id, record_count FROM class_distribution "
            "WHERE dataset_type = ? ORDER BY class_id",
            (dataset_type,)
        )
        rows = cursor.fetchall()
        self.close()
        return [dict(row) for row in rows]

    def get_top_classes(self, dataset_type: str, top_n: int = 5) -> list:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT class_id, record_count FROM class_distribution "
            "WHERE dataset_type = ? ORDER BY record_count DESC LIMIT ?",
            (dataset_type, top_n)
        )
        rows = cursor.fetchall()
        self.close()
        return [dict(row) for row in rows]

    # Датасеты и предсказания
    def save_dataset_info(self, user_id: int, file_name: str, file_path: str,
                          total_records: int, accuracy: float, loss: float) -> int:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO datasets (user_id, file_name, file_path, total_records, overall_accuracy, overall_loss) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, file_name, file_path, total_records, accuracy, loss)
        )
        dataset_id = cursor.lastrowid
        conn.commit()
        self.close()
        return dataset_id

    def save_predictions(self, dataset_id: int, predictions: list[dict]):
        conn = self.connect()
        cursor = conn.cursor()
        for pred in predictions:
            is_correct = 1 if pred["true_class"] == pred["predicted_class"] else 0
            cursor.execute(
                "INSERT INTO test_predictions "
                "(dataset_id, record_index, true_class, predicted_class, confidence, is_correct) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (dataset_id, pred["record_index"], pred["true_class"],
                 pred["predicted_class"], pred["confidence"], is_correct)
            )
        conn.commit()
        self.close()

    def get_predictions(self, dataset_id: int) -> list:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM test_predictions WHERE dataset_id = ? ORDER BY record_index",
            (dataset_id,)
        )
        rows = cursor.fetchall()
        self.close()
        return [dict(row) for row in rows]

    def get_latest_dataset(self) -> dict | None:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM datasets ORDER BY uploaded_at DESC LIMIT 1")
        row = cursor.fetchone()
        self.close()
        return dict(row) if row else None

    # Дамп БД
    def dump_to_sql(self, output_file: str = "back//database//dump.sql"):
        conn = self.connect()
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")
        self.close()
        print(f"[DB] Дамп сохранён в '{output_file}'")


if __name__ == "__main__":
    db = Database()
    db.init_db()

    success = db.create_user("user1", "pass123", "user", "Иван", "Петров")
    print(f"Создание пользователя: {'OK' if success else 'Уже существует'}")

    user = db.authenticate("admin", "admin")
    print(f"Авторизация admin: {user}")

    user = db.authenticate("user1", "pass123")
    print(f"Авторизация user1: {user}")

    user = db.authenticate("hacker", "12345")
    print(f"Авторизация hacker: {user}")

    fake_history = []
    for e in range(1, 21):
        fake_history.append({
            "epoch": e,
            "train_accuracy": min(0.3 + e * 0.035, 0.99),
            "val_accuracy": min(0.25 + e * 0.03, 0.95),
            "train_loss": max(2.0 - e * 0.08, 0.1),
            "val_loss": max(2.2 - e * 0.07, 0.2),
        })
    db.save_training_history(fake_history)
    print(f"История обучения: {len(fake_history)} эпох")

    train_dist = {i: int(50 + 30 * (i % 3)) for i in range(10)}
    db.save_class_distribution("train", train_dist)

    valid_dist = {i: int(20 + 10 * (i % 4)) for i in range(10)}
    db.save_class_distribution("valid", valid_dist)

    top5 = db.get_top_classes("valid", top_n=5)
    print(f"Топ-5 классов valid: {top5}")

    print(f"Все пользователи: {db.get_all_users()}")
    print(f"Сессии: {db.get_sessions()}")

    db.dump_to_sql("dump.sql")
    print("[OK] Все тесты пройдены!")