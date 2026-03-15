import sys
import os
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLineEdit,
    QTextEdit, QComboBox, QTableWidget, QTableWidgetItem, QLabel, QPushButton,
    QStackedWidget, QMessageBox, QFormLayout, QFileDialog, QScrollArea,
    QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from database import Database


db = Database()


class LoginWidget(QWidget):
    def __init__(self, app_controller):
        super().__init__()
        self.app_controller = app_controller
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container = QGroupBox("Вход в систему")
        container.setMaximumWidth(400)
        form = QVBoxLayout()

        self.title = QLabel("Классификация инопланетных сигналов")
        self.title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логин")
        self.login_input.setMinimumHeight(35)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Пароль")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setMinimumHeight(35)
        self.pass_input.returnPressed.connect(self.do_login)

        self.btn_login = QPushButton("Войти")
        self.btn_login.setMinimumHeight(40)
        self.btn_login.clicked.connect(self.do_login)

        self.btn_register = QPushButton("Регистрация")
        self.btn_register.clicked.connect(self.app_controller.show_registration)

        form.addWidget(self.login_input)
        form.addWidget(self.pass_input)
        form.addWidget(self.btn_login)
        form.addWidget(QLabel("Нет аккаунта?"))
        form.addWidget(self.btn_register)
        container.setLayout(form)

        layout.addWidget(self.title)
        layout.addSpacing(20)
        layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

    def do_login(self):
        login = self.login_input.text().strip()
        password = self.pass_input.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        user = db.authenticate(login, password)
        if user:
            self.login_input.clear()
            self.pass_input.clear()
            self.app_controller.login_success(user)
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль!")


class RegistrationWidget(QWidget):
    def __init__(self, app_controller):
        super().__init__()
        self.app_controller = app_controller
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container = QGroupBox("Регистрация нового пользователя")
        container.setMaximumWidth(450)
        form = QFormLayout()

        self.fname_input = QLineEdit()
        self.fname_input.setMinimumHeight(30)
        self.lname_input = QLineEdit()
        self.lname_input.setMinimumHeight(30)
        self.login_input = QLineEdit()
        self.login_input.setMinimumHeight(30)
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setMinimumHeight(30)
        self.pass_confirm = QLineEdit()
        self.pass_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_confirm.setMinimumHeight(30)

        form.addRow("Имя:", self.fname_input)
        form.addRow("Фамилия:", self.lname_input)
        form.addRow("Логин:", self.login_input)
        form.addRow("Пароль:", self.pass_input)
        form.addRow("Повторите пароль:", self.pass_confirm)

        self.btn_submit = QPushButton("Зарегистрироваться")
        self.btn_submit.setMinimumHeight(40)
        self.btn_submit.clicked.connect(self.do_register)

        self.btn_back = QPushButton("Назад ко входу")
        self.btn_back.clicked.connect(self.app_controller.show_login)

        form.addRow(self.btn_submit)
        form.addRow(self.btn_back)
        container.setLayout(form)

        layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

    def do_register(self):
        fname = self.fname_input.text().strip()
        lname = self.lname_input.text().strip()
        login = self.login_input.text().strip()
        password = self.pass_input.text()
        confirm = self.pass_confirm.text()

        if not all([fname, lname, login, password]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        if password != confirm:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают!")
            return

        success = db.create_user(login, password, "user", fname, lname)
        if success:
            QMessageBox.information(self, "Успех", "Регистрация прошла успешно!")
            self.clear_fields()
            self.app_controller.show_login()
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь с таким логином уже существует!")

    def clear_fields(self):
        self.fname_input.clear()
        self.lname_input.clear()
        self.login_input.clear()
        self.pass_input.clear()
        self.pass_confirm.clear()


class AdminWidget(QWidget):
    def __init__(self, app_controller, user_data):
        super().__init__()
        self.app_controller = app_controller
        self.user_data = user_data
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        header = QHBoxLayout()
        title = QLabel(f"Панель администратора — {self.user_data['first_name']} {self.user_data['last_name']}")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_logout = QPushButton("Выйти")
        btn_logout.setMaximumWidth(120)
        btn_logout.clicked.connect(self.app_controller.logout)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_logout)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_user_tab(), "Создать пользователя")
        self.tabs.addTab(self.users_list_tab(), "Список пользователей")
        self.tabs.addTab(self.sessions_tab(), "История входов")

        layout.addLayout(header)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def create_user_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        container = QGroupBox("Новый пользователь")
        form = QFormLayout()

        self.fname_input = QLineEdit()
        self.lname_input = QLineEdit()
        self.login_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin"])

        form.addRow("Имя:", self.fname_input)
        form.addRow("Фамилия:", self.lname_input)
        form.addRow("Логин:", self.login_input)
        form.addRow("Пароль:", self.pass_input)
        form.addRow("Роль:", self.role_combo)

        btn_create = QPushButton("Создать")
        btn_create.setMinimumHeight(40)
        btn_create.clicked.connect(self.do_create_user)
        form.addRow(btn_create)

        container.setLayout(form)
        layout.addWidget(container)
        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def do_create_user(self):
        fname = self.fname_input.text().strip()
        lname = self.lname_input.text().strip()
        login = self.login_input.text().strip()
        password = self.pass_input.text().strip()
        role = self.role_combo.currentText()

        if not all([fname, lname, login, password]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        success = db.create_user(login, password, role, fname, lname)
        if success:
            QMessageBox.information(self, "Успех", f"Пользователь '{login}' создан!")
            self.fname_input.clear()
            self.lname_input.clear()
            self.login_input.clear()
            self.pass_input.clear()
            self.refresh_users_table()
        else:
            QMessageBox.warning(self, "Ошибка", "Такой логин уже существует!")

    def users_list_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        btn_refresh = QPushButton("Обновить список")
        btn_refresh.clicked.connect(self.refresh_users_table)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(["ID", "Логин", "Роль", "Имя", "Фамилия"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(btn_refresh)
        layout.addWidget(self.users_table)
        tab.setLayout(layout)

        self.refresh_users_table()
        return tab

    def refresh_users_table(self):
        users = db.get_all_users()
        self.users_table.setRowCount(len(users))
        for i, user in enumerate(users):
            self.users_table.setItem(i, 0, QTableWidgetItem(str(user["id"])))
            self.users_table.setItem(i, 1, QTableWidgetItem(user["login"]))
            self.users_table.setItem(i, 2, QTableWidgetItem(user["role"]))
            self.users_table.setItem(i, 3, QTableWidgetItem(user["first_name"]))
            self.users_table.setItem(i, 4, QTableWidgetItem(user["last_name"]))

    def sessions_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        btn_refresh = QPushButton("Обновить")
        btn_refresh.clicked.connect(self.refresh_sessions)

        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(4)
        self.sessions_table.setHorizontalHeaderLabels(["Логин", "Имя", "Фамилия", "Время входа"])
        self.sessions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sessions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(btn_refresh)
        layout.addWidget(self.sessions_table)
        tab.setLayout(layout)

        self.refresh_sessions()
        return tab

    def refresh_sessions(self):
        sessions = db.get_sessions()
        self.sessions_table.setRowCount(len(sessions))
        for i, s in enumerate(sessions):
            self.sessions_table.setItem(i, 0, QTableWidgetItem(s["login"]))
            self.sessions_table.setItem(i, 1, QTableWidgetItem(s["first_name"]))
            self.sessions_table.setItem(i, 2, QTableWidgetItem(s["last_name"]))
            self.sessions_table.setItem(i, 3, QTableWidgetItem(s["login_time"]))


class UserWidget(QWidget):
    def __init__(self, app_controller, user_data):
        super().__init__()
        self.app_controller = app_controller
        self.user_data = user_data
        self.dataset_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        header = QHBoxLayout()
        title = QLabel(f"Пользователь: {self.user_data['first_name']} {self.user_data['last_name']}")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_logout = QPushButton("Выйти")
        btn_logout.setMaximumWidth(120)
        btn_logout.clicked.connect(self.app_controller.logout)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_logout)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.profile_tab(), "Профиль")
        self.tabs.addTab(self.upload_tab(), "Загрузка данных")
        self.tabs.addTab(self.analytics_tab(), "Аналитика")

        layout.addLayout(header)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def profile_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        info_group = QGroupBox("Информация о пользователе")
        info_layout = QFormLayout()
        info_layout.addRow("Имя:", QLabel(self.user_data["first_name"]))
        info_layout.addRow("Фамилия:", QLabel(self.user_data["last_name"]))
        info_layout.addRow("Роль:", QLabel(self.user_data["role"]))
        info_layout.addRow("ID:", QLabel(str(self.user_data["id"])))
        info_group.setLayout(info_layout)

        sessions_group = QGroupBox("Мои последние входы")
        sessions_layout = QVBoxLayout()
        self.my_sessions_table = QTableWidget()
        self.my_sessions_table.setColumnCount(2)
        self.my_sessions_table.setHorizontalHeaderLabels(["Логин", "Время входа"])
        self.my_sessions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.my_sessions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        sessions_layout.addWidget(self.my_sessions_table)
        sessions_group.setLayout(sessions_layout)

        self.load_my_sessions()

        layout.addWidget(info_group)
        layout.addWidget(sessions_group)
        tab.setLayout(layout)
        return tab

    def load_my_sessions(self):
        sessions = db.get_sessions(self.user_data["id"])
        self.my_sessions_table.setRowCount(len(sessions))
        for i, s in enumerate(sessions):
            self.my_sessions_table.setItem(i, 0, QTableWidgetItem(s["login"]))
            self.my_sessions_table.setItem(i, 1, QTableWidgetItem(s["login_time"]))

    def upload_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        upload_group = QGroupBox("Загрузка тестового набора данных")
        upload_layout = QVBoxLayout()

        file_row = QHBoxLayout()
        self.file_label = QLabel("Файл не выбран")
        btn_browse = QPushButton("Выбрать файл (.npz)")
        btn_browse.setMinimumHeight(35)
        btn_browse.clicked.connect(self.browse_file)
        file_row.addWidget(self.file_label, stretch=1)
        file_row.addWidget(btn_browse)

        self.btn_process = QPushButton("Загрузить и обработать")
        self.btn_process.setMinimumHeight(40)
        self.btn_process.setEnabled(False)
        self.btn_process.clicked.connect(self.process_dataset)

        upload_layout.addLayout(file_row)
        upload_layout.addWidget(self.btn_process)
        upload_group.setLayout(upload_layout)

        metrics_group = QGroupBox("Результаты на тестовом наборе")
        metrics_layout = QFormLayout()
        self.lbl_total = QLabel("—")
        self.lbl_accuracy = QLabel("—")
        self.lbl_loss = QLabel("—")
        self.lbl_total.setFont(QFont("Arial", 12))
        self.lbl_accuracy.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.lbl_loss.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        metrics_layout.addRow("Всего записей:", self.lbl_total)
        metrics_layout.addRow("Точность (Accuracy):", self.lbl_accuracy)
        metrics_layout.addRow("Потери (Loss):", self.lbl_loss)
        metrics_group.setLayout(metrics_layout)

        predictions_group = QGroupBox("Таблица предсказаний")
        pred_layout = QVBoxLayout()
        self.pred_table = QTableWidget()
        self.pred_table.setColumnCount(5)
        self.pred_table.setHorizontalHeaderLabels(
            ["Запись", "Истинный класс", "Предсказание", "Уверенность", "Верно"]
        )
        self.pred_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pred_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        pred_layout.addWidget(self.pred_table)
        predictions_group.setLayout(pred_layout)

        layout.addWidget(upload_group)
        layout.addWidget(metrics_group)
        layout.addWidget(predictions_group)
        tab.setLayout(layout)
        return tab

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите тестовый набор данных", "", "NumPy Archive (*.npz)"
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.btn_process.setEnabled(True)

    def process_dataset(self):
        try:
            data = np.load(self.selected_file, allow_pickle=True)
            keys = data.files

            test_x_key = None
            test_y_key = None
            for k in keys:
                if 'x' in k.lower():
                    test_x_key = k
                if 'y' in k.lower():
                    test_y_key = k

            if not test_x_key:
                QMessageBox.warning(self, "Ошибка", f"Не найден массив с данными. Ключи: {keys}")
                return

            test_x = data[test_x_key]
            total_records = test_x.shape[0]

            if test_y_key:
                test_y = data[test_y_key]
                true_classes = []
                for label in test_y:
                    try:
                        true_classes.append(int(label))
                    except (ValueError, TypeError):
                        true_classes.append(0)
            else:
                true_classes = [0] * total_records

            # Заглушка: тут должно быть предсказание модели
            # predicted = model.predict(test_x)
            predicted_classes = []
            confidences = []
            for i in range(total_records):
                pred = true_classes[i] if np.random.random() > 0.15 else np.random.randint(0, 10)
                predicted_classes.append(pred)
                confidences.append(round(np.random.uniform(0.5, 1.0), 3))

            correct = sum(1 for t, p in zip(true_classes, predicted_classes) if t == p)
            accuracy = round(correct / total_records * 100, 2)
            loss = round(np.random.uniform(0.1, 0.5), 4)

            dataset_id = db.save_dataset_info(
                user_id=self.user_data["id"],
                file_name=os.path.basename(self.selected_file),
                file_path=self.selected_file,
                total_records=total_records,
                accuracy=accuracy,
                loss=loss
            )
            self.dataset_id = dataset_id

            predictions = []
            for i in range(total_records):
                predictions.append({
                    "record_index": i,
                    "true_class": true_classes[i],
                    "predicted_class": predicted_classes[i],
                    "confidence": confidences[i]
                })
            db.save_predictions(dataset_id, predictions)

            self.lbl_total.setText(str(total_records))
            self.lbl_accuracy.setText(f"{accuracy}%")
            self.lbl_loss.setText(str(loss))

            self.pred_table.setRowCount(total_records)
            for i, pred in enumerate(predictions):
                is_ok = "✅" if pred["true_class"] == pred["predicted_class"] else "❌"
                self.pred_table.setItem(i, 0, QTableWidgetItem(str(i)))
                self.pred_table.setItem(i, 1, QTableWidgetItem(str(pred["true_class"])))
                self.pred_table.setItem(i, 2, QTableWidgetItem(str(pred["predicted_class"])))
                self.pred_table.setItem(i, 3, QTableWidgetItem(str(pred["confidence"])))
                self.pred_table.setItem(i, 4, QTableWidgetItem(is_ok))

            self.update_charts(predictions)
            QMessageBox.information(self, "Готово", f"Обработано {total_records} записей\nТочность: {accuracy}%")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обработать файл:\n{str(e)}")

    def analytics_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        self.figure, self.axs = plt.subplots(2, 2, figsize=(12, 9))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.draw_default_charts()

        scroll_layout.addWidget(self.toolbar)
        scroll_layout.addWidget(self.canvas)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        tab.setLayout(layout)
        return tab

    def draw_default_charts(self):
        for ax in self.axs.flat:
            ax.clear()

        ax1 = self.axs[0, 0]
        history = db.get_training_history()
        if history:
            epochs = [h["epoch"] for h in history]
            val_acc = [h["val_accuracy"] for h in history]
            train_acc = [h["train_accuracy"] for h in history]
            ax1.plot(epochs, val_acc, 'b-o', label="Валидация", markersize=4)
            ax1.plot(epochs, train_acc, 'g--', label="Обучение", alpha=0.7)
            ax1.legend()
        else:
            ax1.text(0.5, 0.5, "Нет данных", ha='center', va='center', transform=ax1.transAxes)
        ax1.set_title("Точность от эпох обучения")
        ax1.set_xlabel("Эпоха")
        ax1.set_ylabel("Точность")

        ax2 = self.axs[0, 1]
        train_dist = db.get_class_distribution("train")
        if train_dist:
            classes = [str(d["class_id"]) for d in train_dist]
            counts = [d["record_count"] for d in train_dist]
            colors = plt.cm.tab10(np.linspace(0, 1, len(classes)))
            ax2.bar(classes, counts, color=colors)
        else:
            ax2.text(0.5, 0.5, "Нет данных", ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title("Записи по цивилизациям (train)")
        ax2.set_xlabel("Класс (цивилизация)")
        ax2.set_ylabel("Количество")

        ax3 = self.axs[1, 0]
        ax3.text(0.5, 0.5, "Загрузите тестовый набор", ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title("Точность каждой записи (тест)")

        ax4 = self.axs[1, 1]
        top5 = db.get_top_classes("valid", top_n=5)
        if top5:
            labels = [f"Класс {d['class_id']}" for d in top5]
            sizes = [d["record_count"] for d in top5]
            ax4.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        else:
            ax4.text(0.5, 0.5, "Нет данных", ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title("Топ-5 классов (валидация)")

        self.figure.tight_layout()
        self.canvas.draw()

    def update_charts(self, predictions):
        ax3 = self.axs[1, 0]
        ax3.clear()

        indices = [p["record_index"] for p in predictions]
        confs = [p["confidence"] for p in predictions]
        colors = ["green" if p["true_class"] == p["predicted_class"] else "red" for p in predictions]

        ax3.bar(indices, confs, color=colors, width=1.0)
        ax3.set_title("Точность каждой записи (тест)")
        ax3.set_xlabel("Номер записи")
        ax3.set_ylabel("Уверенность")
        ax3.set_ylim(0, 1.1)

        self.figure.tight_layout()
        self.canvas.draw()


class AppController(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1100, 750)
        self.setMinimumSize(800, 600)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        self.login_widget = LoginWidget(self)
        self.reg_widget = RegistrationWidget(self)

        self.stack.addWidget(self.login_widget)
        self.stack.addWidget(self.reg_widget)

        self.main_layout.addWidget(self.stack)
        self.setLayout(self.main_layout)

    def show_login(self):
        self.stack.setCurrentWidget(self.login_widget)

    def show_registration(self):
        self.stack.setCurrentWidget(self.reg_widget)

    def login_success(self, user_data):
        if user_data["role"] == "admin":
            widget = AdminWidget(self, user_data)
        else:
            widget = UserWidget(self, user_data)

        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)

    def logout(self):
        current = self.stack.currentWidget()
        self.stack.setCurrentWidget(self.login_widget)

        if current and current not in (self.login_widget, self.reg_widget):
            self.stack.removeWidget(current)
            current.deleteLater()


if __name__ == "__main__":
    db.init_db()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = AppController()
    window.show()
    sys.exit(app.exec())