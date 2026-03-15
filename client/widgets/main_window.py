# client/widgets/main_window.py
"""
Главное окно приложения.
Объединяет авторизацию, панель админа и панель пользователя.
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QStatusBar, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer

from client.api_client import ApiClient
from client.widgets.login_window import LoginWindow
from client.widgets.admin_panel import AdminPanel
from client.widgets.user_panel import UserPanel


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self, server_url: str = "http://localhost:5000"):
        super().__init__()
        self.api_client = ApiClient(server_url)
        self._setup_ui()
        self._show_login()

    def _setup_ui(self):
        self.setWindowTitle("🛸 Alien Signal Classifier — Классификация инопланетных радиосигналов")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)

        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Верхняя панель
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(55)
        self.top_bar.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border-bottom: 2px solid #0f3460;
            }
        """)

        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(15, 0, 15, 0)

        app_title = QLabel("🛸 Alien Signal Classifier")
        app_title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #00d4ff; background: transparent;"
        )
        top_layout.addWidget(app_title)

        top_layout.addStretch()

        # Информация о пользователе
        self.user_info_label = QLabel("")
        self.user_info_label.setStyleSheet(
            "font-size: 13px; color: #b0b0b0; background: transparent;"
        )
        top_layout.addWidget(self.user_info_label)

        self.role_badge = QLabel("")
        self.role_badge.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #1a1a2e; "
            "background-color: #7b68ee; border-radius: 10px; "
            "padding: 3px 10px;"
        )
        self.role_badge.hide()
        top_layout.addWidget(self.role_badge)

        self.logout_btn = QPushButton("Выйти")
        self.logout_btn.setObjectName("logout_btn")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.clicked.connect(self._on_logout)
        self.logout_btn.hide()
        top_layout.addWidget(self.logout_btn)

        self.top_bar.hide()
        main_layout.addWidget(self.top_bar)

        # Контентная область
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        # Пустой виджет-заглушка
        placeholder = QWidget()
        self.content_stack.addWidget(placeholder)

        # Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")

    def _show_login(self):
        """Показ окна авторизации"""
        self.top_bar.hide()

        login_dialog = LoginWindow(self.api_client, self)
        result = login_dialog.exec_()

        if result == LoginWindow.Accepted and login_dialog.login_success:
            self._on_login_success()
        else:
            # Пользователь закрыл окно — выходим
            self.close()

    def _on_login_success(self):
        """Действия после успешной авторизации"""
        user = self.api_client.current_user
        if not user:
            self._show_login()
            return

        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        role = user.get('role', '')

        # Обновляем верхнюю панель
        self.user_info_label.setText(f"{first_name} {last_name}")

        role_text = "АДМИН" if role == "admin" else "ПОЛЬЗОВАТЕЛЬ"
        self.role_badge.setText(role_text)
        if role == "admin":
            self.role_badge.setStyleSheet(
                "font-size: 11px; font-weight: bold; color: #1a1a2e; "
                "background-color: #ffab40; border-radius: 10px; padding: 3px 10px;"
            )
        else:
            self.role_badge.setStyleSheet(
                "font-size: 11px; font-weight: bold; color: #1a1a2e; "
                "background-color: #7b68ee; border-radius: 10px; padding: 3px 10px;"
            )
        self.role_badge.show()
        self.logout_btn.show()
        self.top_bar.show()

        # Создаём панель в зависимости от роли
        if role == 'admin':
            panel = AdminPanel(self.api_client)
            self.status_bar.showMessage("Режим администратора")
        else:
            panel = UserPanel(self.api_client)
            self.status_bar.showMessage("Режим пользователя")

        # Добавляем в стек и показываем
        self.content_stack.addWidget(panel)
        self.content_stack.setCurrentWidget(panel)

    def _on_logout(self):
        """Выход из системы"""
        reply = QMessageBox.question(
            self, "Подтверждение выхода",
            "Вы уверены, что хотите выйти?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.api_client.logout()

            # Удаляем все виджеты кроме placeholder
            while self.content_stack.count() > 1:
                widget = self.content_stack.widget(1)
                self.content_stack.removeWidget(widget)
                widget.deleteLater()

            self.top_bar.hide()
            self.status_bar.showMessage("Выход выполнен")

            # Показываем окно входа заново
            QTimer.singleShot(100, self._show_login)

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.api_client.is_authenticated():
            self.api_client.logout()
        event.accept()