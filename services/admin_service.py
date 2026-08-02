import logging

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from sqlalchemy import select

from database.models import Admin, Topic, TopicStatus, AdminLog, ActionType
from database.database import async_session_maker


logger = logging.getLogger(__name__)


class AdminService:
    async def get_admin(self, user_id: int) -> Admin | None:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Admin).where(Admin.user_id == user_id)
            )
            return result.scalar_one_or_none()

    async def set_topic_spec(self, message: Message, bot: AsyncTeleBot):
        if not message.message_thread_id:
            await bot.reply_to(message, "Эта команда доступна только в теме.")
            return

        async with async_session_maker() as session:
            result = await session.execute(
                select(Topic).where(Topic.topic_id == message.message_thread_id)
            )
            topic = result.scalar_one_or_none()

            if topic:
                topic.status = TopicStatus.SPEC

                log_entry = AdminLog(
                    admin_user_id=message.from_user.id,
                    action_type=ActionType.SPEC_SET,
                    topic_id=topic.id,
                    details=f"User {topic.user_id}"
                )
                session.add(log_entry)

                await session.commit()
                await bot.reply_to(message, "✅ Тема переведена в режим SPEC")

    async def unset_topic_spec(self, message: Message, bot: AsyncTeleBot):
        if not message.message_thread_id:
            await bot.reply_to(message, "Эта команда доступна только в теме.")
            return

        async with async_session_maker() as session:
            result = await session.execute(
                select(Topic).where(Topic.topic_id == message.message_thread_id)
            )
            topic = result.scalar_one_or_none()

            if topic:
                topic.status = TopicStatus.CLAIMED

                log_entry = AdminLog(
                    admin_user_id=message.from_user.id,
                    action_type=ActionType.SPEC_UNSET,
                    topic_id=topic.id,
                    details=f"User {topic.user_id}"
                )
                session.add(log_entry)

                await session.commit()
                await bot.reply_to(message, "✅ Режим SPEC снят")

    async def handle_admin_message(self, message: Message, bot: AsyncTeleBot):
        if not message.message_thread_id:
            return

        if message.forward_from or message.forward_from_chat:
            return

        # Этот хендлер регистрируется раньше хендлеров /ad, /ads и /pet,
        # а telebot отдаёт сообщение первому подходящему. Без этой проверки
        # команда, набранная внутри темы, ушла бы пользователю как обычный ответ.
        text = message.text or message.caption or ""
        if text.startswith("/"):
            return

        async with async_session_maker() as session:
            result = await session.execute(
                select(Topic).where(Topic.topic_id == message.message_thread_id)
            )
            topic = result.scalar_one_or_none()

            if not topic:
                return

            if topic.status == TopicStatus.SPEC:
                admin = await self.get_admin(message.from_user.id)

                if not admin or admin.role_level < 3:
                    await bot.delete_message(message.chat.id, message.message_id)
                    await bot.send_message(message.chat.id, "⛔ Доступ к этой теме ограничен.", message_thread_id=message.message_thread_id)
                    return

            try:
                await bot.copy_message(
                    chat_id=topic.user_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id
                )
            except Exception as e:
                logger.error(f"Failed to deliver reply to user {topic.user_id}: {e}")
