import asyncio
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
from argent.core.loader import ArgentModule

class AdminToolsModule(ArgentModule):
    __version__ = '1.0.0'
    __author__ = 'github.com/lonly19/Argent-Userbot'
    __category__ = 'admin'

    def __init__(self):
        super().__init__()
        self.description = '👑 нструменты администрирования и модерации чатов'
        self.register_command('ban', self.cmd_ban, '🚫 Забанить пользователя')
        self.register_command('unban', self.cmd_unban, '✅ Разбанить пользователя')
        self.register_command('mute', self.cmd_mute, '🔇 Замутить пользователя')
        self.register_command('unmute', self.cmd_unmute, '🔊 Размутить пользователя')
        self.register_command('kick', self.cmd_kick, '👢 Кикнуть пользователя')
        self.register_command('purge', self.cmd_purge, '🧹 Очистить сообщения')
        self.register_command('chatinfo', self.cmd_chatinfo, 'ℹ️ нформация о чате')

    async def _get_user_from_message(self, event):
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            return reply_msg.sender_id
        return None

    async def cmd_ban(self, event, args):
        user_id = await self._get_user_from_message(event)
        if not user_id:
            await event.edit('❌ <b>Ответьте на сообщение пользователя для бана</b>')
            return
        try:
            ban_rights = ChatBannedRights(until_date=None, view_messages=True, send_messages=True, send_media=True, send_stickers=True, send_gifs=True, send_games=True, send_inline=True, embed_links=True)
            await self.client(EditBannedRequest(channel=event.chat_id, participant=user_id, banned_rights=ban_rights))
            user_info = await self.utils.get_user_info(user_id)
            username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
            await event.edit(f'\n\n🚫 <b>Пользователь забанен</b>\n\n<b>👤 Пользователь:</b> @{username} (<code>{user_id}</code>)\n\n<b>⚛️ Статус:</b> Перманентный бан\n\n<b>🔬 Администратор:</b> Вы\n\n')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка бана:</b> <code>{str(e)}</code>')

    async def cmd_unban(self, event, args):
        user_id = await self._get_user_from_message(event)
        if not user_id:
            await event.edit('❌ <b>Ответьте на сообщение пользователя для разбана</b>')
            return
        try:
            unban_rights = ChatBannedRights(until_date=None, view_messages=False, send_messages=False, send_media=False, send_stickers=False, send_gifs=False, send_games=False, send_inline=False, embed_links=False)
            await self.client(EditBannedRequest(channel=event.chat_id, participant=user_id, banned_rights=unban_rights))
            user_info = await self.utils.get_user_info(user_id)
            username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
            await event.edit(f'\n\n✅ <b>Пользователь разбанен</b>\n\n<b>👤 Пользователь:</b> @{username} (<code>{user_id}</code>)\n\n<b>⚛️ Статус:</b> Бан снят\n\n<b>🔬 Администратор:</b> Вы\n\n')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка разбана:</b> <code>{str(e)}</code>')

    async def cmd_mute(self, event, args):
        user_id = await self._get_user_from_message(event)
        if not user_id:
            await event.edit('❌ <b>Ответьте на сообщение пользователя для мута</b>')
            return
        duration = None
        if args:
            duration_str = args[0]
            duration = self.utils.parse_duration(duration_str)
        try:
            mute_rights = ChatBannedRights(until_date=int(time.time() + duration) if duration else None, send_messages=True, send_media=True, send_stickers=True, send_gifs=True, send_games=True, send_inline=True, embed_links=True)
            await self.client(EditBannedRequest(channel=event.chat_id, participant=user_id, banned_rights=mute_rights))
            user_info = await self.utils.get_user_info(user_id)
            username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
            duration_text = f'на {self.utils.format_duration(duration)}' if duration else 'навсегда'
            await event.edit(f'\n\n🔇 <b>Пользователь замучен</b>\n\n<b>👤 Пользователь:</b> @{username} (<code>{user_id}</code>)\n\n<b>⏰ Длительность:</b> {duration_text}\n\n<b>🔬 Администратор:</b> Вы\n\n')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка мута:</b> <code>{str(e)}</code>')

    async def cmd_unmute(self, event, args):
        user_id = await self._get_user_from_message(event)
        if not user_id:
            await event.edit('❌ <b>Ответьте на сообщение пользователя для размута</b>')
            return
        try:
            unmute_rights = ChatBannedRights(until_date=None, send_messages=False, send_media=False, send_stickers=False, send_gifs=False, send_games=False, send_inline=False, embed_links=False)
            await self.client(EditBannedRequest(channel=event.chat_id, participant=user_id, banned_rights=unmute_rights))
            user_info = await self.utils.get_user_info(user_id)
            username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
            await event.edit(f'\n\n🔊 <b>Пользователь размучен</b>\n\n<b>👤 Пользователь:</b> @{username} (<code>{user_id}</code>)\n\n<b>⚛️ Статус:</b> Мут снят\n\n<b>🔬 Администратор:</b> Вы\n\n')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка размута:</b> <code>{str(e)}</code>')

    async def cmd_kick(self, event, args):
        user_id = await self._get_user_from_message(event)
        if not user_id:
            await event.edit('❌ <b>Ответьте на сообщение пользователя для кика</b>')
            return
        try:
            await self.client.kick_participant(event.chat_id, user_id)
            user_info = await self.utils.get_user_info(user_id)
            username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
            await event.edit(f'\n\n👢 <b>Пользователь кикнут</b>\n\n<b>👤 Пользователь:</b> @{username} (<code>{user_id}</code>)\n\n<b>⚛️ Статус:</b> сключен из чата\n\n<b>🔬 Администратор:</b> Вы\n\n')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка кика:</b> <code>{str(e)}</code>')

    async def cmd_purge(self, event, args):
        if not event.is_reply:
            await event.edit('❌ <b>Ответьте на сообщение, с которого начать очистку</b>')
            return
        reply_msg = await event.get_reply_message()
        try:
            messages_to_delete = []
            async for message in self.client.iter_messages(event.chat_id, min_id=reply_msg.id - 1, reverse=True):
                messages_to_delete.append(message.id)
                if len(messages_to_delete) >= 100:
                    break
            if not messages_to_delete:
                await event.edit('❌ <b>Нет сообщений для удаления</b>')
                return
            await self.client.delete_messages(event.chat_id, messages_to_delete)
            await event.edit(f'\n\n🧹 <b>Очистка завершена</b>\n\n<b>🗑️ Удалено сообщений:</b> <code>{len(messages_to_delete)}</code>\n\n<b>⚛️ Диапазон:</b> от ID <code>{reply_msg.id}</code> до текущего\n\n<b>🔬 Администратор:</b> Вы\n\n')
            await asyncio.sleep(3)
            await event.delete()
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка очистки:</b> <code>{str(e)}</code>')

    async def cmd_chatinfo(self, event, args):
        try:
            chat_info = await self.utils.get_chat_info(event.chat_id)
            if not chat_info:
                await event.edit('❌ <b>Не удалось получить информацию о чате</b>')
                return
            chat = await self.client.get_entity(event.chat_id)
            info_text = f"\n\nℹ️ <b>нформация о чате</b>\n\n<b>📝 Название:</b> {chat_info.get('title', 'N/A')}\n\n<b>🆔 ID:</b> <code>{chat_info['id']}</code>\n\n<b>👥 Участников:</b> <code>{chat_info.get('participants_count', 'N/A')}</code>\n\n<b>🔗 Username:</b> @{chat_info.get('username', 'отсутствует')}\n\n<b>⚛️ Тип:</b> <code>{chat_info['type']}</code>\n\n<b>🔬 Дополнительно:</b>\n\n• <b>Описание:</b> {getattr(chat, 'about', 'Отсутствует')[:100]}...\n\n• <b>Создан:</b> {getattr(chat, 'date', 'N/A')}\n\n• <b>Админ-права:</b> {('✅' if getattr(chat, 'admin_rights', None) else '❌')}\n\n"
            await event.edit(info_text)
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка получения информации:</b> <code>{str(e)}</code>')
module = AdminToolsModule()
