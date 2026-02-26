import asyncio
import random
from typing import Callable, List, Optional

from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import InputPhoneContact

from .base_inviter import BaseInviter, InviteResult, InviteStats
from .username_inviter import UsernameInviter


class PhoneInviter(BaseInviter):
    """Invite users by phone numbers"""

    async def invite(
        self,
        target_chat: str,
        phones: List[str],
        add_to_contacts: bool = True,
        remove_after: bool = True,
        delay_min: int = 30,
        delay_max: int = 60,
        batch_size: int = 10,
        batch_delay: int = 300,
        on_progress: Optional[Callable] = None,
    ) -> InviteStats:
        """
        Invite by phone numbers.
        Process: import contact -> get user -> invite -> remove contact
        """
        self.stats = InviteStats(total=len(phones))
        try:
            chat_entity = await self.client.get_entity(target_chat)
        except Exception:
            return self.stats

        username_inviter = UsernameInviter(self.client, self.account_name)

        for i, phone in enumerate(phones):
            if self.is_cancelled:
                break
            await self._wait_if_paused()

            user_entity = None
            contact_id = None

            if add_to_contacts:
                contact = InputPhoneContact(
                    client_id=i,
                    phone=phone,
                    first_name=f"Contact{i}",
                    last_name="",
                )
                try:
                    result = await self.client(ImportContactsRequest([contact]))
                    if result.users:
                        user_entity = result.users[0]
                        contact_id = user_entity.id
                except Exception:
                    self.stats.not_found += 1
                    continue
            else:
                try:
                    user_entity = await self.client.get_entity(phone)
                except Exception:
                    self.stats.not_found += 1
                    continue

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

            if remove_after and contact_id is not None:
                try:
                    await self.client(DeleteContactsRequest(id=[user_entity]))
                except Exception:
                    pass

            if on_progress:
                on_progress(i + 1, len(phones), self.stats)

            if (i + 1) % batch_size == 0 and i + 1 < len(phones):
                await asyncio.sleep(batch_delay)
            else:
                delay = random.randint(delay_min, delay_max)
                await asyncio.sleep(delay)

        return self.stats
