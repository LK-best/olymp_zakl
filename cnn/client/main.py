# client/main.py
"""
Точка входа клиентского приложения.
Запуск: python -m client.main
или:    python client/main.py
"""
import sys
import os

# Добавляем корень проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from client.styles import MAIN_STYLE
from client.widgets.main_window import MainWindow


def main():
    # Настройки High-DPI для 4K мониторов
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Alien Signal Classifier")
    app.setOrganizationName("AlienLab2226")

    # Применяем стили
    app.setStyleSheet(MAIN_STYLE)

    # URL сервера (можно передать аргументом)
    server_url = "http://localhost:5000"
    if len(sys.argv) > 1:
        server_url = sys.argv[1]

    # Создаём и показываем главное окно
    window = MainWindow(server_url)
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()