# server/routes.py
"""
Маршруты REST API.
"""
import os
import uuid
from flask import Blueprint, request, jsonify, g

from server.config import Config
from server.auth import (
    login_required, admin_required, user_required,
    login_user, logout_user
)
from server import database as db
from server import model_service
from server import analytics

api = Blueprint('api', __name__, url_prefix='/api')


# ============================================================
# АВТОРИЗАЦИЯ
# ============================================================

@api.route('/auth/login', methods=['POST'])
def api_login():
    """Вход в систему"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Отсутствуют данные'}), 400
    
    login = data.get('login', '').strip()
    password = data.get('password', '')
    
    if not login or not password:
        return jsonify({'error': 'Логин и пароль обязательны'}), 400
    
    result = login_user(login, password)
    
    if 'error' in result:
        return jsonify(result), 401
    
    return jsonify(result), 200


@api.route('/auth/logout', methods=['POST'])
@login_required
def api_logout():
    """Выход из системы"""
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ', 1)[1] if auth_header.startswith('Bearer ') else ''
    logout_user(token)
    return jsonify({'message': 'Выход выполнен успешно'}), 200


@api.route('/auth/me', methods=['GET'])
@login_required
def api_get_current_user():
    """Получение информации о текущем пользователе"""
    user = g.current_user
    return jsonify({
        'id': user['id'],
        'login': user['login'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'role': user['role'],
        'created_at': user.get('created_at')
    }), 200


# ============================================================
# АДМИНИСТРАТОР: УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ
# ============================================================

@api.route('/admin/users', methods=['POST'])
@admin_required
def api_create_user():
    """Создание нового пользователя (только админ)"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Отсутствуют данные'}), 400
    
    login = data.get('login', '').strip()
    password = data.get('password', '')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    role = data.get('role', 'user')
    
    # Валидация
    errors = []
    if not login:
        errors.append('Логин обязателен')
    if not password:
        errors.append('Пароль обязателен')
    if not first_name:
        errors.append('Имя обязательно')
    if not last_name:
        errors.append('Фамилия обязательна')
    if len(login) < 3:
        errors.append('Логин должен содержать минимум 3 символа')
    if len(password) < 4:
        errors.append('Пароль должен содержать минимум 4 символа')
    if role not in ('user', 'admin'):
        errors.append('Роль должна быть "user" или "admin"')
    
    if errors:
        return jsonify({'error': '; '.join(errors)}), 400
    
    user = db.create_user(
        login=login,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=role,
        created_by=g.current_user['id']
    )
    
    if user is None:
        return jsonify({'error': f'Пользователь с логином "{login}" уже существует'}), 409
    
    # Логируем
    db.log_action(
        g.current_user['id'],
        'create_user',
        f'Создан пользователь: {login} ({first_name} {last_name}), роль: {role}'
    )
    
    return jsonify({
        'message': 'Пользователь успешно создан',
        'user': user
    }), 201


@api.route('/admin/users', methods=['GET'])
@admin_required
def api_get_users():
    """Получение списка всех пользователей (только админ)"""
    users = db.get_all_users()
    return jsonify({'users': users}), 200


@api.route('/admin/users/<int:user_id>', methods=['GET'])
@admin_required
def api_get_user(user_id):
    """Получение информации о конкретном пользователе"""
    user = db.get_user_by_id(user_id)
    if user is None:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    # Убираем хеш пароля
    user.pop('password_hash', None)
    return jsonify({'user': user}), 200


@api.route('/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def api_delete_user(user_id):
    """Удаление пользователя (мягкое)"""
    if user_id == g.current_user['id']:
        return jsonify({'error': 'Нельзя удалить самого себя'}), 400
    
    success = db.delete_user(user_id)
    if not success:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    db.invalidate_user_sessions(user_id)
    db.log_action(g.current_user['id'], 'delete_user', f'Удалён пользователь ID={user_id}')
    
    return jsonify({'message': 'Пользователь удалён'}), 200


@api.route('/admin/stats', methods=['GET'])
@admin_required
def api_get_stats():
    """Статистика системы"""
    stats = db.get_db_stats()
    return jsonify(stats), 200


# ============================================================
# ПОЛЬЗОВАТЕЛЬ: ЗАГРУЗКА ТЕСТОВОГО НАБОРА ДАННЫХ
# ============================================================

@api.route('/test/upload', methods=['POST'])
@login_required
def api_upload_test_data():
    """
    Загрузка тестового набора данных (.npz) и оценка модели.
    ТЗ: "загрузка набора данных для проверки работы модели"
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не загружен'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    # Проверка расширения
    if not file.filename.lower().endswith('.npz'):
        return jsonify({'error': 'Допускаются только файлы формата .npz'}), 400
    
    # Сохранение файла
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
    file.save(file_path)
    
    try:
        # Оценка модели на загруженных данных
        result = model_service.evaluate_test_dataset(file_path)
        
        # Сохранение результата в БД
        db_result = db.save_test_result(
            user_id=g.current_user['id'],
            filename=file.filename,
            total_samples=result['total_samples'],
            accuracy=result['accuracy'],
            loss=result['loss'],
            predictions=result['predicted_classes'],
            true_labels=result['true_classes'],
            per_class_accuracy=result['per_class_accuracy']
        )
        
        # Логируем
        db.log_action(
            g.current_user['id'],
            'upload_test',
            f'Загружен тестовый набор: {file.filename}, '
            f'accuracy={result["accuracy"]:.4f}, loss={result["loss"]:.4f}'
        )
        
        return jsonify({
            'message': 'Тестовый набор загружен и обработан',
            'result_id': db_result['id'],
            'accuracy': result['accuracy'],
            'loss': result['loss'],
            'total_samples': result['total_samples'],
            'correct_predictions': result['correct_predictions'],
            'per_class_accuracy': result['per_class_accuracy'],
            'per_sample_accuracy': result.get('per_sample_accuracy', [])
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Ошибка обработки файла: {str(e)}'}), 500
    finally:
        # Удаляем загруженный файл после обработки
        if os.path.exists(file_path):
            os.remove(file_path)


@api.route('/test/results', methods=['GET'])
@login_required
def api_get_test_results():
    """Получение всех результатов тестирования текущего пользователя"""
    results = db.get_test_results_by_user(g.current_user['id'])
    
    # Убираем тяжёлые поля для списка
    summary_results = []
    for r in results:
        summary_results.append({
            'id': r['id'],
            'filename': r['filename'],
            'total_samples': r['total_samples'],
            'accuracy': r['accuracy'],
            'loss': r['loss'],
            'created_at': r['created_at']
        })
    
    return jsonify({'results': summary_results}), 200


@api.route('/test/results/<int:result_id>', methods=['GET'])
@login_required
def api_get_test_result_detail(result_id):
    """Получение детального результата тестирования"""
    result = db.get_test_result_by_id(result_id)
    
    if result is None:
        return jsonify({'error': 'Результат не найден'}), 404
    
    # Проверяем что результат принадлежит текущему пользователю (или он админ)
    if result['user_id'] != g.current_user['id'] and g.current_user['role'] != 'admin':
        return jsonify({'error': 'Доступ запрещён'}), 403
    
    return jsonify({'result': result}), 200


# ============================================================
# АНАЛИТИКА
# ============================================================

@api.route('/analytics/accuracy-epochs', methods=['GET'])
@login_required
def api_accuracy_vs_epochs():
    """
    График точности от эпох.
    ТЗ: "просмотр графика зависимости точности на валидационных данных
         от количества эпох обучения"
    """
    data = analytics.get_accuracy_vs_epochs()
    return jsonify(data), 200


@api.route('/analytics/class-distribution', methods=['GET'])
@login_required
def api_class_distribution():
    """
    Распределение классов в обучающем наборе.
    ТЗ: "просмотр диаграммы с отображением количества записей в наборе данных
         для обучения, относящихся к каждой цивилизации (классу)"
    """
    data = analytics.get_class_distribution()
    return jsonify(data), 200


@api.route('/analytics/test-per-sample/<int:result_id>', methods=['GET'])
@login_required
def api_test_per_sample(result_id):
    """
    Точность определения каждой записи из тестового набора.
    ТЗ: "диаграмму, демонстрирующую точность определения каждой записи
         из тестового набора данных"
    """
    test_result = db.get_test_result_by_id(result_id)
    if test_result is None:
        return jsonify({'error': 'Результат не найден'}), 404
    
    if test_result['user_id'] != g.current_user['id'] and g.current_user['role'] != 'admin':
        return jsonify({'error': 'Доступ запрещён'}), 403
    
    data = analytics.get_test_per_sample_accuracy(test_result)
    return jsonify(data), 200


@api.route('/analytics/top5-validation', methods=['GET'])
@login_required
def api_top5_validation():
    """
    Топ-5 классов в валидационном наборе.
    ТЗ: "диаграмму, демонстрирующую топ-5 наиболее часто встречающихся
         классов записей в валидационном наборе данных"
    """
    data = analytics.get_top5_validation_classes()
    return jsonify(data), 200


@api.route('/analytics/full', methods=['GET'])
@login_required
def api_full_analytics():
    """Полная аналитика (все графики сразу)"""
    result_id = request.args.get('result_id', type=int)
    data = analytics.get_full_analytics(result_id)
    return jsonify(data), 200


@api.route('/analytics/test-summary/<int:result_id>', methods=['GET'])
@login_required
def api_test_summary(result_id):
    """
    Точность и потери на тестовом наборе.
    ТЗ: "отображение точности и потерь на тестовом наборе данных"
    """
    test_result = db.get_test_result_by_id(result_id)
    if test_result is None:
        return jsonify({'error': 'Результат не найден'}), 404
    
    if test_result['user_id'] != g.current_user['id'] and g.current_user['role'] != 'admin':
        return jsonify({'error': 'Доступ запрещён'}), 403
    
    return jsonify({
        'accuracy': test_result['accuracy'],
        'loss': test_result['loss'],
        'total_samples': test_result['total_samples'],
        'filename': test_result['filename'],
        'created_at': test_result['created_at'],
        'per_class_accuracy': test_result.get('per_class_accuracy', {})
    }), 200


# ============================================================
# МОДЕЛЬ
# ============================================================

@api.route('/model/info', methods=['GET'])
@login_required
def api_model_info():
    """Информация о модели"""
    config = model_service.get_model_config()
    
    try:
        summary = model_service.get_model_summary()
    except Exception:
        summary = 'Модель не загружена'
    
    return jsonify({
        'config': config,
        'summary': summary
    }), 200


@api.route('/model/training-history', methods=['GET'])
@login_required
def api_training_history():
    """Полная история обучения"""
    history = model_service.get_training_history()
    return jsonify(history), 200


# ============================================================
# DATASET INFO
# ============================================================

@api.route('/dataset/info', methods=['GET'])
@login_required
def api_dataset_info():
    """Информация о датасете"""
    info = model_service.get_training_dataset_info()
    return jsonify(info), 200


# ============================================================
# ЗДОРОВЬЕ СЕРВЕРА
# ============================================================

@api.route('/health', methods=['GET'])
def api_health():
    """Проверка здоровья сервера"""
    checks = {
        'server': 'ok',
        'database': 'ok' if db.check_db_exists() else 'error',
        'model': 'ok' if os.path.exists(Config.MODEL_PATH) else 'not_found',
        'dataset': 'ok' if os.path.exists(Config.DATA_PATH) else 'not_found'
    }
    
    status = 200 if all(v == 'ok' for v in checks.values()) else 503
    return jsonify(checks), status