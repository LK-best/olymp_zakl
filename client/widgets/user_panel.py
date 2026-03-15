# client/widgets/user_panel.py
"""
Панель пользователя: загрузка данных, просмотр аналитики.
ТЗ: "В функциональные возможности пользователя должно входить:
     - загрузка набора данных для проверки работы модели;
     - просмотр аналитики."
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt

from client.api_client import ApiClient
from client.widgets.user_info_widget import UserInfoWidget
from client.widgets.upload_widget import UploadWidget
from client.widgets.analytics_widget import AnalyticsWidget


class UserPanel(QWidget):
    """Панель пользователя с навигацией"""

    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Боковая навигация
        nav_frame = QFrame()
        nav_frame.setFixedWidth(220)
        nav_frame.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border-right: 1px solid #0f3460;
            }
        """)

        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(5)

        # Заголовок навигации
        nav_title = QLabel("📡 Навигация")
        nav_title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #7b68ee; "
            "padding: 5px 10px; background: transparent;"
        )
        nav_layout.addWidget(nav_title)

        nav_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Кнопки навигации
        self.nav_buttons = []
        nav_items = [
            ("👤 Профиль", 0),
            ("📤 Загрузка данных", 1),
            ("📈 Аналитика", 2),
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("nav_btn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(40)
            btn.clicked.connect(lambda checked, idx=index: self._switch_page(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        nav_layout.addStretch()

        layout.addWidget(nav_frame)

        # Стек страниц
        self.stack = QStackedWidget()

        # Страница 1: Информация о пользователе
        self.user_info = UserInfoWidget(self.api_client)
        self.stack.addWidget(self.user_info)

        # Страница 2: Загрузка данных
        self.upload_widget = UploadWidget(self.api_client)
        self.upload_widget.upload_completed.connect(self._on_upload_completed)
        self.stack.addWidget(self.upload_widget)

        # Страница 3: Аналитика
        self.analytics_widget = AnalyticsWidget(self.api_client)
        self.stack.addWidget(self.analytics_widget)

        layout.addWidget(self.stack)

        # Устанавливаем первую страницу
        self._switch_page(0)

    def _switch_page(self, index: int):
        """Переключение страницы"""
        self.stack.setCurrentIndex(index)

        # Обновляем стили кнопок
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setObjectName("nav_btn_active")
            else:
                btn.setObjectName("nav_btn")
            # Принудительное обновление стиля
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Загрузка данных при переключении
        if index == 0:
            self.user_info.refresh()
        elif index == 2:
            self.analytics_widget.refresh_all()

    def _on_upload_completed(self, result_id: int):
        """Обработка завершения загрузки тестового набора"""
        self.analytics_widget.set_test_result_id(result_id)