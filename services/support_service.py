import hashlib

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Topic, TopicStatus
from database.database import async_session_maker
from config import settings


def anonymous_code(user_id: int) -> str:
    """Стабильный анонимный код обращения.

    Один и тот же пользователь всегда получает один и тот же код,
    но по коду нельзя восстановить Telegram ID.
    """
    digest = hashlib.sha256(f"support:{user_id}".encode("utf-8")).hexdigest()
    return digest[:6].upper()


class SupportService:
    async def forward_to_support(self, message: Message, bot: AsyncTeleBot):
        async with async_session_maker() as session:
            user = await self._get_or_create_user(session, message.from_user)
            await session.commit()

            topic_id = await self._get_or_create_topic(session, user.user_id, bot)

        # copy_message, а не forward_message: копия не содержит ссылки на автора,
        # поэтому в топике личность пользователя не раскрывается.
        await bot.copy_message(
            chat_id=settings.forum_group_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            message_thread_id=topic_id
        )

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

    async def _get_or_create_topic(self, session: AsyncSession, user_id: int, bot: AsyncTeleBot) -> int:
        result = await session.execute(
            select(Topic).where(
                Topic.user_id == user_id,
                Topic.status != TopicStatus.CLOSED
            )
        )
        topic = result.scalars().first()

        if topic:
            return topic.topic_id

        # В названии темы только анонимный код — ни имени, ни username, ни ID.
        topic_name = f"Обращение #{anonymous_code(user_id)}"
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
        # Коммитим сразу: иначе при ошибке отправки тема останется в Telegram,
        # но не в БД, и на следующем сообщении создастся дубль.
        await session.commit()

        return topic.topic_id
