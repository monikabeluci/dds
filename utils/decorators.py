"""
Декораторы для защиты от дублей процессов и другие утилиты
"""

import asyncio
import functools
from typing import Callable

from utils.logger import logger


def single_account_process(func: Callable) -> Callable:
    """
    Декоратор: защита от запуска нескольких операций на одном аккаунте.
    Ожидает, что первый аргумент функции — имя аккаунта (account_name).
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        from core.session_manager import SessionManager

        # Определяем имя аккаунта
        account_name = kwargs.get("account_name") or (args[1] if len(args) > 1 else None)
        if not account_name:
            return await func(*args, **kwargs)

        session_manager = SessionManager()
        session_manager.cleanup_stale_locks()

        locked, pid = session_manager.is_locked(account_name)
        if locked:
            logger.warning(f"Аккаунт {account_name} уже используется процессом PID={pid}")
            from rich.console import Console
            Console().print(
                f"[yellow]⚠ Аккаунт [bold]{account_name}[/bold] уже используется "
                f"(PID: {pid}). Дождитесь завершения.[/yellow]"
            )
            return None

        if not session_manager.acquire_lock(account_name):
            return None

        try:
            return await func(*args, **kwargs)
        finally:
            session_manager.release_lock(account_name)

    return wrapper


def retry_on_flood(max_retries: int = 3, base_delay: float = 5.0):
    """
    Декоратор: повтор при FloodWait ошибке Telethon.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import telethon.errors as errors

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except errors.FloodWaitError as e:
                    wait_time = e.seconds + 5
                    logger.warning(
                        f"FloodWait: ожидание {wait_time}с (попытка {attempt + 1}/{max_retries})"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(wait_time)
                    else:
                        raise
                except errors.UserDeactivatedBanError:
                    logger.error("Аккаунт заблокирован Telegram")
                    raise
            return None

        return wrapper
    return decorator
