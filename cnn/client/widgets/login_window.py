# client/widgets/login_window.py
"""
Окно авторизации пользователя.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from client.api_client import ApiClient


class LoginWindow(QDialog):
    """Окно входа в систему"""

    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.login_success = False
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Вход в систему — Alien Signal Classifier")
        self.setFixedSize(450, 520)
        self.setWindowFlags(Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Верхний блок с заголовком
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f3460, stop:1 #7b68ee);
                border-bottom: 2px solid #00d4ff;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(30, 30, 30, 25)

        title = QLabel("🛸 Alien Signal Classifier")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white; background: transparent;")
        header_layout.addWidget(title)

        subtitle = QLabel("Система классификации инопланетных радиосигналов")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 12px; color: #b0d4ff; background: transparent;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

        # Форма входа
        form_container = QFrame()
        form_container.setStyleSheet("QFrame { background-color: #1a1a2e; }")
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(40, 30, 40, 30)
        form_layout.setSpacing(15)

        # Заголовок формы
        form_title = QLabel("Авторизация")
        form_title.setAlignment(Qt.AlignCenter)
        form_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0;")
        form_layout.addWidget(form_title)

        form_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Логин
        login_label = QLabel("Логин")
        login_label.setStyleSheet("font-size: 13px; color: #b0b0b0; font-weight: bold;")
        form_layout.addWidget(login_label)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин...")
        self.login_input.setMinimumHeight(42)
        form_layout.addWidget(self.login_input)

        # Пароль
        pass_label = QLabel("Пароль")
        pass_label.setStyleSheet("font-size: 13px; color: #b0b0b0; font-weight: bold;")
        form_layout.addWidget(pass_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль...")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(42)
        self.password_input.returnPressed.connect(self._on_login)
        form_layout.addWidget(self.password_input)

        form_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Сообщение об ошибке
        self.error_label = QLabel("")
        self.error_label.setObjectName("error_label")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        form_layout.addWidget(self.error_label)

        # Кнопка входа
        self.login_btn = QPushButton("  Войти  ")
        self.login_btn.setObjectName("primary_btn")
        self.login_btn.setMinimumHeight(45)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #7b68ee;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9580ff;
            }
            QPushButton:pressed {
                background-color: #5a4db8;
            }
        """)
        self.login_btn.clicked.connect(self._on_login)
        form_layout.addWidget(self.login_btn)

        # Статус подключения
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 11px; color: #666;")
        form_layout.addWidget(self.status_label)

        form_layout.addStretch()

        layout.addWidget(form_container)

        # Проверяем подключение к серверу
        self._check_connection()

    def _check_connection(self):
        """Проверка подключения к серверу"""
        success, data = self.api_client.health_check()
        if success:
            self.status_label.setText("✓ Сервер доступен")
            self.status_label.setStyleSheet("font-size: 11px; color: #00e676;")
        else:
            self.status_label.setText("✗ Сервер недоступен")
            self.status_label.setStyleSheet("font-size: 11px; color: #ff5252;")

    def _on_login(self):
        """Обработка нажатия кнопки входа"""
        login = self.login_input.text().strip()
        password = self.password_input.text()

        if not login:
            self._show_error("Введите логин")
            self.login_input.setFocus()
            return

        if not password:
            self._show_error("Введите пароль")
            self.password_input.setFocus()
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Вход...")

        success, data = self.api_client.login(login, password)

        self.login_btn.setEnabled(True)
        self.login_btn.setText("  Войти  ")

        if success:
            self.login_success = True
            self.accept()
        else:
            error_msg = data.get('error', 'Ошибка авторизации')
            self._show_error(error_msg)

    def _show_error(self, message: str):
        """Показ сообщения об ошибке"""
        self.error_label.setText(message)
        self.error_label.show()

    def get_user_data(self):
        """Получение данных авторизованного пользователя"""
        return self.api_client.current_user