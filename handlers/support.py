from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from services.support_service import SupportService


def register_handlers(bot: AsyncTeleBot):
    @bot.message_handler(commands=['start'])
    async def cmd_start(message: Message):
        await bot.reply_to(
            message,
            "Добро пожаловать в службу поддержки!\n"
            "Отправьте ваше сообщение, и мы ответим в ближайшее время."
        )

    @bot.message_handler(func=lambda message: message.chat.type == 'private', content_types=['text', 'photo', 'video', 'document'])
    async def handle_user_message(message: Message):
        support_service = SupportService()
        await support_service.forward_to_support(message, bot)
        await bot.reply_to(message, "Ваше сообщение отправлено в службу поддержки. Ожидайте ответа.")
