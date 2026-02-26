from typing import List, Set

from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch


class InviteValidator:
    """Validation before inviting"""

    def __init__(self, client):
        self.client = client

    async def check_chat_rights(self, chat: str) -> dict:
        """
        Check rights in a chat.
        Returns info about permissions.
        """
        try:
            entity = await self.client.get_entity(chat)

            chat_type = 'group'
            if hasattr(entity, 'broadcast'):
                chat_type = 'channel' if entity.broadcast else 'supergroup'
            elif hasattr(entity, 'megagroup') and entity.megagroup:
                chat_type = 'supergroup'

            is_admin = False
            is_creator = False
            invite_right = False
            can_invite = False

            if hasattr(entity, 'admin_rights') and entity.admin_rights:
                is_admin = True
                invite_right = bool(entity.admin_rights.invite_users)
                can_invite = invite_right
            if hasattr(entity, 'creator') and entity.creator:
                is_creator = True
                is_admin = True
                can_invite = True
                invite_right = True

            members_count = getattr(entity, 'participants_count', 0) or 0

            return {
                'can_invite': can_invite,
                'is_admin': is_admin,
                'is_creator': is_creator,
                'invite_users_right': invite_right,
                'chat_type': chat_type,
                'members_count': members_count,
            }
        except Exception:
            return {
                'can_invite': False,
                'is_admin': False,
                'is_creator': False,
                'invite_users_right': False,
                'chat_type': 'unknown',
                'members_count': 0,
            }

    async def check_user_valid(self, user) -> dict:
        """Check user validity."""
        try:
            if isinstance(user, str):
                entity = await self.client.get_entity(user.lstrip('@'))
            else:
                entity = user

            return {
                'exists': True,
                'is_deleted': getattr(entity, 'deleted', False),
                'is_bot': getattr(entity, 'bot', False),
                'is_restricted': getattr(entity, 'restricted', False),
                'can_be_invited': not getattr(entity, 'deleted', False),
            }
        except Exception:
            return {
                'exists': False,
                'is_deleted': False,
                'is_bot': False,
                'is_restricted': False,
                'can_be_invited': False,
            }

    async def get_chat_members_ids(self, chat: str) -> Set[int]:
        """Get IDs of all chat members"""
        ids: Set[int] = set()
        try:
            entity = await self.client.get_entity(chat)
            offset = 0
            while True:
                result = await self.client(GetParticipantsRequest(
                    channel=entity,
                    filter=ChannelParticipantsSearch(''),
                    offset=offset,
                    limit=200,
                    hash=0,
                ))
                if not result.users:
                    break
                for u in result.users:
                    ids.add(u.id)
                offset += len(result.users)
                if len(result.users) < 200:
                    break
        except Exception:
            pass
        return ids

    async def filter_already_members(self, chat: str, users: List) -> List:
        """Filter out users already in the chat"""
        member_ids = await self.get_chat_members_ids(chat)
        result = []
        for user in users:
            uid = getattr(user, 'id', None) or getattr(user, 'user_id', None)
            if uid not in member_ids:
                result.append(user)
        return result
