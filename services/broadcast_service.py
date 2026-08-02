import asyncio
from datetime import datetime

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from database.models import Broadcast, BroadcastStatus, User
from database.database import async_session_maker
from config import settings


class BroadcastService:
    async def create_draft(self, message: Message) -> int:
        async with async_session_maker() as session:
            content_type = message.content_type
            text_content = message.text or message.caption or ""
            media_file_id = None

            if message.photo:
                media_file_id = message.photo[-1].file_id
            elif message.video:
                media_file_id = message.video.file_id

            broadcast = Broadcast(
                content=text_content,
                content_type=content_type,
                media_file_id=media_file_id,
                created_by=message.from_user.id,
                status=BroadcastStatus.DRAFT
            )
            session.add(broadcast)
            await session.commit()
            await session.refresh(broadcast)

            return broadcast.id

    async def update_draft(self, message: Message, broadcast_id: int):
        async with async_session_maker() as session:
            result = await session.execute(
                select(Broadcast).where(Broadcast.id == broadcast_id)
            )
            broadcast = result.scalar_one_or_none()

            if broadcast:
                broadcast.content = message.text or message.caption or ""

                if message.photo:
                    broadcast.media_file_id = message.photo[-1].file_id
                    broadcast.content_type = 'photo'
                elif message.video:
                    broadcast.media_file_id = message.video.file_id
                    broadcast.content_type = 'video'
                else:
                    broadcast.content_type = 'text'

                await session.commit()

    async def list_drafts(self, message: Message, bot: AsyncTeleBot):
        async with async_session_maker() as session:
            result = await session.execute(
                select(Broadcast).where(Broadcast.status != BroadcastStatus.DELETED)
            )
            broadcasts = result.scalars().all()

            if not broadcasts:
                await bot.reply_to(message, "Нет доступных рассылок.")
                return

            text = "📨 Список рассылок:\n\n"
            keyboard = InlineKeyboardMarkup()

            for bc in broadcasts:
                status_emoji = "📝" if bc.status == BroadcastStatus.DRAFT else "✅"
                preview = bc.content[:50] + "..." if len(bc.content) > 50 else bc.content
                text += f"{status_emoji} #{bc.id} - {preview}\n"

                button = InlineKeyboardButton(
                    text=f"#{bc.id} - {bc.status.value}",
                    callback_data=f"broadcast_view_{bc.id}"
                )
                keyboard.add(button)

            await bot.reply_to(message, text, reply_markup=keyboard)

    async def handle_callback(self, callback: CallbackQuery, bot: AsyncTeleBot):
        parts = callback.data.split("_")
        action = parts[1]
        broadcast_id = int(parts[2])

        if action == "view":
            await self._show_broadcast(callback, broadcast_id, bot)
        elif action == "send":
            await self._confirm_send(callback, broadcast_id, bot)
        elif action == "confirmsend":
            await self._send_broadcast(callback, broadcast_id, bot)
        elif action == "edit":
            await self._start_edit(callback, broadcast_id, bot)
        elif action == "delete":
            await self._delete_broadcast(callback, broadcast_id, bot)

    async def _show_broadcast(self, callback: CallbackQuery, broadcast_id: int, bot: AsyncTeleBot):
        async with async_session_maker() as session:
            result = await session.execute(
                select(Broadcast).where(Broadcast.id == broadcast_id)
            )
            broadcast = result.scalar_one_or_none()

            if not broadcast:
                await bot.answer_callback_query(callback.id, "Рассылка не найдена.")
                return

            keyboard = InlineKeyboardMarkup()

            if broadcast.status == BroadcastStatus.DRAFT:
                keyboard.row(
                    InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"broadcast_edit_{broadcast_id}"),
                    InlineKeyboardButton(text="📤 Отправить", callback_data=f"broadcast_send_{broadcast_id}")
                )

            keyboard.add(InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"broadcast_delete_{broadcast_id}"))

            text = f"📨 Рассылка #{broadcast_id}\n"
            text += f"Статус: {broadcast.status.value}\n\n"
            text += broadcast.content

            await bot.edit_message_text(text, callback.message.chat.id, callback.message.message_id, reply_markup=keyboard)

    async def _confirm_send(self, callback: CallbackQuery, broadcast_id: int, bot: AsyncTeleBot):
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton(text="✅ Да, отправить", callback_data=f"broadcast_confirmsend_{broadcast_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"broadcast_view_{broadcast_id}")
        )

        await bot.edit_message_text(
            "⚠️ Вы уверены, что хотите отправить рассылку всем пользователям?",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=keyboard
        )

    async def _send_broadcast(self, callback: CallbackQuery, broadcast_id: int, bot: AsyncTeleBot):
        await bot.edit_message_text("📤 Отправка рассылки...", callback.message.chat.id, callback.message.message_id)

        async with async_session_maker() as session:
            result = await session.execute(
                select(Broadcast).where(Broadcast.id == broadcast_id)
            )
            broadcast = result.scalar_one_or_none()

            if not broadcast or broadcast.status != BroadcastStatus.DRAFT:
                await bot.answer_callback_query(callback.id, "Рассылка недоступна для отправки.")
                return

            users_result = await session.execute(
                select(User).where(User.is_active == True)
            )
            users = users_result.scalars().all()

            sent_count = 0
            failed_count = 0

            for user in users:
                try:
                    if broadcast.content_type == "text":
                        await bot.send_message(user.user_id, broadcast.content)
                    elif broadcast.content_type == "photo":
                        await bot.send_photo(user.user_id, broadcast.media_file_id, caption=broadcast.content)
                    elif broadcast.content_type == "video":
                        await bot.send_video(user.user_id, broadcast.media_file_id, caption=broadcast.content)

                    sent_count += 1
                    await asyncio.sleep(settings.broadcast_delay_ms / 1000)

                except Exception:
                    failed_count += 1
                    user.is_active = False

            broadcast.status = BroadcastStatus.SENT
            broadcast.sent_at = datetime.utcnow()
            broadcast.sent_count = sent_count
            broadcast.failed_count = failed_count

            await session.commit()

        await bot.edit_message_text(
            f"✅ Рассылка завершена!\n\n"
            f"Отправлено: {sent_count}\n"
            f"Не доставлено: {failed_count}",
            callback.message.chat.id,
            callback.message.message_id
        )

    async def _start_edit(self, callback: CallbackQuery, broadcast_id: int, bot: AsyncTeleBot):
        from handlers.broadcast import BroadcastStates
        await bot.set_state(callback.from_user.id, BroadcastStates.waiting_edit, callback.message.chat.id)
        async with bot.retrieve_data(callback.from_user.id, callback.message.chat.id) as data:
            data['edit_broadcast_id'] = broadcast_id
        await bot.send_message(callback.message.chat.id, "Отправьте новое содержимое для рассылки.")

    async def _delete_broadcast(self, callback: CallbackQuery, broadcast_id: int, bot: AsyncTeleBot):
        async with async_session_maker() as session:
            result = await session.execute(
                select(Broadcast).where(Broadcast.id == broadcast_id)
            )
            broadcast = result.scalar_one_or_none()

            if broadcast:
                broadcast.status = BroadcastStatus.DELETED
                await session.commit()

        await bot.edit_message_text("🗑️ Рассылка удалена.", callback.message.chat.id, callback.message.message_id)
