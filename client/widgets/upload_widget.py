# client/widgets/upload_widget.py
"""
Виджет загрузки тестового набора данных и отображения результатов.
ТЗ: "загрузка набора данных для проверки работы модели",
    "загрузка 'тестового' набора данных через форму загрузки файла",
    "отображение точности и потерь на тестовом наборе данных"
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QFrame, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from client.api_client import ApiClient
from client.widgets.chart_widgets import TestLossAccuracyChart


class UploadWorker(QThread):
    """Поток для загрузки файла (чтобы не блокировать UI)"""
    finished = pyqtSignal(bool, dict)
    progress = pyqtSignal(str)

    def __init__(self, api_client: ApiClient, file_path: str):
        super().__init__()
        self.api_client = api_client
        self.file_path = file_path

    def run(self):
        self.progress.emit("Загрузка и обработка файла...")
        success, data = self.api_client.upload_test_data(self.file_path)
        self.finished.emit(success, data)


class UploadWidget(QWidget):
    """Виджет загрузки тестового набора данных"""

    # Сигнал при успешной загрузке (передаём result_id)
    upload_completed = pyqtSignal(int)

    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.worker = None
        self.last_result = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок
        title = QLabel("📤 Загрузка тестового набора данных")
        title.setObjectName("title")
        layout.addWidget(title)

        desc = QLabel(
            "Загрузите файл .npz с тестовыми данными для оценки работы модели.\n"
            "Файл должен содержать массивы test_x (аудиозаписи) и test_y (классы)."
        )
        desc.setObjectName("info_label")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Форма загрузки
        upload_frame = QFrame()
        upload_frame.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border: 2px dashed #0f3460;
                border-radius: 12px;
            }
        """)
        upload_layout = QVBoxLayout(upload_frame)
        upload_layout.setContentsMargins(30, 25, 30, 25)
        upload_layout.setSpacing(12)
        upload_layout.setAlignment(Qt.AlignCenter)

        upload_icon = QLabel("📁")
        upload_icon.setAlignment(Qt.AlignCenter)
        upload_icon.setStyleSheet("font-size: 40px; background: transparent;")
        upload_layout.addWidget(upload_icon)

        self.file_label = QLabel("Файл не выбран")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setStyleSheet(
            "font-size: 14px; color: #888; background: transparent;"
        )
        upload_layout.addWidget(self.file_label)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)

        self.select_btn = QPushButton("  Выбрать файл (.npz)  ")
        self.select_btn.setObjectName("primary_btn")
        self.select_btn.setCursor(Qt.PointingHandCursor)
        self.select_btn.setMinimumHeight(40)
        self.select_btn.clicked.connect(self._select_file)
        btn_row.addWidget(self.select_btn)

        self.upload_btn = QPushButton("  Загрузить и оценить  ")
        self.upload_btn.setObjectName("success_btn")
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.setMinimumHeight(40)
        self.upload_btn.setEnabled(False)
        self.upload_btn.clicked.connect(self._upload_file)
        btn_row.addWidget(self.upload_btn)

        upload_layout.addLayout(btn_row)

        # Прогресс
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # неопределённый
        self.progress_bar.hide()
        upload_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("background: transparent;")
        self.status_label.hide()
        upload_layout.addWidget(self.status_label)

        layout.addWidget(upload_frame)

        # Результаты
        self.results_frame = QFrame()
        self.results_frame.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 12px;
                border: 1px solid #0f3460;
            }
        """)
        results_layout = QVBoxLayout(self.results_frame)
        results_layout.setContentsMargins(20, 15, 20, 15)
        results_layout.setSpacing(10)

        results_title = QLabel("📊 Результаты тестирования")
        results_title.setObjectName("subtitle")
        results_layout.addWidget(results_title)

        # Метрики
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(20)

        self.accuracy_label = QLabel("—")
        self.accuracy_label.setObjectName("stat_value")
        self.accuracy_label.setAlignment(Qt.AlignCenter)

        self.loss_label = QLabel("—")
        self.loss_label.setObjectName("stat_value")
        self.loss_label.setAlignment(Qt.AlignCenter)

        self.samples_label = QLabel("—")
        self.samples_label.setObjectName("stat_value")
        self.samples_label.setAlignment(Qt.AlignCenter)

        for val_label, desc_text in [
            (self.accuracy_label, "Accuracy"),
            (self.loss_label, "Loss"),
            (self.samples_label, "Записей"),
        ]:
            box = QVBoxLayout()
            box.setAlignment(Qt.AlignCenter)
            box.addWidget(val_label)
            desc = QLabel(desc_text)
            desc.setObjectName("stat_label")
            desc.setAlignment(Qt.AlignCenter)
            desc.setStyleSheet(
                "font-size: 11px; color: #888; background: transparent;"
            )
            box.addWidget(desc)
            metrics_row.addLayout(box)

        results_layout.addLayout(metrics_row)

        # График accuracy/loss
        self.test_chart = TestLossAccuracyChart()
        self.test_chart.setMinimumHeight(350)
        results_layout.addWidget(self.test_chart)

        self.results_frame.hide()
        layout.addWidget(self.results_frame)

        # История результатов
        self.history_frame = QFrame()
        self.history_frame.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 12px;
                border: 1px solid #0f3460;
            }
        """)
        history_layout = QVBoxLayout(self.history_frame)
        history_layout.setContentsMargins(15, 15, 15, 15)

        history_title = QLabel("📋 История тестирований")
        history_title.setObjectName("subtitle")
        history_layout.addWidget(history_title)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "Файл", "Записей", "Accuracy", "Дата"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setMaximumHeight(200)
        history_layout.addWidget(self.history_table)

        layout.addWidget(self.history_frame)

        layout.addStretch()

        self.selected_file_path = None

        # Загружаем историю
        self._load_history()

    def _select_file(self):
        """Выбор файла для загрузки"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл тестового набора данных",
            "", "NumPy Archive (*.npz)"
        )
        if file_path:
            self.selected_file_path = file_path
            filename = file_path.split('/')[-1].split('\\')[-1]
            self.file_label.setText(f"📄 {filename}")
            self.file_label.setStyleSheet(
                "font-size: 14px; color: #00d4ff; font-weight: bold; background: transparent;"
            )
            self.upload_btn.setEnabled(True)

    def _upload_file(self):
        """Загрузка и обработка файла"""
        if not self.selected_file_path:
            return

        self.upload_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.progress_bar.show()
        self.status_label.setText("⏳ Загрузка и оценка модели...")
        self.status_label.setStyleSheet(
            "font-size: 13px; color: #ffab40; background: transparent;"
        )
        self.status_label.show()

        self.worker = UploadWorker(self.api_client, self.selected_file_path)
        self.worker.finished.connect(self._on_upload_finished)
        self.worker.start()

    def _on_upload_finished(self, success: bool, data: dict):
        """Обработка завершения загрузки"""
        self.progress_bar.hide()
        self.upload_btn.setEnabled(True)
        self.select_btn.setEnabled(True)

        if success:
            self.status_label.setText("✓ Тестирование завершено успешно!")
            self.status_label.setStyleSheet(
                "font-size: 13px; color: #00e676; font-weight: bold; background: transparent;"
            )

            self.last_result = data

            # Обновляем метрики
            accuracy = data.get('accuracy', 0)
            loss = data.get('loss', 0)
            total = data.get('total_samples', 0)

            self.accuracy_label.setText(f"{accuracy:.2%}")
            acc_color = '#00e676' if accuracy > 0.8 else '#ffab40' if accuracy > 0.5 else '#ff5252'
            self.accuracy_label.setStyleSheet(
                f"font-size: 28px; font-weight: bold; color: {acc_color}; background: transparent;"
            )

            self.loss_label.setText(f"{loss:.4f}")
            self.loss_label.setStyleSheet(
                "font-size: 28px; font-weight: bold; color: #ff8a80; background: transparent;"
            )

            self.samples_label.setText(str(total))
            self.samples_label.setStyleSheet(
                "font-size: 28px; font-weight: bold; color: #00d4ff; background: transparent;"
            )

            # График
            per_class = data.get('per_class_accuracy', {})
            self.test_chart.plot(accuracy, loss, per_class if per_class else None)

            self.results_frame.show()

            # Обновляем историю
            self._load_history()

            # Сигнал о завершении
            result_id = data.get('result_id')
            if result_id:
                self.upload_completed.emit(result_id)
        else:
            error = data.get('error', 'Неизвестная ошибка')
            self.status_label.setText(f"✗ Ошибка: {error}")
            self.status_label.setStyleSheet(
                "font-size: 13px; color: #ff5252; background: transparent;"
            )

            QMessageBox.critical(self, "Ошибка загрузки", error)

    def _load_history(self):
        """Загрузка истории тестирований"""
        success, data = self.api_client.get_test_results()
        if not success:
            return

        results = data.get('results', [])
        self.history_table.setRowCount(len(results))

        for row, result in enumerate(results):
            self.history_table.setItem(row, 0, QTableWidgetItem(str(result.get('id', ''))))
            self.history_table.setItem(row, 1, QTableWidgetItem(result.get('filename', '')))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(result.get('total_samples', ''))))
            self.history_table.setItem(row, 3, QTableWidgetItem(f"{result.get('accuracy', 0):.2%}"))
            self.history_table.setItem(row, 4, QTableWidgetItem(result.get('created_at', '')))

        if results:
            self.history_frame.show()