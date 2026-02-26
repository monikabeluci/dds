"""
Автоматическое получение кода входа из Telegram.
"""

import asyncio
from typing import Optional

from utils.logger import logger


class AutoAuth:
    """Автоматическое получение кода входа."""

    TELEGRAM_SERVICE_NUMBER = 777000

    async def authorize_with_auto_code(
        self,
        client,
        phone: str,
        code_source: str = "telegram",
        password: Optional[str] = None,
    ) -> bool:
        """
        Авторизация с автоматическим получением кода.

        code_source:
        - "telegram" - код из сообщения Telegram (если есть авторизованная сессия)
        - "sms"      - ручной ввод SMS
        - "call"     - ручной ввод из звонка
        """
        from telethon.errors import SessionPasswordNeededError
        from rich.prompt import Prompt

        try:
            await client.send_code_request(phone)

            if code_source == "telegram":
                code = await self.get_code_from_telegram(client, phone)
                if not code:
                    logger.warning("Не удалось получить код автоматически, переключаемся на ручной ввод")
                    code = Prompt.ask("Введите код вручную")
            else:
                source_label = "SMS" if code_source == "sms" else "звонка"
                code = Prompt.ask(f"Введите код из {source_label}")

            try:
                await client.sign_in(phone, code)
                logger.info(f"Успешная авторизация для {phone}")
                return True
            except SessionPasswordNeededError:
                if password:
                    await client.sign_in(password=password)
                    return True
                else:
                    pwd = Prompt.ask("Введите пароль 2FA", password=True)
                    await client.sign_in(password=pwd)
                    return True

        except Exception as e:
            logger.error(f"Ошибка авторизации для {phone}: {e}")
            return False

    async def get_code_from_telegram(
        self,
        client,
        phone: str,
        timeout: int = 60,
    ) -> Optional[str]:
        """
        Получить код авторизации из сообщений Telegram (от 777000).

        Используется, когда есть другая авторизованная сессия Telethon,
        из которой можно прочитать входящее сообщение от сервиса Telegram.
        """
        import re

        logger.info(f"Ожидание кода от Telegram для {phone} (таймаут: {timeout}с)")

        try:
            # Ожидаем новое сообщение от сервисного номера 777000
            async with client.conversation(
                self.TELEGRAM_SERVICE_NUMBER, timeout=timeout
            ) as conv:
                response = await conv.get_response()
                text = response.text or ""
                logger.debug(f"Сообщение от Telegram: {text[:100]}")

                # Извлекаем код (обычно 5 цифр)
                match = re.search(r"\b(\d{5,6})\b", text)
                if match:
                    code = match.group(1)
                    logger.info(f"Код получен автоматически: {code}")
                    return code

        except asyncio.TimeoutError:
            logger.warning(f"Таймаут при ожидании кода для {phone}")
        except Exception as e:
            logger.debug(f"Не удалось получить код автоматически: {e}")

        return None
