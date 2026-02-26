from typing import List, Optional
from datetime import datetime, timezone

from telethon.tl.types import User

from .base_parser import BaseParser, ParsedUser
from .chat_parser import _user_to_parsed


class MessagesParser(BaseParser):
    """Parse users from messages"""

    async def parse(
        self,
        chat: str,
        limit: int = 1000,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        keywords: Optional[List[str]] = None,
        only_forwards: bool = False,
    ) -> List[ParsedUser]:
        """Parse message authors, optionally filtered by keywords."""
        self.parsed_users = []
        try:
            entity = await self.client.get_entity(chat)
            messages = await self.client.get_messages(
                entity,
                limit=limit,
                offset_date=to_date,
                reverse=False,
            )
            for msg in messages:
                if from_date and msg.date:
                    msg_date = msg.date
                    if msg_date.tzinfo is None:
                        msg_date = msg_date.replace(tzinfo=timezone.utc)
                    fd = from_date
                    if fd.tzinfo is None:
                        fd = fd.replace(tzinfo=timezone.utc)
                    if msg_date < fd:
                        continue
                if keywords and msg.text:
                    text_lower = msg.text.lower()
                    if not any(kw.lower() in text_lower for kw in keywords):
                        continue
                if only_forwards and not msg.forward:
                    continue

                sender = msg.sender
                if only_forwards and msg.forward and msg.forward.sender:
                    sender = msg.forward.sender

                if sender and isinstance(sender, User):
                    parsed = _user_to_parsed(
                        sender,
                        source=f"messages:{chat}",
                        source_id=entity.id,
                    )
                    self.parsed_users.append(parsed)
        except Exception:
            pass

        self.parsed_users = self.deduplicate(self.parsed_users)
        self.stats['total_found'] = len(self.parsed_users)
        self.stats['unique'] = len(self.parsed_users)
        return self.parsed_users
