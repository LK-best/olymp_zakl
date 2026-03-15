# server/app.py
"""
Главный файл Flask-приложения.
Запуск: python -m server.app
"""
import os
import sys

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from routes import api
from init_db import init_database
import database as db


def create_app() -> Flask:
    """Фабрика приложения Flask"""
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    
    # CORS для фронтенда
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Регистрация блюпринта API
    app.register_blueprint(api)
    
    # Создание необходимых директорий
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
    
    # Инициализация БД при первом запуске
    if not db.check_db_exists():
        print("БД не найдена, инициализация...")
        init_database()
    
    # Обработчики ошибок
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Ресурс не найден'}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': 'Метод не разрешён'}), 405
    
    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({'error': 'Файл слишком большой (макс. 500 MB)'}), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500
    
    # Корневой маршрут
    @app.route('/')
    def index():
        return jsonify({
            'name': 'Alien Signal Classifier API',
            'version': '1.0',
            'description': 'API для классификации инопланетных радиосигналов',
            'endpoints': {
                'auth': {
                    'POST /api/auth/login': 'Вход в систему',
                    'POST /api/auth/logout': 'Выход из системы',
                    'GET /api/auth/me': 'Информация о текущем пользователе'
                },
                'admin': {
                    'POST /api/admin/users': 'Создание пользователя',
                    'GET /api/admin/users': 'Список пользователей',
                    'GET /api/admin/users/<id>': 'Информация о пользователе',
                    'DELETE /api/admin/users/<id>': 'Удаление пользователя',
                    'GET /api/admin/stats': 'Статистика системы'
                },
                'test': {
                    'POST /api/test/upload': 'Загрузка тестового набора данных',
                    'GET /api/test/results': 'Список результатов тестирования',
                    'GET /api/test/results/<id>': 'Детали результата'
                },
                'analytics': {
                    'GET /api/analytics/accuracy-epochs': 'Точность от эпох',
                    'GET /api/analytics/class-distribution': 'Распределение классов',
                    'GET /api/analytics/test-per-sample/<id>': 'Точность по записям',
                    'GET /api/analytics/top5-validation': 'Топ-5 классов валидации',
                    'GET /api/analytics/full': 'Полная аналитика',
                    'GET /api/analytics/test-summary/<id>': 'Сводка теста'
                },
                'model': {
                    'GET /api/model/info': 'Информация о модели',
                    'GET /api/model/training-history': 'История обучения'
                },
                'other': {
                    'GET /api/dataset/info': 'Информация о датасете',
                    'GET /api/health': 'Состояние сервера'
                }
            }
        }), 200
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    print("=" * 50)
    print("ЗАПУСК СЕРВЕРА")
    print("=" * 50)
    print(f"БД: {Config.DB_PATH}")
    print(f"Модель: {Config.MODEL_PATH}")
    print(f"Датасет: {Config.DATA_PATH}")
    print(f"Загрузки: {Config.UPLOAD_FOLDER}")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )