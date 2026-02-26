import asyncio
import random
from typing import Callable, List, Optional

from telethon.tl.functions.messages import GetDiscussionMessageRequest

from .base_sender import BaseSender, MessageContent, SendResult, SendStats


class CommentsSender(BaseSender):
    """Send comments under posts"""

    async def send(
        self,
        channels: List[str],
        content: MessageContent,
        posts_limit: int = 10,
        only_with_comments: bool = True,
        reply_to_top: bool = False,
        delay_min: int = 30,
        delay_max: int = 60,
        on_progress: Optional[Callable] = None,
        **kwargs,
    ) -> SendStats:
        """Send comments under channel posts."""
        all_posts = []
        for channel in channels:
            posts = await self.get_commentable_posts(channel, posts_limit)
            all_posts.extend([(channel, post) for post in posts])

        self.stats = SendStats(total=len(all_posts))

        for i, (channel, post) in enumerate(all_posts):
            if self.is_cancelled:
                break

            try:
                entity = await self.client.get_entity(channel)
                discussion = await self.client(GetDiscussionMessageRequest(
                    peer=entity,
                    msg_id=post.id,
                ))
                if not discussion.messages:
                    self.stats.other_errors += 1
                    continue

                discussion_peer = discussion.messages[0].peer_id
                reply_to = discussion.messages[0].id if reply_to_top else None

                await self.client.send_message(
                    entity=discussion_peer,
                    message=content.text or '',
                    reply_to=reply_to,
                    parse_mode=content.parse_mode,
                )
                self.stats.success += 1
            except Exception:
                self.stats.other_errors += 1

            if on_progress:
                on_progress(i + 1, len(all_posts), self.stats)

            delay = random.randint(delay_min, delay_max)
            await asyncio.sleep(delay)

        return self.stats

    async def get_commentable_posts(self, channel: str, limit: int) -> List:
        """Get posts with enabled comments"""
        posts = []
        try:
            entity = await self.client.get_entity(channel)
            messages = await self.client.get_messages(entity, limit=limit)
            for msg in messages:
                if msg.replies and msg.replies.replies > 0:
                    posts.append(msg)
        except Exception:
            pass
        return posts
