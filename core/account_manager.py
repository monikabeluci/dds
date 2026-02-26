"""
Управление аккаунтами Telegram.
Добавление, удаление, просмотр аккаунтов.
"""

import json
import os
from pathlib import Path
from typing import Optional

from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    FloodWaitError,
)

from config import ACCOUNTS_DIR, get_api_credentials, setup_first_run
from utils.logger import logger
from utils.helpers import list_accounts, get_account_session_path, format_phone


# Файл метаданных аккаунтов
ACCOUNTS_META_FILE = ACCOUNTS_DIR / "accounts_meta.json"


def load_accounts_meta() -> dict:
    """Загрузить метаданные аккаунтов."""
    if ACCOUNTS_META_FILE.exists():
        with open(ACCOUNTS_META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_accounts_meta(meta: dict):
    """Сохранить метаданные аккаунтов."""
    with open(ACCOUNTS_META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


class AccountManager:
    """Управление аккаунтами Telegram."""

    def __init__(self):
        self.api_id, self.api_hash = get_api_credentials()

    def _ensure_credentials(self):
        """Убедиться, что API credentials настроены."""
        if not self.api_id or not self.api_hash:
            self.api_id, self.api_hash = setup_first_run()

    def create_client(self, account_name: str) -> TelegramClient:
        """Создать клиент Telethon для аккаунта."""
        self._ensure_credentials()
        session_path = str(get_account_session_path(account_name))
        return TelegramClient(session_path, self.api_id, self.api_hash)

    async def add_account(
        self,
        phone: str,
        account_name: str,
        password: Optional[str] = None,
        auto_code: bool = False,
    ) -> bool:
        """
        Добавить новый аккаунт.
        Выполняет авторизацию и сохраняет сессию.
        """
        from rich.console import Console
        from rich.prompt import Prompt

        console = Console()
        self._ensure_credentials()

        phone = format_phone(phone)

        if not account_name:
            account_name = phone.replace("+", "").replace(" ", "")

        # Проверяем, не существует ли уже
        if get_account_session_path(account_name).exists():
            console.print(f"[yellow]Аккаунт '{account_name}' уже существует[/yellow]")
            return False

        session_path = str(get_account_session_path(account_name))
        client = TelegramClient(session_path, self.api_id, self.api_hash)

        try:
            await client.connect()

            if await client.is_user_authorized():
                console.print(f"[green]✓ Аккаунт {account_name} уже авторизован[/green]")
                await self._save_account_meta(client, account_name, phone)
                return True

            # Отправляем код
            console.print(f"[bold]Отправка кода на {phone}...[/bold]")
            await client.send_code_request(phone)

            # Получаем код
            if auto_code:
                from features.auto_auth import AutoAuth
                auto_auth = AutoAuth()
                code = await auto_auth.get_code_from_telegram(client, phone)
                if not code:
                    console.print("[red]Не удалось автоматически получить код[/red]")
                    code = Prompt.ask("Введите код вручную")
            else:
                code = Prompt.ask(f"Введите код из Telegram/SMS для {phone}")

            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                # 2FA требуется
                if password:
                    await client.sign_in(password=password)
                else:
                    pwd = Prompt.ask("Введите пароль 2FA", password=True)
                    await client.sign_in(password=pwd)

            me = await client.get_me()
            console.print(f"[green]✓ Аккаунт добавлен: {me.first_name} ({phone})[/green]")
            logger.info(f"Аккаунт {account_name} ({phone}) успешно добавлен")

            await self._save_account_meta(client, account_name, phone)
            return True

        except PhoneCodeInvalidError:
            console.print("[red]Ошибка: неверный код[/red]")
            logger.error(f"Неверный код для {phone}")
            self._cleanup_session(account_name)
            return False
        except PhoneCodeExpiredError:
            console.print("[red]Ошибка: код истёк[/red]")
            logger.error(f"Код истёк для {phone}")
            self._cleanup_session(account_name)
            return False
        except FloodWaitError as e:
            console.print(f"[red]FloodWait: ожидайте {e.seconds} секунд[/red]")
            logger.error(f"FloodWait для {phone}: {e.seconds}с")
            self._cleanup_session(account_name)
            return False
        except Exception as e:
            console.print(f"[red]Ошибка при добавлении аккаунта: {e}[/red]")
            logger.error(f"Ошибка добавления аккаунта {account_name}: {e}")
            self._cleanup_session(account_name)
            return False
        finally:
            await client.disconnect()

    async def remove_account(self, account_name: str) -> bool:
        """Удалить аккаунт (файл сессии и метаданные)."""
        from rich.console import Console
        console = Console()

        session_file = get_account_session_path(account_name)
        if not session_file.exists():
            console.print(f"[red]Аккаунт '{account_name}' не найден[/red]")
            return False

        # Удаляем файл сессии
        try:
            session_file.unlink()
            # Telethon создаёт также .session-journal
            journal = session_file.with_suffix(".session-journal")
            if journal.exists():
                journal.unlink()
        except OSError as e:
            logger.error(f"Ошибка при удалении сессии {account_name}: {e}")

        # Удаляем метаданные
        meta = load_accounts_meta()
        meta.pop(account_name, None)
        save_accounts_meta(meta)

        console.print(f"[green]✓ Аккаунт '{account_name}' удалён[/green]")
        logger.info(f"Аккаунт {account_name} удалён")
        return True

    def list_accounts_info(self) -> list[dict]:
        """Получить список аккаунтов с метаданными."""
        accounts = list_accounts()
        meta = load_accounts_meta()
        result = []
        for name in accounts:
            info = {"name": name}
            info.update(meta.get(name, {}))
            result.append(info)
        return result

    async def _save_account_meta(self, client, account_name: str, phone: str):
        """Сохранить метаданные аккаунта."""
        try:
            me = await client.get_me()
            meta = load_accounts_meta()
            meta[account_name] = {
                "phone": phone,
                "user_id": me.id,
                "first_name": me.first_name or "",
                "last_name": me.last_name or "",
                "username": me.username or "",
            }
            save_accounts_meta(meta)
        except Exception as e:
            logger.warning(f"Не удалось сохранить метаданные для {account_name}: {e}")

    def _cleanup_session(self, account_name: str):
        """Удалить файл сессии при ошибке."""
        session_file = get_account_session_path(account_name)
        if session_file.exists():
            try:
                session_file.unlink()
            except OSError:
                pass
