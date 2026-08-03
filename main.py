import asyncio
import logging

from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from sqlalchemy import select

from config import settings
from database.database import init_db, async_session_maker
from database.models import UserPet
from handlers import support, admin, broadcast, miniapp
from handlers import chat_admin
from services.pet_service import PetService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = AsyncTeleBot(settings.bot_token, state_storage=StateMemoryStorage())


async def parameter_decay_task():
    """Фоновая задача для деградации параметров питомцев"""
    pet_service = PetService()

    while True:
        try:
            await asyncio.sleep(3600)

            async with async_session_maker() as session:
                result = await session.execute(select(UserPet.user_id))
                user_ids = result.scalars().all()

                for user_id in user_ids:
                    try:
                        await pet_service.update_parameters(user_id)
                    except Exception as e:
                        logger.error(f"Error updating parameters for user {user_id}: {e}")

            logger.info(f"Updated parameters for {len(user_ids)} pets")

        except Exception as e:
            logger.error(f"Error in parameter decay task: {e}")
            await asyncio.sleep(60)


async def queue_waiting_task():
    """Фоновая задача для отправки предложения игр при долгом ожидании"""
    from datetime import datetime, timedelta
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
    from database.models import Topic, TopicStatus

    while True:
        try:
            await asyncio.sleep(60)

            threshold_time = datetime.utcnow() - timedelta(minutes=settings.queue_wait_minutes)

            async with async_session_maker() as session:
                result = await session.execute(
                    select(Topic).where(
                        Topic.status == TopicStatus.OPEN,
                        Topic.game_offer_sent == False,
                        Topic.created_at <= threshold_time
                    )
                )
                topics = result.scalars().all()

                for topic in topics:
                    try:
                        markup = InlineKeyboardMarkup()
                        webapp = WebAppInfo(url=f"{settings.mini_app_url}#games")
                        button = InlineKeyboardButton(text="🎮 Поиграть в игры", web_app=webapp)
                        markup.add(button)

                        await bot.send_message(
                            topic.user_id,
                            "Пока ожидаете ответ, можете поиграть в мини-игры и заработать монеты для питомца!",
                            reply_markup=markup
                        )

                        topic.game_offer_sent = True
                    except Exception as e:
                        logger.error(f"Error sending game offer to user {topic.user_id}: {e}")

                if topics:
                    await session.commit()
                    logger.info(f"Sent game offers to {len(topics)} users")

        except Exception as e:
            logger.error(f"Error in queue waiting task: {e}")
            await asyncio.sleep(60)


async def main():
    await init_db()

    support.register_handlers(bot)
    # Раньше admin: там есть обработчик всех сообщений группы, а сообщение
    # достаётся первому подходящему обработчику.
    chat_admin.register_handlers(bot)
    admin.register_handlers(bot)
    broadcast.register_handlers(bot)
    miniapp.register_handlers(bot)

    decay_task = asyncio.create_task(parameter_decay_task())
    queue_task = asyncio.create_task(queue_waiting_task())

    logger.info("Бот запущен...")

    try:
        await bot.infinity_polling()
    finally:
        decay_task.cancel()
        queue_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
