"""
Система валидации аккаунтов.
Детальная проверка каждого аккаунта перед рассылкой.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from config import (
    RATING_EXCELLENT,
    RATING_GOOD,
    RATING_WARNING,
    RATING_RESTRICTED,
    SPAMBOT_USERNAME,
    SPAMBOT_TIMEOUT,
)
from utils.logger import logger


class AccountStatus:
    """Статусы аккаунта."""

    EXCELLENT = "excellent"      # Отличный - готов к рассылке
    GOOD = "good"                # Хороший - можно использовать
    WARNING = "warning"          # Предупреждение - нужен прогрев
    RESTRICTED = "restricted"    # Ограничен - временный бан
    BANNED = "banned"            # Забанен
    INVALID = "invalid"          # Невалидный

    @classmethod
    def from_rating(cls, rating: int) -> str:
        if rating >= RATING_EXCELLENT:
            return cls.EXCELLENT
        elif rating >= RATING_GOOD:
            return cls.GOOD
        elif rating >= RATING_WARNING:
            return cls.WARNING
        elif rating >= RATING_RESTRICTED:
            return cls.RESTRICTED
        else:
            return cls.BANNED

    @classmethod
    def emoji(cls, status: str) -> str:
        return {
            cls.EXCELLENT: "✅",
            cls.GOOD: "🟢",
            cls.WARNING: "⚠️",
            cls.RESTRICTED: "🔴",
            cls.BANNED: "💀",
            cls.INVALID: "❌",
        }.get(status, "❓")


class AccountValidator:
    """Валидатор аккаунтов Telegram."""

    async def validate_account(self, client, account_name: str) -> dict:
        """
        Полная валидация аккаунта.

        Возвращает словарь с полной информацией о состоянии аккаунта.
        """
        result = {
            "status": AccountStatus.INVALID,
            "rating": 0,
            "suitable_for_sending": False,
            "reasons": [],
            "recommendations": [],
            "details": {
                "phone_verified": False,
                "has_username": False,
                "has_avatar": False,
                "has_bio": False,
                "has_2fa": False,
                "account_age_days": 0,
                "dialogs_count": 0,
                "contacts_count": 0,
                "restrictions": [],
                "spam_bot_status": "unknown",
                "validation_time": None,
            },
        }

        try:
            # 1. Базовая авторизация
            me = await client.get_me()
            if not me:
                result["reasons"].append("Аккаунт не авторизован")
                return result

            result["details"]["phone_verified"] = True
            rating = 30  # Базовый рейтинг за авторизацию

            # 2. Получаем полную информацию профиля
            from telethon.tl.functions.users import GetFullUserRequest
            from telethon.tl.functions.account import GetPasswordRequest

            try:
                full_user = await client(GetFullUserRequest(me))
                user_full = full_user.full_user

                # Проверка ограничений
                if me.restricted:
                    restrictions = me.restriction_reason or []
                    result["details"]["restrictions"] = [str(r) for r in restrictions]
                    result["reasons"].append(f"Аккаунт ограничен: {', '.join(result['details']['restrictions'])}")
                    rating -= 30
                else:
                    rating += 10

                # BIO
                bio = getattr(user_full, "about", None) or ""
                if bio:
                    result["details"]["has_bio"] = True
                    rating += 5
                else:
                    result["reasons"].append("Нет BIO (-5)")
                    result["recommendations"].append("Добавьте BIO")

            except Exception as e:
                logger.warning(f"Не удалось получить полную информацию профиля: {e}")

            # 3. Username
            if me.username:
                result["details"]["has_username"] = True
                rating += 5
            else:
                result["reasons"].append("Нет username (-5)")
                result["recommendations"].append("Установите username")

            # 4. Аватар
            if me.photo:
                result["details"]["has_avatar"] = True
                rating += 10
            else:
                result["reasons"].append("Нет аватара (-10)")
                result["recommendations"].append("Установите аватар")

            # 5. Возраст аккаунта (по ID пользователя)
            account_age_days = self._estimate_account_age(me.id)
            result["details"]["account_age_days"] = account_age_days

            if account_age_days < 7:
                result["reasons"].append(f"Аккаунт очень новый: {account_age_days} дней (-25)")
                rating -= 25
            elif account_age_days < 30:
                result["reasons"].append(f"Аккаунт новый: {account_age_days} дней (-20)")
                rating -= 20
            elif account_age_days < 90:
                result["reasons"].append(f"Аккаунт молодой: {account_age_days} дней (-10)")
                rating -= 10
            elif account_age_days >= 365:
                rating += 15
            else:
                rating += 5

            # 6. Диалоги
            try:
                dialogs = await client.get_dialogs(limit=50)
                dialogs_count = len(dialogs)
                result["details"]["dialogs_count"] = dialogs_count

                if dialogs_count < 5:
                    result["reasons"].append(f"Мало диалогов: {dialogs_count} (-15)")
                    rating -= 15
                    result["recommendations"].append("Запустите прогрев для увеличения активности")
                elif dialogs_count < 20:
                    result["reasons"].append(f"Немного диалогов: {dialogs_count} (-5)")
                    rating -= 5
                else:
                    rating += 10

            except Exception as e:
                logger.warning(f"Не удалось получить диалоги: {e}")

            # 7. Контакты
            try:
                from telethon.tl.functions.contacts import GetContactsRequest
                contacts_result = await client(GetContactsRequest(hash=0))
                contacts_count = len(getattr(contacts_result, "contacts", []))
                result["details"]["contacts_count"] = contacts_count

                if contacts_count > 5:
                    rating += 5
            except Exception as e:
                logger.warning(f"Не удалось получить контакты: {e}")

            # 8. 2FA
            try:
                password_info = await client(GetPasswordRequest())
                if password_info.has_password:
                    result["details"]["has_2fa"] = True
                    rating += 5
                else:
                    result["recommendations"].append("Установите двухфакторную аутентификацию (2FA)")
            except Exception as e:
                logger.warning(f"Не удалось проверить 2FA: {e}")

            # 9. SpamBot проверка
            try:
                spam_status = await self._check_spambot(client)
                result["details"]["spam_bot_status"] = spam_status

                if "free" in spam_status.lower() or "не ограничен" in spam_status.lower():
                    rating += 10
                elif "limited" in spam_status.lower() or "ограничен" in spam_status.lower():
                    result["reasons"].append(f"SpamBot: {spam_status} (-5)")
                    rating -= 5
                elif "banned" in spam_status.lower() or "забанен" in spam_status.lower():
                    result["reasons"].append(f"SpamBot: {spam_status} (-30)")
                    rating -= 30
                    result["status"] = AccountStatus.BANNED
                    result["rating"] = max(0, rating)
                    result["suitable_for_sending"] = False
                    return result
            except Exception as e:
                logger.warning(f"Не удалось проверить SpamBot: {e}")
                result["details"]["spam_bot_status"] = "check failed"

            # 10. Время валидации
            result["details"]["validation_time"] = datetime.now(timezone.utc)

            # Итоговый рейтинг
            rating = max(0, min(100, rating))
            result["rating"] = rating
            result["status"] = AccountStatus.from_rating(rating)
            result["suitable_for_sending"] = rating >= RATING_GOOD

            if not result["suitable_for_sending"] and not result["recommendations"]:
                result["recommendations"].append("Запустите прогрев на 7 дней")

        except Exception as e:
            logger.error(f"Ошибка при валидации аккаунта {account_name}: {e}")
            result["reasons"].append(f"Ошибка: {str(e)}")
            result["status"] = AccountStatus.INVALID

        return result

    async def _check_spambot(self, client) -> str:
        """Проверить статус аккаунта через @SpamBot."""
        try:
            async with client.conversation(SPAMBOT_USERNAME, timeout=SPAMBOT_TIMEOUT) as conv:
                await conv.send_message("/start")
                response = await conv.get_response()
                text = response.text or ""
                return text[:200]  # Первые 200 символов ответа
        except Exception as e:
            logger.debug(f"SpamBot check failed: {e}")
            return "unavailable"

    def _estimate_account_age(self, user_id: int) -> int:
        """
        Оценить возраст аккаунта в днях по ID пользователя.
        Telegram ID примерно коррелирует с временем регистрации.
        """
        # Примерные точки отсчёта (ID → дата)
        # Это приближённая оценка
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        # Приближённая таблица соответствия ID и дат
        id_dates = [
            (100000000, datetime(2013, 8, 1, tzinfo=timezone.utc)),
            (200000000, datetime(2014, 1, 1, tzinfo=timezone.utc)),
            (500000000, datetime(2015, 6, 1, tzinfo=timezone.utc)),
            (1000000000, datetime(2017, 1, 1, tzinfo=timezone.utc)),
            (2000000000, datetime(2019, 1, 1, tzinfo=timezone.utc)),
            (4000000000, datetime(2021, 1, 1, tzinfo=timezone.utc)),
            (5000000000, datetime(2022, 1, 1, tzinfo=timezone.utc)),
            (6000000000, datetime(2022, 12, 1, tzinfo=timezone.utc)),
            (7000000000, datetime(2023, 6, 1, tzinfo=timezone.utc)),
            (8000000000, datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ]

        reg_date = datetime(2013, 8, 1, tzinfo=timezone.utc)
        for threshold_id, threshold_date in id_dates:
            if user_id < threshold_id:
                reg_date = threshold_date
                break
        else:
            reg_date = datetime(2024, 6, 1, tzinfo=timezone.utc)

        age = (now - reg_date).days
        return max(0, age)
