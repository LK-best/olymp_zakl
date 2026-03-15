# client/widgets/user_info_widget.py
"""
Экранная форма с информацией о пользователе.
ТЗ: "экранная форма/веб-страница с информацией о пользователе"
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt

from client.api_client import ApiClient


class UserInfoWidget(QWidget):
    """Виджет отображения информации о пользователе"""

    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("👤 Профиль пользователя")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        # Карточка пользователя
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 12px;
                border: 1px solid #0f3460;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(15)

        # Аватар / Иконка
        avatar_label = QLabel("🛸")
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setStyleSheet("font-size: 60px; background: transparent;")
        card_layout.addWidget(avatar_label)

        # Имя
        self.name_label = QLabel("—")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #00d4ff; background: transparent;"
        )
        card_layout.addWidget(self.name_label)

        # Роль
        self.role_label = QLabel("")
        self.role_label.setAlignment(Qt.AlignCenter)
        self.role_label.setStyleSheet(
            "font-size: 13px; color: #7b68ee; font-weight: bold; background: transparent;"
        )
        card_layout.addWidget(self.role_label)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #0f3460; max-height: 1px;")
        card_layout.addWidget(separator)

        # Детали в сетке
        details_grid = QGridLayout()
        details_grid.setSpacing(12)

        self.detail_labels = {}
        fields = [
            ("ID:", "id"),
            ("Логин:", "login"),
            ("Имя:", "first_name"),
            ("Фамилия:", "last_name"),
            ("Роль:", "role"),
            ("Дата создания:", "created_at"),
        ]

        for row, (label_text, key) in enumerate(fields):
            label = QLabel(label_text)
            label.setStyleSheet(
                "font-size: 13px; color: #888; font-weight: bold; background: transparent;"
            )
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            details_grid.addWidget(label, row, 0)

            value = QLabel("—")
            value.setStyleSheet("font-size: 13px; color: #e0e0e0; background: transparent;")
            value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            details_grid.addWidget(value, row, 1)
            self.detail_labels[key] = value

        card_layout.addLayout(details_grid)

        layout.addWidget(card)

        # Статистика сессии
        stats_card = QFrame()
        stats_card.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 12px;
                border: 1px solid #0f3460;
            }
        """)
        stats_layout = QHBoxLayout(stats_card)
        stats_layout.setContentsMargins(20, 15, 20, 15)
        stats_layout.setSpacing(30)

        self.stat_widgets = {}
        stat_items = [
            ("server_status", "Сервер", "—"),
            ("model_status", "Модель", "—"),
            ("dataset_status", "Датасет", "—"),
        ]

        for key, label_text, default_val in stat_items:
            stat_box = QVBoxLayout()
            stat_box.setAlignment(Qt.AlignCenter)

            val_label = QLabel(default_val)
            val_label.setAlignment(Qt.AlignCenter)
            val_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #00d4ff; background: transparent;"
            )
            stat_box.addWidget(val_label)

            desc_label = QLabel(label_text)
            desc_label.setAlignment(Qt.AlignCenter)
            desc_label.setStyleSheet(
                "font-size: 11px; color: #888; background: transparent;"
            )
            stat_box.addWidget(desc_label)

            stats_layout.addLayout(stat_box)
            self.stat_widgets[key] = val_label

        layout.addWidget(stats_card)

        layout.addStretch()

    def refresh(self):
        """Обновление информации"""
        user = self.api_client.current_user
        if not user:
            success, data = self.api_client.get_current_user()
            if success:
                user = data
            else:
                return

        # Заполняем данные
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        self.name_label.setText(f"{first_name} {last_name}")

        role = user.get('role', '')
        role_text = "Администратор" if role == "admin" else "Пользователь"
        self.role_label.setText(f"🔑 {role_text}")

        field_map = {
            'id': str(user.get('id', '—')),
            'login': user.get('login', '—'),
            'first_name': first_name or '—',
            'last_name': last_name or '—',
            'role': role_text,
            'created_at': user.get('created_at', '—'),
        }

        for key, value in field_map.items():
            if key in self.detail_labels:
                self.detail_labels[key].setText(str(value))

        # Проверяем статусы
        self._check_statuses()

    def _check_statuses(self):
        """Проверка статусов сервера, модели, датасета"""
        success, data = self.api_client.health_check()
        if success:
            server_ok = data.get('server') == 'ok'
            model_ok = data.get('model') == 'ok'
            dataset_ok = data.get('dataset') == 'ok'

            self.stat_widgets['server_status'].setText("✓ OK" if server_ok else "✗")
            self.stat_widgets['server_status'].setStyleSheet(
                f"font-size: 16px; font-weight: bold; background: transparent; "
                f"color: {'#00e676' if server_ok else '#ff5252'};"
            )

            self.stat_widgets['model_status'].setText("✓ OK" if model_ok else "✗ Нет")
            self.stat_widgets['model_status'].setStyleSheet(
                f"font-size: 16px; font-weight: bold; background: transparent; "
                f"color: {'#00e676' if model_ok else '#ff5252'};"
            )

            self.stat_widgets['dataset_status'].setText("✓ OK" if dataset_ok else "✗ Нет")
            self.stat_widgets['dataset_status'].setStyleSheet(
                f"font-size: 16px; font-weight: bold; background: transparent; "
                f"color: {'#00e676' if dataset_ok else '#ff5252'};"
            )
        else:
            for key in self.stat_widgets:
                self.stat_widgets[key].setText("✗")
                self.stat_widgets[key].setStyleSheet(
                    "font-size: 16px; font-weight: bold; color: #ff5252; background: transparent;"
                )