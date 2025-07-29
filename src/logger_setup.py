# logger_setup.py

import logging
import os
import atexit
from pathlib import Path

# Путь к файлу логов во временной директории (в корне проекта или в temp)
LOG_FILE_PATH = Path("app_errors.log")

# Формат логов
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Создаём логгер
logger = logging.getLogger("AppLogger")
logger.setLevel(logging.ERROR)  # Логируем только ошибки и критические события

# Предотвращаем дублирование логов, если обработчики уже есть
if not logger.handlers:
    # Обработчик записи в файл
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setLevel(logging.ERROR)

    # Форматтер
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(formatter)

    # Добавляем обработчик к логгеру
    logger.addHandler(file_handler)

# Функция для копирования лога на рабочий стол при завершении программы
def _save_log_to_desktop():
    try:
        # Определяем путь к рабочему столу
        desktop_path = Path.home() / "Desktop"
        if os.name == "nt":  # Windows
            desktop_path = Path(os.path.expandvars("%USERPROFILE%")) / "Desktop"

        # Целевой файл на рабочем столе
        dest_file = desktop_path / "error_report.txt"

        # Копируем содержимое лога
        if LOG_FILE_PATH.exists():
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as src:
                content = src.read()
            with open(dest_file, "w", encoding="utf-8") as dst:
                dst.write("=== ОТЧЁТ ОБ ОШИБКАХ ПРИЛОЖЕНИЯ ===\n")
                dst.write(f"Дата: {logging.Formatter().formatTime(logging.LogRecord('', '', '', '', '', '', ''))}\n")
                dst.write("=" * 50 + "\n\n")
                dst.write(content)
            print(f"Лог ошибок сохранён на рабочем столе: {dest_file}")
        else:
            print("Файл лога не найден.")
    except Exception as e:
        print(f"Не удалось сохранить лог на рабочем столе: {e}")

# Регистрируем функцию — она вызовется при выходе из программы
atexit.register(_save_log_to_desktop)

# Экспортируем логгер
__all__ = ["logger"]