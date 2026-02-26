import asyncio
import random
from typing import Callable, List, Optional

from .base_sender import BaseSender, MessageContent, SendResult, SendStats


class DialogsSender(BaseSender):
    """Send messages to existing dialogs"""

    async def send(
        self,
        content: MessageContent,
        dialog_types: Optional[List[str]] = None,
        only_unread: bool = False,
        min_messages: int = 1,
        delay_min: int = 30,
        delay_max: int = 60,
        on_progress: Optional[Callable] = None,
        **kwargs,
    ) -> SendStats:
        """Send to dialogs (personal chats, groups)."""
        if dialog_types is None:
            dialog_types = ['user']

        targets = []
        try:
            async for dialog in self.client.iter_dialogs():
                from telethon.tl.types import User, Chat, Channel
                entity = dialog.entity
                entity_type = ''
                if isinstance(entity, User):
                    entity_type = 'user'
                elif isinstance(entity, Channel):
                    entity_type = 'channel' if entity.broadcast else 'group'
                elif isinstance(entity, Chat):
                    entity_type = 'group'

                if entity_type not in dialog_types:
                    continue
                if only_unread and dialog.unread_count == 0:
                    continue
                if min_messages > 1 and (not dialog.message):
                    continue
                targets.append(entity)
        except Exception:
            pass

        self.stats = SendStats(total=len(targets))

        for i, target in enumerate(targets):
            if self.is_cancelled:
                break

            result = await self._send_message(target, content)

            if result == SendResult.SUCCESS:
                self.stats.success += 1
            elif result == SendResult.USER_PRIVACY:
                self.stats.privacy_restricted += 1
            elif result == SendResult.USER_BLOCKED:
                self.stats.blocked += 1
            elif result in (SendResult.FLOOD_WAIT, SendResult.PEER_FLOOD):
                self.stats.flood_errors += 1
            else:
                self.stats.other_errors += 1

            if on_progress:
                on_progress(i + 1, len(targets), self.stats)

            delay = random.randint(delay_min, delay_max)
            await asyncio.sleep(delay)

        return self.stats
