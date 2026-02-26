from typing import List

from telethon.tl.functions.channels import EditAdminRequest
from telethon.tl.types import ChatAdminRights


class AdminManager:
    """Manage admins in a chat"""

    def __init__(self, client):
        self.client = client

    async def promote_for_invite(self, chat: str, user) -> bool:
        """
        Promote to admin with ONLY invite_users right.
        """
        try:
            entity = await self.client.get_entity(chat)
            if isinstance(user, str):
                user_entity = await self.client.get_entity(user.lstrip('@'))
            else:
                user_entity = user

            rights = ChatAdminRights(
                change_info=False,
                post_messages=False,
                edit_messages=False,
                delete_messages=False,
                ban_users=False,
                invite_users=True,
                pin_messages=False,
                add_admins=False,
                anonymous=False,
                manage_call=False,
                other=False,
                manage_topics=False,
            )
            await self.client(EditAdminRequest(
                channel=entity,
                user_id=user_entity,
                admin_rights=rights,
                rank="",
            ))
            return True
        except Exception:
            return False

    async def demote(self, chat: str, user) -> bool:
        """Remove admin rights"""
        try:
            entity = await self.client.get_entity(chat)
            if isinstance(user, str):
                user_entity = await self.client.get_entity(user.lstrip('@'))
            else:
                user_entity = user

            rights = ChatAdminRights(
                change_info=False,
                post_messages=False,
                edit_messages=False,
                delete_messages=False,
                ban_users=False,
                invite_users=False,
                pin_messages=False,
                add_admins=False,
                anonymous=False,
                manage_call=False,
                other=False,
                manage_topics=False,
            )
            await self.client(EditAdminRequest(
                channel=entity,
                user_id=user_entity,
                admin_rights=rights,
                rank="",
            ))
            return True
        except Exception:
            return False

    async def get_admins(self, chat: str) -> List:
        """Get list of admins"""
        try:
            from telethon.tl.functions.channels import GetParticipantsRequest
            from telethon.tl.types import ChannelParticipantsAdmins
            entity = await self.client.get_entity(chat)
            result = await self.client(GetParticipantsRequest(
                channel=entity,
                filter=ChannelParticipantsAdmins(),
                offset=0,
                limit=200,
                hash=0,
            ))
            return result.users
        except Exception:
            return []
