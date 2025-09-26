import asyncio
import time
import random
from datetime import datetime, timedelta
from argent.core.loader import ArgentModule
from telethon.events import NewMessage

class AutoFeaturesModule(ArgentModule):
    __version__ = '1.0.0'
    __author__ = 'github.com/lonly19/Argent-Userbot'
    __category__ = 'utils'

    def __init__(self):
        super().__init__()
        self.description = '🤖 Автоматические функции: авто-ответы, реакции, рассылки'
        self.register_command('autoreply', self.cmd_autoreply, '💬 Настроить авто-ответ')
        self.register_command('autoreact', self.cmd_autoreact, ' Настроить авто-реакции')
        self.register_command('autopm', self.cmd_autopm, '📨 Авто-ответ в ЛС')
        self.register_command('schedule', self.cmd_schedule, '⏰ Запланировать сообщение')
        self.register_command('broadcast', self.cmd_broadcast, '📢 Рассылка сообщений')
        self.register_command('afk', self.cmd_afk, ' Режим AFK')
        self.register_command('autoread', self.cmd_autoread, '👁️ Авто-прочтение')
        self.register_command('autotype', self.cmd_autotype, '⌨️ Авто-печатание')
        self.register_command('autoforward', self.cmd_autoforward, '↗️ Авто-пересылка')
        self.auto_tasks = {}

    async def on_load(self):
        self.client.add_event_handler(self._handle_auto_reply, NewMessage(incoming=True))
        self.client.add_event_handler(self._handle_auto_react, NewMessage)
        asyncio.create_task(self._scheduled_messages_loop())
        self.client.add_event_handler(self._handle_afk, NewMessage(incoming=True))

    async def _handle_auto_reply(self, event):
        auto_replies = self.db.get_config('auto_replies', {})
        for trigger, response in auto_replies.items():
            if trigger.lower() in event.text.lower():
                await asyncio.sleep(random.uniform(1, 3))
                await event.respond(response)
                break

    async def _handle_auto_react(self, event):
        auto_reactions = self.db.get_config('auto_reactions', {})
        if not auto_reactions.get('enabled', False):
            return
        chat_id = event.chat_id
        allowed_chats = auto_reactions.get('chats', [])
        if allowed_chats and chat_id not in allowed_chats:
            return
        chance = auto_reactions.get('chance', 10)
        if random.randint(1, 100) > chance:
            return
        reactions = auto_reactions.get('reactions', ['👍', '❤️', '', '🔥', '⚡'])
        reaction = random.choice(reactions)
        try:
            await asyncio.sleep(random.uniform(2, 5))
            await event.react(reaction)
        except:
            pass

    async def _scheduled_messages_loop(self):
        while True:
            try:
                scheduled = self.db.get_config('scheduled_messages', [])
                current_time = time.time()
                for i, msg in enumerate(scheduled):
                    if msg['time'] <= current_time:
                        try:
                            await self.client.send_message(msg['chat_id'], msg['text'])
                            scheduled.pop(i)
                            self.db.set_config('scheduled_messages', scheduled)
                        except:
                            pass
                await asyncio.sleep(60)
            except:
                await asyncio.sleep(60)

    async def _handle_afk(self, event):
        afk_data = self.db.get_config('afk_mode')
        if not afk_data or not afk_data.get('enabled'):
            return
        if event.sender_id == (await self.client.get_me()).id:
            return
        last_responses = afk_data.get('last_responses', {})
        user_id = str(event.sender_id)
        if user_id in last_responses:
            if time.time() - last_responses[user_id] < 300:
                return
        afk_message = afk_data.get('message', ' Я сейчас AFK')
        afk_since = afk_data.get('since', time.time())
        duration = self.utils.format_duration(time.time() - afk_since)
        full_message = f'{afk_message}\n\n⏰ AFK уже: {duration}'
        try:
            await event.respond(full_message)
            last_responses[user_id] = time.time()
            afk_data['last_responses'] = last_responses
            self.db.set_config('afk_mode', afk_data)
        except:
            pass

    async def cmd_autoreply(self, event, args):
        if not args:
            auto_replies = self.db.get_config('auto_replies', {})
            if not auto_replies:
                await event.edit('💬 <b>Авто-ответы не настроены</b>')
                return
            reply_text = '💬 <b>Настроенные авто-ответы:</b>\n\n'
            for trigger, response in auto_replies.items():
                reply_text += f'<b>Триггер:</b> <code>{trigger}</code>\n<b>Ответ:</b> {response}\n\n'
            reply_text += '<b>🔧 Управление:</b>\n'
            reply_text += '• `.autoreply add <триггер> | <ответ>` - добавить\n'
            reply_text += '• `.autoreply remove <триггер>` - удалить\n'
            reply_text += '• <code>.autoreply clear</code> - очистить все'
            await event.edit(reply_text)
            return
        action = args[0].lower()
        if action == 'add':
            if len(args) < 2 or '|' not in ' '.join(args[1:]):
                await event.edit('❌ **Использование:** `.autoreply add <триггер> | <ответ>`')
                return
            content = ' '.join(args[1:])
            trigger, response = content.split('|', 1)
            trigger = trigger.strip()
            response = response.strip()
            auto_replies = self.db.get_config('auto_replies', {})
            auto_replies[trigger] = response
            self.db.set_config('auto_replies', auto_replies)
            await event.edit(f'\n\n✅ <b>Авто-ответ добавлен</b>\n\n<b>🎯 Триггер:</b> <code>{trigger}</code>\n\n<b>💬 Ответ:</b> {response}\n\n<b>⚛️ Теперь бот будет отвечать на сообщения содержащие этот триггер</b>\n\n            ')
        elif action == 'remove':
            if len(args) < 2:
                await event.edit('❌ **Использование:** `.autoreply remove <триггер>`')
                return
            trigger = ' '.join(args[1:])
            auto_replies = self.db.get_config('auto_replies', {})
            if trigger in auto_replies:
                del auto_replies[trigger]
                self.db.set_config('auto_replies', auto_replies)
                await event.edit(f'✅ <b>Авто-ответ <code>{trigger}</code> удален</b>')
            else:
                await event.edit(f'❌ <b>Авто-ответ <code>{trigger}</code> не найден</b>')
        elif action == 'clear':
            self.db.set_config('auto_replies', {})
            await event.edit('✅ <b>Все авто-ответы очищены</b>')

    async def cmd_autoreact(self, event, args):
        if not args:
            auto_reactions = self.db.get_config('auto_reactions', {})
            status = '✅ Включены' if auto_reactions.get('enabled') else '❌ Отключены'
            chance = auto_reactions.get('chance', 10)
            reactions = auto_reactions.get('reactions', ['👍', '❤️', ''])
            await event.edit(f"\n\n **Настройки авто-реакций**\n\n**📊 Статус:** {status}\n\n**🎲 Вероятность:** {chance}%\n\n** Реакции:** {' '.join(reactions)}\n\n**🔧 Команды:**\n\n• `.autoreact on/off` - включить/выключить\n\n• `.autoreact chance <число>` - установить вероятность\n\n• `.autoreact reactions <эмодзи>` - установить реакции\n\n            ")
            return
        action = args[0].lower()
        if action in ['on', 'enable']:
            auto_reactions = self.db.get_config('auto_reactions', {})
            auto_reactions['enabled'] = True
            self.db.set_config('auto_reactions', auto_reactions)
            await event.edit('✅ <b>Авто-реакции включены</b>')
        elif action in ['off', 'disable']:
            auto_reactions = self.db.get_config('auto_reactions', {})
            auto_reactions['enabled'] = False
            self.db.set_config('auto_reactions', auto_reactions)
            await event.edit('❌ <b>Авто-реакции отключены</b>')
        elif action == 'chance':
            if len(args) < 2:
                await event.edit('❌ **Использование:** `.autoreact chance <число>`')
                return
            try:
                chance = int(args[1])
                if not 1 <= chance <= 100:
                    await event.edit('❌ <b>Вероятность должна быть от 1 до 100</b>')
                    return
                auto_reactions = self.db.get_config('auto_reactions', {})
                auto_reactions['chance'] = chance
                self.db.set_config('auto_reactions', auto_reactions)
                await event.edit(f'✅ <b>Вероятность авто-реакций установлена: {chance}%</b>')
            except ValueError:
                await event.edit('❌ <b>Укажите корректное число</b>')
        elif action == 'reactions':
            if len(args) < 2:
                await event.edit('❌ **Использование:** `.autoreact reactions <эмодзи>`')
                return
            reactions = args[1:]
            auto_reactions = self.db.get_config('auto_reactions', {})
            auto_reactions['reactions'] = reactions
            self.db.set_config('auto_reactions', auto_reactions)
            await event.edit(f"✅ <b>Реакции обновлены:</b> {' '.join(reactions)}")

    async def cmd_autopm(self, event, args):
        if not args:
            autopm = self.db.get_config('autopm', {})
            if not autopm.get('enabled'):
                await event.edit('📨 <b>Авто-ответ в ЛС отключен</b>')
                return
            message = autopm.get('message', 'Привет! Я сейчас не могу ответить.')
            await event.edit(f'\n\n📨 **Авто-ответ в ЛС**\n\n**📝 Сообщение:**\n\n{message}\n\n**🔧 Команды:**\n\n• `.autopm on` - включить\n\n• `.autopm off` - выключить\n\n• `.autopm set <сообщение>` - установить сообщение\n\n            ')
            return
        action = args[0].lower()
        if action == 'on':
            autopm = self.db.get_config('autopm', {})
            autopm['enabled'] = True
            if 'message' not in autopm:
                autopm['message'] = '🤖 Привет! Я сейчас не могу ответить, но обязательно прочитаю ваше сообщение.'
            self.db.set_config('autopm', autopm)
            await event.edit('✅ <b>Авто-ответ в ЛС включен</b>')
        elif action == 'off':
            autopm = self.db.get_config('autopm', {})
            autopm['enabled'] = False
            self.db.set_config('autopm', autopm)
            await event.edit('❌ <b>Авто-ответ в ЛС отключен</b>')
        elif action == 'set':
            if len(args) < 2:
                await event.edit('❌ **Использование:** `.autopm set <сообщение>`')
                return
            message = ' '.join(args[1:])
            autopm = self.db.get_config('autopm', {})
            autopm['message'] = message
            self.db.set_config('autopm', autopm)
            await event.edit(f'✅ <b>Сообщение авто-ответа обновлено:</b>\n\n{message}')

    async def cmd_schedule(self, event, args):
        if not args:
            scheduled = self.db.get_config('scheduled_messages', [])
            if not scheduled:
                await event.edit('⏰ <b>Запланированных сообщений нет</b>')
                return
            schedule_text = '⏰ <b>Запланированные сообщения:</b>\n\n'
            for i, msg in enumerate(scheduled, 1):
                send_time = datetime.fromtimestamp(msg['time']).strftime('%Y-%m-%d %H:%M')
                schedule_text += f"<b>{i}.</b> {send_time}\n📝 {msg['text'][:50]}...\n\n"
            await event.edit(schedule_text)
            return
        if len(args) < 3:
            await event.edit('❌ **Использование:** `.schedule <время> <чат_id> <сообщение>`\n\n**Пример:** `.schedule 2h @username Привет!`')
            return
        time_str = args[0]
        chat_id = args[1]
        message = ' '.join(args[2:])
        if time_str.endswith(('m', 'h', 'd')):
            duration = self.utils.parse_duration(time_str)
            if not duration:
                await event.edit('❌ <b>Неверный формат времени</b>')
                return
            send_time = time.time() + duration
        else:
            await event.edit('❌ <b>спользуйте формат времени: 30m, 2h, 1d</b>')
            return
        try:
            if chat_id.startswith('@'):
                entity = await self.client.get_entity(chat_id)
                chat_id = entity.id
            else:
                chat_id = int(chat_id)
        except:
            await event.edit('❌ <b>Не удалось найти чат</b>')
            return
        scheduled = self.db.get_config('scheduled_messages', [])
        scheduled.append({'time': send_time, 'chat_id': chat_id, 'text': message})
        self.db.set_config('scheduled_messages', scheduled)
        send_date = datetime.fromtimestamp(send_time).strftime('%Y-%m-%d %H:%M:%S')
        await event.edit(f'\n\n⏰ <b>Сообщение запланировано</b>\n\n<b>📅 Время отправки:</b> {send_date}\n\n<b>💬 Чат:</b> <code>{chat_id}</code>\n\n<b>📝 Сообщение:</b> {message}\n\n<b>⚛️ Сообщение будет отправлено автоматически</b>\n\n        ')

    async def cmd_broadcast(self, event, args):
        if not args:
            await event.edit('❌ **Использование:** `.broadcast <сообщение>`')
            return
        message = ' '.join(args)
        await event.edit('📢 <b>Начинаю рассылку...</b>')
        dialogs = await self.client.get_dialogs()
        sent = 0
        failed = 0
        for dialog in dialogs:
            try:
                if dialog.is_user and (not dialog.entity.bot):
                    await self.client.send_message(dialog.entity, message)
                    sent += 1
                    await asyncio.sleep(1)
            except:
                failed += 1
        await event.edit(f'\n\n📢 <b>Рассылка завершена</b>\n\n<b>✅ Отправлено:</b> {sent}\n\n<b>❌ Ошибок:</b> {failed}\n\n<b>📝 Сообщение:</b> {message[:100]}...\n\n<b>⚛️ Рассылка выполнена успешно</b>\n\n        ')

    async def cmd_afk(self, event, args):
        if not args:
            afk_data = self.db.get_config('afk_mode')
            if not afk_data or not afk_data.get('enabled'):
                await event.edit(' <b>AFK режим отключен</b>')
                return
            since = afk_data.get('since', time.time())
            duration = self.utils.format_duration(time.time() - since)
            message = afk_data.get('message', 'Я сейчас AFK')
            await event.edit(f'\n\n **AFK режим активен**\n\n**📝 Сообщение:** {message}\n\n**⏰ AFK уже:** {duration}\n\n**🔧 Команды:**\n\n• `.afk off` - отключить\n\n• `.afk <сообщение>` - изменить сообщение\n\n            ')
            return
        if args[0].lower() == 'off':
            self.db.set_config('afk_mode', {'enabled': False})
            await event.edit('✅ <b>AFK режим отключен</b>')
            return
        message = ' '.join(args)
        afk_data = {'enabled': True, 'message': message, 'since': time.time(), 'last_responses': {}}
        self.db.set_config('afk_mode', afk_data)
        await event.edit(f"\n\n <b>AFK режим включен</b>\n\n<b>📝 Сообщение:</b> {message}\n\n<b>⏰ Начало:</b> {datetime.now().strftime('%H:%M:%S')}\n\n<b>⚛️ Буду автоматически отвечать на сообщения</b>\n\n        ")

    async def cmd_autoread(self, event, args):
        if not args:
            autoread = self.db.get_config('autoread', False)
            status = '✅ Включено' if autoread else '❌ Отключено'
            await event.edit(f'\n\n👁️ <b>Авто-прочтение сообщений</b>\n\n<b>📊 Статус:</b> {status}\n\n<b>🔧 Команды:</b>\n\n• <code>.autoread on</code> - включить\n\n• <code>.autoread off</code> - отключить\n\n<b>⚛️ Автоматически помечает все входящие сообщения как прочитанные</b>\n\n            ')
            return
        action = args[0].lower()
        if action == 'on':
            self.db.set_config('autoread', True)
            await event.edit('✅ <b>Авто-прочтение включено</b>')
        elif action == 'off':
            self.db.set_config('autoread', False)
            await event.edit('❌ <b>Авто-прочтение отключено</b>')

    async def cmd_autotype(self, event, args):
        if not args:
            autotype = self.db.get_config('autotype', {})
            if not autotype.get('enabled'):
                await event.edit('⌨️ <b>Авто-печатание отключено</b>')
                return
            duration = autotype.get('duration', 5)
            await event.edit(f'\n\n⌨️ **Авто-печатание**\n\n**📊 Статус:** ✅ Включено\n\n**⏰ Длительность:** {duration} секунд\n\n**🔧 Команды:**\n\n• `.autotype on <секунды>` - включить\n\n• `.autotype off` - отключить\n\n**⚛️ Показывает статус "печатает" перед отправкой сообщений**\n\n            ')
            return
        action = args[0].lower()
        if action == 'on':
            duration = 5
            if len(args) > 1:
                try:
                    duration = int(args[1])
                    if not 1 <= duration <= 30:
                        duration = 5
                except:
                    duration = 5
            autotype = {'enabled': True, 'duration': duration}
            self.db.set_config('autotype', autotype)
            await event.edit(f'✅ <b>Авто-печатание включено на {duration} секунд</b>')
        elif action == 'off':
            self.db.set_config('autotype', {'enabled': False})
            await event.edit('❌ <b>Авто-печатание отключено</b>')

    async def cmd_autoforward(self, event, args):
        if not args:
            autoforward = self.db.get_config('autoforward', {})
            if not autoforward:
                await event.edit('↗️ <b>Авто-пересылка не настроена</b>')
                return
            forward_text = '↗️ <b>Настройки авто-пересылки:</b>\n\n'
            for source, target in autoforward.items():
                forward_text += f'<b>з:</b> <code>{source}</code>\n<b>В:</b> <code>{target}</code>\n\n'
            forward_text += '<b>🔧 Команды:</b>\n'
            forward_text += '• `.autoforward add <источник> <цель>` - добавить\n'
            forward_text += '• `.autoforward remove <источник>` - удалить'
            await event.edit(forward_text)
            return
        action = args[0].lower()
        if action == 'add':
            if len(args) < 3:
                await event.edit('❌ **Использование:** `.autoforward add <источник> <цель>`')
                return
            source = args[1]
            target = args[2]
            try:
                if source.startswith('@'):
                    source_entity = await self.client.get_entity(source)
                    source_id = source_entity.id
                else:
                    source_id = int(source)
                if target.startswith('@'):
                    target_entity = await self.client.get_entity(target)
                    target_id = target_entity.id
                else:
                    target_id = int(target)
            except:
                await event.edit('❌ <b>Не удалось найти один из чатов</b>')
                return
            autoforward = self.db.get_config('autoforward', {})
            autoforward[str(source_id)] = target_id
            self.db.set_config('autoforward', autoforward)
            await event.edit(f'\n\n✅ <b>Авто-пересылка настроена</b>\n\n<b>📥 сточник:</b> <code>{source_id}</code>\n\n<b>📤 Цель:</b> <code>{target_id}</code>\n\n<b>⚛️ Все сообщения из источника будут пересылаться в цель</b>\n\n            ')
        elif action == 'remove':
            if len(args) < 2:
                await event.edit('❌ **Использование:** `.autoforward remove <источник>`')
                return
            source = args[1]
            try:
                if source.startswith('@'):
                    source_entity = await self.client.get_entity(source)
                    source_id = str(source_entity.id)
                else:
                    source_id = source
            except:
                source_id = source
            autoforward = self.db.get_config('autoforward', {})
            if source_id in autoforward:
                del autoforward[source_id]
                self.db.set_config('autoforward', autoforward)
                await event.edit(f'✅ <b>Авто-пересылка из <code>{source_id}</code> удалена</b>')
            else:
                await event.edit(f'❌ <b>Авто-пересылка из <code>{source_id}</code> не найдена</b>')
module = AutoFeaturesModule()
