import asyncio
import contextlib
import logging
import os
import platform
import time
from typing import Dict, List, Optional
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from .loader import ArgentLoader
from ..storage.database import ArgentDatabase
from ..utils.utils import ArgentUtils
from ..utils.config_manager import ConfigManager
from ..storage.session_manager import SessionManager
from ..storage.session_storage import SessionStorage
try:
    import psutil
except Exception:
    psutil = None
logger = logging.getLogger(__name__)

def get_platform_name() -> str:
    with contextlib.suppress(Exception):
        if os.path.isfile('/proc/device-tree/model'):
            with open('/proc/device-tree/model') as f:
                model = f.read().strip()
                if 'Orange' in model:
                    return f'🍊 {model}'
                return f'🍇 {model}' if 'Raspberry' in model else f'❓ {model}'
    system = platform.system().lower()
    if system == 'windows':
        return '💻 Windows'
    elif system == 'darwin':
        return '🍏 macOS'
    elif system == 'linux':
        try:
            with open('/etc/os-release') as f:
                os_info = f.read().lower()
                if 'ubuntu' in os_info:
                    return '🐧 Ubuntu Linux'
                elif 'debian' in os_info:
                    return '🌀 Debian Linux'
                elif 'centos' in os_info:
                    return '🔴 CentOS Linux'
                elif 'fedora' in os_info:
                    return '🎩 Fedora Linux'
                elif 'arch' in os_info:
                    return '⚡ Arch Linux'
        except:
            pass
        if os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup'):
            return '🐳 Docker Container'
        try:
            with open('/proc/version') as f:
                if 'microsoft' in f.read().lower():
                    return '🍀 WSL (Windows Subsystem for Linux)'
        except:
            pass
        return '🐧 Linux'
    return f'❓ {system.title()}'

def get_platform_emoji() -> str:
    system = platform.system().lower()
    BASE_EMOJIS = {'windows': '<emoji document_id=5431376038628171216>💻</emoji>', 'macos': '<emoji document_id=5431815203040510393>🍏</emoji>', 'linux': '<emoji document_id=5431456208487716895>🐧</emoji>', 'docker': '<emoji document_id=5352678227582152630>🐳</emoji>', 'wsl': '<emoji document_id=5431892851492112847>🍀</emoji>', 'unknown': '<emoji document_id=5393588431026674882>❓</emoji>'}
    if os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup'):
        return BASE_EMOJIS['docker']
    if system == 'linux':
        try:
            with open('/proc/version') as f:
                if 'microsoft' in f.read().lower():
                    return BASE_EMOJIS['wsl']
        except:
            pass
    return BASE_EMOJIS.get(system, BASE_EMOJIS['unknown'])

class ArgentUserBot:

    def __init__(self, data_dir: str='.argent_data'):
        self.data_dir = data_dir
        self.client: Optional[TelegramClient] = None
        self.config = ConfigManager(data_dir)
        self.db = ArgentDatabase(data_dir)
        self.session_storage = SessionStorage(data_dir)
        self.session_manager = SessionManager(self.session_storage)
        self.utils = ArgentUtils()
        self.loader: Optional[ArgentLoader] = None
        self._running = False
        self._start_time = 0
        self._commands_executed = 0
        self.name = self.config.get('userbot.name', 'Argent UserBot')
        self.version = self.config.get('userbot.version', '2.0.0')
        self.author = self.config.get('userbot.author', 'github.com/lonly19/Argent-Userbot')
        self.emoji = self.config.get('userbot.emoji', '⚗️')

    async def start(self):
        logger.info(f'{self.emoji} Starting {self.name} v{self.version}')
        try:
            api_credentials = self.config.get_api_credentials()
            if not api_credentials:
                raise RuntimeError('❌ API credentials not found. Please configure API ID and hash.')
            try:
                argent_session = self.config.get_session_string()
                if argent_session and (not self.session_manager.has_sessions()):
                    temp_client = TelegramClient(StringSession(argent_session), api_credentials['api_id'], api_credentials['api_hash'])
                    await temp_client.connect()
                    if await temp_client.is_user_authorized():
                        me = await temp_client.get_me()
                        self.session_storage.save_session(session_string=argent_session, phone=None, user_id=me.id, username=me.username, first_name=me.first_name)
                        self.config.clear_argent_session_key()
                        logger.info('🔄 Argent session_string migrated to sessions storage')
                    await temp_client.disconnect()
            except Exception as _e:
                logger.warning(f'⚠️ Argent session migration skipped: {_e}')
            if self.config.is_first_run():
                if not self.session_manager.has_sessions():
                    raise RuntimeError('❌ No sessions found. Please run the setup process first.\nUse the web installer or create a session manually.')
                self.config.mark_setup_completed()
            self.client = await self.session_manager.load_session(api_credentials['api_id'], api_credentials['api_hash'])
            if not self.client:
                raise RuntimeError('❌ Failed to load session. Please check your saved sessions.')
            self.utils.client = self.client
            try:
                self.client.parse_mode = 'html'
            except Exception:
                pass
            self.loader = ArgentLoader(self.client, self.db, self.utils)
            self._register_handlers()
            await self._load_configured_modules()
            bot_token = self.config.get_bot_token()
            if bot_token:
                await self._init_inline_bot(bot_token)
            self._running = True
            self._start_time = time.time()
            await self._display_startup_info()
            try:
                if not self.config.get('installed_banner_shown', False):
                    banner = 'Argent Userbot успешно установлен\nGitHub: github.com/lonly19/Argent-Userbot'
                    await self.client.send_message('me', banner)
                    self.config.set_system('installed_banner_shown', True)
            except Exception:
                pass
            await self._handle_restart_marker()
        except Exception as e:
            logger.error(f'❌ Startup failed: {e}')
            raise

    async def _load_configured_modules(self):
        try:
            if self.config.get('modules.auto_load', True):
                await self.loader.load_all_modules()
            else:
                modules_to_load = self.config.get('modules.load_on_startup', [])
                for module_name in modules_to_load:
                    await self.loader.load_module(module_name)
            logger.info(f'🧪 Loaded {len(self.loader.modules)} modules with {len(self.loader.commands)} commands')
        except Exception as e:
            logger.error(f'❌ Module loading error: {e}')

    async def _init_inline_bot(self, bot_token: str):
        try:
            from ..bot.inline_bot import ArgentInlineBot
            self.inline_bot = ArgentInlineBot(bot_token, self.db, self.client)
            await self.inline_bot.start()
            logger.info('🤖 Inline bot initialized')
        except Exception as e:
            logger.warning(f'⚠️ Inline bot initialization failed: {e}')

    async def _display_startup_info(self):
        try:
            user_info = await self.session_manager.get_current_user()
            if user_info:
                logger.info('✅ User session authorized')
                pass
        except Exception as e:
            logger.error(f'❌ Error displaying startup info: {e}')

    def _register_handlers(self):

        @self.client.on(events.NewMessage(outgoing=True))
        async def handle_outgoing(event: events.NewMessage.Event):
            text = event.raw_text
            if not text or not text.startswith('.'):
                return
            parts = text.split()
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            if self.config.get('interface.hide_commands', False):
                return
            self._commands_executed += 1
            if self.loader and await self.loader.execute_command(command, event, args):
                return
            await self._handle_core_command(command, event, args)

    async def _handle_core_command(self, command: str, event: events.NewMessage.Event, args: List[str]):
        if command == '.help':
            await self._cmd_help(event, args)
        elif command == '.info':
            await self._cmd_info(event, args)
        elif command == '.sysinfo':
            await self._cmd_sysinfo(event, args)
        elif command == '.ping':
            await self._cmd_ping(event, args)
        elif command == '.modules':
            await self._cmd_modules(event, args)
        elif command == '.load':
            await self._cmd_load(event, args)
        elif command == '.unload':
            await self._cmd_unload(event, args)
        elif command == '.reload':
            await self._cmd_reload(event, args)
        elif command == '.stats':
            await self._cmd_stats(event, args)
        elif command == '.config':
            await self._cmd_config(event, args)
        elif command == '.sessions':
            await self._cmd_sessions(event, args)
        elif command == '.restart':
            await self._cmd_restart(event, args)

    async def _cmd_help(self, event: events.NewMessage.Event, args: List[str]):
        if not self.loader:
            await event.edit('❌ Module loader not initialized')
            return
        categories = self.loader.get_commands_by_category()
        help_text = f'<b>{self.emoji} {self.name} - Справочник</b>\n<blockquote><b>🧪 Основные команды:</b>\n<code>.help</code> — это меню\n<code>.info</code> — краткая информация о боте\n<code>.sysinfo</code> — подробная системная информация\n<code>.ping</code> — проверка скорости\n<code>.stats</code> — статистика работы\n<code>.config</code> — управление конфигурацией\n<code>.sessions</code> — управление сессиями\n<code>.restart</code> — перезапуск юзербота\n\n<b>⚙️ Управление модулями:</b>\n<code>.modules</code> — список модулей\n<code>.load &lt;module&gt;</code> — загрузить модуль\n<code>.unload &lt;module&gt;</code> — выгрузить модуль\n<code>.reload &lt;module&gt;</code> — перезагрузить модуль\n\n<b>📚 Категории модулей:</b>\n'
        for category, commands in categories.items():
            if commands:
                emoji_map = {'core': '🧪', 'utils': '🔧', 'admin': '👑', 'fun': '🎭', 'misc': '📦'}
                emoji = emoji_map.get(category, '📁')
                help_text += f'{emoji} <b>{category.title()}:</b> {len(commands)} команд\n'
        help_text += f'\n<b>🔬 Всего команд:</b> <code>{len(self.loader.commands)}</code></blockquote>'
        await event.edit(help_text)

    async def _cmd_info(self, event: events.NewMessage.Event, args: List[str]):
        cpu_text = 'N/A'
        ram_text = 'N/A'
        if psutil:
            try:
                cpu_text = f'{psutil.cpu_percent(interval=0):.1f}%'
                ram_text = f'{psutil.virtual_memory().percent:.1f}%'
            except:
                pass
        info_text = f'<b>{self.emoji} {self.name} v{self.version}</b>\n<blockquote><b>CPU:</b> {cpu_text}\n<b>RAM:</b> {ram_text}\n<b>GitHub:</b> {self.author}\n<b>Platform:</b> {platform_name}</blockquote>'
        await event.edit(info_text, parse_mode='html')

    async def _cmd_sysinfo(self, event: events.NewMessage.Event, args: List[str]):
        uptime = time.time() - self._start_time
        db_stats = self.db.get_stats()
        system_info = ''
        if psutil:
            try:
                cpu = psutil.cpu_percent(interval=0)
                vm = psutil.virtual_memory()
                mem_used = vm.used
                mem_total = vm.total
                mem_pct = vm.percent
                proc = psutil.Process()
                rss = getattr(proc.memory_info(), 'rss', 0)
                threads = proc.num_threads()
                py_ver = platform.python_version()
                os_name = platform.system()
                system_info = f'• <b>Операционная система:</b> <code>{os_name}</code>\n• <b>Версия Python:</b> <code>{py_ver}</code>\n• <b>Загрузка CPU:</b> <code>{cpu:.1f}%</code>\n• <b>Использование RAM:</b> <code>{mem_pct:.1f}%</code> ({self.utils.format_bytes(mem_used)}/{self.utils.format_bytes(mem_total)})\n• <b>RAM процесса:</b> <code>{self.utils.format_bytes(rss)}</code>\n• <b>Активных потоков:</b> <code>{threads}</code>'
            except Exception:
                system_info = '• <b>Системная информация:</b> <code>Ошибка получения данных</code>'
        else:
            system_info = '• <b>Системная информация:</b> <code>psutil недоступен</code>'
        sysinfo_text = f"<b>🖥️ {self.name} - Системная информация</b>\n<blockquote><b>💾 База данных:</b>\n• <b>JSON секций:</b> <code>{db_stats.get('json_sections', 0)}</code>\n• <b>Данных модулей:</b> <code>{db_stats.get('module_data_count', 0)}</code>\n• <b>Данных пользователей:</b> <code>{db_stats.get('user_data_count', 0)}</code>\n• <b>Размер базы данных:</b> <code>{self.utils.format_bytes(db_stats.get('json_size', 0) + db_stats.get('sqlite_size', 0))}</code>\n\n<b>🖥️ Система:</b>\n{system_info}\n\n<b>📊 Статистика работы:</b>\n• <b>Время работы:</b> <code>{self.utils.format_duration(uptime)}</code>\n• <b>Версия бота:</b> <code>{self.version}</code>\n• <b>Команд выполнено:</b> <code>{self._commands_executed}</code>\n• <b>Модулей загружено:</b> <code>{(len(self.loader.modules) if self.loader else 0)}</code></blockquote>"
        await event.edit(sysinfo_text)

    async def _handle_restart_marker(self):
        try:
            marker = self.config.get('restart_marker')
            if not marker:
                return
            self.config.delete_system('restart_marker')
            chat_id = marker.get('chat_id')
            msg_id = marker.get('message_id')
            started_at = marker.get('started_at', time.time())
            elapsed = max(0, time.time() - started_at)
            text = f'✅ <b>{self.name} перезапущен</b>\n⏱️ <b>Загрузка заняла:</b> {self.utils.format_duration(elapsed)}'
            try:
                await self.client.edit_message(chat_id, msg_id, text)
            except Exception:
                await self.client.send_message(chat_id, text)
        except Exception as e:
            logger.warning(f'⚠️ Restart marker handling failed: {e}')

    async def _cmd_ping(self, event: events.NewMessage.Event, args: List[str]):
        start_time = time.time()
        await event.edit('🌙')
        end_time = time.time()
        ping_ms = round((end_time - start_time) * 1000, 2)
        uptime = time.time() - self._start_time
        if ping_ms < 100:
            status = '⚡ <b>Молниеносно</b>'
            emoji = '🚀'
        elif ping_ms < 300:
            status = '✅ <b>Отлично</b>'
            emoji = '⚗️'
        elif ping_ms < 500:
            status = '⚠️ <b>Нормально</b>'
            emoji = '🧪'
        else:
            status = '🐌 <b>Медленно</b>'
            emoji = '🔬'
        await event.edit(f'{emoji} <b>Пинг:</b> <code>{ping_ms} ms</code>\n⏳ <b>Аптайм:</b> {self.utils.format_duration(uptime)}\n📊 <b>Статус:</b> {status}')

    async def _cmd_modules(self, event: events.NewMessage.Event, args: List[str]):
        if not self.loader:
            await event.edit('❌ Module loader not initialized')
            return
        modules = self.loader.get_all_modules()
        if not modules:
            await event.edit('📦 <b>Модули не загружены</b>\n\n🔬 Поместите модули в папку <code>argent/modules/</code>')
            return
        modules_text = f'<b>🧪 Загруженные модули ({len(modules)}):</b>\n<blockquote>'
        categories = {}
        for name, info in modules.items():
            if info.category not in categories:
                categories[info.category] = []
            categories[info.category].append(info)
        for category, module_list in categories.items():
            emoji_map = {'core': '🧪', 'utils': '🔧', 'admin': '👑', 'fun': '🎭', 'misc': '📦'}
            emoji = emoji_map.get(category, '📁')
            modules_text += f'<b>{emoji} {category.title()}:</b>\n'
            for info in module_list:
                status = '✅' if info.loaded else '❌'
                modules_text += f'• {status} <code>{info.name}</code> v{info.version} - {len(info.commands)} команд\n'
            modules_text += '\n'
        modules_text += '</blockquote>'
        await event.edit(modules_text)

    async def _cmd_load(self, event: events.NewMessage.Event, args: List[str]):
        if not args:
            await event.edit('❌ Использование: `.load <module_name>`')
            return
        module_name = args[0]
        if not self.loader:
            await event.edit('❌ Module loader not initialized')
            return
        await event.edit(f'🔄 <b>Загрузка модуля</b> <code>{module_name}</code>...')
        success = await self.loader.load_module(module_name)
        if success:
            info = self.loader.get_module_info(module_name)
            await event.edit(f'✅ <b>Модуль загружен:</b> <code>{info.name}</code> v{info.version}\n🔧 <b>Команд:</b> {len(info.commands)}')
        else:
            await event.edit(f'❌ <b>Ошибка загрузки модуля:</b> <code>{module_name}</code>')

    async def _cmd_unload(self, event: events.NewMessage.Event, args: List[str]):
        if not args:
            await event.edit('❌ Использование: `.unload <module_name>`')
            return
        module_name = args[0]
        if not self.loader:
            await event.edit('❌ Module loader not initialized')
            return
        await event.edit(f'🔄 <b>Выгрузка модуля</b> <code>{module_name}</code>...')
        success = await self.loader.unload_module(module_name)
        if success:
            await event.edit(f'✅ <b>Модуль выгружен:</b> <code>{module_name}</code>')
        else:
            await event.edit(f'❌ <b>Ошибка выгрузки модуля:</b> <code>{module_name}</code>')

    async def _cmd_reload(self, event: events.NewMessage.Event, args: List[str]):
        if not args:
            await event.edit('❌ Использование: `.reload <module_name>`')
            return
        module_name = args[0]
        if not self.loader:
            await event.edit('❌ Module loader not initialized')
            return
        await event.edit(f'🔄 <b>Перезагрузка модуля</b> <code>{module_name}</code>...')
        success = await self.loader.reload_module(module_name)
        if success:
            info = self.loader.get_module_info(module_name)
            await event.edit(f'✅ <b>Модуль перезагружен:</b> <code>{info.name}</code> v{info.version}\n🔧 <b>Команд:</b> {len(info.commands)}')
        else:
            await event.edit(f'❌ <b>Ошибка перезагрузки модуля:</b> <code>{module_name}</code>')

    async def _cmd_stats(self, event: events.NewMessage.Event, args: List[str]):
        uptime = time.time() - self._start_time
        db_stats = self.db.get_stats()
        stats_text = f"\n\n<b>📊 {self.name} - Статистика</b>\n\n<b>⏱️ Время работы:</b>\n• <b>Запущен:</b> {self.utils.format_timestamp(int(self._start_time))}\n• <b>Работает:</b> {self.utils.format_duration(uptime)}\n• <b>Команд выполнено:</b> <code>{self._commands_executed}</code>\n\n<b>🧪 Модули:</b>\n• <b>Загружено:</b> <code>{(len(self.loader.modules) if self.loader else 0)}</code>\n• <b>Команд доступно:</b> <code>{(len(self.loader.commands) if self.loader else 0)}</code>\n\n<b>💾 База данных:</b>\n• <b>JSON секций:</b> <code>{db_stats.get('json_sections', 0)}</code>\n• <b>Записей модулей:</b> <code>{db_stats.get('module_data_count', 0)}</code>\n• <b>Записей пользователей:</b> <code>{db_stats.get('user_data_count', 0)}</code>\n• <b>Записей чатов:</b> <code>{db_stats.get('chat_data_count', 0)}</code>\n• <b>Размер JSON:</b> <code>{self.utils.format_bytes(db_stats.get('json_size', 0))}</code>\n• <b>Размер SQLite:</b> <code>{self.utils.format_bytes(db_stats.get('sqlite_size', 0))}</code>\n\n<b>🔬 Система:</b>\n• <b>Версия:</b> <code>{self.version}</code>\n• <b>Автор:</b> {self.author}\n\n"
        await event.edit(stats_text)

    async def _cmd_config(self, event: events.NewMessage.Event, args: List[str]):
        if not args:
            config_text = f'<b>⚙️ {self.name} - Конфигурация</b>\n<blockquote><b>📋 Использование:</b>\n<code>.config get &lt;path&gt;</code> — получить значение\n<code>.config set &lt;path&gt; &lt;value&gt;</code> — установить значение\n<code>.config reset &lt;path&gt;</code> — сбросить к умолчанию\n<code>.config list</code> — показать всю конфигурацию\n\n<b>📝 Примеры:</b>\n<code>.config get userbot.name</code>\n<code>.config set userbot.emoji 🧪</code>\n<code>.config reset modules.auto_load</code></blockquote>'
            await event.edit(config_text)
            return
        action = args[0].lower()
        if action == 'get' and len(args) > 1:
            path = args[1]
            value = self.config.get(path)
            await event.edit(f'<b>⚙️ Конфигурация</b>\n\n<b>Путь:</b> <code>{path}</code>\n<b>Значение:</b> <code>{value}</code>')
        elif action == 'set' and len(args) > 2:
            path = args[1]
            value = ' '.join(args[2:])
            try:
                import json
                value = json.loads(value)
            except:
                pass
            self.config.set(path, value)
            await event.edit(f'✅ <b>Конфигурация обновлена</b>\n\n<b>Путь:</b> <code>{path}</code>\n<b>Новое значение:</b> <code>{value}</code>')
        elif action == 'reset' and len(args) > 1:
            path = args[1]
            self.config.reset_to_default(path)
            new_value = self.config.get(path)
            await event.edit(f'🔄 <b>Конфигурация сброшена</b>\n\n<b>Путь:</b> <code>{path}</code>\n<b>Значение по умолчанию:</b> <code>{new_value}</code>')
        elif action == 'list':
            config_data = self.config.get_all_config()
            config_text = '<b>📋 Полная конфигурация:</b>\n\n'
            for section, values in config_data.items():
                if isinstance(values, dict):
                    config_text += f'<b>{section}:</b>\n'
                    for key, value in values.items():
                        config_text += f'• <code>{section}.{key}</code>: <code>{value}</code>\n'
                else:
                    config_text += f'• <code>{section}</code>: <code>{values}</code>\n'
                config_text += '\n'
            if len(config_text) > 4000:
                config_text = config_text[:4000] + '\n\n... (обрезано)'
            await event.edit(config_text)
        else:
            await event.edit('❌ <b>Неверное использование</b>\n\nИспользуйте <code>.config</code> без аргументов для справки')

    async def _cmd_sessions(self, event: events.NewMessage.Event, args: List[str]):
        if not args:
            sessions = self.session_manager.list_sessions()
            current_session_id = self.session_manager.get_current_session_id()
            if not sessions:
                await event.edit('📱 <b>Сессии не найдены</b>')
                return
            sessions_text = f'<b>📱 Управление сессиями ({len(sessions)})</b>\n\n'
            for session_info in sessions:
                is_current = session_info['session_id'] == current_session_id
                status = '🟢 Активная' if is_current else '⚪ Неактивная'
                sessions_text += f'<b>{status}</b>\n'
                sessions_text += f"• <b>ID:</b> <code>{session_info['session_id']}</code>\n"
                sessions_text += f"• <b>Имя:</b> <code>{session_info['first_name'] or 'не указано'}</code>\n"
                sessions_text += f"• <b>Username:</b> <code>@{session_info['username'] or 'не указан'}</code>\n"
                sessions_text += f"• <b>Создана:</b> <code>{session_info['created_at'][:19]}</code>\n\n"
            sessions_text += '<b>📋 Команды:</b>\n'
            sessions_text += '• `.sessions switch <id>` — переключиться\n'
            sessions_text += '• `.sessions delete <id>` — удалить\n'
            sessions_text += '• <code>.sessions backup</code> — создать резервную копию'
            await event.edit(sessions_text)
            return
        action = args[0].lower()
        if action == 'switch' and len(args) > 1:
            session_id = args[1]
            api_creds = self.config.get_api_credentials()
            if not api_creds:
                await event.edit('❌ API credentials не найдены')
                return
            success = await self.session_manager.switch_session(api_creds['api_id'], api_creds['api_hash'], session_id)
            if success:
                await event.edit(f'✅ <b>Переключено на сессию:</b> <code>{session_id}</code>')
            else:
                await event.edit(f'❌ <b>Ошибка переключения на сессию:</b> <code>{session_id}</code>')
        elif action == 'delete' and len(args) > 1:
            session_id = args[1]
            current_session_id = self.session_manager.get_current_session_id()
            if session_id == current_session_id:
                await event.edit('❌ <b>Нельзя удалить активную сессию</b>')
                return
            success = self.session_manager.delete_session(session_id)
            if success:
                await event.edit(f'✅ <b>Сессия удалена:</b> <code>{session_id}</code>')
            else:
                await event.edit(f'❌ <b>Ошибка удаления сессии:</b> <code>{session_id}</code>')
        elif action == 'backup':
            try:
                backup_path = self.session_manager.backup_sessions()
                await event.edit(f'✅ <b>Резервная копия создана:</b>\n<code>{backup_path}</code>')
            except Exception as e:
                await event.edit(f'❌ <b>Ошибка создания резервной копии:</b> {e}')
        else:
            await event.edit('❌ <b>Неверное использование</b>\n\nИспользуйте <code>.sessions</code> без аргументов для справки')

    async def _cmd_restart(self, event: events.NewMessage.Event, args: List[str]):
        start_ts = time.time()
        await event.edit('🔄 <b>Перезагружаюсь...</b>')
        try:
            marker = {'chat_id': event.chat_id, 'message_id': event.id, 'started_at': start_ts}
            self.config.set_system('restart_marker', marker)
        except Exception:
            pass
        await self.stop()
        import sys
        import os
        try:
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception:
            sys.exit(0)

    async def run_until_disconnected(self):
        if not self.client:
            raise RuntimeError('❌ Client not initialized')
        await self.client.run_until_disconnected()

    async def stop(self):
        try:
            if hasattr(self, 'inline_bot'):
                await self.inline_bot.stop()
        except Exception:
            pass
        try:
            await self.session_manager.disconnect()
        except Exception:
            pass
        self._running = False
        logger.info(f'🛑 {self.name} stopped')

async def main():
    import os
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    data_dir = os.getenv('ARGENT_DATA_DIR', '.argent_data')
    bot = ArgentUserBot(data_dir)
    try:
        await bot.start()
        print(f'✅ {bot.name} v{bot.version} started successfully!')
        print('🔬 Press Ctrl+C to stop')
        await bot.run_until_disconnected()
    except KeyboardInterrupt:
        print('\n🛑 Stopping...')
    except Exception as e:
        print(f'❌ Error: {e}')
        logger.exception('Fatal error')
        if 'session' in str(e).lower() or 'api' in str(e).lower():
            print('\n💡 Возможные решения:')
            print('1. Запустите веб-установщик для настройки')
            print('2. Проверьте файлы сессий в папке sessions/')
            print('3. Убедитесь, что API ID и Hash настроены правильно')
    finally:
        await bot.stop()
if __name__ == '__main__':
    asyncio.run(main())
