from typing import List, Optional
from datetime import datetime, timezone

from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import (
    ChannelParticipantsSearch,
    ChannelParticipantsAdmins,
    User,
)

from .base_parser import BaseParser, ParsedUser


class ChatParser(BaseParser):
    """Parse members from chats/groups/channels"""

    async def parse(
        self,
        chat_ids: List[str],
        limit_per_chat: Optional[int] = None,
        only_admins: bool = False,
        only_recent: bool = False,
        aggressive: bool = False,
    ) -> List[ParsedUser]:
        """Parse participants from chats."""
        self.parsed_users = []
        for chat_id in chat_ids:
            users = await self.parse_single_chat(
                chat_id,
                limit=limit_per_chat,
                only_admins=only_admins,
                aggressive=aggressive,
            )
            self.parsed_users.extend(users)
            self.stats['total_found'] += len(users)

        self.parsed_users = self.deduplicate(self.parsed_users)
        self.stats['unique'] = len(self.parsed_users)
        self.stats['with_username'] = sum(1 for u in self.parsed_users if u.username)
        self.stats['premium'] = sum(1 for u in self.parsed_users if u.is_premium)
        return self.parsed_users

    async def parse_single_chat(
        self,
        chat_id: str,
        limit: Optional[int] = None,
        only_admins: bool = False,
        aggressive: bool = False,
    ) -> List[ParsedUser]:
        """Parse a single chat."""
        users: List[ParsedUser] = []
        try:
            entity = await self.client.get_entity(chat_id)
        except Exception:
            return users

        filter_type = ChannelParticipantsAdmins() if only_admins else ChannelParticipantsSearch('')
        offset = 0
        batch = 200

        while True:
            try:
                result = await self.client(GetParticipantsRequest(
                    channel=entity,
                    filter=filter_type,
                    offset=offset,
                    limit=batch,
                    hash=0,
                ))
            except Exception:
                break

            if not result.users:
                break

            for tg_user in result.users:
                if not isinstance(tg_user, User):
                    continue
                parsed = _user_to_parsed(tg_user, source=str(chat_id), source_id=entity.id)
                users.append(parsed)

            offset += len(result.users)
            if limit and len(users) >= limit:
                users = users[:limit]
                break
            if len(result.users) < batch:
                break

        if aggressive and not only_admins:
            extra = await self._aggressive_parse(entity, chat_id)
            users.extend(extra)

        return users

    async def _aggressive_parse(self, entity, chat_id: str) -> List[ParsedUser]:
        """Search by alphabet letters to find more members in large chats."""
        users: List[ParsedUser] = []
        alphabet = 'abcdefghijklmnopqrstuvwxyz0123456789'
        for letter in alphabet:
            try:
                result = await self.client(GetParticipantsRequest(
                    channel=entity,
                    filter=ChannelParticipantsSearch(letter),
                    offset=0,
                    limit=200,
                    hash=0,
                ))
                for tg_user in result.users:
                    if isinstance(tg_user, User):
                        parsed = _user_to_parsed(tg_user, source=str(chat_id), source_id=entity.id)
                        users.append(parsed)
            except Exception:
                continue
        return users


def _user_to_parsed(user: 'User', source: str, source_id: Optional[int]) -> ParsedUser:
    last_online: Optional[datetime] = None
    if hasattr(user, 'status') and user.status is not None:
        status = user.status
        if hasattr(status, 'was_online'):
            last_online = status.was_online

    return ParsedUser(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        bio=None,
        is_premium=bool(getattr(user, 'premium', False)),
        is_bot=bool(user.bot),
        is_verified=bool(getattr(user, 'verified', False)),
        last_online=last_online,
        source=source,
        source_id=source_id,
        parsed_at=datetime.now(timezone.utc),
    )
