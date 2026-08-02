from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Topic, TopicStatus
from database.database import async_session_maker
from config import settings


class SupportService:
    async def forward_to_support(self, message: Message, bot: AsyncTeleBot):
        async with async_session_maker() as session:
            user = await self._get_or_create_user(session, message.from_user)

            user_display_name = message.from_user.first_name or message.from_user.username or f"User {user.user_id}"
            topic = await self._get_or_create_topic(session, user.user_id, bot, user_display_name)

            await bot.forward_message(
                chat_id=settings.forum_group_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
                message_thread_id=topic.topic_id
            )

            await session.commit()

    async def _get_or_create_user(self, session: AsyncSession, from_user) -> User:
        result = await session.execute(
            select(User).where(User.user_id == from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                user_id=from_user.id,
                username=from_user.username,
                first_name=from_user.first_name
            )
            session.add(user)

        return user

    async def _get_or_create_topic(self, session: AsyncSession, user_id: int, bot: AsyncTeleBot, user_name: str) -> Topic:
        result = await session.execute(
            select(Topic).where(
                Topic.user_id == user_id,
                Topic.status != TopicStatus.CLOSED
            )
        )
        topic = result.scalar_one_or_none()

        if not topic:
            topic_name = f"Обращение от {user_name}"
            created_topic = await bot.create_forum_topic(
                chat_id=settings.forum_group_id,
                name=topic_name
            )

            topic = Topic(
                user_id=user_id,
                topic_id=created_topic.message_thread_id,
                status=TopicStatus.OPEN
            )
            session.add(topic)

        return topic
