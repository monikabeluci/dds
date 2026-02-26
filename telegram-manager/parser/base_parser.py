from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone


@dataclass
class ParsedUser:
    """Structure of a parsed user"""
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    bio: Optional[str]
    is_premium: bool
    is_bot: bool
    is_verified: bool
    last_online: Optional[datetime]
    source: str
    source_id: Optional[int]
    parsed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseParser(ABC):
    """Base class for all parsers"""

    def __init__(self, client, account_name: str):
        self.client = client
        self.account_name = account_name
        self.parsed_users: List[ParsedUser] = []
        self.stats = {
            'total_found': 0,
            'unique': 0,
            'with_username': 0,
            'premium': 0,
            'bots_skipped': 0,
            'deleted_skipped': 0,
        }

    @abstractmethod
    async def parse(self, **kwargs) -> List[ParsedUser]:
        """Main parsing method"""

    async def filter_users(
        self,
        users: List[ParsedUser],
        skip_bots: bool = True,
        skip_deleted: bool = True,
        only_with_username: bool = False,
        only_premium: bool = False,
        only_online_days: Optional[int] = None,
    ) -> List[ParsedUser]:
        """Filter users by various criteria"""
        result = []
        now = datetime.now(timezone.utc)
        for user in users:
            if skip_bots and user.is_bot:
                self.stats['bots_skipped'] += 1
                continue
            if skip_deleted and user.first_name is None and user.username is None:
                self.stats['deleted_skipped'] += 1
                continue
            if only_with_username and not user.username:
                continue
            if only_premium and not user.is_premium:
                continue
            if only_online_days and user.last_online:
                last_online = user.last_online
                if last_online.tzinfo is None:
                    last_online = last_online.replace(tzinfo=timezone.utc)
                delta = now - last_online
                if delta.days > only_online_days:
                    continue
            result.append(user)
        return result

    def deduplicate(self, users: List[ParsedUser]) -> List[ParsedUser]:
        """Remove duplicates by user_id"""
        seen = set()
        result = []
        for user in users:
            if user.user_id not in seen:
                seen.add(user.user_id)
                result.append(user)
        return result
