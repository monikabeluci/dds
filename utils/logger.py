"""
Система логирования
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from config import LOGS_DIR


def get_logger(name: str = "telegram_manager") -> logging.Logger:
    """Получить настроенный логгер."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Форматтер
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Файловый обработчик (ротация по дням)
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Консольный обработчик (только WARNING и выше)
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


# Глобальный логгер
logger = get_logger()
