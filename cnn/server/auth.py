# server/auth.py
"""
Модуль авторизации: JWT-токены, декораторы проверки доступа.
"""
import jwt
import datetime
import uuid
from functools import wraps
from flask import request, jsonify, g

from server.config import Config
from server import database as db


def generate_token(user_id: int, role: str) -> str:
    """Генерация JWT-токена"""
    payload = {
        'user_id': user_id,
        'role': role,
        'jti': str(uuid.uuid4()),  # Уникальный ID токена
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(
            hours=Config.JWT_EXPIRATION_HOURS
        )
    }
    token = jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')
    return token


def decode_token(token: str) -> dict:
    """Декодирование JWT-токена"""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Токен истёк'}
    except jwt.InvalidTokenError:
        return {'error': 'Невалидный токен'}


def login_user(login: str, password: str) -> dict:
    """
    Авторизация пользователя.
    Возвращает токен и информацию о пользователе.
    """
    user = db.authenticate_user(login, password)
    if user is None:
        return {'error': 'Неверный логин или пароль'}
    
    token = generate_token(user['id'], user['role'])
    
    # Сохраняем сессию в БД
    db.create_session(
        user_id=user['id'],
        token=token,
        expiration_hours=Config.JWT_EXPIRATION_HOURS
    )
    
    # Логируем вход
    db.log_action(user['id'], 'login', f'Вход в систему: {login}')
    
    return {
        'token': token,
        'user': {
            'id': user['id'],
            'login': user['login'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'role': user['role']
        }
    }


def logout_user(token: str) -> bool:
    """Выход пользователя (инвалидация токена)"""
    payload = decode_token(token)
    if 'error' not in payload:
        db.log_action(payload.get('user_id'), 'logout', 'Выход из системы')
    db.invalidate_session(token)
    return True


def get_current_user_from_token():
    """Извлечение текущего пользователя из заголовка Authorization"""
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ', 1)[1]
    payload = decode_token(token)
    
    if 'error' in payload:
        return None
    
    # Проверяем сессию в БД
    session = db.get_session_by_token(token)
    if session is None:
        return None
    
    user = db.get_user_by_id(payload['user_id'])
    return user


# ============================================================
# ДЕКОРАТОРЫ
# ============================================================

def login_required(f):
    """Декоратор: требуется авторизация"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user_from_token()
        if user is None:
            return jsonify({'error': 'Требуется авторизация'}), 401
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Декоратор: требуется роль администратора"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user_from_token()
        if user is None:
            return jsonify({'error': 'Требуется авторизация'}), 401
        if user['role'] != 'admin':
            return jsonify({'error': 'Требуются права администратора'}), 403
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def user_required(f):
    """Декоратор: требуется роль пользователя (или админа)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user_from_token()
        if user is None:
            return jsonify({'error': 'Требуется авторизация'}), 401
        g.current_user = user
        return f(*args, **kwargs)
    return decorated