from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from config import settings
from services.admin_service import AdminService
from filters.role_filter import role_filter


def register_handlers(bot: AsyncTeleBot):
    @bot.message_handler(commands=['spec'])
    async def cmd_spec(message: Message):
        if not await role_filter(message, min_level=3):
            await bot.reply_to(message, "⛔ Недостаточно прав для выполнения команды.")
            return

        admin_service = AdminService()
        await admin_service.set_topic_spec(message, bot)

    @bot.message_handler(commands=['unspec'])
    async def cmd_unspec(message: Message):
        if not await role_filter(message, min_level=3):
            await bot.reply_to(message, "⛔ Недостаточно прав для выполнения команды.")
            return

        admin_service = AdminService()
        await admin_service.unset_topic_spec(message, bot)

    @bot.message_handler(
        func=lambda m: m.chat.id == settings.forum_group_id,
        content_types=['text', 'photo', 'video', 'document']
    )
    async def handle_admin_reply(message: Message):
        admin_service = AdminService()
        await admin_service.handle_admin_message(message, bot)
