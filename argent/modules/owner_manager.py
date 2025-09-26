import asyncio
import time
from datetime import datetime, timedelta
from argent.core.loader import ArgentModule

class OwnerManagerModule(ArgentModule):
    __version__ = '1.0.0'
    __author__ = 'github.com/lonly19/Argent-Userbot'
    __category__ = 'admin'

    def __init__(self):
        super().__init__()
        self.description = '👑 Расширенное управление овнерами и правами доступа'
        self.register_command('giveowner', self.cmd_give_owner, '👑 Выдать овнерку')
        self.register_command('removeowner', self.cmd_remove_owner, '❌ Забрать овнерку')
        self.register_command('ownerlist', self.cmd_owner_list, '📋 Список овнеров')
        self.register_command('tempowner', self.cmd_temp_owner, '⏰ Временная овнерка')
        self.register_command('ownerinfo', self.cmd_owner_info, 'ℹ️ нформация об овнере')
        self.register_command('permissions', self.cmd_permissions, '🔐 Управление правами')
        self.register_command('sudo', self.cmd_sudo, '🔧 Выполнить от имени овнера')
        self.register_command('ownerlog', self.cmd_owner_log, '📊 Лог действий овнеров')

    async def on_load(self):
        me = await self.client.get_me()
        owners = self.db.get_config('owners', [])
        if me.id not in owners:
            owners.append(me.id)
            self.db.set_config('owners', owners)
        if not self.db.get_config('owner_permissions'):
            self.db.set_config('owner_permissions', {})
        if not self.db.get_config('owner_logs'):
            self.db.set_config('owner_logs', [])

    def _is_owner(self, user_id: int) -> bool:
        owners = self.db.get_config('owners', [])
        return user_id in owners

    def _is_main_owner(self, user_id: int) -> bool:
        owners = self.db.get_config('owners', [])
        return len(owners) > 0 and owners[0] == user_id

    def _has_permission(self, user_id: int, permission: str) -> bool:
        if self._is_main_owner(user_id):
            return True
        permissions = self.db.get_config('owner_permissions', {})
        user_perms = permissions.get(str(user_id), [])
        return permission in user_perms or 'all' in user_perms

    def _log_action(self, user_id: int, action: str, target: str=None):
        logs = self.db.get_config('owner_logs', [])
        log_entry = {'user_id': user_id, 'action': action, 'target': target, 'timestamp': time.time(), 'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        logs.append(log_entry)
        if len(logs) > 100:
            logs = logs[-100:]
        self.db.set_config('owner_logs', logs)

    async def cmd_give_owner(self, event, args):
        if not self._is_owner(event.sender_id):
            await event.edit('❌ <b>Доступ запрещен:</b> Только овнеры могут выдавать овнерку')
            return
        if not event.is_reply:
            await event.edit('❌ <b>Ответьте на сообщение пользователя для выдачи овнерки</b>')
            return
        reply_msg = await event.get_reply_message()
        user_id = reply_msg.sender_id
        owners = self.db.get_config('owners', [])
        if user_id in owners:
            await event.edit('⚠️ <b>Пользователь уже является овнером</b>')
            return
        owners.append(user_id)
        self.db.set_config('owners', owners)
        permissions = self.db.get_config('owner_permissions', {})
        permissions[str(user_id)] = ['modules', 'system', 'admin']
        self.db.set_config('owner_permissions', permissions)
        self._log_action(event.sender_id, 'give_owner', str(user_id))
        user_info = await self.utils.get_user_info(user_id)
        username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
        first_name = user_info.get('first_name', 'Unknown') if user_info else 'Unknown'
        await event.edit(f'\n\n👑 <b>Овнерка выдана</b>\n\n<b>👤 Пользователь:</b> {first_name} (@{username})\n\n<b>🆔 ID:</b> <code>{user_id}</code>\n\n<b>⚛️ Статус:</b> Полный доступ активирован\n\n<b>🔐 Права:</b> Модули, Система, Админ\n\n<b>🔬 Выдал:</b> Вы\n\n<b>📊 Всего овнеров:</b> <code>{len(owners)}</code>\n\n<b>🤖 Пользователь получит уведомление в inline боте</b>\n\n        ')
        try:
            if hasattr(self, 'client') and hasattr(self.client, 'inline_bot'):
                await self.client.inline_bot.bot.send_message(user_id, f'\n\n🎉 <b>Вам выдана овнерка Argent UserBot!</b>\n\n<b>⚗️ Теперь у вас есть доступ к:</b>\n\n• 🔧 Управление модулями\n\n• ⚙️ Системные настройки\n\n• 👑 Административные функции\n\n<b>🔬 спользуйте команды в чатах или этот бот для управления</b>\n\n                    ')
        except:
            pass

    async def cmd_remove_owner(self, event, args):
        if not self._is_owner(event.sender_id):
            await event.edit('❌ <b>Доступ запрещен:</b> Только овнеры могут забирать овнерку')
            return
        if not event.is_reply:
            await event.edit('❌ <b>Ответьте на сообщение пользователя для удаления овнерки</b>')
            return
        reply_msg = await event.get_reply_message()
        user_id = reply_msg.sender_id
        owners = self.db.get_config('owners', [])
        if self._is_main_owner(user_id):
            await event.edit('❌ <b>Нельзя удалить главного овнера</b>')
            return
        if user_id == event.sender_id and (not self._is_main_owner(event.sender_id)):
            await event.edit('❌ <b>Вы не можете удалить себя</b>')
            return
        if user_id not in owners:
            await event.edit('⚠️ <b>Пользователь не является овнером</b>')
            return
        owners.remove(user_id)
        self.db.set_config('owners', owners)
        permissions = self.db.get_config('owner_permissions', {})
        permissions.pop(str(user_id), None)
        self.db.set_config('owner_permissions', permissions)
        self._log_action(event.sender_id, 'remove_owner', str(user_id))
        user_info = await self.utils.get_user_info(user_id)
        username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
        first_name = user_info.get('first_name', 'Unknown') if user_info else 'Unknown'
        await event.edit(f'\n\n❌ <b>Овнерка отозвана</b>\n\n<b>👤 Пользователь:</b> {first_name} (@{username})\n\n<b>🆔 ID:</b> <code>{user_id}</code>\n\n<b>⚛️ Статус:</b> Доступ отозван\n\n<b>🔬 Удалил:</b> Вы\n\n<b>📊 Осталось овнеров:</b> <code>{len(owners)}</code>\n\n        ')

    async def cmd_owner_list(self, event, args):
        owners = self.db.get_config('owners', [])
        permissions = self.db.get_config('owner_permissions', {})
        if not owners:
            await event.edit('👥 <b>Список овнеров пуст</b>')
            return
        owners_text = '👑 <b>Список овнеров системы</b>\n\n'
        for i, owner_id in enumerate(owners, 1):
            try:
                user_info = await self.utils.get_user_info(owner_id)
                if user_info:
                    username = user_info.get('username', 'Unknown')
                    first_name = user_info.get('first_name', 'Unknown')
                else:
                    username = 'Unknown'
                    first_name = 'Unknown'
                user_perms = permissions.get(str(owner_id), [])
                perm_text = ', '.join(user_perms) if user_perms else 'Базовые'
                status = '🔱 Главный' if i == 1 else '👑 Овнер'
                owners_text += f'\n\n<b>{i}.</b> {first_name} (@{username})\n\n• <b>ID:</b> <code>{owner_id}</code>\n\n• <b>Статус:</b> {status}\n\n• <b>Права:</b> {perm_text}\n\n'
            except Exception as e:
                owners_text += f'<b>{i}.</b> Unknown User (<code>{owner_id}</code>)\n\n'
        owners_text += f'<b>🔬 Всего овнеров:</b> <code>{len(owners)}</code>'
        await event.edit(owners_text)

    async def cmd_temp_owner(self, event, args):
        if not self._is_owner(event.sender_id):
            await event.edit('❌ <b>Доступ запрещен:</b> Только овнеры могут выдавать временную овнерку')
            return
        if not event.is_reply or not args:
            await event.edit('❌ <b>Использование:</b> Ответьте на сообщение и укажите время (например: 1h, 30m, 2d)')
            return
        reply_msg = await event.get_reply_message()
        user_id = reply_msg.sender_id
        duration_str = args[0]
        duration = self.utils.parse_duration(duration_str)
        if not duration:
            await event.edit('❌ <b>Неверный формат времени</b>\n\nПримеры: 1h, 30m, 2d, 1w')
            return
        owners = self.db.get_config('owners', [])
        if user_id in owners:
            await event.edit('⚠️ <b>Пользователь уже является овнером</b>')
            return
        temp_owners = self.db.get_config('temp_owners', {})
        expire_time = time.time() + duration
        temp_owners[str(user_id)] = {'expire_time': expire_time, 'granted_by': event.sender_id, 'granted_at': time.time()}
        self.db.set_config('temp_owners', temp_owners)
        owners.append(user_id)
        self.db.set_config('owners', owners)
        permissions = self.db.get_config('owner_permissions', {})
        permissions[str(user_id)] = ['modules']
        self.db.set_config('owner_permissions', permissions)
        self._log_action(event.sender_id, 'temp_owner', f'{user_id}:{duration_str}')
        asyncio.create_task(self._remove_temp_owner_after(user_id, duration))
        user_info = await self.utils.get_user_info(user_id)
        username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
        first_name = user_info.get('first_name', 'Unknown') if user_info else 'Unknown'
        expire_date = datetime.fromtimestamp(expire_time).strftime('%Y-%m-%d %H:%M:%S')
        await event.edit(f'\n\n⏰ <b>Временная овнерка выдана</b>\n\n<b>👤 Пользователь:</b> {first_name} (@{username})\n\n<b>🆔 ID:</b> <code>{user_id}</code>\n\n<b>⏱️ Длительность:</b> {self.utils.format_duration(duration)}\n\n<b>📅 стекает:</b> {expire_date}\n\n<b>🔐 Права:</b> Только модули\n\n<b>🔬 Выдал:</b> Вы\n\n<b>⚛️ Доступ будет автоматически отозван</b>\n\n        ')

    async def _remove_temp_owner_after(self, user_id: int, duration: int):
        await asyncio.sleep(duration)
        owners = self.db.get_config('owners', [])
        if user_id in owners:
            owners.remove(user_id)
            self.db.set_config('owners', owners)
        permissions = self.db.get_config('owner_permissions', {})
        permissions.pop(str(user_id), None)
        self.db.set_config('owner_permissions', permissions)
        temp_owners = self.db.get_config('temp_owners', {})
        temp_owners.pop(str(user_id), None)
        self.db.set_config('temp_owners', temp_owners)
        try:
            await self.client.send_message(user_id, '⏰ <b>Временная овнерка истекла</b>\n\n🔒 Ваш доступ к Argent UserBot отозван')
        except:
            pass

    async def cmd_owner_info(self, event, args):
        if not event.is_reply:
            await event.edit('❌ <b>Ответьте на сообщение пользователя</b>')
            return
        reply_msg = await event.get_reply_message()
        user_id = reply_msg.sender_id
        owners = self.db.get_config('owners', [])
        if user_id not in owners:
            await event.edit('❌ <b>Пользователь не является овнером</b>')
            return
        user_info = await self.utils.get_user_info(user_id)
        username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
        first_name = user_info.get('first_name', 'Unknown') if user_info else 'Unknown'
        permissions = self.db.get_config('owner_permissions', {})
        user_perms = permissions.get(str(user_id), [])
        temp_owners = self.db.get_config('temp_owners', {})
        is_temp = str(user_id) in temp_owners
        logs = self.db.get_config('owner_logs', [])
        user_logs = [log for log in logs if log['user_id'] == user_id]
        info_text = f"\n\nℹ️ <b>нформация об овнере</b>\n\n<b>👤 Пользователь:</b> {first_name} (@{username})\n\n<b>🆔 ID:</b> <code>{user_id}</code>\n\n<b>👑 Статус:</b> {('🔱 Главный овнер' if self._is_main_owner(user_id) else '👑 Овнер')}\n\n<b>⏰ Тип:</b> {('Временный' if is_temp else 'Постоянный')}\n\n<b>🔐 Права доступа:</b>\n\n{(chr(10).join([f'• {perm}' for perm in user_perms]) if user_perms else '• Базовые права')}\n\n<b>📊 Статистика:</b>\n\n• <b>Действий выполнено:</b> {len(user_logs)}\n\n• <b>Последняя активность:</b> {(user_logs[-1]['date'] if user_logs else 'Нет данных')}\n\n        "
        if is_temp:
            temp_info = temp_owners[str(user_id)]
            expire_time = temp_info['expire_time']
            remaining = expire_time - time.time()
            if remaining > 0:
                info_text += f'\n<b>⏰ Остается времени:</b> {self.utils.format_duration(remaining)}'
            else:
                info_text += '\n<b>⏰ Время истекло</b> (ожидает удаления)'
        await event.edit(info_text)

    async def cmd_permissions(self, event, args):
        if not self._is_main_owner(event.sender_id):
            await event.edit('❌ <b>Доступ запрещен:</b> Только главный овнер может управлять правами')
            return
        if not args:
            await event.edit('\n\n🔐 **Управление правами доступа**\n\n**📋 Доступные права:**\n\n• `all` - все права\n\n• `modules` - управление модулями\n\n• `system` - системные настройки\n\n• `admin` - административные функции\n\n• `owner` - управление овнерами\n\n**🔧 Команды:**\n\n• `.permissions list` - список прав всех овнеров\n\n• `.permissions <user_id> <права>` - установить права\n\n• `.permissions <user_id> remove <право>` - удалить право\n\n**💡 Пример:** `.permissions 123456789 modules system`\n\n            ')
            return
        if args[0] == 'list':
            permissions = self.db.get_config('owner_permissions', {})
            perm_text = '🔐 <b>Права доступа овнеров</b>\n\n'
            for user_id, perms in permissions.items():
                try:
                    user_info = await self.utils.get_user_info(int(user_id))
                    username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
                    perm_text += f'<b>@{username}</b> (<code>{user_id}</code>):\n'
                    perm_text += f"• {', '.join(perms)}\n\n"
                except:
                    perm_text += f'<b>Unknown</b> (<code>{user_id}</code>):\n'
                    perm_text += f"• {', '.join(perms)}\n\n"
            await event.edit(perm_text)
            return
        try:
            user_id = int(args[0])
            new_perms = args[1:]
            if 'remove' in new_perms:
                perm_to_remove = new_perms[new_perms.index('remove') + 1]
                permissions = self.db.get_config('owner_permissions', {})
                user_perms = permissions.get(str(user_id), [])
                if perm_to_remove in user_perms:
                    user_perms.remove(perm_to_remove)
                    permissions[str(user_id)] = user_perms
                    self.db.set_config('owner_permissions', permissions)
                    await event.edit(f'✅ <b>Право <code>{perm_to_remove}</code> удалено у пользователя <code>{user_id}</code></b>')
                else:
                    await event.edit(f'❌ <b>У пользователя нет права <code>{perm_to_remove}</code></b>')
            else:
                permissions = self.db.get_config('owner_permissions', {})
                permissions[str(user_id)] = new_perms
                self.db.set_config('owner_permissions', permissions)
                await event.edit(f"\n\n✅ <b>Права обновлены</b>\n\n<b>👤 Пользователь:</b> <code>{user_id}</code>\n\n<b>🔐 Новые права:</b> {', '.join(new_perms)}\n\n                ")
        except (ValueError, IndexError):
            await event.edit('❌ <b>Неверный формат команды</b>')

    async def cmd_sudo(self, event, args):
        if not args:
            await event.edit('❌ **Использование:** `.sudo <команда>`')
            return
        if not self._is_owner(event.sender_id):
            await event.edit('❌ <b>Доступ запрещен:</b> Только овнеры могут использовать sudo')
            return
        command = ' '.join(args)
        self._log_action(event.sender_id, 'sudo', command)
        await event.edit(f'🔧 <b>Выполнение с правами овнера:</b>\n\n<code>{command}</code>')

    async def cmd_owner_log(self, event, args):
        if not self._is_owner(event.sender_id):
            await event.edit('❌ <b>Доступ запрещен:</b> Только овнеры могут просматривать логи')
            return
        logs = self.db.get_config('owner_logs', [])
        if not logs:
            await event.edit('📊 <b>Лог действий пуст</b>')
            return
        recent_logs = logs[-10:]
        log_text = '📊 <b>Лог действий овнеров</b>\n\n'
        for log in reversed(recent_logs):
            try:
                user_info = await self.utils.get_user_info(log['user_id'])
                username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
                log_text += f"""\n\n<b>{log['date']}</b>\n\n👤 @{username} ({log['user_id']})\n\n🔧 {log['action']}\n\n{(f"🎯 {log['target']}" if log.get('target') else '')}\n\n"""
            except:
                log_text += f"\n\n<b>{log['date']}</b>\n\n👤 Unknown ({log['user_id']})\n\n🔧 {log['action']}\n\n"
        log_text += f'<b>📈 Всего записей:</b> {len(logs)}'
        await event.edit(log_text)
module = OwnerManagerModule()
