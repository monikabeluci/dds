"""
Вспомогательные функции
"""

import asyncio
import random
from pathlib import Path
from typing import Optional


def read_lines_from_file(filepath: str | Path) -> list[str]:
    """Читать непустые строки из файла."""
    path = Path(filepath)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


async def random_delay(min_seconds: float = 2.0, max_seconds: float = 8.0):
    """Случайная задержка для имитации действий человека."""
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)


def truncate_string(text: str, max_length: int) -> str:
    """Обрезать строку до максимальной длины."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_phone(phone: str) -> str:
    """Нормализовать номер телефона."""
    phone = phone.strip().replace(" ", "").replace("-", "")
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone


def get_account_session_path(account_name: str) -> Path:
    """Получить путь к файлу сессии аккаунта."""
    from config import ACCOUNTS_DIR
    return ACCOUNTS_DIR / f"{account_name}.session"


def account_exists(account_name: str) -> bool:
    """Проверить существует ли аккаунт (файл сессии)."""
    return get_account_session_path(account_name).exists()


def list_accounts() -> list[str]:
    """Получить список всех сохранённых аккаунтов."""
    from config import ACCOUNTS_DIR
    return [p.stem for p in ACCOUNTS_DIR.glob("*.session")]


def format_timedelta(seconds: int) -> str:
    """Форматировать секунды в читаемый вид."""
    if seconds < 60:
        return f"{seconds}с"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}мин"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}ч {minutes}мин"


def parse_groups_file(filepath: Optional[str] = None) -> list[str]:
    """Прочитать список групп из файла."""
    from config import GROUPS_FILE
    path = Path(filepath) if filepath else GROUPS_FILE
    return read_lines_from_file(path)


def parse_messages_file(filepath: Optional[str] = None) -> list[str]:
    """Прочитать шаблоны сообщений из файла."""
    from config import MESSAGES_FILE
    path = Path(filepath) if filepath else MESSAGES_FILE
    lines = read_lines_from_file(path)
    # Разделитель сообщений - строка "---"
    messages = []
    current_message: list[str] = []
    for line in lines:
        if line == "---":
            if current_message:
                messages.append("\n".join(current_message))
                current_message = []
        else:
            current_message.append(line)
    if current_message:
        messages.append("\n".join(current_message))
    return messages if messages else lines
