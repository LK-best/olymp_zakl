# client/widgets/admin_panel.py
"""
Панель администратора: создание новых пользователей.
ТЗ: "В функциональные возможности администратора должно входить
     только создание новых пользователей, с внесением информации
     о пользователе не менее чем в два текстовых полях (Имя, Фамилия)."
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QFrame,
    QHeaderView, QMessageBox, QComboBox, QGroupBox, QGridLayout,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt

from client.api_client import ApiClient


class AdminPanel(QWidget):
    """Панель администратора"""

    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self._setup_ui()
        self._load_users()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("⚙️ Панель администратора")
        title.setObjectName("title")
        layout.addWidget(title)

        # Форма создания пользователя
        create_group = QGroupBox("Создание нового пользователя")
        create_layout = QGridLayout(create_group)
        create_layout.setSpacing(12)
        create_layout.setContentsMargins(20, 20, 20, 20)

        # Логин
        create_layout.addWidget(QLabel("Логин:"), 0, 0)
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин (мин. 3 символа)")
        create_layout.addWidget(self.login_input, 0, 1)

        # Пароль
        create_layout.addWidget(QLabel("Пароль:"), 1, 0)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль (мин. 4 символа)")
        self.password_input.setEchoMode(QLineEdit.Password)
        create_layout.addWidget(self.password_input, 1, 1)

        # Имя
        create_layout.addWidget(QLabel("Имя:"), 2, 0)
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Введите имя")
        create_layout.addWidget(self.first_name_input, 2, 1)

        # Фамилия
        create_layout.addWidget(QLabel("Фамилия:"), 3, 0)
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Введите фамилию")
        create_layout.addWidget(self.last_name_input, 3, 1)

        # Роль
        create_layout.addWidget(QLabel("Роль:"), 4, 0)
        self.role_combo = QComboBox()
        self.role_combo.addItem("Пользователь", "user")
        self.role_combo.addItem("Администратор", "admin")
        create_layout.addWidget(self.role_combo, 4, 1)

        # Сообщение
        self.create_message = QLabel("")
        self.create_message.setWordWrap(True)
        self.create_message.hide()
        create_layout.addWidget(self.create_message, 5, 0, 1, 2)

        # Кнопка создания
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.create_btn = QPushButton("  ➕ Создать пользователя  ")
        self.create_btn.setObjectName("success_btn")
        self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.setMinimumHeight(42)
        self.create_btn.clicked.connect(self._create_user)
        btn_row.addWidget(self.create_btn)

        create_layout.addLayout(btn_row, 6, 0, 1, 2)

        layout.addWidget(create_group)

        # Таблица пользователей
        users_group = QGroupBox("Список пользователей")
        users_layout = QVBoxLayout(users_group)

        btn_row2 = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Обновить список")
        refresh_btn.clicked.connect(self._load_users)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        btn_row2.addWidget(refresh_btn)
        btn_row2.addStretch()

        self.user_count_label = QLabel("")
        self.user_count_label.setStyleSheet("color: #888; font-size: 12px;")
        btn_row2.addWidget(self.user_count_label)

        users_layout.addLayout(btn_row2)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Логин", "Имя", "Фамилия", "Роль", "Дата создания"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #0d1b30;
            }
        """)
        users_layout.addWidget(self.users_table)

        # Кнопка удаления
        del_row = QHBoxLayout()
        del_row.addStretch()
        self.delete_btn = QPushButton("  🗑 Удалить выбранного  ")
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.clicked.connect(self._delete_user)
        del_row.addWidget(self.delete_btn)
        users_layout.addLayout(del_row)

        layout.addWidget(users_group)

    def _create_user(self):
        """Создание нового пользователя"""
        login = self.login_input.text().strip()
        password = self.password_input.text()
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        role = self.role_combo.currentData()

        # Валидация на стороне клиента
        errors = []
        if not login or len(login) < 3:
            errors.append("Логин должен содержать минимум 3 символа")
        if not password or len(password) < 4:
            errors.append("Пароль должен содержать минимум 4 символа")
        if not first_name:
            errors.append("Имя обязательно")
        if not last_name:
            errors.append("Фамилия обязательна")

        if errors:
            self._show_message("; ".join(errors), is_error=True)
            return

        self.create_btn.setEnabled(False)
        self.create_btn.setText("Создание...")

        success, data = self.api_client.create_user(
            login=login,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role
        )

        self.create_btn.setEnabled(True)
        self.create_btn.setText("  ➕ Создать пользователя  ")

        if success:
            self._show_message(
                f"✓ Пользователь '{login}' ({first_name} {last_name}) "
                f"успешно создан!",
                is_error=False
            )
            # Очистка полей
            self.login_input.clear()
            self.password_input.clear()
            self.first_name_input.clear()
            self.last_name_input.clear()
            self.role_combo.setCurrentIndex(0)
            # Обновляем таблицу
            self._load_users()
        else:
            error = data.get('error', 'Ошибка создания пользователя')
            self._show_message(f"✗ {error}", is_error=True)

    def _load_users(self):
        """Загрузка списка пользователей"""
        success, data = self.api_client.get_users()
        if not success:
            return

        users = data.get('users', [])
        self.users_table.setRowCount(len(users))

        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user.get('id', ''))))
            self.users_table.setItem(row, 1, QTableWidgetItem(user.get('login', '')))
            self.users_table.setItem(row, 2, QTableWidgetItem(user.get('first_name', '')))
            self.users_table.setItem(row, 3, QTableWidgetItem(user.get('last_name', '')))

            role = user.get('role', '')
            role_text = "Администратор" if role == "admin" else "Пользователь"
            role_item = QTableWidgetItem(role_text)
            if role == "admin":
                role_item.setForeground(Qt.yellow)
            self.users_table.setItem(row, 4, role_item)

            self.users_table.setItem(row, 5, QTableWidgetItem(user.get('created_at', '')))

        self.user_count_label.setText(f"Всего: {len(users)} пользователей")

    def _delete_user(self):
        """Удаление выбранного пользователя"""
        current_row = self.users_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите пользователя для удаления")
            return

        user_id = int(self.users_table.item(current_row, 0).text())
        login = self.users_table.item(current_row, 1).text()
        name = self.users_table.item(current_row, 2).text()

        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Удалить пользователя '{login}' ({name})?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, data = self.api_client.delete_user(user_id)
            if success:
                self._show_message(f"✓ Пользователь '{login}' удалён", is_error=False)
                self._load_users()
            else:
                error = data.get('error', 'Ошибка удаления')
                self._show_message(f"✗ {error}", is_error=True)

    def _show_message(self, text: str, is_error: bool = False):
        """Показ сообщения в форме"""
        if is_error:
            self.create_message.setObjectName("error_label")
            self.create_message.setStyleSheet(
                "color: #ff5252; font-size: 13px; font-weight: bold; "
                "background: transparent; padding: 5px;"
            )
        else:
            self.create_message.setObjectName("success_label")
            self.create_message.setStyleSheet(
                "color: #00e676; font-size: 13px; font-weight: bold; "
                "background: transparent; padding: 5px;"
            )
        self.create_message.setText(text)
        self.create_message.show()