# server/database.py
"""
Модуль работы с базой данных SQLite.
Все CRUD-операции для всех таблиц.
"""
import sqlite3
import hashlib
import datetime
import json
import os
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

from server.config import Config


# ============================================================
# ПОДКЛЮЧЕНИЕ К БД
# ============================================================

@contextmanager
def get_db():
    """Контекстный менеджер для подключения к БД"""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row  # Доступ по имени столбца
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def dict_from_row(row) -> Optional[Dict]:
    """Преобразование sqlite3.Row в dict"""
    if row is None:
        return None
    return dict(row)


def get_password_hash(password: str) -> str:
    """Хеширование пароля SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Проверка пароля"""
    return get_password_hash(password) == password_hash


# ============================================================
# ПОЛЬЗОВАТЕЛИ
# ============================================================

def create_user(
    login: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str = 'user',
    created_by: Optional[int] = None
) -> Optional[Dict]:
    """
    Создание нового пользователя.
    Возвращает dict с данными пользователя или None при ошибке.
    """
    password_hash = get_password_hash(password)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Проверяем уникальность логина
        cursor.execute('SELECT id FROM users WHERE login = ?', (login,))
        if cursor.fetchone() is not None:
            return None  # Логин занят
        
        cursor.execute('''
            INSERT INTO users (login, password_hash, first_name, last_name, role, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (login, password_hash, first_name, last_name, role, created_by))
        
        user_id = cursor.lastrowid
        
        return {
            'id': user_id,
            'login': login,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
            'created_by': created_by
        }


def get_user_by_login(login: str) -> Optional[Dict]:
    """Получение пользователя по логину"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE login = ? AND is_active = 1',
            (login,)
        )
        row = cursor.fetchone()
        return dict_from_row(row)


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Получение пользователя по ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE id = ? AND is_active = 1',
            (user_id,)
        )
        row = cursor.fetchone()
        return dict_from_row(row)


def authenticate_user(login: str, password: str) -> Optional[Dict]:
    """
    Аутентификация пользователя.
    Возвращает данные пользователя при успехе, None при неудаче.
    """
    user = get_user_by_login(login)
    if user is None:
        return None
    if not verify_password(password, user['password_hash']):
        return None
    return user


def get_all_users() -> List[Dict]:
    """Получение списка всех активных пользователей"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, login, first_name, last_name, role, created_at, created_by
            FROM users
            WHERE is_active = 1
            ORDER BY created_at DESC
        ''')
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


def get_users_by_role(role: str) -> List[Dict]:
    """Получение пользователей по роли"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, login, first_name, last_name, role, created_at, created_by
            FROM users
            WHERE role = ? AND is_active = 1
            ORDER BY created_at DESC
        ''', (role,))
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


def update_user(user_id: int, **kwargs) -> bool:
    """Обновление данных пользователя"""
    allowed_fields = {'first_name', 'last_name', 'login', 'is_active'}
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        return False
    
    set_clause = ', '.join(f'{k} = ?' for k in updates.keys())
    values = list(updates.values()) + [user_id]
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE users SET {set_clause} WHERE id = ?',
            values
        )
        return cursor.rowcount > 0


def change_password(user_id: int, new_password: str) -> bool:
    """Смена пароля пользователя"""
    password_hash = get_password_hash(new_password)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (password_hash, user_id)
        )
        return cursor.rowcount > 0


def delete_user(user_id: int) -> bool:
    """Мягкое удаление пользователя (деактивация)"""
    return update_user(user_id, is_active=0)


def get_user_count() -> Dict[str, int]:
    """Количество пользователей по ролям"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT role, COUNT(*) as count
            FROM users
            WHERE is_active = 1
            GROUP BY role
        ''')
        rows = cursor.fetchall()
        result = {'total': 0}
        for row in rows:
            r = dict_from_row(row)
            result[r['role']] = r['count']
            result['total'] += r['count']
        return result


# ============================================================
# СЕССИИ
# ============================================================

def create_session(user_id: int, token: str, expiration_hours: int = 24) -> Dict:
    """Создание сессии для пользователя"""
    expires_at = datetime.datetime.now() + datetime.timedelta(hours=expiration_hours)
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (user_id, token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, token, expires_at.isoformat()))
        
        return {
            'id': cursor.lastrowid,
            'user_id': user_id,
            'token': token,
            'expires_at': expires_at.isoformat()
        }


def get_session_by_token(token: str) -> Optional[Dict]:
    """Получение активной сессии по токену"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, u.login, u.first_name, u.last_name, u.role
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
              AND s.is_active = 1
              AND s.expires_at > ?
              AND u.is_active = 1
        ''', (token, datetime.datetime.now().isoformat()))
        row = cursor.fetchone()
        return dict_from_row(row)


def invalidate_session(token: str) -> bool:
    """Деактивация сессии (выход)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE sessions SET is_active = 0 WHERE token = ?',
            (token,)
        )
        return cursor.rowcount > 0


def invalidate_user_sessions(user_id: int) -> int:
    """Деактивация всех сессий пользователя"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE sessions SET is_active = 0 WHERE user_id = ? AND is_active = 1',
            (user_id,)
        )
        return cursor.rowcount


def cleanup_expired_sessions() -> int:
    """Очистка истекших сессий"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE sessions SET is_active = 0 WHERE expires_at < ? AND is_active = 1',
            (datetime.datetime.now().isoformat(),)
        )
        return cursor.rowcount


# ============================================================
# РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ
# ============================================================

def save_test_result(
    user_id: int,
    filename: str,
    total_samples: int,
    accuracy: float,
    loss: float,
    predictions: Optional[List] = None,
    true_labels: Optional[List] = None,
    per_class_accuracy: Optional[Dict] = None
) -> Dict:
    """Сохранение результата тестирования"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO test_results
            (user_id, filename, total_samples, accuracy, loss,
             predictions, true_labels, per_class_accuracy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            filename,
            total_samples,
            accuracy,
            loss,
            json.dumps(predictions) if predictions else None,
            json.dumps(true_labels) if true_labels else None,
            json.dumps(per_class_accuracy) if per_class_accuracy else None
        ))
        
        return {
            'id': cursor.lastrowid,
            'user_id': user_id,
            'filename': filename,
            'total_samples': total_samples,
            'accuracy': accuracy,
            'loss': loss
        }


def get_test_results_by_user(user_id: int) -> List[Dict]:
    """Получение всех результатов тестирования пользователя"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM test_results
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        results = []
        for row in rows:
            r = dict_from_row(row)
            # Десериализация JSON-полей
            if r.get('predictions'):
                r['predictions'] = json.loads(r['predictions'])
            if r.get('true_labels'):
                r['true_labels'] = json.loads(r['true_labels'])
            if r.get('per_class_accuracy'):
                r['per_class_accuracy'] = json.loads(r['per_class_accuracy'])
            results.append(r)
        return results


def get_test_result_by_id(result_id: int) -> Optional[Dict]:
    """Получение конкретного результата тестирования"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM test_results WHERE id = ?', (result_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        r = dict_from_row(row)
        if r.get('predictions'):
            r['predictions'] = json.loads(r['predictions'])
        if r.get('true_labels'):
            r['true_labels'] = json.loads(r['true_labels'])
        if r.get('per_class_accuracy'):
            r['per_class_accuracy'] = json.loads(r['per_class_accuracy'])
        return r


def get_latest_test_result(user_id: int) -> Optional[Dict]:
    """Получение последнего результата тестирования пользователя"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM test_results
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        r = dict_from_row(row)
        if r.get('predictions'):
            r['predictions'] = json.loads(r['predictions'])
        if r.get('true_labels'):
            r['true_labels'] = json.loads(r['true_labels'])
        if r.get('per_class_accuracy'):
            r['per_class_accuracy'] = json.loads(r['per_class_accuracy'])
        return r


def delete_test_result(result_id: int) -> bool:
    """Удаление результата тестирования"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM test_results WHERE id = ?', (result_id,))
        return cursor.rowcount > 0


# ============================================================
# ЛОГИ ДЕЙСТВИЙ
# ============================================================

def log_action(user_id: Optional[int], action: str, details: Optional[str] = None):
    """Запись действия в лог"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO action_logs (user_id, action, details)
            VALUES (?, ?, ?)
        ''', (user_id, action, details))


def get_action_logs(
    user_id: Optional[int] = None,
    limit: int = 100
) -> List[Dict]:
    """Получение логов действий"""
    with get_db() as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute('''
                SELECT al.*, u.login, u.first_name, u.last_name
                FROM action_logs al
                LEFT JOIN users u ON al.user_id = u.id
                WHERE al.user_id = ?
                ORDER BY al.created_at DESC
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT al.*, u.login, u.first_name, u.last_name
                FROM action_logs al
                LEFT JOIN users u ON al.user_id = u.id
                ORDER BY al.created_at DESC
                LIMIT ?
            ''', (limit,))
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


# ============================================================
# УТИЛИТЫ
# ============================================================

def get_db_stats() -> Dict:
    """Статистика по БД"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin" AND is_active = 1')
        admin_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "user" AND is_active = 1')
        user_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE is_active = 1')
        active_sessions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM test_results')
        total_tests = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM action_logs')
        total_logs = cursor.fetchone()[0]
        
        # Размер файла БД
        db_size = os.path.getsize(Config.DB_PATH) if os.path.exists(Config.DB_PATH) else 0
        
        return {
            'total_users': total_users,
            'admins': admin_count,
            'users': user_count,
            'active_sessions': active_sessions,
            'total_tests': total_tests,
            'total_logs': total_logs,
            'db_size_bytes': db_size,
            'db_size_mb': round(db_size / (1024 * 1024), 2)
        }


def check_db_exists() -> bool:
    """Проверка существования БД"""
    return os.path.exists(Config.DB_PATH)