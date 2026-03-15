# server/config.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'alien-signals-secret-key-2226')
    
    # Пути
    DB_PATH = os.path.join(BASE_DIR, 'db', 'app.db')
    MODEL_PATH = os.path.join(BASE_DIR, 'data', 'model.h5')
    DATA_PATH = os.path.join(BASE_DIR, 'data', 'Data.npz')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    TRAINING_HISTORY_PATH = os.path.join(BASE_DIR, 'data', 'training_history.json')
    LABEL_MAPPING_PATH = os.path.join(BASE_DIR, 'data', 'label_mapping.json')
    MODEL_CONFIG_PATH = os.path.join(BASE_DIR, 'data', 'model_config.json')
    
    # JWT
    JWT_EXPIRATION_HOURS = 24
    
    # Администратор по умолчанию
    DEFAULT_ADMIN_LOGIN = 'admin'
    DEFAULT_ADMIN_PASSWORD = 'admin123'
    DEFAULT_ADMIN_FIRST_NAME = 'Михаил'
    DEFAULT_ADMIN_LAST_NAME = 'Администратор'
    
    # Допустимые расширения файлов
    ALLOWED_EXTENSIONS = {'npz'}
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB