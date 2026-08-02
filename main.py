import asyncio
import logging

from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from sqlalchemy import select

from config import settings
from database.database import init_db, async_session_maker
from handlers import support, admin, broadcast, miniapp


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = AsyncTeleBot(settings.bot_token, state_storage=StateMemoryStorage())


# Фоновой задачи деградации больше нет. Параметры считаются по времени
# при каждом обращении к питомцу (PetService._apply_decay). Результат для
# пользователя тот же, но без ежечасного прохода по всем питомцам с отдельной
# сессией БД на каждого.


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
    admin.register_handlers(bot)
    broadcast.register_handlers(bot)
    miniapp.register_handlers(bot)

    queue_task = asyncio.create_task(queue_waiting_task())

    logger.info("Бот запущен...")

    try:
        await bot.infinity_polling()
    finally:
        queue_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
