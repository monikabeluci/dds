import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional


class InviteResult(Enum):
    SUCCESS = "success"
    ALREADY_MEMBER = "already_member"
    USER_PRIVACY = "user_privacy"
    USER_NOT_FOUND = "user_not_found"
    USER_BANNED = "user_banned"
    USER_DELETED = "user_deleted"
    FLOOD_WAIT = "flood_wait"
    PEER_FLOOD = "peer_flood"
    NO_RIGHTS = "no_rights"
    TOO_MANY_REQUESTS = "too_many_requests"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class InviteStats:
    total: int = 0
    success: int = 0
    already_member: int = 0
    privacy_restricted: int = 0
    not_found: int = 0
    banned: int = 0
    deleted: int = 0
    flood_errors: int = 0
    other_errors: int = 0


class BaseInviter:
    """Base class for inviters"""

    def __init__(self, client, account_name: str):
        self.client = client
        self.account_name = account_name
        self.stats = InviteStats()
        self.is_cancelled = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()

    async def invite(
        self,
        target_chat: str,
        users: List,
        delay_min: int = 30,
        delay_max: int = 60,
        batch_size: int = 10,
        batch_delay: int = 300,
        on_progress: Optional[Callable] = None,
    ) -> InviteStats:
        """Main invite method - to be implemented by subclasses"""
        raise NotImplementedError

    def cancel(self) -> None:
        """Cancel the process in real time"""
        self.is_cancelled = True

    def pause(self) -> None:
        """Pause the process"""
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume the process"""
        self._pause_event.set()

    async def _wait_if_paused(self) -> None:
        """Wait if paused"""
        await self._pause_event.wait()
