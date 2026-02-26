import asyncio
import random
from dataclasses import dataclass


@dataclass
class InviteLimits:
    """Invite limit settings"""

    delay_min: int = 30
    delay_max: int = 60

    batch_size: int = 10
    batch_delay: int = 300

    daily_limit: int = 50
    hourly_limit: int = 10

    max_flood_wait: int = 3600
    stop_on_flood: bool = False

    pause_after_errors: int = 5
    pause_duration: int = 600

    archive_chat: bool = False


class LimitsManager:
    """Manage limits"""

    def __init__(self, limits: InviteLimits):
        self.limits = limits
        self.daily_count = 0
        self.hourly_count = 0
        self.consecutive_errors = 0

    async def get_delay(self) -> int:
        """Get random delay within configured range"""
        return random.randint(self.limits.delay_min, self.limits.delay_max)

    def check_limits(self) -> tuple:
        """Check if limits are exceeded"""
        if self.daily_count >= self.limits.daily_limit:
            return False, f"Daily limit reached ({self.limits.daily_limit})"
        if self.hourly_count >= self.limits.hourly_limit:
            return False, f"Hourly limit reached ({self.limits.hourly_limit})"
        return True, "OK"

    def record_success(self) -> None:
        """Record a successful invite"""
        self.daily_count += 1
        self.hourly_count += 1
        self.consecutive_errors = 0

    def record_error(self) -> None:
        """Record an error"""
        self.consecutive_errors += 1

    def should_pause(self) -> bool:
        """Check if we should pause due to consecutive errors"""
        return self.consecutive_errors >= self.limits.pause_after_errors
