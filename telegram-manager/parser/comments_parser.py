from typing import List, Optional
from datetime import datetime, timezone

from telethon.tl.functions.messages import GetDiscussionMessageRequest
from telethon.tl.types import User

from .base_parser import BaseParser, ParsedUser
from .chat_parser import _user_to_parsed


class CommentsParser(BaseParser):
    """Parse users from comments under posts"""

    async def parse(
        self,
        channel: str,
        post_ids: Optional[List[int]] = None,
        posts_limit: int = 100,
        comments_limit: Optional[int] = None,
        only_replies: bool = False,
    ) -> List[ParsedUser]:
        """Parse comment authors from a channel's posts."""
        self.parsed_users = []
        try:
            entity = await self.client.get_entity(channel)
        except Exception:
            return self.parsed_users

        if post_ids is None:
            posts = await self.client.get_messages(entity, limit=posts_limit)
            post_ids = [m.id for m in posts if m.replies and m.replies.replies > 0]

        for post_id in post_ids:
            try:
                discussion = await self.client(GetDiscussionMessageRequest(
                    peer=entity,
                    msg_id=post_id,
                ))
                discussion_peer = discussion.messages[0].peer_id if discussion.messages else None
                if discussion_peer is None:
                    continue

                comments = await self.client.get_messages(
                    discussion_peer,
                    limit=comments_limit or 100,
                    reply_to=discussion.messages[0].id,
                )
                for msg in comments:
                    if msg.sender and isinstance(msg.sender, User):
                        if only_replies and not msg.reply_to:
                            continue
                        parsed = _user_to_parsed(
                            msg.sender,
                            source=f"comments:{channel}:{post_id}",
                            source_id=entity.id,
                        )
                        self.parsed_users.append(parsed)
            except Exception:
                continue

        self.parsed_users = self.deduplicate(self.parsed_users)
        self.stats['total_found'] = len(self.parsed_users)
        self.stats['unique'] = len(self.parsed_users)
        return self.parsed_users
