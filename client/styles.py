# client/styles.py
"""
Стили приложения — единая тема оформления.
"""

MAIN_STYLE = """
QMainWindow, QDialog, QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QLabel {
    color: #e0e0e0;
    font-size: 13px;
}

QLabel#title {
    font-size: 22px;
    font-weight: bold;
    color: #00d4ff;
    padding: 10px 0;
}

QLabel#subtitle {
    font-size: 16px;
    font-weight: bold;
    color: #7b68ee;
    padding: 5px 0;
}

QLabel#info_label {
    font-size: 14px;
    color: #b0b0b0;
    padding: 3px 0;
}

QLabel#success_label {
    color: #00e676;
    font-size: 13px;
    font-weight: bold;
}

QLabel#error_label {
    color: #ff5252;
    font-size: 13px;
    font-weight: bold;
}

QLabel#stat_value {
    font-size: 28px;
    font-weight: bold;
    color: #00d4ff;
}

QLabel#stat_label {
    font-size: 11px;
    color: #888;
}

QLineEdit {
    background-color: #16213e;
    color: #e0e0e0;
    border: 2px solid #0f3460;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
    selection-background-color: #7b68ee;
}

QLineEdit:focus {
    border-color: #00d4ff;
}

QLineEdit:disabled {
    background-color: #0d1b30;
    color: #666;
}

QPushButton {
    background-color: #0f3460;
    color: #e0e0e0;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #1a4a8a;
}

QPushButton:pressed {
    background-color: #0a2540;
}

QPushButton:disabled {
    background-color: #1a1a2e;
    color: #555;
}

QPushButton#primary_btn {
    background-color: #7b68ee;
    color: white;
}

QPushButton#primary_btn:hover {
    background-color: #9580ff;
}

QPushButton#primary_btn:pressed {
    background-color: #5a4db8;
}

QPushButton#success_btn {
    background-color: #00897b;
    color: white;
}

QPushButton#success_btn:hover {
    background-color: #00a890;
}

QPushButton#danger_btn {
    background-color: #c62828;
    color: white;
}

QPushButton#danger_btn:hover {
    background-color: #e53935;
}

QPushButton#logout_btn {
    background-color: transparent;
    color: #ff8a80;
    border: 1px solid #ff8a80;
    padding: 6px 16px;
    font-size: 12px;
}

QPushButton#logout_btn:hover {
    background-color: #ff8a80;
    color: #1a1a2e;
}

QPushButton#nav_btn {
    background-color: transparent;
    color: #b0b0b0;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: normal;
    text-align: left;
}

QPushButton#nav_btn:hover {
    background-color: #16213e;
    color: #e0e0e0;
}

QPushButton#nav_btn_active {
    background-color: #0f3460;
    color: #00d4ff;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: bold;
    text-align: left;
    border-left: 3px solid #00d4ff;
}

QComboBox {
    background-color: #16213e;
    color: #e0e0e0;
    border: 2px solid #0f3460;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #00d4ff;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e0e0e0;
    selection-background-color: #0f3460;
    border: 1px solid #0f3460;
}

QTableWidget {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 8px;
    gridline-color: #0f3460;
    selection-background-color: #0f3460;
    font-size: 12px;
}

QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #0a1e3d;
}

QTableWidget::item:selected {
    background-color: #1a4a8a;
}

QHeaderView::section {
    background-color: #0f3460;
    color: #00d4ff;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid #1a1a2e;
    font-weight: bold;
    font-size: 12px;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #0f3460;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #1a4a8a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #1a1a2e;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #0f3460;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #1a4a8a;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QGroupBox {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 10px;
    margin-top: 10px;
    padding: 15px;
    padding-top: 25px;
    font-size: 13px;
    font-weight: bold;
    color: #7b68ee;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 8px;
}

QTabWidget::pane {
    background-color: #1a1a2e;
    border: 1px solid #0f3460;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: #16213e;
    color: #b0b0b0;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-size: 13px;
}

QTabBar::tab:selected {
    background-color: #0f3460;
    color: #00d4ff;
    font-weight: bold;
}

QTabBar::tab:hover {
    background-color: #1a3a5c;
}

QProgressBar {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 8px;
    text-align: center;
    color: #e0e0e0;
    font-size: 12px;
    min-height: 22px;
}

QProgressBar::chunk {
    background-color: #7b68ee;
    border-radius: 7px;
}

QMessageBox {
    background-color: #1a1a2e;
    color: #e0e0e0;
}

QMessageBox QLabel {
    color: #e0e0e0;
    font-size: 13px;
}

QMessageBox QPushButton {
    min-width: 80px;
}

QStatusBar {
    background-color: #0d1117;
    color: #888;
    font-size: 11px;
    border-top: 1px solid #0f3460;
}

QToolTip {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 4px;
    padding: 5px;
    font-size: 12px;
}

QSplitter::handle {
    background-color: #0f3460;
    width: 2px;
}
"""

# Цвета для графиков matplotlib
CHART_COLORS = {
    'background': '#1a1a2e',
    'face': '#16213e',
    'text': '#e0e0e0',
    'grid': '#0f3460',
    'primary': '#7b68ee',
    'secondary': '#00d4ff',
    'success': '#00e676',
    'danger': '#ff5252',
    'warning': '#ffab40',
    'accent1': '#ff6ec7',
    'accent2': '#40c4ff',
    'accent3': '#b388ff',
    'accent4': '#64ffda',
    'accent5': '#ffd740',
    'bar_colors': [
        '#7b68ee', '#00d4ff', '#00e676', '#ff6ec7', '#ffab40',
        '#40c4ff', '#b388ff', '#64ffda', '#ffd740', '#ff5252',
        '#80cbc4', '#ce93d8', '#a5d6a7', '#ef9a9a', '#90caf9',
        '#fff59d', '#f48fb1', '#80deea', '#c5e1a5', '#ffcc80'
    ]
}