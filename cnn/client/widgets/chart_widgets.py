# client/widgets/chart_widgets.py
"""
Виджеты отдельных графиков и диаграмм с поддержкой масштабирования.
Используют matplotlib для построения графиков.
"""
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy
)
from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure

from client.styles import CHART_COLORS


class BaseChartWidget(QWidget):
    """
    Базовый виджет графика с тулбаром масштабирования.
    ТЗ: "масштабирование построенных графиков и диаграмм"
    """

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.chart_title = title
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        # Заголовок
        if self.chart_title:
            title_label = QLabel(self.chart_title)
            title_label.setObjectName("subtitle")
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)

        # Фигура matplotlib
        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.figure.patch.set_facecolor(CHART_COLORS['background'])
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Панель навигации (масштабирование, сохранение)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 6px;
                padding: 2px;
            }
            QToolButton {
                background-color: transparent;
                color: #e0e0e0;
                padding: 4px;
                border-radius: 4px;
            }
            QToolButton:hover {
                background-color: #0f3460;
            }
        """)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def _style_axes(self, ax):
        """Применение общего стиля к осям"""
        ax.set_facecolor(CHART_COLORS['face'])
        ax.tick_params(colors=CHART_COLORS['text'], labelsize=9)
        ax.xaxis.label.set_color(CHART_COLORS['text'])
        ax.yaxis.label.set_color(CHART_COLORS['text'])
        ax.title.set_color(CHART_COLORS['text'])
        for spine in ax.spines.values():
            spine.set_color(CHART_COLORS['grid'])
        ax.grid(True, alpha=0.3, color=CHART_COLORS['grid'])

    def clear(self):
        """Очистка графика"""
        self.figure.clear()
        self.canvas.draw()


class AccuracyEpochsChart(BaseChartWidget):
    """
    График зависимости точности от эпох обучения.
    ТЗ: "просмотр графика зависимости точности на валидационных данных
         от количества эпох обучения"
    """

    def __init__(self, parent=None):
        super().__init__("Точность от эпох обучения", parent)

    def plot(self, data: dict):
        self.figure.clear()

        epochs = data.get('epochs', [])
        train_acc = data.get('train_accuracy', [])
        val_acc = data.get('val_accuracy', [])
        train_loss = data.get('train_loss', [])
        val_loss = data.get('val_loss', [])

        if not epochs:
            ax = self.figure.add_subplot(111)
            self._style_axes(ax)
            ax.text(0.5, 0.5, 'Нет данных об обучении',
                    ha='center', va='center', color=CHART_COLORS['text'], fontsize=14)
            self.canvas.draw()
            return

        # Два подграфика: точность и потери
        ax1 = self.figure.add_subplot(121)
        ax2 = self.figure.add_subplot(122)

        self._style_axes(ax1)
        self._style_axes(ax2)

        # График точности
        if train_acc:
            ax1.plot(epochs, train_acc, '-o', color=CHART_COLORS['primary'],
                     label='Обучение', linewidth=2, markersize=3)
        if val_acc:
            ax1.plot(epochs, val_acc, '-s', color=CHART_COLORS['secondary'],
                     label='Валидация', linewidth=2, markersize=3)
        ax1.set_xlabel('Эпоха', fontsize=11)
        ax1.set_ylabel('Точность', fontsize=11)
        ax1.set_title('Accuracy', fontsize=13, fontweight='bold',
                       color=CHART_COLORS['text'])
        ax1.legend(facecolor=CHART_COLORS['face'], edgecolor=CHART_COLORS['grid'],
                   labelcolor=CHART_COLORS['text'], fontsize=9)

        # График потерь
        if train_loss:
            ax2.plot(epochs, train_loss, '-o', color=CHART_COLORS['danger'],
                     label='Обучение', linewidth=2, markersize=3)
        if val_loss:
            ax2.plot(epochs, val_loss, '-s', color=CHART_COLORS['warning'],
                     label='Валидация', linewidth=2, markersize=3)
        ax2.set_xlabel('Эпоха', fontsize=11)
        ax2.set_ylabel('Потери', fontsize=11)
        ax2.set_title('Loss', fontsize=13, fontweight='bold',
                       color=CHART_COLORS['text'])
        ax2.legend(facecolor=CHART_COLORS['face'], edgecolor=CHART_COLORS['grid'],
                   labelcolor=CHART_COLORS['text'], fontsize=9)

        self.figure.tight_layout(pad=2.0)
        self.canvas.draw()


class ClassDistributionChart(BaseChartWidget):
    """
    Диаграмма распределения классов в обучающем наборе.
    ТЗ: "просмотр диаграммы с отображением количества записей в наборе данных
         для обучения, относящихся к каждой цивилизации (классу)"
    """

    def __init__(self, parent=None):
        super().__init__("Распределение классов (обучающий набор)", parent)

    def plot(self, data: dict):
        self.figure.clear()

        classes = data.get('classes', [])
        counts = data.get('counts', [])

        if not classes:
            ax = self.figure.add_subplot(111)
            self._style_axes(ax)
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center',
                    color=CHART_COLORS['text'], fontsize=14)
            self.canvas.draw()
            return

        ax = self.figure.add_subplot(111)
        self._style_axes(ax)

        n = len(classes)
        colors = [CHART_COLORS['bar_colors'][i % len(CHART_COLORS['bar_colors'])]
                  for i in range(n)]

        bars = ax.bar(range(n), counts, color=colors, edgecolor='none', alpha=0.9)

        ax.set_xlabel('Класс (цивилизация)', fontsize=11)
        ax.set_ylabel('Количество записей', fontsize=11)
        ax.set_title(f'Распределение по {n} классам '
                     f'(всего: {data.get("total_samples", sum(counts))} записей)',
                     fontsize=12, fontweight='bold', color=CHART_COLORS['text'])

        ax.set_xticks(range(n))
        ax.set_xticklabels(classes, rotation=45 if n > 10 else 0, fontsize=8)

        # Подписи значений на столбцах
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.5,
                    str(count), ha='center', va='bottom',
                    color=CHART_COLORS['text'], fontsize=7)

        self.figure.tight_layout()
        self.canvas.draw()


class PerSampleAccuracyChart(BaseChartWidget):
    """
    Диаграмма точности определения каждой записи из тестового набора.
    ТЗ: "диаграмму, демонстрирующую точность определения каждой записи
         из тестового набора данных"
    """

    def __init__(self, parent=None):
        super().__init__("Точность определения каждой записи (тестовый набор)", parent)

    def plot(self, data: dict):
        self.figure.clear()

        samples = data.get('samples', [])
        if not samples:
            ax = self.figure.add_subplot(111)
            self._style_axes(ax)
            ax.text(0.5, 0.5, 'Нет данных тестирования\nЗагрузите тестовый набор',
                    ha='center', va='center', color=CHART_COLORS['text'], fontsize=14)
            self.canvas.draw()
            return

        ax = self.figure.add_subplot(111)
        self._style_axes(ax)

        indices = [s['index'] for s in samples]
        confidences = [s['confidence'] for s in samples]
        correct = [s.get('correct', False) for s in samples]

        colors = [CHART_COLORS['success'] if c else CHART_COLORS['danger'] for c in correct]

        ax.bar(indices, confidences, color=colors, alpha=0.8, width=1.0, edgecolor='none')

        ax.set_xlabel('Номер записи', fontsize=11)
        ax.set_ylabel('Уверенность модели', fontsize=11)

        total = len(samples)
        correct_count = sum(1 for c in correct if c)
        acc = data.get('accuracy', correct_count / total if total > 0 else 0)

        ax.set_title(
            f'Точность по записям: {correct_count}/{total} верных '
            f'(accuracy = {acc:.2%})',
            fontsize=12, fontweight='bold', color=CHART_COLORS['text']
        )

        # Легенда
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=CHART_COLORS['success'], label=f'Верно ({correct_count})'),
            Patch(facecolor=CHART_COLORS['danger'],
                  label=f'Неверно ({total - correct_count})')
        ]
        ax.legend(handles=legend_elements,
                  facecolor=CHART_COLORS['face'],
                  edgecolor=CHART_COLORS['grid'],
                  labelcolor=CHART_COLORS['text'],
                  fontsize=9)

        ax.set_ylim(0, 1.05)
        self.figure.tight_layout()
        self.canvas.draw()


class Top5ValidationChart(BaseChartWidget):
    """
    Топ-5 классов валидационного набора.
    ТЗ: "диаграмму, демонстрирующую топ-5 наиболее часто встречающихся
         классов записей в валидационном наборе данных"
    """

    def __init__(self, parent=None):
        super().__init__("Топ-5 классов (валидационный набор)", parent)

    def plot(self, data: dict):
        self.figure.clear()

        classes = data.get('classes', [])
        counts = data.get('counts', [])

        if not classes:
            ax = self.figure.add_subplot(111)
            self._style_axes(ax)
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center',
                    color=CHART_COLORS['text'], fontsize=14)
            self.canvas.draw()
            return

        # Два подграфика: столбцы и круговая
        ax1 = self.figure.add_subplot(121)
        ax2 = self.figure.add_subplot(122)

        self._style_axes(ax1)
        ax2.set_facecolor(CHART_COLORS['face'])

        colors = CHART_COLORS['bar_colors'][:len(classes)]

        # Столбчатая диаграмма
        bars = ax1.barh(range(len(classes)), counts, color=colors, edgecolor='none')
        ax1.set_yticks(range(len(classes)))
        ax1.set_yticklabels([f'Класс {c}' for c in classes], fontsize=10)
        ax1.set_xlabel('Количество записей', fontsize=11)
        ax1.set_title('Топ-5 классов', fontsize=13, fontweight='bold',
                       color=CHART_COLORS['text'])
        ax1.invert_yaxis()

        for bar, count in zip(bars, counts):
            ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2.,
                     str(count), ha='left', va='center',
                     color=CHART_COLORS['text'], fontsize=10, fontweight='bold')

        # Круговая диаграмма
        wedges, texts, autotexts = ax2.pie(
            counts,
            labels=[f'Класс {c}' for c in classes],
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'color': CHART_COLORS['text'], 'fontsize': 9}
        )
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')

        ax2.set_title(
            f'Доля (всего: {data.get("total_valid_samples", sum(counts))})',
            fontsize=13, fontweight='bold', color=CHART_COLORS['text']
        )

        self.figure.tight_layout(pad=2.0)
        self.canvas.draw()


class TestLossAccuracyChart(BaseChartWidget):
    """
    Дополнительная диаграмма: точность и потери на тестовом наборе.
    ТЗ: "отображение точности и потерь на тестовом наборе данных"
    """

    def __init__(self, parent=None):
        super().__init__("Точность и потери (тестовый набор)", parent)

    def plot(self, accuracy: float, loss: float,
             per_class_accuracy: dict = None):
        self.figure.clear()

        if per_class_accuracy:
            # Два подграфика
            ax1 = self.figure.add_subplot(121)
            ax2 = self.figure.add_subplot(122)
        else:
            ax1 = self.figure.add_subplot(111)
            ax2 = None

        self._style_axes(ax1)

        # Столбцы Accuracy и Loss
        metrics = ['Accuracy', 'Loss']
        values = [accuracy, loss]
        colors_m = [CHART_COLORS['success'], CHART_COLORS['danger']]

        bars = ax1.bar(metrics, values, color=colors_m, width=0.5, edgecolor='none')

        for bar, val in zip(bars, values):
            ax1.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.01,
                     f'{val:.4f}', ha='center', va='bottom',
                     color=CHART_COLORS['text'], fontsize=14, fontweight='bold')

        ax1.set_title('Метрики на тестовом наборе',
                       fontsize=13, fontweight='bold', color=CHART_COLORS['text'])
        ax1.set_ylim(0, max(values) * 1.3 + 0.1)

        # По-классовая точность
        if ax2 and per_class_accuracy:
            self._style_axes(ax2)
            sorted_items = sorted(per_class_accuracy.items(), key=lambda x: int(x[0]))
            cls_names = [f'{k}' for k, _ in sorted_items]
            cls_accs = [v['accuracy'] for _, v in sorted_items]

            n = len(cls_names)
            c = [CHART_COLORS['bar_colors'][i % len(CHART_COLORS['bar_colors'])]
                 for i in range(n)]

            ax2.bar(range(n), cls_accs, color=c, edgecolor='none', alpha=0.9)
            ax2.set_xticks(range(n))
            ax2.set_xticklabels(cls_names, rotation=45, fontsize=7)
            ax2.set_xlabel('Класс', fontsize=10)
            ax2.set_ylabel('Accuracy', fontsize=10)
            ax2.set_title('Точность по классам',
                           fontsize=12, fontweight='bold', color=CHART_COLORS['text'])
            ax2.set_ylim(0, 1.05)

        self.figure.tight_layout(pad=2.0)
        self.canvas.draw()