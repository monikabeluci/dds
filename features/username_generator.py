"""
Генератор свободных username для Telegram аккаунтов.
"""

import random
import string
from typing import Optional

from utils.logger import logger


class UsernameGenerator:
    """Генерация и проверка доступных username."""

    # Суффиксы для вариаций
    NUMBER_SUFFIXES = [str(i) for i in range(1, 100)]
    COMMON_WORDS = ["pro", "real", "the", "official", "me", "online", "life", "world"]
    SEPARATORS = ["", "_", "."]

    async def generate_available_username(
        self,
        client,
        base_name: Optional[str] = None,
        count: int = 10,
    ) -> list[str]:
        """
        Генерирует список свободных username.
        Проверяет доступность через API.
        """
        if not base_name:
            base_name = self._random_base()

        available = []
        variations = self.generate_variations(base_name)

        for username in variations:
            if len(available) >= count:
                break
            if await self.check_username_available(client, username):
                available.append(username)

        return available

    async def check_username_available(self, client, username: str) -> bool:
        """Проверить доступность username через Telegram API."""
        from telethon.tl.functions.account import CheckUsernameRequest
        from telethon.errors import UsernameInvalidError

        username = username.lstrip("@").strip()

        # Базовая валидация: 5-32 символа, только латиница и цифры
        if not self._is_valid_username_format(username):
            return False

        try:
            result = await client(CheckUsernameRequest(username=username))
            return bool(result)
        except UsernameInvalidError:
            return False
        except Exception as e:
            logger.debug(f"Ошибка проверки username @{username}: {e}")
            return False

    def generate_variations(self, base: str) -> list[str]:
        """
        Генерация вариаций username.
        Форматы: base123, base_xyz, baseName и т.д.
        """
        base = base.lower().strip()
        variations = set()

        # С числовыми суффиксами
        for n in random.sample(self.NUMBER_SUFFIXES, min(20, len(self.NUMBER_SUFFIXES))):
            for sep in self.SEPARATORS:
                candidate = f"{base}{sep}{n}"
                if self._is_valid_username_format(candidate):
                    variations.add(candidate)

        # С общими словами
        for word in self.COMMON_WORDS:
            for sep in self.SEPARATORS:
                candidate = f"{base}{sep}{word}"
                if self._is_valid_username_format(candidate):
                    variations.add(candidate)
                candidate2 = f"{word}{sep}{base}"
                if self._is_valid_username_format(candidate2):
                    variations.add(candidate2)

        # С случайными буквами
        for _ in range(20):
            suffix = "".join(random.choices(string.ascii_lowercase, k=3))
            for sep in self.SEPARATORS:
                candidate = f"{base}{sep}{suffix}"
                if self._is_valid_username_format(candidate):
                    variations.add(candidate)

        result = list(variations)
        random.shuffle(result)
        return result

    def _is_valid_username_format(self, username: str) -> bool:
        """Проверить формат username (5-32 символа, латиница/цифры/подчёркивание)."""
        if not (5 <= len(username) <= 32):
            return False
        allowed = set(string.ascii_letters + string.digits + "_")
        if not all(c in allowed for c in username):
            return False
        if username.startswith("_") or username.endswith("_"):
            return False
        return True

    def _random_base(self) -> str:
        """Сгенерировать случайное базовое имя."""
        length = random.randint(4, 8)
        return "".join(random.choices(string.ascii_lowercase, k=length))
