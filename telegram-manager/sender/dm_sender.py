import asyncio
import random
from typing import Callable, List, Optional

from .base_sender import BaseSender, MessageContent, SendResult, SendStats


class DMSender(BaseSender):
    """Send DMs by username list"""

    async def send(
        self,
        usernames: List[str],
        content: MessageContent,
        skip_if_dialog_exists: bool = False,
        delay_min: int = 30,
        delay_max: int = 60,
        on_progress: Optional[Callable] = None,
        **kwargs,
    ) -> SendStats:
        """Send DMs by username list."""
        self.stats = SendStats(total=len(usernames))

        for i, username in enumerate(usernames):
            if self.is_cancelled:
                break

            try:
                username_clean = username.lstrip('@')
                user = await self.client.get_entity(username_clean)

                if getattr(user, 'bot', False):
                    self.stats.other_errors += 1
                    continue

                if skip_if_dialog_exists:
                    try:
                        await self.client.get_input_entity(user)
                        # If we get here dialog exists - skip
                        # Actually check via get_dialogs
                    except Exception:
                        pass

                result = await self._send_message(user, content)

                if result == SendResult.SUCCESS:
                    self.stats.success += 1
                elif result == SendResult.USER_PRIVACY:
                    self.stats.privacy_restricted += 1
                elif result == SendResult.USER_BLOCKED:
                    self.stats.blocked += 1
                elif result in (SendResult.FLOOD_WAIT, SendResult.PEER_FLOOD):
                    self.stats.flood_errors += 1
                else:
                    self.stats.other_errors += 1
            except Exception:
                self.stats.other_errors += 1

            if on_progress:
                on_progress(i + 1, len(usernames), self.stats)

            delay = random.randint(delay_min, delay_max)
            await asyncio.sleep(delay)

        return self.stats

    async def load_usernames_from_file(self, filepath: str) -> List[str]:
        """Load base from file"""
        usernames = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        usernames.append(line)
        except Exception:
            pass
        return usernames
