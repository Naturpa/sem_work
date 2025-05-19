import os
from datetime import datetime
from config import LOGS_DIR


class DialogLogger:
    """Класс для логирования диалогов с пользователями"""

    def __init__(self):
        self._ensure_logs_dir_exists()

    def _ensure_logs_dir_exists(self):
        """Создает директорию для логов, если она не существует"""
        try:
            if not os.path.exists(LOGS_DIR):
                os.makedirs(LOGS_DIR)
                print(f"Создана директория для логов: {LOGS_DIR}")
        except Exception as e:
            print(f"Ошибка при создании директории логов: {e}")

    def log_message(self, user_id: int, username: str, message: str, is_bot: bool = False):
        """
        Логирует сообщение в файл пользователя

        :param user_id: ID пользователя в Telegram
        :param username: имя пользователя
        :param message: текст сообщения
        :param is_bot: True, если сообщение от бота, False - от пользователя
        """
        try:
            # Создаем имя файла лога
            log_file = os.path.join(LOGS_DIR, f"{user_id}.log")

            # Определяем отправителя
            sender = "BOT" if is_bot else f"USER {username}"

            # Форматируем строку для записи
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {sender}: {message}\n"

            # Записываем в файл
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)

            print(f"Сообщение записано в лог: {log_file}")  # Для отладки
        except Exception as e:
            print(f"Ошибка при записи в лог: {e}")