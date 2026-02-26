"""
Управление безопасностью аккаунта:
- Двухфакторная аутентификация (2FA / облачный пароль)
- Управление активными сессиями
"""

from typing import Optional

from utils.logger import logger


class SecurityManager:
    """Управление безопасностью Telegram аккаунта."""

    async def setup_2fa(
        self, client, password: str, hint: str = "", email: str = ""
    ) -> bool:
        """Установить двухфакторную аутентификацию."""
        from telethon.tl.functions.account import (
            GetPasswordRequest,
            UpdatePasswordSettingsRequest,
        )
        from telethon.tl.types import account as account_types

        try:
            password_info = await client(GetPasswordRequest())

            if password_info.has_password:
                logger.warning("2FA уже установлена. Используйте change_2fa_password для смены.")
                return False

            # Вычисляем new_settings используя Telethon helper
            from telethon.utils import get_password_hash
            import os

            new_salt1 = os.urandom(32)
            new_password_hash = get_password_hash(password, new_salt1)

            await client(UpdatePasswordSettingsRequest(
                password=account_types.PasswordInputSettings(
                    new_algo=None,
                    new_password_hash=new_password_hash,
                    hint=hint,
                    email=email or None,
                    new_secure_settings=None,
                ),
                current_password_hash=b"",
            ))
            logger.info("2FA успешно установлена")
            return True
        except Exception as e:
            logger.error(f"Ошибка при установке 2FA: {e}")
            return False

    async def remove_2fa(self, client, current_password: str) -> bool:
        """Удалить 2FA."""
        from telethon.tl.functions.account import (
            GetPasswordRequest,
            UpdatePasswordSettingsRequest,
        )

        try:
            password_info = await client(GetPasswordRequest())

            if not password_info.has_password:
                logger.info("2FA не установлена")
                return True

            from telethon.utils import compute_check
            current_hash = compute_check(password_info, current_password)

            from telethon.tl.types import account as account_types
            await client(UpdatePasswordSettingsRequest(
                password=account_types.PasswordInputSettings(
                    new_algo=None,
                    new_password_hash=b"",
                    hint="",
                    email=None,
                    new_secure_settings=None,
                ),
                current_password_hash=current_hash,
            ))
            logger.info("2FA успешно удалена")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении 2FA: {e}")
            return False

    async def change_2fa_password(
        self, client, old_password: str, new_password: str, hint: str = ""
    ) -> bool:
        """Изменить пароль 2FA."""
        from telethon.tl.functions.account import (
            GetPasswordRequest,
            UpdatePasswordSettingsRequest,
        )

        try:
            password_info = await client(GetPasswordRequest())

            if not password_info.has_password:
                logger.warning("2FA не установлена")
                return False

            from telethon.utils import compute_check
            current_hash = compute_check(password_info, old_password)

            import os
            new_salt = os.urandom(32)
            from telethon.utils import get_password_hash
            new_hash = get_password_hash(new_password, new_salt)

            from telethon.tl.types import account as account_types
            await client(UpdatePasswordSettingsRequest(
                password=account_types.PasswordInputSettings(
                    new_algo=None,
                    new_password_hash=new_hash,
                    hint=hint,
                    email=None,
                    new_secure_settings=None,
                ),
                current_password_hash=current_hash,
            ))
            logger.info("Пароль 2FA успешно изменён")
            return True
        except Exception as e:
            logger.error(f"Ошибка при смене пароля 2FA: {e}")
            return False

    async def terminate_all_sessions(
        self, client, except_current: bool = True
    ) -> bool:
        """Закрыть все другие активные сессии."""
        from telethon.tl.functions.auth import ResetAuthorizationsRequest

        try:
            await client(ResetAuthorizationsRequest())
            logger.info("Все другие сессии завершены")
            return True
        except Exception as e:
            logger.error(f"Ошибка при завершении сессий: {e}")
            return False

    async def get_active_sessions(self, client) -> list[dict]:
        """Получить список активных сессий."""
        from telethon.tl.functions.account import GetAuthorizationsRequest

        sessions = []
        try:
            result = await client(GetAuthorizationsRequest())
            for auth in result.authorizations:
                sessions.append({
                    "hash": auth.hash,
                    "device_model": getattr(auth, "device_model", ""),
                    "platform": getattr(auth, "platform", ""),
                    "system_version": getattr(auth, "system_version", ""),
                    "app_name": getattr(auth, "app_name", ""),
                    "app_version": getattr(auth, "app_version", ""),
                    "date_created": getattr(auth, "date_created", None),
                    "date_active": getattr(auth, "date_active", None),
                    "ip": getattr(auth, "ip", ""),
                    "country": getattr(auth, "country", ""),
                    "region": getattr(auth, "region", ""),
                    "current": getattr(auth, "current", False),
                })
        except Exception as e:
            logger.error(f"Ошибка при получении сессий: {e}")

        return sessions
