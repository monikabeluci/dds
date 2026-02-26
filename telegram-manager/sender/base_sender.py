from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class SendResult(Enum):
    SUCCESS = "success"
    USER_PRIVACY = "user_privacy"
    USER_BLOCKED = "user_blocked"
    FLOOD_WAIT = "flood_wait"
    PEER_FLOOD = "peer_flood"
    CHAT_WRITE_FORBIDDEN = "chat_write_forbidden"
    SLOW_MODE = "slow_mode"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class MessageContent:
    """Message content"""
    text: Optional[str] = None
    photo: Optional[str] = None
    video: Optional[str] = None
    document: Optional[str] = None
    voice: Optional[str] = None
    video_note: Optional[str] = None
    sticker: Optional[str] = None
    buttons: Optional[List] = None
    parse_mode: str = "html"


@dataclass
class SendStats:
    total: int = 0
    success: int = 0
    privacy_restricted: int = 0
    blocked: int = 0
    flood_errors: int = 0
    other_errors: int = 0


class BaseSender:
    """Base class for senders"""

    def __init__(self, client, account_name: str):
        self.client = client
        self.account_name = account_name
        self.stats = SendStats()
        self.is_cancelled = False

    async def send(
        self,
        targets: List,
        content: 'MessageContent',
        delay_min: int = 30,
        delay_max: int = 60,
        **kwargs,
    ) -> 'SendStats':
        """Main send method - to be implemented by subclasses"""
        raise NotImplementedError

    def cancel(self) -> None:
        """Cancel in real time"""
        self.is_cancelled = True

    async def _send_message(self, target, content: 'MessageContent') -> SendResult:
        """Send a single message to target"""
        import asyncio
        from telethon.errors import (
            UserPrivacyRestrictedError,
            UserIsBlockedError,
            FloodWaitError,
            PeerFloodError,
            ChatWriteForbiddenError,
            SlowModeWaitError,
        )

        try:
            file = None
            if content.photo:
                file = content.photo
            elif content.video:
                file = content.video
            elif content.document:
                file = content.document
            elif content.voice:
                file = content.voice
            elif content.video_note:
                file = content.video_note

            await self.client.send_message(
                entity=target,
                message=content.text or '',
                file=file,
                parse_mode=content.parse_mode,
                buttons=content.buttons,
            )
            return SendResult.SUCCESS
        except UserPrivacyRestrictedError:
            return SendResult.USER_PRIVACY
        except UserIsBlockedError:
            return SendResult.USER_BLOCKED
        except FloodWaitError as e:
            await asyncio.sleep(min(e.seconds, 3600))
            return SendResult.FLOOD_WAIT
        except PeerFloodError:
            return SendResult.PEER_FLOOD
        except ChatWriteForbiddenError:
            return SendResult.CHAT_WRITE_FORBIDDEN
        except SlowModeWaitError:
            return SendResult.SLOW_MODE
        except Exception:
            return SendResult.UNKNOWN_ERROR
