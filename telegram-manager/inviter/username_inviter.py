import asyncio
import random
from typing import Callable, List, Optional

from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import (
    FloodWaitError,
    UserPrivacyRestrictedError,
    UserNotMutualContactError,
    UserAlreadyParticipantError,
    PeerFloodError,
    UserChannelsTooMuchError,
    UserBannedInChannelError,
    UserKickedError,
    ChatWriteForbiddenError,
)

from .base_inviter import BaseInviter, InviteResult, InviteStats


class UsernameInviter(BaseInviter):
    """Invite users by username"""

    async def invite(
        self,
        target_chat: str,
        usernames: List[str],
        delay_min: int = 30,
        delay_max: int = 60,
        batch_size: int = 10,
        batch_delay: int = 300,
        on_progress: Optional[Callable] = None,
    ) -> InviteStats:
        """Invite by username list."""
        self.stats = InviteStats(total=len(usernames))
        try:
            entity = await self.client.get_entity(target_chat)
        except Exception:
            return self.stats

        for i, username in enumerate(usernames):
            if self.is_cancelled:
                break
            await self._wait_if_paused()

            user_entity = await self._resolve_username(username)
            if user_entity is None:
                self.stats.not_found += 1
                continue

            result = await self._do_invite(entity, user_entity)

            if result == InviteResult.SUCCESS:
                self.stats.success += 1
            elif result == InviteResult.ALREADY_MEMBER:
                self.stats.already_member += 1
            elif result == InviteResult.USER_PRIVACY:
                self.stats.privacy_restricted += 1
            elif result == InviteResult.USER_NOT_FOUND:
                self.stats.not_found += 1
            elif result in (InviteResult.USER_BANNED, InviteResult.USER_DELETED):
                self.stats.banned += 1
            elif result in (InviteResult.FLOOD_WAIT, InviteResult.PEER_FLOOD):
                self.stats.flood_errors += 1
            else:
                self.stats.other_errors += 1

            if on_progress:
                on_progress(i + 1, len(usernames), self.stats)

            if (i + 1) % batch_size == 0 and i + 1 < len(usernames):
                await asyncio.sleep(batch_delay)
            else:
                delay = random.randint(delay_min, delay_max)
                await asyncio.sleep(delay)

        return self.stats

    async def _resolve_username(self, username: str):
        """Resolve username to entity"""
        try:
            username = username.lstrip('@')
            return await self.client.get_entity(username)
        except Exception:
            return None

    async def _do_invite(self, chat_entity, user_entity) -> InviteResult:
        """Perform the actual invite"""
        try:
            await self.client(InviteToChannelRequest(
                channel=chat_entity,
                users=[user_entity],
            ))
            return InviteResult.SUCCESS
        except UserAlreadyParticipantError:
            return InviteResult.ALREADY_MEMBER
        except (UserPrivacyRestrictedError, UserNotMutualContactError):
            return InviteResult.USER_PRIVACY
        except (UserBannedInChannelError, UserKickedError):
            return InviteResult.USER_BANNED
        except FloodWaitError as e:
            await asyncio.sleep(min(e.seconds, 3600))
            return InviteResult.FLOOD_WAIT
        except PeerFloodError:
            return InviteResult.PEER_FLOOD
        except UserChannelsTooMuchError:
            return InviteResult.USER_BANNED
        except ChatWriteForbiddenError:
            return InviteResult.NO_RIGHTS
        except Exception:
            return InviteResult.UNKNOWN_ERROR
