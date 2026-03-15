# server/model_service.py
"""
Сервис работы с моделью нейросети.
Загрузка модели, предсказания, оценка на тестовом наборе.
"""
import numpy as np
import json
import os
import io
from typing import Dict, List, Optional, Tuple

from server.config import Config

# Ленивая загрузка TensorFlow (тяжёлый импорт)
_model = None
_label_mapping = None
_model_config = None
_training_history = None


def _load_tensorflow():
    """Импорт TensorFlow (вызывается один раз)"""
    import tensorflow as tf
    return tf


def get_model():
    """Загрузка обученной модели (синглтон)"""
    global _model
    if _model is None:
        if not os.path.exists(Config.MODEL_PATH):
            raise FileNotFoundError(f"Модель не найдена: {Config.MODEL_PATH}")
        tf = _load_tensorflow()
        _model = tf.keras.models.load_model(Config.MODEL_PATH)
        print(f"Модель загружена: {Config.MODEL_PATH}")
    return _model


def get_label_mapping() -> Dict:
    """Загрузка маппинга меток"""
    global _label_mapping
    if _label_mapping is None:
        if os.path.exists(Config.LABEL_MAPPING_PATH):
            with open(Config.LABEL_MAPPING_PATH, 'r') as f:
                _label_mapping = json.load(f)
        else:
            _label_mapping = {}
    return _label_mapping


def get_model_config() -> Dict:
    """Загрузка конфигурации модели"""
    global _model_config
    if _model_config is None:
        if os.path.exists(Config.MODEL_CONFIG_PATH):
            with open(Config.MODEL_CONFIG_PATH, 'r') as f:
                _model_config = json.load(f)
        else:
            _model_config = {}
    return _model_config


def get_training_history() -> Dict:
    """Загрузка истории обучения"""
    global _training_history
    if _training_history is None:
        if os.path.exists(Config.TRAINING_HISTORY_PATH):
            with open(Config.TRAINING_HISTORY_PATH, 'r') as f:
                _training_history = json.load(f)
        else:
            _training_history = {}
    return _training_history


def preprocess_audio(audio_data: np.ndarray) -> np.ndarray:
    """Предобработка одного аудио-сигнала"""
    audio = np.array(audio_data, dtype=np.float32)
    if len(audio.shape) == 1:
        audio = audio.reshape(-1, 1)
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val
    return audio


def predict_single(audio_data: np.ndarray) -> Dict:
    """
    Предсказание для одного аудио-сигнала.
    Возвращает класс и вероятности.
    """
    model = get_model()
    processed = preprocess_audio(audio_data)
    processed = np.expand_dims(processed, axis=0)  # batch dim
    
    predictions = model.predict(processed, verbose=0)
    predicted_class = int(np.argmax(predictions[0]))
    confidence = float(predictions[0][predicted_class])
    
    return {
        'predicted_class': predicted_class,
        'confidence': confidence,
        'probabilities': predictions[0].tolist()
    }


def evaluate_test_dataset(file_path: str) -> Dict:
    """
    Оценка модели на тестовом наборе данных (.npz файл).
    Возвращает accuracy, loss, предсказания, per-class accuracy.
    """
    tf = _load_tensorflow()
    model = get_model()
    config = get_model_config()
    num_classes = config.get('num_classes', None)
    
    # Загрузка тестовых данных
    data = np.load(file_path, allow_pickle=True)
    
    test_x = data['test_x']
    test_y = data['test_y']
    
    # Предобработка
    X_test = np.array([preprocess_audio(x) for x in test_x])
    
    # Преобразование меток в числовые (test_y может быть числовым)
    test_y_numeric = np.array(test_y, dtype=np.int32)
    
    # Определяем num_classes
    if num_classes is None:
        num_classes = int(np.max(test_y_numeric)) + 1
    
    # One-hot encoding
    y_test = tf.keras.utils.to_categorical(test_y_numeric, num_classes)
    
    # Оценка
    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    
    # Предсказания
    predictions_prob = model.predict(X_test, verbose=0)
    predicted_classes = np.argmax(predictions_prob, axis=1).tolist()
    true_classes = test_y_numeric.tolist()
    
    # Уверенность для каждого предсказания
    confidences = [
        float(predictions_prob[i][predicted_classes[i]])
        for i in range(len(predicted_classes))
    ]
    
    # Per-class accuracy
    per_class_accuracy = {}
    unique_classes = np.unique(test_y_numeric)
    for cls in unique_classes:
        cls = int(cls)
        mask = test_y_numeric == cls
        if np.sum(mask) > 0:
            cls_predictions = np.argmax(predictions_prob[mask], axis=1)
            cls_accuracy = float(np.mean(cls_predictions == cls))
            per_class_accuracy[str(cls)] = {
                'accuracy': round(cls_accuracy, 4),
                'total': int(np.sum(mask)),
                'correct': int(np.sum(cls_predictions == cls))
            }
    
    # Per-sample accuracy (для диаграммы точности каждой записи)
    per_sample_accuracy = []
    for i in range(len(predicted_classes)):
        per_sample_accuracy.append({
            'index': i,
            'true_class': true_classes[i],
            'predicted_class': predicted_classes[i],
            'confidence': round(confidences[i], 4),
            'correct': predicted_classes[i] == true_classes[i]
        })
    
    return {
        'accuracy': round(float(accuracy), 4),
        'loss': round(float(loss), 4),
        'total_samples': len(test_x),
        'correct_predictions': int(sum(
            1 for p, t in zip(predicted_classes, true_classes) if p == t
        )),
        'predicted_classes': predicted_classes,
        'true_classes': true_classes,
        'confidences': confidences,
        'per_class_accuracy': per_class_accuracy,
        'per_sample_accuracy': per_sample_accuracy
    }


def get_training_dataset_info() -> Dict:
    """
    Информация об обучающем датасете.
    Распределение классов, количество записей и т.д.
    """
    if not os.path.exists(Config.DATA_PATH):
        return {'error': 'Датасет не найден'}
    
    data = np.load(Config.DATA_PATH, allow_pickle=True)
    
    result = {}
    
    # Обучающие данные
    if 'train_x' in data and 'train_y' in data:
        train_y = data['train_y']
        
        # Восстановление меток (сортировка уникальных)
        unique_labels = sorted(np.unique(train_y))
        label_map = {label: idx for idx, label in enumerate(unique_labels)}
        train_y_numeric = np.array([label_map[l] for l in train_y])
        
        # Распределение классов
        class_distribution = {}
        for cls in range(len(unique_labels)):
            count = int(np.sum(train_y_numeric == cls))
            class_distribution[str(cls)] = count
        
        result['train'] = {
            'total_samples': len(data['train_x']),
            'num_classes': len(unique_labels),
            'class_distribution': class_distribution,
            'sample_shape': list(data['train_x'][0].shape) if len(data['train_x']) > 0 else []
        }
    
    # Валидационные данные
    if 'valid_x' in data and 'valid_y' in data:
        valid_y = data['valid_y']
        
        unique_valid_labels = sorted(np.unique(valid_y))
        valid_label_map = {label: idx for idx, label in enumerate(unique_valid_labels)}
        valid_y_numeric = np.array([valid_label_map[l] for l in valid_y])
        
        # Распределение
        valid_class_distribution = {}
        for cls in np.unique(valid_y_numeric):
            cls = int(cls)
            count = int(np.sum(valid_y_numeric == cls))
            valid_class_distribution[str(cls)] = count
        
        # Топ-5 классов
        sorted_classes = sorted(
            valid_class_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )
        top5 = dict(sorted_classes[:5])
        
        result['valid'] = {
            'total_samples': len(data['valid_x']),
            'num_classes': len(unique_valid_labels),
            'class_distribution': valid_class_distribution,
            'top5_classes': top5
        }
    
    return result


def get_model_summary() -> str:
    """Получение текстового описания архитектуры модели"""
    model = get_model()
    stream = io.StringIO()
    model.summary(print_fn=lambda x: stream.write(x + '\n'))
    return stream.getvalue()