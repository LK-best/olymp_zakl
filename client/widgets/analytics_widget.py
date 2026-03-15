# client/widgets/analytics_widget.py
"""
Виджет аналитики: все графики и диаграммы в одном месте.
ТЗ: "экранная форма/веб-страница с графиками и диаграммами",
    "просмотр аналитики"
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QTabWidget, QComboBox, QMessageBox,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt

from client.api_client import ApiClient
from client.widgets.chart_widgets import (
    AccuracyEpochsChart,
    ClassDistributionChart,
    PerSampleAccuracyChart,
    Top5ValidationChart,
    TestLossAccuracyChart
)


class AnalyticsWidget(QWidget):
    """Виджет со всеми графиками и диаграммами"""

    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.current_test_result_id = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Заголовок и кнопки
        header_row = QHBoxLayout()

        title = QLabel("📈 Аналитика и визуализация")
        title.setObjectName("title")
        header_row.addWidget(title)

        header_row.addStretch()

        # Выбор результата тестирования
        self.result_combo = QComboBox()
        self.result_combo.setMinimumWidth(250)
        self.result_combo.setPlaceholderText("Выберите результат теста...")
        self.result_combo.currentIndexChanged.connect(self._on_result_selected)
        header_row.addWidget(self.result_combo)

        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.setObjectName("primary_btn")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_all)
        header_row.addWidget(refresh_btn)

        main_layout.addLayout(header_row)

        # Табы с графиками
        self.tabs = QTabWidget()

        # Таб 1: Обучение
        tab_training = QWidget()
        tab_training_layout = QVBoxLayout(tab_training)
        tab_training_layout.setContentsMargins(5, 10, 5, 5)

        self.accuracy_epochs_chart = AccuracyEpochsChart()
        self.accuracy_epochs_chart.setMinimumHeight(400)
        tab_training_layout.addWidget(self.accuracy_epochs_chart)

        self.tabs.addTab(tab_training, "📉 Точность/Эпохи")

        # Таб 2: Распределение классов
        tab_distribution = QWidget()
        tab_distribution_layout = QVBoxLayout(tab_distribution)
        tab_distribution_layout.setContentsMargins(5, 10, 5, 5)

        self.class_dist_chart = ClassDistributionChart()
        self.class_dist_chart.setMinimumHeight(400)
        tab_distribution_layout.addWidget(self.class_dist_chart)

        self.tabs.addTab(tab_distribution, "📊 Классы (обучение)")

        # Таб 3: Точность по записям теста
        tab_per_sample = QWidget()
        tab_per_sample_layout = QVBoxLayout(tab_per_sample)
        tab_per_sample_layout.setContentsMargins(5, 10, 5, 5)

        self.per_sample_chart = PerSampleAccuracyChart()
        self.per_sample_chart.setMinimumHeight(400)
        tab_per_sample_layout.addWidget(self.per_sample_chart)

        self.tabs.addTab(tab_per_sample, "🎯 Записи (тест)")

        # Таб 4: Топ-5 валидации
        tab_top5 = QWidget()
        tab_top5_layout = QVBoxLayout(tab_top5)
        tab_top5_layout.setContentsMargins(5, 10, 5, 5)

        self.top5_chart = Top5ValidationChart()
        self.top5_chart.setMinimumHeight(400)
        tab_top5_layout.addWidget(self.top5_chart)

        self.tabs.addTab(tab_top5, "🏆 Топ-5 (валидация)")

        # Таб 5: Сводка по тесту
        tab_test = QWidget()
        tab_test_layout = QVBoxLayout(tab_test)
        tab_test_layout.setContentsMargins(5, 10, 5, 5)

        self.test_summary_chart = TestLossAccuracyChart()
        self.test_summary_chart.setMinimumHeight(400)
        tab_test_layout.addWidget(self.test_summary_chart)

        self.tabs.addTab(tab_test, "📋 Метрики (тест)")

        main_layout.addWidget(self.tabs)

    def refresh_all(self):
        """Обновление всех графиков"""
        self._load_test_results_combo()
        self._load_accuracy_epochs()
        self._load_class_distribution()
        self._load_top5_validation()

        if self.current_test_result_id:
            self._load_per_sample(self.current_test_result_id)
            self._load_test_summary(self.current_test_result_id)

    def set_test_result_id(self, result_id: int):
        """Установка текущего result_id (вызывается после загрузки теста)"""
        self.current_test_result_id = result_id
        self._load_test_results_combo()
        self._load_per_sample(result_id)
        self._load_test_summary(result_id)

    def _load_test_results_combo(self):
        """Загрузка списка результатов в комбобокс"""
        self.result_combo.blockSignals(True)
        self.result_combo.clear()

        success, data = self.api_client.get_test_results()
        if success:
            results = data.get('results', [])
            for r in results:
                text = (f"#{r['id']} — {r['filename']} "
                        f"(acc: {r['accuracy']:.2%}, {r['created_at']})")
                self.result_combo.addItem(text, r['id'])

            # Выбираем текущий
            if self.current_test_result_id:
                for i in range(self.result_combo.count()):
                    if self.result_combo.itemData(i) == self.current_test_result_id:
                        self.result_combo.setCurrentIndex(i)
                        break

        self.result_combo.blockSignals(False)

    def _on_result_selected(self, index):
        """Обработка выбора результата из комбобокса"""
        if index < 0:
            return
        result_id = self.result_combo.itemData(index)
        if result_id:
            self.current_test_result_id = result_id
            self._load_per_sample(result_id)
            self._load_test_summary(result_id)

    def _load_accuracy_epochs(self):
        """Загрузка графика точности от эпох"""
        success, data = self.api_client.get_accuracy_vs_epochs()
        if success:
            self.accuracy_epochs_chart.plot(data)
        else:
            self.accuracy_epochs_chart.plot({})

    def _load_class_distribution(self):
        """Загрузка распределения классов"""
        success, data = self.api_client.get_class_distribution()
        if success:
            self.class_dist_chart.plot(data)
        else:
            self.class_dist_chart.plot({})

    def _load_per_sample(self, result_id: int):
        """Загрузка точности по записям"""
        success, data = self.api_client.get_test_per_sample(result_id)
        if success:
            self.per_sample_chart.plot(data)
        else:
            self.per_sample_chart.plot({})

    def _load_top5_validation(self):
        """Загрузка топ-5 классов валидации"""
        success, data = self.api_client.get_top5_validation()
        if success:
            self.top5_chart.plot(data)
        else:
            self.top5_chart.plot({})

    def _load_test_summary(self, result_id: int):
        """Загрузка сводки тестирования"""
        success, data = self.api_client.get_test_summary(result_id)
        if success:
            accuracy = data.get('accuracy', 0)
            loss = data.get('loss', 0)
            per_class = data.get('per_class_accuracy', {})
            self.test_summary_chart.plot(accuracy, loss, per_class if per_class else None)
        else:
            self.test_summary_chart.clear()