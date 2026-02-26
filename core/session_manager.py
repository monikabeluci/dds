"""
Защита от запуска нескольких процессов на одном аккаунте.
Использует .lock файлы с PID процесса.
"""

import os
import sys
from pathlib import Path

from config import LOCKS_DIR
from utils.logger import logger


class SessionManager:
    """Защита от запуска нескольких процессов на одном аккаунте."""

    LOCK_DIR = LOCKS_DIR

    def _lock_file(self, account_name: str) -> Path:
        return self.LOCK_DIR / f"{account_name}.lock"

    def acquire_lock(self, account_name: str) -> bool:
        """
        Получить блокировку на аккаунт.
        Создаёт .lock файл с PID текущего процесса.
        Возвращает True при успехе, False если уже заблокирован.
        """
        lock_file = self._lock_file(account_name)

        # Проверяем, не заблокирован ли уже
        locked, pid = self.is_locked(account_name)
        if locked:
            logger.debug(f"Не удалось получить блокировку для {account_name}: занят PID={pid}")
            return False

        try:
            lock_file.parent.mkdir(parents=True, exist_ok=True)
            with open(lock_file, "w") as f:
                f.write(str(os.getpid()))
            logger.debug(f"Блокировка получена для {account_name} (PID={os.getpid()})")
            return True
        except OSError as e:
            logger.error(f"Ошибка при создании lock-файла для {account_name}: {e}")
            return False

    def release_lock(self, account_name: str):
        """Освободить блокировку."""
        lock_file = self._lock_file(account_name)
        if lock_file.exists():
            try:
                lock_file.unlink()
                logger.debug(f"Блокировка снята для {account_name}")
            except OSError as e:
                logger.warning(f"Не удалось удалить lock-файл {account_name}: {e}")

    def is_locked(self, account_name: str) -> tuple[bool, int]:
        """
        Проверить заблокирован ли аккаунт.
        Возвращает (True, PID) если заблокирован, (False, 0) если свободен.
        """
        lock_file = self._lock_file(account_name)
        if not lock_file.exists():
            return False, 0

        try:
            with open(lock_file, "r") as f:
                pid = int(f.read().strip())
        except (OSError, ValueError):
            return False, 0

        # Проверяем, жив ли процесс
        if _is_process_alive(pid):
            return True, pid

        # Процесс мёртв — устаревший lock файл
        logger.debug(f"Найден устаревший lock-файл для {account_name} (PID={pid}), удаляем")
        self.release_lock(account_name)
        return False, 0

    def cleanup_stale_locks(self):
        """Очистить устаревшие блокировки (мёртвые процессы)."""
        if not self.LOCK_DIR.exists():
            return
        cleaned = 0
        for lock_file in self.LOCK_DIR.glob("*.lock"):
            account_name = lock_file.stem
            locked, _ = self.is_locked(account_name)
            if not locked and lock_file.exists():
                # is_locked уже удалил устаревший файл, но на случай гонки:
                try:
                    lock_file.unlink(missing_ok=True)
                    cleaned += 1
                except OSError:
                    pass
        if cleaned:
            logger.debug(f"Очищено {cleaned} устаревших lock-файлов")

    def list_locked_accounts(self) -> list[dict]:
        """Получить список заблокированных аккаунтов."""
        result = []
        if not self.LOCK_DIR.exists():
            return result
        for lock_file in self.LOCK_DIR.glob("*.lock"):
            account_name = lock_file.stem
            locked, pid = self.is_locked(account_name)
            if locked:
                result.append({"account": account_name, "pid": pid})
        return result


def _is_process_alive(pid: int) -> bool:
    """Проверить, запущен ли процесс с данным PID."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False
