# client/api_client.py
"""
HTTP-клиент для взаимодействия с REST API сервера.
Все запросы к серверу проходят через этот модуль.
"""
import requests
from typing import Optional, Dict, Any, Tuple


class ApiClient:
    """Клиент для работы с API сервера"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.token: Optional[str] = None
        self.current_user: Optional[Dict] = None
        self.session = requests.Session()
        self.timeout = 120  # секунд (модель может долго обрабатывать)

    # --------------------------------------------------------
    # Вспомогательные методы
    # --------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        """Заголовки с токеном авторизации"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Tuple[int, Dict]:
        """GET-запрос"""
        try:
            resp = self.session.get(
                f"{self.base_url}{endpoint}",
                headers=self._headers(),
                params=params,
                timeout=self.timeout
            )
            return resp.status_code, resp.json()
        except requests.ConnectionError:
            return 0, {"error": "Нет соединения с сервером"}
        except requests.Timeout:
            return 0, {"error": "Таймаут соединения"}
        except Exception as e:
            return 0, {"error": str(e)}

    def _post(self, endpoint: str, data: Optional[Dict] = None) -> Tuple[int, Dict]:
        """POST-запрос с JSON"""
        try:
            resp = self.session.post(
                f"{self.base_url}{endpoint}",
                headers=self._headers(),
                json=data,
                timeout=self.timeout
            )
            return resp.status_code, resp.json()
        except requests.ConnectionError:
            return 0, {"error": "Нет соединения с сервером"}
        except requests.Timeout:
            return 0, {"error": "Таймаут соединения"}
        except Exception as e:
            return 0, {"error": str(e)}

    def _post_file(self, endpoint: str, file_path: str) -> Tuple[int, Dict]:
        """POST-запрос с файлом (multipart)"""
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            with open(file_path, 'rb') as f:
                files = {"file": (file_path.split('/')[-1].split('\\')[-1], f)}
                resp = self.session.post(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    files=files,
                    timeout=self.timeout
                )
            return resp.status_code, resp.json()
        except requests.ConnectionError:
            return 0, {"error": "Нет соединения с сервером"}
        except requests.Timeout:
            return 0, {"error": "Таймаут соединения"}
        except Exception as e:
            return 0, {"error": str(e)}

    def _delete(self, endpoint: str) -> Tuple[int, Dict]:
        """DELETE-запрос"""
        try:
            resp = self.session.delete(
                f"{self.base_url}{endpoint}",
                headers=self._headers(),
                timeout=self.timeout
            )
            return resp.status_code, resp.json()
        except requests.ConnectionError:
            return 0, {"error": "Нет соединения с сервером"}
        except requests.Timeout:
            return 0, {"error": "Таймаут соединения"}
        except Exception as e:
            return 0, {"error": str(e)}

    # --------------------------------------------------------
    # Авторизация
    # --------------------------------------------------------

    def login(self, login: str, password: str) -> Tuple[bool, Dict]:
        """Вход в систему"""
        status, data = self._post("/api/auth/login", {
            "login": login,
            "password": password
        })
        if status == 200 and "token" in data:
            self.token = data["token"]
            self.current_user = data.get("user")
            return True, data
        return False, data

    def logout(self) -> Tuple[bool, Dict]:
        """Выход из системы"""
        status, data = self._post("/api/auth/logout")
        self.token = None
        self.current_user = None
        return status == 200, data

    def get_current_user(self) -> Tuple[bool, Dict]:
        """Получение информации о текущем пользователе"""
        status, data = self._get("/api/auth/me")
        if status == 200:
            self.current_user = data
        return status == 200, data

    def is_authenticated(self) -> bool:
        """Проверка авторизации"""
        return self.token is not None

    def is_admin(self) -> bool:
        """Проверка роли администратора"""
        if self.current_user:
            return self.current_user.get("role") == "admin"
        return False

    # --------------------------------------------------------
    # Администратор: управление пользователями
    # --------------------------------------------------------

    def create_user(self, login: str, password: str,
                    first_name: str, last_name: str,
                    role: str = "user") -> Tuple[bool, Dict]:
        """Создание нового пользователя"""
        status, data = self._post("/api/admin/users", {
            "login": login,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "role": role
        })
        return status == 201, data

    def get_users(self) -> Tuple[bool, Dict]:
        """Получение списка пользователей"""
        status, data = self._get("/api/admin/users")
        return status == 200, data

    def get_user(self, user_id: int) -> Tuple[bool, Dict]:
        """Получение информации о пользователе"""
        status, data = self._get(f"/api/admin/users/{user_id}")
        return status == 200, data

    def delete_user(self, user_id: int) -> Tuple[bool, Dict]:
        """Удаление пользователя"""
        status, data = self._delete(f"/api/admin/users/{user_id}")
        return status == 200, data

    def get_admin_stats(self) -> Tuple[bool, Dict]:
        """Статистика системы"""
        status, data = self._get("/api/admin/stats")
        return status == 200, data

    # --------------------------------------------------------
    # Пользователь: тестирование модели
    # --------------------------------------------------------

    def upload_test_data(self, file_path: str) -> Tuple[bool, Dict]:
        """Загрузка тестового набора данных"""
        status, data = self._post_file("/api/test/upload", file_path)
        return status == 200, data

    def get_test_results(self) -> Tuple[bool, Dict]:
        """Получение списка результатов тестирования"""
        status, data = self._get("/api/test/results")
        return status == 200, data

    def get_test_result_detail(self, result_id: int) -> Tuple[bool, Dict]:
        """Получение детального результата тестирования"""
        status, data = self._get(f"/api/test/results/{result_id}")
        return status == 200, data

    # --------------------------------------------------------
    # Аналитика
    # --------------------------------------------------------

    def get_accuracy_vs_epochs(self) -> Tuple[bool, Dict]:
        """График точности от эпох"""
        status, data = self._get("/api/analytics/accuracy-epochs")
        return status == 200, data

    def get_class_distribution(self) -> Tuple[bool, Dict]:
        """Распределение классов обучающего набора"""
        status, data = self._get("/api/analytics/class-distribution")
        return status == 200, data

    def get_test_per_sample(self, result_id: int) -> Tuple[bool, Dict]:
        """Точность каждой записи тестового набора"""
        status, data = self._get(f"/api/analytics/test-per-sample/{result_id}")
        return status == 200, data

    def get_top5_validation(self) -> Tuple[bool, Dict]:
        """Топ-5 классов валидационного набора"""
        status, data = self._get("/api/analytics/top5-validation")
        return status == 200, data

    def get_full_analytics(self, result_id: Optional[int] = None) -> Tuple[bool, Dict]:
        """Полная аналитика"""
        params = {}
        if result_id:
            params["result_id"] = result_id
        status, data = self._get("/api/analytics/full", params=params)
        return status == 200, data

    def get_test_summary(self, result_id: int) -> Tuple[bool, Dict]:
        """Сводка по тестированию"""
        status, data = self._get(f"/api/analytics/test-summary/{result_id}")
        return status == 200, data

    # --------------------------------------------------------
    # Модель и датасет
    # --------------------------------------------------------

    def get_model_info(self) -> Tuple[bool, Dict]:
        """Информация о модели"""
        status, data = self._get("/api/model/info")
        return status == 200, data

    def get_training_history(self) -> Tuple[bool, Dict]:
        """История обучения модели"""
        status, data = self._get("/api/model/training-history")
        return status == 200, data

    def get_dataset_info(self) -> Tuple[bool, Dict]:
        """Информация о датасете"""
        status, data = self._get("/api/dataset/info")
        return status == 200, data

    # --------------------------------------------------------
    # Здоровье сервера
    # --------------------------------------------------------

    def health_check(self) -> Tuple[bool, Dict]:
        """Проверка доступности сервера"""
        status, data = self._get("/api/health")
        return status == 200, data