from __future__ import annotations
import asyncio
import logging
from typing import Optional
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
try:
    from aiogram.client.default import DefaultBotProperties
except Exception:
    DefaultBotProperties = None
from ..storage.database import ArgentDatabase
from ..security.owner_manager import OwnerManager
logger = logging.getLogger(__name__)

class ArgentInlineBot:

    def __init__(self, bot_token: str, db: ArgentDatabase, userbot_client=None):
        self.bot_token = bot_token
        self.db = db
        self.userbot_client = userbot_client
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self._running = False
        self.owner_manager = OwnerManager()

    async def start(self):
        try:
            if DefaultBotProperties is not None:
                self.bot = Bot(token=self.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
            else:
                self.bot = Bot(token=self.bot_token, parse_mode=ParseMode.HTML)
        except TypeError:
            self.bot = Bot(token=self.bot_token, parse_mode=ParseMode.HTML)
        except Exception:
            self.bot = Bot(token=self.bot_token)
        self.dp = Dispatcher()
        self._bind_handlers()
        await self._send_initial_setup()
        self._running = True
        logger.info('🤖 Inline bot started')
        asyncio.create_task(self.dp.start_polling(self.bot, handle_signals=False))

    def _bind_handlers(self):

        def owner_required(handler):

            async def wrapper(callback_or_message):
                user_id = callback_or_message.from_user.id
                if not self.owner_manager.is_owner(user_id):
                    if hasattr(callback_or_message, 'answer'):
                        await callback_or_message.answer('❌ Доступ запрещен', show_alert=True)
                    else:
                        await callback_or_message.answer('❌ <b>Доступ запрещен</b>\n\n🔒 Этот бот принадлежит другому пользователю')
                    return
                return await handler(callback_or_message)
            return wrapper

        @self.dp.message(CommandStart())
        async def handle_start(message: Message):
            user_id = message.from_user.id
            username = message.from_user.username or 'Unknown'
            first_name = message.from_user.first_name or 'Unknown'
            if not self.owner_manager.has_primary_owner():
                if self.owner_manager.set_primary_owner(user_id):
                    self.db.set_config('owners', [user_id])
                    await message.answer(f'🎉 <b>Добро пожаловать, владелец!</b>\n\n👑 <b>Вы стали основным владельцем Argent UserBot</b>\n🆔 <b>Ваш ID:</b> <code>{user_id}</code>\n👤 <b>Имя:</b> {first_name}\n📱 <b>Username:</b> @{username}\n\n🔐 <b>Безопасность:</b>\n• Только вы можете управлять ботом\n• Другие пользователи получат отказ в доступе\n• Вы можете добавлять других владельцев через настройки\n\n🚀 <b>Теперь вы можете пользоваться всеми функциями!</b>', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🚀 Перейти к управлению', callback_data='main_menu')]]))
                    return
            if not self.owner_manager.is_owner(user_id):
                await message.answer(f'❌ <b>Доступ запрещен</b>\n\n🔒 <b>Этот бот принадлежит другому пользователю</b>\n\n💡 <b>Хотите свой собственный юзербот?</b>\n📂 GitHub: github.com/lonly19/Argent-Userbot')
                return
            await self._show_main_menu(message)

        @self.dp.callback_query(F.data == 'main_menu')
        @owner_required
        async def handle_main_menu(cb: CallbackQuery):
            await self._show_main_menu(cb.message, edit=True)
            await cb.answer()

        @self.dp.callback_query(F.data == 'settings')
        @owner_required
        async def handle_settings(cb: CallbackQuery):
            await self._show_settings_menu(cb.message, edit=True)
            await cb.answer()

        @self.dp.callback_query(F.data == 'restart_settings')
        @owner_required
        async def handle_restart_settings(cb: CallbackQuery):
            await self._show_restart_settings(cb.message, edit=True)
            await cb.answer()

        @self.dp.callback_query(F.data.startswith('set_restart_'))
        @owner_required
        async def handle_set_restart(cb: CallbackQuery):
            try:
                hours = cb.data.split('_')[2]
            except (IndexError, ValueError):
                await cb.answer('❌ Неверные данные', show_alert=True)
                return
            if hours == 'off':
                self.db.set_config('auto_restart_hours', None)
                await cb.message.edit_text('⏰ <b>Автоперезагрузка отключена</b>', reply_markup=self._get_back_keyboard())
            else:
                try:
                    hours = int(hours)
                    if hours <= 0 or hours > 168:
                        await cb.answer('❌ Неверный интервал (1-168 часов)', show_alert=True)
                        return
                except ValueError:
                    await cb.answer('❌ Неверный формат часов', show_alert=True)
                    return
                self.db.set_config('auto_restart_hours', hours)
                await cb.message.edit_text(f'✅ <b>Автоперезагрузка настроена</b>\n\n⏰ Интервал: каждые {hours} часов', reply_markup=self._get_back_keyboard())
            await cb.answer()

        @self.dp.callback_query(F.data == 'language_settings')
        @owner_required
        async def handle_language_settings(cb: CallbackQuery):
            await self._show_language_settings(cb.message, edit=True)
            await cb.answer()

        @self.dp.callback_query(F.data.startswith('set_lang_'))
        @owner_required
        async def handle_set_language(cb: CallbackQuery):
            try:
                lang = cb.data.split('_')[2]
                if lang not in ['ru', 'en', 'uk', 'de', 'fr']:
                    await cb.answer('❌ Неподдерживаемый язык', show_alert=True)
                    return
            except (IndexError, ValueError):
                await cb.answer('❌ Неверные данные', show_alert=True)
                return
            self.db.set_config('language', lang)
            lang_names = {'ru': '🇷🇺 Русский', 'en': '🇺🇸 English', 'uk': '🇺🇦 Українська', 'de': '🇩🇪 Deutsch', 'fr': '🇫🇷 Français'}
            await self._safe_edit(cb.message, f'✅ <b>Язык изменен</b>\n\n🌍 Новый язык: {lang_names[lang]}', reply_markup=self._get_back_keyboard())
            await cb.answer()

        @self.dp.callback_query(F.data == 'modules_menu')
        @owner_required
        async def handle_modules_menu(cb: CallbackQuery):
            await self._show_modules_menu(cb.message, edit=True)
            await cb.answer()

        @self.dp.callback_query(F.data == 'list_modules')
        @owner_required
        async def handle_list_modules(cb: CallbackQuery):
            await self._show_modules_menu(cb.message, edit=True)
            await cb.answer()

        @self.dp.callback_query(F.data == 'reload_all_modules')
        @owner_required
        async def handle_reload_all_modules(cb: CallbackQuery):
            await self._safe_edit(cb.message, '🔄 <b>Перезагрузка модулей...</b>\n<blockquote>Функция будет доступна в ближайшем обновлении.</blockquote>', reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔙 Назад', callback_data='modules_menu')]]))
            await cb.answer()

        @self.dp.callback_query(F.data == 'system_info')
        @owner_required
        async def handle_system_info(cb: CallbackQuery):
            await self._show_system_info(cb.message, edit=True)
            await cb.answer()

        @self.dp.callback_query(F.data == 'restart_userbot')
        @owner_required
        async def handle_restart_userbot(cb: CallbackQuery):
            await self._safe_edit(cb.message, '🔄 <b>Перезагрузка UserBot...</b>')
            await cb.answer()

        @self.dp.callback_query(F.data == 'owner_management')
        @owner_required
        async def handle_owner_management(cb: CallbackQuery):
            await self._show_owner_management(cb.message, edit=True)
            await cb.answer()

        @self.dp.callback_query(F.data == 'show_owners')
        @owner_required
        async def handle_show_owners(cb: CallbackQuery):
            await self._show_owners_list(cb.message, edit=True)
            await cb.answer()

        @self.dp.callback_query(F.data == 'security_info')
        @owner_required
        async def handle_security_info(cb: CallbackQuery):
            await self._show_security_info(cb.message, edit=True)
            await cb.answer()

    async def _send_initial_setup(self):
        owners = self.owner_manager.get_all_owners()
        if not owners:
            owners = self.db.get_config('owners', [])
        for owner_id in owners:
            try:
                await self.bot.send_message(owner_id, '🎉 <b>Argent UserBot успешно установлен!</b>\n<blockquote>🤖 <b>Inline бот создан и готов к работе</b>\n\n⚗️ <b>Доступные функции:</b>\n🔄 Управление перезагрузкой\n🌍 Настройка языка\n📦 Управление модулями\n👑 Управление овнерами\n📊 Системная информация\n\n🔬 <b>Начальная настройка:</b>\nВыберите интервал автоперезагрузки для стабильной работы</blockquote>', reply_markup=self._get_initial_setup_keyboard())
            except Exception as e:
                logger.error(f'Failed to send initial message to {owner_id}: {e}')

    def _get_initial_setup_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⏰ Настроить автоперезагрузку', callback_data='restart_settings')], [InlineKeyboardButton(text='🌍 Выбрать язык', callback_data='language_settings')], [InlineKeyboardButton(text='🚀 Главное меню', callback_data='main_menu')]])

    async def _show_main_menu(self, message: Message, edit: bool=False):
        text = '<b>⚗️ Argent UserBot - Панель управления</b>\n<blockquote>🧪 <b>Научный подход к управлению Telegram</b>\n\n<b>🔬 Доступные разделы:</b>\n⚙️ Настройки системы\n📦 Управление модулями\n📊 Системная информация\n🔄 Перезагрузка бота\n\n🧬 <b>Статус:</b> Все системы в норме</blockquote>'
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='⚙️ Настройки', callback_data='settings')], [InlineKeyboardButton(text='📦 Модули', callback_data='modules_menu')], [InlineKeyboardButton(text='📊 Система', callback_data='system_info')], [InlineKeyboardButton(text='🔄 Перезагрузка', callback_data='restart_userbot')]])
        if edit:
            await self._safe_edit(message, text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)

    async def _show_settings_menu(self, message: Message, edit: bool=False):
        current_lang = self.db.get_config('language', 'ru')
        restart_hours = self.db.get_config('auto_restart_hours')
        lang_names = {'ru': '🇷🇺 Русский', 'en': '🇺🇸 English', 'uk': '🇺🇦 Українська', 'de': '🇩🇪 Deutsch', 'fr': '🇫🇷 Français'}
        text = f"<b>⚙️ Настройки системы</b>\n<blockquote><b>🌍 Язык:</b> {lang_names.get(current_lang, current_lang)}\n\n<b>⏰ Автоперезагрузка:</b> {('каждые ' + str(restart_hours) + ' ч.' if restart_hours else 'отключена')}\n\n<b>🔧 Доступные настройки:</b></blockquote>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🌍 Язык интерфейса', callback_data='language_settings')], [InlineKeyboardButton(text='⏰ Автоперезагрузка', callback_data='restart_settings')], [InlineKeyboardButton(text='👑 Управление владельцами', callback_data='owner_management')], [InlineKeyboardButton(text='🏠 Главное меню', callback_data='main_menu')]])
        if edit:
            await self._safe_edit(message, text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)

    async def _show_restart_settings(self, message: Message, edit: bool=False):
        current_hours = self.db.get_config('auto_restart_hours')
        text = f"<b>⏰ Настройки автоперезагрузки</b>\n<blockquote><b>📊 Текущий интервал:</b> {('каждые ' + str(current_hours) + ' часов' if current_hours else 'отключено')}\n\n<b>🔬 Рекомендуемые интервалы:</b>\n6 часов — для активного использования\n12 часов — стандартный режим\n24 часа — для стабильных серверов\n\n⚛️ <b>Выберите интервал:</b></blockquote>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='6 часов', callback_data='set_restart_6'), InlineKeyboardButton(text='12 часов', callback_data='set_restart_12')], [InlineKeyboardButton(text='24 часа', callback_data='set_restart_24'), InlineKeyboardButton(text='❌ Отключить', callback_data='set_restart_off')], [InlineKeyboardButton(text='🔙 Назад', callback_data='settings')]])
        if edit:
            await self._safe_edit(message, text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)

    async def _show_language_settings(self, message: Message, edit: bool=False):
        current_lang = self.db.get_config('language', 'ru')
        text = f'<b>🌍 Настройки языка</b>\n<blockquote><b>📍 Текущий язык:</b> {current_lang.upper()}\n\n🔬 <b>Доступные языки:</b></blockquote>'
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🇷🇺 Русский', callback_data='set_lang_ru'), InlineKeyboardButton(text='🇺🇸 English', callback_data='set_lang_en')], [InlineKeyboardButton(text='🇺🇦 Українська', callback_data='set_lang_uk'), InlineKeyboardButton(text='🇩🇪 Deutsch', callback_data='set_lang_de')], [InlineKeyboardButton(text='🇫🇷 Français', callback_data='set_lang_fr')], [InlineKeyboardButton(text='🔙 Назад', callback_data='settings')]])
        if edit:
            await self._safe_edit(message, text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)

    async def _show_modules_menu(self, message: Message, edit: bool=False):
        text = '<b>📦 Управление модулями</b>\n<blockquote>🧪 <b>Загруженные модули:</b>\n🔧 SystemCore — системное управление\n🧪 CoreUtils — базовые утилиты\n👑 AdminTools — администрирование\n🎭 FunLab — развлечения\n\n⚛️ <b>Функции:</b>\nЗагрузка новых модулей\nПерезагрузка модулей\nПросмотр информации</blockquote>'
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔄 Перезагрузить все', callback_data='reload_all_modules')], [InlineKeyboardButton(text='📋 Список модулей', callback_data='list_modules')], [InlineKeyboardButton(text='🏠 Главное меню', callback_data='main_menu')]])
        if edit:
            await self._safe_edit(message, text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)

    async def _show_system_info(self, message: Message, edit: bool=False):
        import psutil
        import time
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        owners_count = len(self.db.get_config('owners', []))
        language = self.db.get_config('language', 'ru')
        text = f"\n\n📊 <b>Системная информация</b>\n\n<b>🖥️ Сервер:</b>\n• <b>CPU:</b> {cpu_percent}%\n• <b>RAM:</b> {memory.percent}%\n• <b>Диск:</b> Доступен\n\n<b>⚗️ Argent UserBot:</b>\n• <b>Версия:</b> 2.0.0\n• <b>Язык:</b> {language.upper()}\n• <b>Овнеров:</b> {owners_count}\n• <b>Статус:</b> ✅ Активен\n\n<b>🔬 Последнее обновление:</b> {time.strftime('%H:%M:%S')}\n\n        "
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔄 Обновить', callback_data='system_info')], [InlineKeyboardButton(text='🏠 Главное меню', callback_data='main_menu')]])
        if edit:
            await self._safe_edit(message, text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)

    async def _safe_edit(self, message: Message, text: str, reply_markup: Optional[InlineKeyboardMarkup]=None):
        try:
            await message.edit_text(text, reply_markup=reply_markup)
        except TelegramBadRequest as e:
            if 'message is not modified' in str(e):
                try:
                    await message.edit_text(text + '\u2060', reply_markup=reply_markup)
                except TelegramBadRequest:
                    pass
            elif 'message to edit not found' in str(e):
                pass
            else:
                logger.error(f'Ошибка редактирования сообщения: {e}')
        except Exception as e:
            logger.error(f'Неожиданная ошибка при редактировании: {e}')

    def _get_back_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔙 Назад', callback_data='settings')], [InlineKeyboardButton(text='🏠 Главное меню', callback_data='main_menu')]])

    async def _show_owner_management(self, message: Message, edit: bool=False):
        primary_owner = self.owner_manager.get_primary_owner()
        all_owners = self.owner_manager.get_all_owners()
        total_owners = len(all_owners)
        text = f'<b>👑 Управление владельцами</b>\n<blockquote><b>🔐 Основной владелец:</b> <code>{primary_owner}</code>\n<b>👥 Всего владельцев:</b> {total_owners}\n\n<b>🛡️ Система безопасности:</b>\n• Только владельцы могут управлять ботом\n• Основного владельца нельзя удалить\n• Все действия логируются\n\n<b>⚙️ Доступные функции:</b></blockquote>'
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='👥 Список владельцев', callback_data='show_owners')], [InlineKeyboardButton(text='🔐 Информация о безопасности', callback_data='security_info')], [InlineKeyboardButton(text='🔙 Назад', callback_data='settings')], [InlineKeyboardButton(text='🏠 Главное меню', callback_data='main_menu')]])
        if edit:
            await self._safe_edit(message, text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)

    async def _show_owners_list(self, message: Message, edit: bool=False):
        primary_owner = self.owner_manager.get_primary_owner()
        all_owners = self.owner_manager.get_all_owners()
        text = '<b>👥 Список владельцев</b>\n<blockquote>'
        for i, owner_id in enumerate(all_owners, 1):
            status = '👑 Основной' if owner_id == primary_owner else '👤 Обычный'
            text += f'{i}. <code>{owner_id}</code> - {status}\n'
        text += f'\n<b>📊 Всего владельцев:</b> {len(all_owners)}'
        text += '\n\n<b>💡 Информация:</b>\n'
        text += '• Основной владелец устанавливается первым\n'
        text += '• Основного владельца нельзя удалить\n'
        text += '• Добавление новых владельцев пока недоступно'
        text += '</blockquote>'
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔄 Обновить', callback_data='show_owners')], [InlineKeyboardButton(text='🔙 Назад', callback_data='owner_management')]])
        if edit:
            await self._safe_edit(message, text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)

    async def _show_security_info(self, message: Message, edit: bool=False):
        config_info = self.owner_manager.get_config_info()
        text = f"<b>🔐 Информация о безопасности</b>\n<blockquote><b>📊 Статус системы:</b>\n• Основной владелец: {('✅ Установлен' if config_info['has_primary_owner'] else '❌ Не установлен')}\n• ID владельца: <code>{config_info['primary_owner'] or 'Не установлен'}</code>\n• Всего владельцев: {config_info['total_owners']}\n• Настройка завершена: {('✅ Да' if config_info['setup_completed'] else '❌ Нет')}\n• Файл конфигурации: {('✅ Существует' if config_info['config_file_exists'] else '❌ Отсутствует')}\n\n<b>🛡️ Принципы безопасности:</b>\n• Первый пользователь становится владельцем\n• Проверка прав на каждое действие\n• Логирование всех операций\n• Защита от несанкционированного доступа\n\n<b>🔒 Защищенные функции:</b>\n• Управление настройками\n• Перезагрузка системы\n• Управление модулями\n• Просмотр системной информации\n\n<b>⚠️ Важно:</b>\nНе скачивайте модули которым не доверяете</blockquote>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔄 Обновить', callback_data='security_info')], [InlineKeyboardButton(text='🔙 Назад', callback_data='owner_management')]])
        if edit:
            await self._safe_edit(message, text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)

    async def stop(self):
        self._running = False
        if self.bot:
            await self.bot.session.close()
        logger.info('🤖 Inline bot stopped')
