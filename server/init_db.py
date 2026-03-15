# server/init_db.py
"""
Скрипт инициализации базы данных.
Создаёт таблицы и администратора по умолчанию.
Запуск: python -m server.init_db
"""
import os
import sys
import sqlite3
import hashlib
import datetime

# Добавляем корень проекта в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.config import Config


def get_password_hash(password: str) -> str:
    """Хеширование пароля SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def init_database():
    """Полная инициализация БД: создание таблиц и дефолтного админа"""
    
    # Создаём директорию для БД если нет
    db_dir = os.path.dirname(Config.DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"Создана директория: {db_dir}")
    
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 50)
    print("ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    # --------------------------------------------------------
    # Таблица пользователей
    # --------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    print("✓ Таблица 'users' создана/проверена")
    
    # --------------------------------------------------------
    # Таблица сессий (для отслеживания входов)
    # --------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    print("✓ Таблица 'sessions' создана/проверена")
    
    # --------------------------------------------------------
    # Таблица результатов тестирования
    # --------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            total_samples INTEGER NOT NULL,
            accuracy REAL NOT NULL,
            loss REAL NOT NULL,
            predictions TEXT,
            true_labels TEXT,
            per_class_accuracy TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    print("✓ Таблица 'test_results' создана/проверена")
    
    # --------------------------------------------------------
    # Таблица логов действий
    # --------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    print("✓ Таблица 'action_logs' создана/проверена")
    
    # --------------------------------------------------------
    # Создание администратора по умолчанию
    # --------------------------------------------------------
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('admin',))
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        password_hash = get_password_hash(Config.DEFAULT_ADMIN_PASSWORD)
        cursor.execute('''
            INSERT INTO users (login, password_hash, first_name, last_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            Config.DEFAULT_ADMIN_LOGIN,
            password_hash,
            Config.DEFAULT_ADMIN_FIRST_NAME,
            Config.DEFAULT_ADMIN_LAST_NAME,
            'admin'
        ))
        print(f"\n✓ Администратор создан:")
        print(f"  Логин: {Config.DEFAULT_ADMIN_LOGIN}")
        print(f"  Пароль: {Config.DEFAULT_ADMIN_PASSWORD}")
    else:
        print(f"\n✓ Администратор уже существует ({admin_count} шт.)")
    
    # --------------------------------------------------------
    # Создание индексов
    # --------------------------------------------------------
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_login ON users(login)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_results_user ON test_results(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_action_logs_user ON action_logs(user_id)')
    print("✓ Индексы созданы/проверены")
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ База данных инициализирована: {Config.DB_PATH}")
    print("=" * 50)


def reset_database():
    """Полный сброс БД (удаление и пересоздание)"""
    if os.path.exists(Config.DB_PATH):
        os.remove(Config.DB_PATH)
        print(f"Старая БД удалена: {Config.DB_PATH}")
    init_database()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_database()
    else:
        init_database()