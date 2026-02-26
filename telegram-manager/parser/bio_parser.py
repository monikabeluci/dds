from typing import List, Optional
from datetime import datetime, timezone

from .base_parser import BaseParser, ParsedUser


class BioParser(BaseParser):
    """Parse users by keywords in BIO"""

    async def parse(
        self,
        source_users: List[ParsedUser],
        keywords: List[str],
        match_mode: str = "any",
    ) -> List[ParsedUser]:
        """
        Filter users by BIO keywords.
        match_mode: "any" (any keyword), "all" (all keywords), "exact" (exact phrase)
        """
        self.parsed_users = []
        for user in source_users:
            bio = user.bio
            if bio is None:
                fetched_bio = await self.fetch_bio(user.user_id)
                bio = fetched_bio
                if bio:
                    user.bio = bio

            if not bio:
                continue

            bio_lower = bio.lower()
            kws_lower = [kw.lower() for kw in keywords]

            if match_mode == "any":
                match = any(kw in bio_lower for kw in kws_lower)
            elif match_mode == "all":
                match = all(kw in bio_lower for kw in kws_lower)
            elif match_mode == "exact":
                match = any(kw == bio_lower for kw in kws_lower)
            else:
                match = any(kw in bio_lower for kw in kws_lower)

            if match:
                self.parsed_users.append(user)

        self.stats['total_found'] = len(self.parsed_users)
        self.stats['unique'] = len(self.parsed_users)
        return self.parsed_users

    async def fetch_bio(self, user_id: int) -> Optional[str]:
        """Fetch user BIO"""
        try:
            full_user = await self.client.get_entity(user_id)
            if hasattr(full_user, 'about'):
                return full_user.about
            from telethon.tl.functions.users import GetFullUserRequest
            full = await self.client(GetFullUserRequest(user_id))
            return full.full_user.about
        except Exception:
            return None
