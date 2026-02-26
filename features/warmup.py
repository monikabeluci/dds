"""
Прогрев аккаунтов для повышения рейтинга и снижения риска блокировки.
"""

import asyncio
import random
from datetime import datetime

from utils.logger import logger
from utils.helpers import random_delay
from config import load_config


class AccountWarmer:
    """Прогрев аккаунтов."""

    INTENSITY_SETTINGS = {
        "light": {"actions_per_session": 5, "delay_min": 30, "delay_max": 90},
        "normal": {"actions_per_session": 15, "delay_min": 10, "delay_max": 40},
        "intensive": {"actions_per_session": 30, "delay_min": 5, "delay_max": 20},
    }

    async def warmup_account(
        self,
        client,
        account_name: str,
        intensity: str = "normal",
        duration_minutes: int = 30,
    ) -> dict:
        """
        Прогрев аккаунта.

        intensity: "light", "normal", "intensive"
        duration_minutes: продолжительность сессии прогрева
        """
        settings = self.INTENSITY_SETTINGS.get(intensity, self.INTENSITY_SETTINGS["normal"])
        stats = {
            "account": account_name,
            "intensity": intensity,
            "actions_performed": 0,
            "started_at": datetime.now().isoformat(),
            "ended_at": None,
        }

        logger.info(f"Начало прогрева {account_name} (интенсивность: {intensity})")

        try:
            await self.run_warmup_session(
                client,
                duration_minutes=duration_minutes,
                actions_count=settings["actions_per_session"],
                delay_min=settings["delay_min"],
                delay_max=settings["delay_max"],
            )
            stats["actions_performed"] = settings["actions_per_session"]
        except Exception as e:
            logger.error(f"Ошибка при прогреве {account_name}: {e}")
        finally:
            stats["ended_at"] = datetime.now().isoformat()

        return stats

    async def run_warmup_session(
        self,
        client,
        duration_minutes: int = 30,
        actions_count: int = 15,
        delay_min: float = 10.0,
        delay_max: float = 40.0,
    ):
        """
        Сессия прогрева аккаунта.

        Выполняет действия, имитирующие живого пользователя:
        - Чтение сообщений
        - Отправка сообщения в "Избранное"
        - Просмотр диалогов
        """
        actions_done = 0
        session_start = asyncio.get_event_loop().time()
        max_seconds = duration_minutes * 60

        warmup_messages = [
            "Тест",
            "Привет",
            "Проверка",
            "👍",
            "Заметка",
            "Напоминание",
            "Идея",
        ]

        while actions_done < actions_count:
            # Проверяем время сессии
            elapsed = asyncio.get_event_loop().time() - session_start
            if elapsed >= max_seconds:
                logger.debug(f"Прогрев завершён по времени ({duration_minutes} мин)")
                break

            action = random.choice(["read_dialogs", "send_to_saved", "read_history"])

            try:
                if action == "read_dialogs":
                    await self._action_read_dialogs(client)
                elif action == "send_to_saved":
                    msg = random.choice(warmup_messages)
                    await self._action_send_to_saved(client, msg)
                elif action == "read_history":
                    await self._action_read_history(client)

                actions_done += 1
                logger.debug(f"Прогрев: действие '{action}' выполнено ({actions_done}/{actions_count})")

            except Exception as e:
                logger.warning(f"Ошибка при действии прогрева '{action}': {e}")

            # Пауза между действиями
            await random_delay(delay_min, delay_max)

    async def _action_read_dialogs(self, client, limit: int = 10):
        """Просмотр диалогов."""
        dialogs = await client.get_dialogs(limit=limit)
        logger.debug(f"Прочитано {len(dialogs)} диалогов")

    async def _action_send_to_saved(self, client, message: str):
        """Отправить сообщение в 'Избранное' (Saved Messages)."""
        me = await client.get_me()
        await client.send_message(me, message)
        logger.debug(f"Отправлено в Избранное: '{message}'")

    async def _action_read_history(self, client):
        """Прочитать историю случайного диалога."""
        dialogs = await client.get_dialogs(limit=20)
        if not dialogs:
            return
        dialog = random.choice(dialogs)
        await client.get_messages(dialog, limit=5)
        logger.debug(f"Прочитана история: {dialog.title}")

    async def schedule_warmup(
        self,
        accounts: list,
        client_factory,
        days: int = 7,
        intensity: str = "normal",
        sessions_per_day: int = 2,
    ):
        """
        Запланировать прогрев на несколько дней.

        accounts: список имён аккаунтов
        client_factory: функция(account_name) → TelegramClient
        days: количество дней
        sessions_per_day: количество сессий в день
        """
        from rich.console import Console
        console = Console()

        console.print(f"[bold]Запуск прогрева на {days} дней[/bold]")
        console.print(f"Аккаунтов: {len(accounts)}, интенсивность: {intensity}")

        total_sessions = days * sessions_per_day * len(accounts)  # noqa: F841
        session_interval = 24 * 3600 / sessions_per_day

        for day in range(days):
            console.print(f"\n[cyan]День {day + 1}/{days}[/cyan]")
            for session_num in range(sessions_per_day):
                for account_name in accounts:
                    console.print(f"  Прогрев: {account_name} (сессия {session_num + 1})")
                    try:
                        client = client_factory(account_name)
                        async with client:
                            await self.warmup_account(client, account_name, intensity)
                    except Exception as e:
                        console.print(f"  [red]Ошибка: {e}[/red]")

                if session_num < sessions_per_day - 1:
                    await asyncio.sleep(session_interval)

            if day < days - 1:
                # Ждём до следующего дня (24 часа)
                await asyncio.sleep(24 * 3600)

        console.print("[green]✓ Прогрев завершён[/green]")
