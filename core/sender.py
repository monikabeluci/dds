"""
Логика рассылки сообщений в группы.
"""

import asyncio
import random
from typing import Optional

from telethon.errors import (
    FloodWaitError,
    ChatWriteForbiddenError,
    UserBannedInChannelError,
    ChannelPrivateError,
    PeerFloodError,
    SlowModeWaitError,
)

from config import load_config
from utils.logger import logger
from utils.helpers import random_delay, parse_groups_file, parse_messages_file


class Sender:
    """Рассылка сообщений в группы Telegram."""

    def __init__(self):
        config = load_config()
        self.delay_min = config.get("send_delay_min", 30)
        self.delay_max = config.get("send_delay_max", 60)
        self.max_per_day = config.get("max_messages_per_day", 20)

    async def send_to_groups(
        self,
        client,
        account_name: str,
        groups: list[str],
        messages: list[str],
        delay_min: Optional[int] = None,
        delay_max: Optional[int] = None,
        dry_run: bool = False,
        progress_callback=None,
    ) -> dict:
        """
        Отправить сообщения в список групп.

        Возвращает статистику: {
            'sent': int,
            'failed': int,
            'skipped': int,
            'errors': list[str],
        }
        """
        stats = {"sent": 0, "failed": 0, "skipped": 0, "errors": []}

        delay_min = delay_min or self.delay_min
        delay_max = delay_max or self.delay_max

        for i, group in enumerate(groups):
            message = random.choice(messages) if messages else ""
            if not message:
                stats["skipped"] += 1
                continue

            try:
                if dry_run:
                    logger.info(f"[DRY RUN] {account_name} → {group}: {message[:50]}...")
                    stats["sent"] += 1
                else:
                    entity = await client.get_entity(group)
                    await client.send_message(entity, message)
                    stats["sent"] += 1
                    logger.info(f"{account_name} → {group}: отправлено")

                if progress_callback:
                    progress_callback(i + 1, len(groups), group, "sent")

                # Задержка между отправками
                if i < len(groups) - 1:
                    await random_delay(delay_min, delay_max)

            except FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(f"FloodWait {wait_time}с для {account_name} → {group}")
                stats["errors"].append(f"{group}: FloodWait {wait_time}с")
                await asyncio.sleep(wait_time + 5)
                stats["skipped"] += 1

            except PeerFloodError:
                error_msg = f"{group}: PeerFlood - аккаунт ограничен на рассылку"
                logger.error(f"{account_name}: {error_msg}")
                stats["errors"].append(error_msg)
                stats["failed"] += 1
                break  # Останавливаем рассылку с этого аккаунта

            except SlowModeWaitError as e:
                error_msg = f"{group}: SlowMode - ожидание {e.seconds}с"
                logger.warning(f"{account_name}: {error_msg}")
                stats["errors"].append(error_msg)
                stats["skipped"] += 1

            except (ChatWriteForbiddenError, UserBannedInChannelError):
                error_msg = f"{group}: нет прав на запись"
                logger.warning(f"{account_name}: {error_msg}")
                stats["errors"].append(error_msg)
                stats["failed"] += 1

            except ChannelPrivateError:
                error_msg = f"{group}: канал/группа недоступны"
                logger.warning(f"{account_name}: {error_msg}")
                stats["errors"].append(error_msg)
                stats["failed"] += 1

            except Exception as e:
                error_msg = f"{group}: {str(e)}"
                logger.error(f"{account_name} ошибка при отправке в {group}: {e}")
                stats["errors"].append(error_msg)
                stats["failed"] += 1

        return stats

    async def get_account_groups(self, client) -> list[dict]:
        """Получить список групп аккаунта."""
        groups = []
        try:
            async for dialog in client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    groups.append({
                        "title": dialog.title,
                        "id": dialog.id,
                        "username": getattr(dialog.entity, "username", None) or "",
                        "members_count": getattr(dialog.entity, "participants_count", 0) or 0,
                        "type": "group" if dialog.is_group else "channel",
                    })
        except Exception as e:
            logger.error(f"Ошибка при получении групп: {e}")
        return groups
