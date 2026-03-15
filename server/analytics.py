# server/analytics.py
"""
Модуль аналитики: генерация данных для графиков и диаграмм.
"""
import json
import os
import numpy as np
from typing import Dict, List, Optional

from server.config import Config
from server import model_service


def get_accuracy_vs_epochs() -> Dict:
    """
    График зависимости точности на валидационных данных от количества эпох.
    ТЗ: "просмотр графика зависимости точности на валидационных данных
         от количества эпох обучения"
    """
    history = model_service.get_training_history()
    
    result = {
        'epochs': list(range(1, len(history.get('accuracy', [])) + 1)),
        'train_accuracy': history.get('accuracy', []),
        'train_loss': history.get('loss', []),
    }
    
    # Если есть валидационные данные в истории
    if 'val_accuracy' in history:
        result['val_accuracy'] = history['val_accuracy']
    if 'val_loss' in history:
        result['val_loss'] = history['val_loss']
    
    return result


def get_class_distribution() -> Dict:
    """
    Диаграмма количества записей в обучающем наборе по классам.
    ТЗ: "просмотр диаграммы с отображением количества записей в наборе данных
         для обучения, относящихся к каждой цивилизации (классу)"
    """
    dataset_info = model_service.get_training_dataset_info()
    
    if 'train' not in dataset_info:
        return {'error': 'Данные обучения не найдены'}
    
    train_info = dataset_info['train']
    distribution = train_info.get('class_distribution', {})
    
    # Сортируем по номеру класса
    sorted_classes = sorted(distribution.items(), key=lambda x: int(x[0]))
    
    return {
        'classes': [item[0] for item in sorted_classes],
        'counts': [item[1] for item in sorted_classes],
        'total_samples': train_info.get('total_samples', 0),
        'num_classes': train_info.get('num_classes', 0)
    }


def get_test_per_sample_accuracy(test_result: Dict) -> Dict:
    """
    Диаграмма точности определения каждой записи из тестового набора.
    ТЗ: "диаграмму, демонстрирующую точность определения каждой записи
         из тестового набора данных"
    """
    if not test_result:
        return {'error': 'Нет результатов тестирования'}
    
    per_sample = test_result.get('per_sample_accuracy', [])
    
    if not per_sample and 'confidences' in test_result:
        # Восстанавливаем из сырых данных
        predicted = test_result.get('predicted_classes', [])
        true = test_result.get('true_classes', [])
        confidences = test_result.get('confidences', [])
        
        per_sample = []
        for i in range(len(predicted)):
            per_sample.append({
                'index': i,
                'true_class': true[i] if i < len(true) else None,
                'predicted_class': predicted[i],
                'confidence': confidences[i] if i < len(confidences) else 0,
                'correct': predicted[i] == true[i] if i < len(true) else False
            })
    
    return {
        'samples': per_sample,
        'total': len(per_sample),
        'correct_count': sum(1 for s in per_sample if s.get('correct', False)),
        'accuracy': test_result.get('accuracy', 0)
    }


def get_top5_validation_classes() -> Dict:
    """
    Топ-5 наиболее часто встречающихся классов в валидационном наборе.
    ТЗ: "диаграмму, демонстрирующую топ-5 наиболее часто встречающихся
         классов записей в валидационном наборе данных"
    """
    dataset_info = model_service.get_training_dataset_info()
    
    if 'valid' not in dataset_info:
        return {'error': 'Валидационные данные не найдены'}
    
    valid_info = dataset_info['valid']
    distribution = valid_info.get('class_distribution', {})
    
    # Сортируем по количеству (убывание) и берём топ-5
    sorted_classes = sorted(
        distribution.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    return {
        'classes': [item[0] for item in sorted_classes],
        'counts': [item[1] for item in sorted_classes],
        'total_valid_samples': valid_info.get('total_samples', 0)
    }


def get_per_class_accuracy_from_test(test_result: Dict) -> Dict:
    """Точность по каждому классу из результатов тестирования"""
    if not test_result:
        return {'error': 'Нет результатов тестирования'}
    
    per_class = test_result.get('per_class_accuracy', {})
    
    sorted_classes = sorted(per_class.items(), key=lambda x: int(x[0]))
    
    return {
        'classes': [item[0] for item in sorted_classes],
        'accuracies': [item[1]['accuracy'] for item in sorted_classes],
        'totals': [item[1]['total'] for item in sorted_classes],
        'corrects': [item[1]['correct'] for item in sorted_classes]
    }


def get_full_analytics(test_result_id: Optional[int] = None) -> Dict:
    """Полная аналитика для дашборда"""
    from server import database as db
    
    result = {
        'accuracy_vs_epochs': get_accuracy_vs_epochs(),
        'class_distribution': get_class_distribution(),
        'top5_validation': get_top5_validation_classes(),
    }
    
    # Если есть конкретный результат теста
    if test_result_id:
        test_result = db.get_test_result_by_id(test_result_id)
        if test_result:
            result['test_per_sample'] = get_test_per_sample_accuracy(test_result)
            result['test_per_class'] = get_per_class_accuracy_from_test(test_result)
            result['test_summary'] = {
                'accuracy': test_result.get('accuracy'),
                'loss': test_result.get('loss'),
                'total_samples': test_result.get('total_samples'),
                'filename': test_result.get('filename')
            }
    
    # Конфигурация модели
    result['model_config'] = model_service.get_model_config()
    
    return result