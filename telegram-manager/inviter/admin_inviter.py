import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import Callable, List, Optional

from telethon.tl.functions.channels import InviteToChannelRequest, ExportInviteRequest
from telethon.errors import FloodWaitError, UserAlreadyParticipantError

from .base_inviter import BaseInviter, InviteResult, InviteStats
from .username_inviter import UsernameInviter


class AdminInviter(BaseInviter):
    """Invite using admin rights"""

    async def invite(
        self,
        target_chat: str,
        users: List,
        use_invite_link: bool = False,
        delay_min: int = 30,
        delay_max: int = 60,
        batch_size: int = 10,
        batch_delay: int = 300,
        on_progress: Optional[Callable] = None,
    ) -> InviteStats:
        """Invite using admin rights."""
        self.stats = InviteStats(total=len(users))
        try:
            chat_entity = await self.client.get_entity(target_chat)
        except Exception:
            return self.stats

        username_inviter = UsernameInviter(self.client, self.account_name)

        for i, user in enumerate(users):
            if self.is_cancelled:
                break
            await self._wait_if_paused()

            if isinstance(user, str):
                user_entity = await username_inviter._resolve_username(user)
            else:
                user_entity = user

            if user_entity is None:
                self.stats.not_found += 1
                continue

            result = await username_inviter._do_invite(chat_entity, user_entity)

            if result == InviteResult.SUCCESS:
                self.stats.success += 1
            elif result == InviteResult.ALREADY_MEMBER:
                self.stats.already_member += 1
            elif result == InviteResult.USER_PRIVACY:
                self.stats.privacy_restricted += 1
            elif result in (InviteResult.FLOOD_WAIT, InviteResult.PEER_FLOOD):
                self.stats.flood_errors += 1
            else:
                self.stats.other_errors += 1

            if on_progress:
                on_progress(i + 1, len(users), self.stats)

            if (i + 1) % batch_size == 0 and i + 1 < len(users):
                await asyncio.sleep(batch_delay)
            else:
                delay = random.randint(delay_min, delay_max)
                await asyncio.sleep(delay)

        return self.stats

    async def create_invite_link(
        self,
        chat: str,
        expire_hours: int = 24,
        usage_limit: Optional[int] = None,
    ) -> str:
        """Create an invite link"""
        try:
            entity = await self.client.get_entity(chat)
            expire_date = datetime.now(timezone.utc) + timedelta(hours=expire_hours)
            result = await self.client(ExportInviteRequest(
                peer=entity,
                expire_date=expire_date,
                usage_limit=usage_limit or 0,
            ))
            return result.link
        except Exception as e:
            raise RuntimeError(f"Failed to create invite link: {e}") from e
