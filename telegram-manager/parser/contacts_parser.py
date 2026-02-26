from typing import List
from datetime import datetime, timezone

from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.types import User

from .base_parser import BaseParser, ParsedUser
from .chat_parser import _user_to_parsed


class ContactsParser(BaseParser):
    """Parse account contacts"""

    async def parse(
        self,
        include_mutual: bool = True,
        include_non_mutual: bool = True,
    ) -> List[ParsedUser]:
        """Parse contacts from the account's phonebook."""
        self.parsed_users = []
        try:
            result = await self.client(GetContactsRequest(hash=0))
        except Exception:
            return self.parsed_users

        for user in result.users:
            if not isinstance(user, User):
                continue
            is_mutual = getattr(user, 'mutual_contact', False)
            if is_mutual and not include_mutual:
                continue
            if not is_mutual and not include_non_mutual:
                continue
            parsed = _user_to_parsed(user, source='contacts', source_id=None)
            self.parsed_users.append(parsed)

        self.stats['total_found'] = len(self.parsed_users)
        self.stats['unique'] = len(self.parsed_users)
        return self.parsed_users
