"""
Конфигурация и константы для Telegram Multi-Account Manager
"""

import json
import os
from pathlib import Path

# Корневая директория проекта
BASE_DIR = Path(__file__).parent

# Директории
ACCOUNTS_DIR = BASE_DIR / "accounts"
AVATARS_DIR = BASE_DIR / "avatars"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
LOCKS_DIR = BASE_DIR / "locks"

# Файлы данных
GROUPS_FILE = DATA_DIR / "groups.txt"
MESSAGES_FILE = DATA_DIR / "messages.txt"
CONFIG_FILE = BASE_DIR / "config.json"

# Создаём директории при первом запуске
for _dir in [ACCOUNTS_DIR, AVATARS_DIR, LOGS_DIR, DATA_DIR, LOCKS_DIR]:
    _dir.mkdir(exist_ok=True)

# Значения по умолчанию
DEFAULT_CONFIG = {
    "api_id": None,
    "api_hash": None,
    "send_delay_min": 30,
    "send_delay_max": 60,
    "warmup_delay_min": 5,
    "warmup_delay_max": 15,
    "max_messages_per_day": 20,
    "language": "ru",
}

# Пороги рейтинга аккаунтов
RATING_EXCELLENT = 80
RATING_GOOD = 60
RATING_WARNING = 40
RATING_RESTRICTED = 20

# Параметры SpamBot
SPAMBOT_USERNAME = "SpamBot"
SPAMBOT_TIMEOUT = 15

# Максимальная длина BIO
BIO_MAX_LENGTH = 70


def load_config() -> dict:
    """Загрузить конфигурацию из файла."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        config = DEFAULT_CONFIG.copy()
        config.update(data)
        return config
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Сохранить конфигурацию в файл."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_api_credentials() -> tuple[int | None, str | None]:
    """Получить API ID и API Hash из конфига."""
    config = load_config()
    return config.get("api_id"), config.get("api_hash")


def setup_first_run() -> tuple[int, str]:
    """Настройка при первом запуске - запрос API credentials."""
    from rich.console import Console
    from rich.prompt import Prompt

    console = Console()
    console.print("\n[bold yellow]Первый запуск Telegram Manager[/bold yellow]")
    console.print("Получите API ID и API Hash на [link]https://my.telegram.org[/link]\n")

    api_id_str = Prompt.ask("[bold]API ID[/bold]")
    api_hash = Prompt.ask("[bold]API Hash[/bold]")

    try:
        api_id = int(api_id_str.strip())
    except ValueError:
        console.print("[red]Ошибка: API ID должен быть числом[/red]")
        raise ValueError("Неверный формат API ID")

    api_hash = api_hash.strip()

    config = load_config()
    config["api_id"] = api_id
    config["api_hash"] = api_hash
    save_config(config)

    console.print("[green]✓ Конфигурация сохранена[/green]\n")
    return api_id, api_hash
