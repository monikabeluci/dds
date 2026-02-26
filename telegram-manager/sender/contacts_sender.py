import asyncio
import random
from typing import Callable, List, Optional

from telethon.tl.functions.contacts import GetContactsRequest

from .base_sender import BaseSender, MessageContent, SendResult, SendStats


class ContactsSender(BaseSender):
    """Send messages to phone book contacts"""

    async def send(
        self,
        content: MessageContent,
        only_mutual: bool = False,
        exclude_recent: bool = True,
        delay_min: int = 30,
        delay_max: int = 60,
        on_progress: Optional[Callable] = None,
        **kwargs,
    ) -> SendStats:
        """Send to all account contacts."""
        contacts = await self.get_contacts(only_mutual=only_mutual)
        self.stats = SendStats(total=len(contacts))

        for i, user in enumerate(contacts):
            if self.is_cancelled:
                break

            result = await self._send_message(user, content)

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
                on_progress(i + 1, len(contacts), self.stats)

            delay = random.randint(delay_min, delay_max)
            await asyncio.sleep(delay)

        return self.stats

    async def get_contacts(self, only_mutual: bool = False) -> List:
        """Get list of contacts"""
        try:
            result = await self.client(GetContactsRequest(hash=0))
            if only_mutual:
                return [u for u in result.users if getattr(u, 'mutual_contact', False)]
            return list(result.users)
        except Exception:
            return []
