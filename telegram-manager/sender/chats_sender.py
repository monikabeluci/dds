import asyncio
import random
from typing import Callable, List, Optional

from .base_sender import BaseSender, MessageContent, SendResult, SendStats


class ChatsSender(BaseSender):
    """Send messages to chats/groups"""

    async def send(
        self,
        chats: List[str],
        content: MessageContent,
        check_rights: bool = True,
        skip_slow_mode: bool = True,
        delay_min: int = 30,
        delay_max: int = 60,
        on_progress: Optional[Callable] = None,
        **kwargs,
    ) -> SendStats:
        """Send to chats/groups."""
        self.stats = SendStats(total=len(chats))

        for i, chat in enumerate(chats):
            if self.is_cancelled:
                break

            try:
                entity = await self.client.get_entity(chat)

                if check_rights:
                    if hasattr(entity, 'default_banned_rights') and entity.default_banned_rights:
                        if entity.default_banned_rights.send_messages:
                            self.stats.other_errors += 1
                            continue

                result = await self._send_message(entity, content)

                if result == SendResult.SUCCESS:
                    self.stats.success += 1
                elif result == SendResult.SLOW_MODE and skip_slow_mode:
                    self.stats.other_errors += 1
                    continue
                elif result == SendResult.CHAT_WRITE_FORBIDDEN:
                    self.stats.other_errors += 1
                elif result in (SendResult.FLOOD_WAIT, SendResult.PEER_FLOOD):
                    self.stats.flood_errors += 1
                else:
                    self.stats.other_errors += 1
            except Exception:
                self.stats.other_errors += 1

            if on_progress:
                on_progress(i + 1, len(chats), self.stats)

            delay = random.randint(delay_min, delay_max)
            await asyncio.sleep(delay)

        return self.stats

    async def get_writable_chats(self) -> List:
        """Get chats where we can write"""
        writable = []
        try:
            async for dialog in self.client.iter_dialogs():
                from telethon.tl.types import Chat, Channel
                entity = dialog.entity
                if not isinstance(entity, (Chat, Channel)):
                    continue
                if hasattr(entity, 'default_banned_rights') and entity.default_banned_rights:
                    if entity.default_banned_rights.send_messages:
                        continue
                writable.append(entity)
        except Exception:
            pass
        return writable
