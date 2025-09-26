from __future__ import annotations
import asyncio
import base64
import io
import threading
import time
from typing import Dict, Optional
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
try:
    from aiogram.client.default import DefaultBotProperties
except Exception:
    DefaultBotProperties = None
from .telethon_manager import TelethonAuthFlow, SessionStore, AuthError
from ..security.owner_manager import OwnerManager

class BotRunner:

    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._bot: Optional[Bot] = None
        self._dp: Optional[Dispatcher] = None
        self._running = False
        self._state: Dict[int, Dict] = {}
        self._store: Optional[SessionStore] = None
        self._owner_manager = OwnerManager()
        self._max_states = 10
        self._rate_limit: Dict[int, float] = {}
        self._auto_started_userbot: bool = False

    async def _get_me_username(self, token: str) -> Optional[str]:
        url = f'https://api.telegram.org/bot{token}/getMe'
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url, timeout=10) as r:
                if r.status != 200:
                    return None
                data = await r.json()
                if not data.get('ok'):
                    return None
                return data['result'].get('username')

    def get_username_sync(self, token: str) -> Optional[str]:

        async def _wrap():
            return await self._get_me_username(token)
        return asyncio.run(_wrap())

    def _cleanup_old_states(self):
        current_time = time.time()
        timeout = 30 * 60
        to_remove = []
        for uid, state in self._state.items():
            if current_time - state.get('timestamp', 0) > timeout:
                to_remove.append(uid)
        for uid in to_remove:
            self._state.pop(uid, None)

    def start(self, bot_token: str, store: SessionStore):
        if self._running:
            return
        self._running = True
        self._store = store
        self._thread = threading.Thread(target=self._run, args=(bot_token,), daemon=True)
        self._thread.start()

    def _run(self, bot_token: str):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._run_async(bot_token))

    async def _run_async(self, bot_token: str):
        try:
            if DefaultBotProperties is not None:
                self._bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
            else:
                self._bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        except TypeError:
            self._bot = Bot(token=bot_token, parse_mode=ParseMode.HTML)
        except Exception as e:
            self._bot = Bot(token=bot_token)
        self._dp = Dispatcher()
        self._bind_handlers()
        try:
            await self._dp.start_polling(self._bot, handle_signals=False)
        except Exception as e:
            pass
        finally:
            self._running = False

    def _bind_handlers(self):
        assert self._dp is not None
        dp = self._dp

        def owner_required(handler):

            async def wrapper(message_or_callback):
                user_id = message_or_callback.from_user.id
                current_time = time.time()
                if user_id in self._rate_limit:
                    if current_time - self._rate_limit[user_id] < 1.0:
                        if hasattr(message_or_callback, 'answer'):
                            if hasattr(message_or_callback, 'message'):
                                await message_or_callback.answer('⏱️ Слишком быстро', show_alert=True)
                            else:
                                await message_or_callback.answer('⏱️ Подождите секунду перед следующим действием')
                        return
                self._rate_limit[user_id] = current_time
                if not self._owner_manager.is_owner(user_id):
                    if hasattr(message_or_callback, 'answer'):
                        if hasattr(message_or_callback, 'message'):
                            await message_or_callback.answer('❌ Доступ запрещен', show_alert=True)
                        else:
                            await message_or_callback.answer('❌ <b>Доступ запрещен</b>\n\n🔒 Этот бот принадлежит другому пользователю')
                    return
                return await handler(message_or_callback)
            return wrapper

        @dp.message(CommandStart())
        async def handle_start(message: Message):
            uid = message.from_user.id
            username = message.from_user.username or 'Unknown'
            first_name = message.from_user.first_name or 'Unknown'
            if not self._owner_manager.has_primary_owner():
                if self._owner_manager.set_primary_owner(uid):
                    await message.answer(f'🎉 <b>Добро пожаловать, владелец!</b>\n\n👑 <b>Вы стали основным владельцем Argent UserBot</b>\n🆔 <b>Ваш ID:</b> <code>{uid}</code>\n👤 <b>Имя:</b> {first_name}\n📱 <b>Username:</b> @{username}\n\n🔐 <b>Безопасность активирована:</b>\n• Только вы можете управлять ботом\n• Другие пользователи получат отказ в доступе\n• Ваш ID сохранен в конфигурации\n\n🚀 <b>Продолжаем установку...</b>')
            elif not self._owner_manager.is_owner(uid):
                await message.answer(f'❌ <b>Доступ запрещен</b>\n\n🔒 <b>Этот бот принадлежит другому пользователю</b>\n\n💡 <b>Хотите свой собственный юзербот?</b>\n📂 GitHub: github.com/lonly19/Argent-Userbot')
                return
            if len(self._state) >= self._max_states and uid not in self._state:
                await message.answer('⚠️ Слишком много активных сессий. Попробуйте позже.')
                return
            self._state[uid] = {'step': 'ask_api_id', 'timestamp': time.time()}
            await message.answer('👋 Добро пожаловать в Argent UserBot установщик!\n\nВведите ваш <b>api_id</b>:')

        @dp.message(F.text.regexp('^/info(.*)'))
        @owner_required
        async def handle_info(message: Message):
            await message.answer('<b>Argent UserBot</b> \n\n• Версия: 0.1.0\n• Статус: установка/настройка\n• Модулей: скоро будет доступно\n• GitHub: github.com/lonly19/Argent-Userbot\n')

        @dp.message(F.text.regexp('^/help(.*)'))
        @owner_required
        async def handle_help(message: Message):
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='📦 Основные', callback_data='help_cat:core')], [InlineKeyboardButton(text='🧰 Утилиты', callback_data='help_cat:utils')], [InlineKeyboardButton(text='⚙️ Система', callback_data='help_cat:system')]])
            await message.answer('<b>Помощь — Argent UserBot</b>\n\nВыберите категорию, чтобы увидеть список команд.\nСовет: используйте меню для навигации.', reply_markup=kb)

        @dp.callback_query(F.data.startswith('help_cat:'))
        @owner_required
        async def handle_help_cat(cb: CallbackQuery):
            cat = cb.data.split(':', 1)[1]
            if cat == 'core':
                text = '📦 <b>Основные</b>\n\n• .info — сведения о боте\n• .help — меню помощи'
            elif cat == 'utils':
                text = '🧰 <b>Утилиты</b>\n\n• (скоро)'
            else:
                text = '⚙️ <b>Система</b>\n\n• (скоро)'
            await cb.message.edit_text(text, reply_markup=cb.message.reply_markup)
            await cb.answer()

        @dp.message(F.text == '.help')
        @owner_required
        async def handle_dot_help(message: Message):
            return await handle_help(message)

        @dp.message(F.text == '.info')
        @owner_required
        async def handle_dot_info(message: Message):
            return await handle_info(message)

        @dp.message()
        @owner_required
        async def handle_text(message: Message):
            uid = message.from_user.id
            self._cleanup_old_states()
            if uid not in self._state:
                return
            st = self._state[uid]
            step = st.get('step')
            text = (message.text or '').strip()
            if step == 'ask_api_id':
                if not text.isdigit():
                    await message.answer('❗ api_id должен быть числом. Попробуйте снова.')
                    return
                st['api_id'] = int(text)
                st['step'] = 'ask_api_hash'
                await message.answer('Отлично. Теперь введите <b>api_hash</b>:')
                return
            if step == 'ask_api_hash':
                if len(text) < 10:
                    await message.answer('❗ api_hash выглядит слишком коротким. Попробуйте снова.')
                    return
                st['api_hash'] = text
                st['step'] = 'choose_method'
                kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='📱 QR-код', callback_data='login_qr'), InlineKeyboardButton(text='📞 SMS-код', callback_data='login_sms')]])
                await message.answer('Выберите метод входа:', reply_markup=kb)
                return
            if step == 'ask_phone':
                phone = text
                st['phone'] = phone
                api_id = st['api_id']
                api_hash = st['api_hash']
                flow = TelethonAuthFlow(api_id, api_hash, self._store)
                try:
                    token = await flow.start_sms_login(phone)
                    st['sms_token'] = token
                    st['step'] = 'ask_sms_code'
                    await message.answer('Мы отправили код. Введите его:')
                except AuthError as e:
                    await message.answer(f'❗ Ошибка: {e}')
                return
            if step == 'ask_sms_code':
                code = text
                api_id = st['api_id']
                api_hash = st['api_hash']
                token = st.get('sms_token')
                flow = TelethonAuthFlow(api_id, api_hash, self._store)
                try:
                    session_string = await flow.finish_sms_login(token, code, password=None)
                    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Пропустить', callback_data='skip_2fa')]])
                    await message.answer("✅ Вход выполнен! Если у вас есть 2FA, отправьте пароль, иначе нажмите кнопку 'Пропустить'.", reply_markup=kb)
                    st['pending_session'] = session_string
                    st['step'] = 'optional_2fa'
                except AuthError as e:
                    if '2FA' in str(e):
                        st['step'] = 'ask_2fa'
                        await message.answer('🔒 Укажите пароль 2FA:')
                    else:
                        await message.answer(f'❗ Ошибка: {e}')
                return
            if step == 'ask_2fa':
                password = text
                api_id = st['api_id']
                api_hash = st['api_hash']
                token = st.get('sms_token')
                flow = TelethonAuthFlow(api_id, api_hash, self._store)
                try:
                    session_string = await flow.finish_sms_login(token, code=None, password=password)
                    st['pending_session'] = session_string
                    st['step'] = 'save_and_done'
                    await self._finalize_install(uid, message)
                except AuthError as e:
                    await message.answer(f'❗ Ошибка 2FA: {e}')
                return
            if step == 'optional_2fa':
                st['step'] = 'save_and_done'
                await self._finalize_install(uid, message)
                return

        @dp.callback_query(F.data == 'login_qr')
        @owner_required
        async def handle_login_qr(cb: CallbackQuery):
            uid = cb.from_user.id
            st = self._state.setdefault(uid, {})
            api_id = st.get('api_id')
            api_hash = st.get('api_hash')
            flow = TelethonAuthFlow(api_id, api_hash, self._store)
            try:
                qr_png_b64, token, _ = await flow.start_qr_login()
                st['qr_token'] = token
                img_bytes = base64.b64decode(qr_png_b64.split(',', 1)[1])
                file = InputFile(io.BytesIO(img_bytes), filename='qr.png')
                await cb.message.answer_photo(photo=file, caption='Сканируйте QR в Telegram на другом устройстве')
                await cb.answer()
                for _ in range(60):
                    ok, session_string = await flow.poll_qr_login(token)
                    if ok:
                        st['pending_session'] = session_string
                        st['step'] = 'save_and_done'
                        await self._finalize_install(uid, cb.message)
                        return
                    await asyncio.sleep(2)
                await cb.message.answer('⌛ стекло время ожидания. Попробуйте снова.')
            except AuthError as e:
                await cb.message.answer(f'❗ Ошибка: {e}')

        @dp.callback_query(F.data == 'login_sms')
        @owner_required
        async def handle_login_sms(cb: CallbackQuery):
            uid = cb.from_user.id
            st = self._state.setdefault(uid, {})
            st['step'] = 'ask_phone'
            await cb.message.answer('Укажите номер телефона в международном формате, например +79991234567:')
            await cb.answer()

        @dp.callback_query(F.data == 'skip_2fa')
        @owner_required
        async def handle_skip_2fa(cb: CallbackQuery):
            uid = cb.from_user.id
            st = self._state.setdefault(uid, {})
            st['step'] = 'save_and_done'
            await self._finalize_install(uid, cb.message)
            await cb.answer()

    async def _finalize_install(self, uid: int, message: Message):
        st = self._state.get(uid) or {}
        sess = st.get('pending_session')
        api_id = st.get('api_id')
        api_hash = st.get('api_hash')
        if not (sess and api_id and api_hash):
            await message.answer('❗ Не хватает данных для сохранения установки.')
            return
        assert self._bot is not None
        bot_token = self._bot.token
        self._store.save_install(user_session=sess, bot_token=bot_token, api_id=api_id, api_hash=api_hash)
        await message.answer('🎉 Установка завершена! Argent UserBot готов к работе.')
        self._state.pop(uid, None)

    async def _delayed_start_userbot(self, delay: int=10):
        await asyncio.sleep(delay)
        try:
            import sys
            import subprocess
            import os
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
            script_path = os.path.join(project_root, 'start_argent.py')
            if not os.path.exists(script_path):
                return
            creationflags = 0
            if os.name == 'nt':
                creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            subprocess.Popen([sys.executable, script_path], cwd=project_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, creationflags=creationflags)
        except Exception:
            pass
global_bot_runner = BotRunner()
