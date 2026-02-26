from telethon.errors import (
    FloodWaitError,
    UserPrivacyRestrictedError,
    UserNotMutualContactError,
    UserChannelsTooMuchError,
    ChatWriteForbiddenError,
    UserKickedError,
    UserBannedInChannelError,
    PeerFloodError,
    UserAlreadyParticipantError,
)

from .base_inviter import InviteResult


class InviteErrorHandler:
    """Enhanced error handling for invites"""

    def __init__(self, max_flood_wait: int = 3600):
        self.max_flood_wait = max_flood_wait

    async def handle_error(self, error: Exception, user, chat: str) -> tuple:
        """
        Handle error and determine action.
        Returns (InviteResult, action) where action is one of:
        'continue', 'pause', 'stop', 'switch_account'
        """
        if isinstance(error, UserAlreadyParticipantError):
            return InviteResult.ALREADY_MEMBER, 'continue'
        elif isinstance(error, (UserPrivacyRestrictedError, UserNotMutualContactError)):
            return InviteResult.USER_PRIVACY, 'continue'
        elif isinstance(error, FloodWaitError):
            result, action = await self.handle_flood_wait(error)
            return InviteResult.FLOOD_WAIT, action
        elif isinstance(error, PeerFloodError):
            return InviteResult.PEER_FLOOD, 'switch_account'
        elif isinstance(error, (UserBannedInChannelError, UserKickedError)):
            return InviteResult.USER_BANNED, 'continue'
        elif isinstance(error, UserChannelsTooMuchError):
            return InviteResult.USER_BANNED, 'continue'
        elif isinstance(error, ChatWriteForbiddenError):
            return InviteResult.NO_RIGHTS, 'stop'
        else:
            return InviteResult.UNKNOWN_ERROR, 'continue'

    async def handle_flood_wait(self, error: FloodWaitError) -> tuple:
        """Handle FloodWait"""
        import asyncio
        if error.seconds <= self.max_flood_wait:
            await asyncio.sleep(error.seconds)
            return InviteResult.FLOOD_WAIT, 'continue'
        else:
            return InviteResult.FLOOD_WAIT, 'switch_account'

    def get_error_message(self, result: InviteResult) -> str:
        """Human-readable error message"""
        messages = {
            InviteResult.SUCCESS: "✅ Successfully invited",
            InviteResult.ALREADY_MEMBER: "ℹ️ Already a member",
            InviteResult.USER_PRIVACY: "🔒 Privacy restrictions",
            InviteResult.USER_NOT_FOUND: "❓ User not found",
            InviteResult.USER_BANNED: "🚫 User banned",
            InviteResult.USER_DELETED: "🗑️ User deleted",
            InviteResult.FLOOD_WAIT: "⏳ FloodWait - waiting",
            InviteResult.PEER_FLOOD: "🚦 PeerFlood - switch account",
            InviteResult.NO_RIGHTS: "⛔ No rights in chat",
            InviteResult.TOO_MANY_REQUESTS: "🔄 Too many requests",
            InviteResult.UNKNOWN_ERROR: "❌ Unknown error",
        }
        return messages.get(result, "❓ Unknown")
