from typing import List
from datetime import datetime, timezone

from telethon.tl.types import User

from .base_parser import BaseParser, ParsedUser
from .chat_parser import _user_to_parsed


class GiftsParser(BaseParser):
    """Parse users who sent/received gifts"""

    async def parse(
        self,
        chat: str,
        gift_type: str = "all",
        direction: str = "senders",
    ) -> List[ParsedUser]:
        """
        Parse by Telegram Stars gifts.
        Collects senders and receivers of gifts.
        """
        self.parsed_users = []
        try:
            entity = await self.client.get_entity(chat)
            messages = await self.client.get_messages(entity, limit=500)
            for msg in messages:
                if msg.sender and isinstance(msg.sender, User):
                    # Check for gift-related service messages
                    if hasattr(msg, 'action') and msg.action is not None:
                        action_type = type(msg.action).__name__
                        if 'Gift' in action_type or 'Stars' in action_type or 'Premium' in action_type:
                            parsed = _user_to_parsed(
                                msg.sender,
                                source=f"gifts:{chat}",
                                source_id=entity.id,
                            )
                            self.parsed_users.append(parsed)
        except Exception:
            pass

        self.parsed_users = self.deduplicate(self.parsed_users)
        self.stats['total_found'] = len(self.parsed_users)
        self.stats['unique'] = len(self.parsed_users)
        return self.parsed_users
