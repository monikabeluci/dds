import asyncio
import random
from typing import Callable, List, Optional

from .base_sender import BaseSender, MessageContent, SendResult, SendStats


class GiftsSender(BaseSender):
    """Send gifts via Telegram Stars"""

    async def send_gift(
        self,
        user,
        stars_amount: int,
        message: Optional[str] = None,
    ) -> bool:
        """Send a gift (Telegram Stars) to a user."""
        try:
            entity = await self.client.get_entity(user)
            # Stars payment is done via invoice - simplified implementation
            await self.client.send_message(
                entity=entity,
                message=f"⭐ {stars_amount} Stars" + (f"\n{message}" if message else ""),
            )
            return True
        except Exception:
            return False

    async def send_gifts_batch(
        self,
        users: List,
        stars_amount: int,
        message: Optional[str] = None,
        delay_min: int = 30,
        delay_max: int = 60,
        on_progress: Optional[Callable] = None,
        **kwargs,
    ) -> SendStats:
        """Mass gift sending."""
        self.stats = SendStats(total=len(users))

        for i, user in enumerate(users):
            if self.is_cancelled:
                break

            success = await self.send_gift(user, stars_amount, message)
            if success:
                self.stats.success += 1
            else:
                self.stats.other_errors += 1

            if on_progress:
                on_progress(i + 1, len(users), self.stats)

            delay = random.randint(delay_min, delay_max)
            await asyncio.sleep(delay)

        return self.stats

    async def get_stars_balance(self) -> int:
        """Get Stars balance"""
        try:
            from telethon.tl.functions.payments import GetStarsTransactionsRequest
            result = await self.client(GetStarsTransactionsRequest(
                peer=await self.client.get_me(),
                offset='',
                limit=0,
            ))
            return getattr(result, 'balance', 0) or 0
        except Exception:
            return 0

    async def check_gift_available(self, user) -> bool:
        """Check if a gift can be sent to user"""
        try:
            entity = await self.client.get_entity(user)
            return not getattr(entity, 'deleted', False) and not getattr(entity, 'bot', False)
        except Exception:
            return False
