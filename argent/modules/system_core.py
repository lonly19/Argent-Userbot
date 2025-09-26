import asyncio
import time
import os
import sys
import json
import glob
from datetime import datetime, timedelta
from pathlib import Path
from argent.core.loader import ArgentModule

class SystemCoreModule(ArgentModule):
    __version__ = '1.0.0'
    __author__ = 'github.com/lonly19/Argent-Userbot'
    __category__ = 'core'

    def __init__(self):
        super().__init__()
        self.description = 'Системное управление и настройки'
        self.register_command('restart', self.cmd_restart, 'Перезапуск бота')
        self.register_command('shutdown', self.cmd_shutdown, 'Выключение бота')
        self.register_command('addowner', self.cmd_addowner, 'Добавить овнера')
        self.register_command('delowner', self.cmd_delowner, 'Удалить овнера')
        self.register_command('owners', self.cmd_owners, 'Список овнеров')
        self.register_command('lang', self.cmd_lang, 'Сменить язык')
        self.register_command('autorestart', self.cmd_autorestart, 'Автоперезагрузка')
        self.register_command('backupdb', self.cmd_backupdb, 'Резервное копирование данных')
        self.restart_task = None

    async def on_load(self):
        if not self.db.get_config('language'):
            self.db.set_config('language', 'ru')
        me = await self.client.get_me()
        owners = self.db.get_config('owners', [])
        if me.id not in owners:
            owners.append(me.id)
            self.db.set_config('owners', owners)
        restart_hours = self.db.get_config('auto_restart_hours')
        if restart_hours:
            await self._schedule_restart(restart_hours)

    def _is_owner(self, user_id: int) -> bool:
        owners = self.db.get_config('owners', [])
        return user_id in owners

    async def _schedule_restart(self, hours: int):
        if self.restart_task:
            self.restart_task.cancel()

        async def restart_timer():
            await asyncio.sleep(hours * 3600)
            owners = self.db.get_config('owners', [])
            for owner_id in owners:
                try:
                    await self.client.send_message(owner_id, '🔄 <b>Автоматический перезапуск</b>\n\nUserBot перезапускается, подождите...')
                except:
                    pass
            os.execv(sys.executable, ['python'] + sys.argv)
        self.restart_task = asyncio.create_task(restart_timer())

    async def cmd_restart(self, event, args):
        if not self._is_owner(event.sender_id):
            await event.edit('❌ <b>Ошибка доступа:</b> Только владельцы могут перезапускать бота')
            return
        await event.edit('🔄 <b>Перезапуск...</b>\n\nUserBot перезапускается...')
        await asyncio.sleep(2)
        os.execv(sys.executable, ['python'] + sys.argv)

    async def cmd_shutdown(self, event, args):
        if not self._is_owner(event.sender_id):
            await event.edit('❌ <b>Ошибка доступа:</b> Только владельцы могут выключать бота')
            return
        await event.edit('⚡ <b>Выключение...</b>\n\nUserBot выключается...')
        await asyncio.sleep(2)
        sys.exit(0)

    async def cmd_addowner(self, event, args):
        if not self._is_owner(event.sender_id):
            await event.edit('❌ <b>Ошибка доступа:</b> Только владельцы могут добавлять овнеров')
            return
        if not event.is_reply:
            await event.edit('❌ <b>Ошибка:</b> Ответьте на сообщение пользователя')
            return
        reply_msg = await event.get_reply_message()
        user_id = reply_msg.sender_id
        owners = self.db.get_config('owners', [])
        if user_id in owners:
            await event.edit('❌ <b>Пользователь уже является овнером</b>')
            return
        owners.append(user_id)
        self.db.set_config('owners', owners)
        user_info = await self.utils.get_user_info(user_id)
        username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
        await event.edit(f'\n✅ <b>Овнер добавлен</b>\n\n<b>👤 Пользователь:</b> @{username} (<code>{user_id}</code>)\n\n<b>🔐 Права:</b> Полный доступ к боту\n\n<b>📝 Статус:</b> Активен\n\n<b>👥 Всего овнеров:</b> <code>{len(owners)}</code>\n')

    async def cmd_delowner(self, event, args):
        if not self._is_owner(event.sender_id):
            await event.edit('❌ <b>Ошибка доступа:</b> Только владельцы могут удалять овнеров')
            return
        if not event.is_reply:
            await event.edit('❌ <b>Ошибка:</b> Ответьте на сообщение пользователя')
            return
        reply_msg = await event.get_reply_message()
        user_id = reply_msg.sender_id
        owners = self.db.get_config('owners', [])
        if len(owners) == 1 and user_id == event.sender_id:
            await event.edit('❌ <b>Нельзя удалить последнего овнера</b>')
            return
        if user_id not in owners:
            await event.edit('❌ <b>Пользователь не является овнером</b>')
            return
        owners.remove(user_id)
        self.db.set_config('owners', owners)
        user_info = await self.utils.get_user_info(user_id)
        username = user_info.get('username', 'Unknown') if user_info else 'Unknown'
        await event.edit(f'\n✅ <b>Овнер удален</b>\n\n<b>👤 Пользователь:</b> @{username} (<code>{user_id}</code>)\n\n<b>🔐 Права:</b> Доступ отозван\n\n<b>📝 Статус:</b> Неактивен\n\n<b>👥 Всего овнеров:</b> <code>{len(owners)}</code>\n')

    async def cmd_owners(self, event, args):
        owners = self.db.get_config('owners', [])
        if not owners:
            await event.edit('❌ <b>Овнеры не найдены</b>')
            return
        owners_text = '👥 <b>Список овнеров</b>\n\n'
        for i, owner_id in enumerate(owners, 1):
            try:
                user_info = await self.utils.get_user_info(owner_id)
                if user_info:
                    username = user_info.get('username', 'Unknown')
                    first_name = user_info.get('first_name', 'Unknown')
                    owners_text += f'<b>{i}.</b> {first_name} (@{username}) - <code>{owner_id}</code>\n'
                else:
                    owners_text += f'<b>{i}.</b> Unknown User - <code>{owner_id}</code>\n'
            except:
                owners_text += f'<b>{i}.</b> Unknown User - <code>{owner_id}</code>\n'
        owners_text += f'\n<b>👥 Всего овнеров:</b> <code>{len(owners)}</code>'
        await event.edit(owners_text)

    async def cmd_lang(self, event, args):
        if not args:
            current_lang = self.db.get_config('language', 'ru')
            lang_names = {'ru': '🇷🇺 Русский', 'en': '🇺🇸 English', 'uk': '🇺🇦 Українська', 'de': '🇩🇪 Deutsch', 'fr': '🇫🇷 Français'}
            await event.edit(f'\n🌐 **Настройка языка**\n\n**🔤 Текущий язык:** {lang_names.get(current_lang, current_lang)}\n\n**📋 Доступные языки:**\n\n• `ru` - 🇷🇺 Русский\n\n• `en` - 🇺🇸 English\n\n• `uk` - 🇺🇦 Українська\n\n• `de` - 🇩🇪 Deutsch\n\n• `fr` - 🇫🇷 Français\n\n**💡 Использование:** `.lang <код_языка>`\n')
            return
        lang_code = args[0].lower()
        supported_langs = ['ru', 'en', 'uk', 'de', 'fr']
        if lang_code not in supported_langs:
            await event.edit(f'❌ <b>Неподдерживаемый язык:</b> <code>{lang_code}</code>')
            return
        self.db.set_config('language', lang_code)
        lang_names = {'ru': '🇷🇺 Русский', 'en': '🇺🇸 English', 'uk': '🇺🇦 Українська', 'de': '🇩🇪 Deutsch', 'fr': '🇫🇷 Français'}
        await event.edit(f'\n✅ <b>Язык изменен</b>\n\n<b>🌐 Новый язык:</b> {lang_names[lang_code]}\n\n<b>📝 Примечание:</b> Некоторые модули могут требовать перезапуска\n\n<b>🔄 Статус:</b> Настройки сохранены\n')

    async def cmd_autorestart(self, event, args):
        if not self._is_owner(event.sender_id):
            await event.edit('❌ <b>Ошибка доступа:</b> Только владельцы могут настраивать автоперезагрузку')
            return
        if not args:
            current_hours = self.db.get_config('auto_restart_hours')
            if current_hours:
                await event.edit(f'\n⏰ **Автоперезагрузка**\n\n**📊 Статус:** ✅ Включена каждые `{current_hours}` часов\n\n**⚙️ Управление:**\n\n• `.autorestart off` - Отключить\n\n• `.autorestart <часы>` - Изменить интервал\n')
            else:
                await event.edit('\n⏰ <b>Автоперезагрузка отключена</b>\n\n<b>💡 Примеры настройки:</b>\n\n• <code>.autorestart 6</code> - каждые 6 часов\n\n• <code>.autorestart 12</code> - каждые 12 часов\n\n• <code>.autorestart 24</code> - каждые 24 часа\n')
            return
        if args[0].lower() == 'off':
            self.db.set_config('auto_restart_hours', None)
            if self.restart_task:
                self.restart_task.cancel()
                self.restart_task = None
            await event.edit('✅ <b>Автоперезагрузка отключена</b>')
            return
        try:
            hours = int(args[0])
            if hours < 1 or hours > 168:
                await event.edit('❌ <b>Интервал должен быть от 1 до 168 часов</b>')
                return
            self.db.set_config('auto_restart_hours', hours)
            await self._schedule_restart(hours)
            await event.edit(f'\n✅ <b>Автоперезагрузка настроена</b>\n\n<b>⏰ Интервал:</b> каждые <code>{hours}</code> часов\n\n<b>🔄 Следующий перезапуск:</b> через <code>{hours}</code> часов\n\n<b>📝 Примечание:</b> Уведомления будут отправлены всем владельцам\n')
        except ValueError:
            await event.edit('❌ <b>Ошибка: Укажите число часов</b>')

    async def cmd_backupdb(self, event, args):
        if not self._is_owner(event.sender_id):
            await event.edit('❌ <b>Ошибка доступа:</b> Только владельцы могут создавать резервные копии')
            return
        await event.edit('🔄 <b>Создание резервной копии...</b>\n\n⏳ Процесс может занять несколько минут...')
        try:
            current_time = datetime.now()
            timestamp = current_time.strftime('%Y%m%d_%H%M%S')
            readable_time = current_time.strftime('%d.%m.%Y в %H:%M:%S')
            backup_data = {'backup_info': {'created_at': readable_time, 'timestamp': timestamp, 'version': '2.0.0', 'userbot': 'Argent UserBot', 'backup_type': 'full_data_backup'}, 'database': {}, 'config_files': {}, 'statistics': {}}
            if hasattr(self.db, '_json_data'):
                backup_data['database'] = self.db._json_data.copy()
            else:
                backup_data['database'] = {'config': self.db.get_section('config'), 'modules': self.db.get_section('modules'), 'users': self.db.get_section('users'), 'chats': self.db.get_section('chats'), 'misc': self.db.get_section('misc')}
            data_dir = Path('.argent_data')
            if data_dir.exists():
                for file_path in data_dir.rglob('*'):
                    if file_path.is_file() and (not file_path.suffix == '.session'):
                        try:
                            relative_path = str(file_path.relative_to(data_dir))
                            if file_path.suffix == '.json':
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    backup_data['config_files'][relative_path] = json.load(f)
                            else:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    backup_data['config_files'][relative_path] = f.read()
                        except Exception as e:
                            backup_data['config_files'][relative_path] = f'❌ Ошибка чтения: {str(e)}'
            db_stats = self.db.get_stats()
            backup_data['statistics'] = {'database_stats': db_stats, 'config_files_count': len(backup_data['config_files']), 'total_sections': len(backup_data['database']), 'modules_count': len(backup_data['database'].get('modules', {})), 'users_count': len(backup_data['database'].get('users', {})), 'chats_count': len(backup_data['database'].get('chats', {}))}
            backup_filename = f'argent_backup_{timestamp}.json'
            backup_path = Path(backup_filename)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            file_size = backup_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            caption = f"\n🔒 <b>Резервная копия Argent UserBot</b>\n\n📅 <b>Дата создания:</b> {readable_time}\n🏷️ <b>Версия:</b> v2.0.0\n📦 <b>Тип:</b> Полный бэкап данных\n\n📊 <b>Статистика:</b>\n• <b>Размер файла:</b> {file_size_mb:.2f} МБ\n• <b>Секций БД:</b> {backup_data['statistics']['total_sections']}\n• <b>Модулей:</b> {backup_data['statistics']['modules_count']}\n• <b>Пользователей:</b> {backup_data['statistics']['users_count']}\n• <b>Чатов:</b> {backup_data['statistics']['chats_count']}\n• <b>Конфиг. файлов:</b> {backup_data['statistics']['config_files_count']}\n\n💾 <b>Содержимое:</b>\n• База данных (JSON)\n• Конфигурационные файлы\n• Настройки модулей\n• Пользовательские данные\n\n🔐 <b>Безопасность:</b> Сессии исключены из бэкапа\n\n⚡ <b>Восстановление:</b> Импортируйте этот файл для восстановления настроек\n\n🤖 <b>Argent UserBot</b> | github.com/lonly19/Argent-Userbot\n"
            me = await self.client.get_me()
            await self.client.send_file(me.id, backup_path, caption=caption, parse_mode='html')
            backup_path.unlink()
            await event.edit(f"\n✅ <b>Резервная копия создана успешно!</b>\n\n📦 <b>Файл:</b> <code>{backup_filename}</code>\n📤 <b>Отправлен в:</b> Избранное\n💾 <b>Размер:</b> {file_size_mb:.2f} МБ\n\n📊 <b>Сохранено:</b>\n• {backup_data['statistics']['total_sections']} секций БД\n• {backup_data['statistics']['modules_count']} модулей\n• {backup_data['statistics']['users_count']} пользователей\n• {backup_data['statistics']['chats_count']} чатов\n• {backup_data['statistics']['config_files_count']} конфиг. файлов\n\n💡 <b>Совет:</b> Сохраните файл в надежном месте для восстановления данных\n")
        except Exception as e:
            await event.edit(f'\n❌ <b>Ошибка создания резервной копии!</b>\n\n<b>Детали ошибки:</b>\n<code>{str(e)}</code>\n\n<b>Возможные причины:</b>\n• Недостаточно места на диске\n• Проблемы с доступом к файлам\n• Ошибка сети при отправке\n\n<b>Решение:</b> Попробуйте еще раз или обратитесь к разработчику\n')
            backup_path = Path(f"argent_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            if backup_path.exists():
                backup_path.unlink()
module = SystemCoreModule()
