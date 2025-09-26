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
from .database import ArgentDatabase
from .utils import ArgentUtils
from .config_manager import ConfigManager
from .session_manager import SessionManager
from .session_storage import SessionStorage
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
            if self.config.is_first_run():
                if not self.session_manager.has_sessions():
                    raise RuntimeError('❌ No sessions found. Please run the setup process first.\nUse the web installer or create a session manually.')
                else:
                    self.config.mark_setup_completed()
            api_credentials = self.config.get_api_credentials()
            if not api_credentials:
                raise RuntimeError('❌ API credentials not found. Please configure API ID and hash.')
            self.client = await self.session_manager.load_session(api_credentials['api_id'], api_credentials['api_hash'])
            if not self.client:
                raise RuntimeError('❌ Failed to load session. Please check your saved sessions.')
            self.utils.client = self.client
            self.loader = ArgentLoader(self.client, self.db, self.utils)
            self._register_handlers()
            await self._load_configured_modules()
            bot_token = self.config.get_bot_token()
            if bot_token:
                await self._init_inline_bot(bot_token)
            self._running = True
            self._start_time = time.time()
            await self._display_startup_info()
        except Exception as e:
            logger.error(f'❌ Startup failed: {e}')
            raise

    def _load_config(self) -> Optional[Dict]:
        import json
        import os
        config_path = os.path.join(self.data_dir, 'config.json')
        if not os.path.exists(config_path):
            return None
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f'❌ Config load error: {e}')
            return None

    def _register_handlers(self):

        @self.client.on(events.NewMessage(outgoing=True))
        async def handle_outgoing(event: events.NewMessage.Event):
            text = event.raw_text
            if not text or not text.startswith('.'):
                return
            parts = text.split()
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            self._commands_executed += 1
            if self.loader and await self.loader.execute_command(command, event, args):
                return
            await self._handle_core_command(command, event, args)

    async def _handle_core_command(self, command: str, event: events.NewMessage.Event, args: List[str]):
        if command == '.help':
            await self._cmd_help(event, args)
        elif command == '.info':
            await self._cmd_info(event, args)
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

    async def _cmd_help(self, event: events.NewMessage.Event, args: List[str]):
        if not self.loader:
            await event.edit('❌ Module loader not initialized')
            return
        categories = self.loader.get_commands_by_category()
        help_text = f'\n\n**{self.emoji} {self.name} - Справочник**\n\n**🧪 Основные команды:**\n\n• `.help` — это меню\n\n• `.info` — информация о системе\n\n• `.ping` — проверка скорости\n\n• `.stats` — статистика работы\n\n**⚙️ Управление модулями:**\n\n• `.modules` — список модулей\n\n• `.load <module>` — загрузить модуль\n\n• `.unload <module>` — выгрузить модуль\n\n• `.reload <module>` — перезагрузить модуль\n\n**📚 Категории модулей:**\n\n'
        for category, commands in categories.items():
            if commands:
                emoji_map = {'core': '🧪', 'utils': '🔧', 'admin': '👑', 'fun': '🎭', 'misc': '📦'}
                emoji = emoji_map.get(category, '📁')
                help_text += f'• {emoji} <b>{category.title()}:</b> {len(commands)} команд\n'
        help_text += f'\n<b>🔬 Всего команд:</b> <code>{len(self.loader.commands)}</code>'
        await event.edit(help_text)

    async def _cmd_info(self, event: events.NewMessage.Event, args: List[str]):
        me = await self.client.get_me()
        uptime = time.time() - self._start_time
        db_stats = self.db.get_stats()
        platform_name = get_platform_name()
        platform_emoji = get_platform_emoji()
        info_text = f"\n\n<b>{self.emoji} {self.name} v{self.version}</b>\n\n<b>👤 Пользователь:</b>\n\n• <b>мя:</b> {me.first_name}\n\n• <b>Username:</b> @{me.username or 'не установлен'}\n\n• <b>ID:</b> <code>{me.id}</code>\n\n<b>🖥️ Платформа:</b>\n\n• <b>Система:</b> {platform_name}\n\n• <b>Архитектура:</b> <code>{platform.machine()}</code>\n\n• <b>Python:</b> <code>{platform.python_version()}</code>\n\n<b>📊 Статистика:</b>\n\n• <b>Время работы:</b> {self.utils.format_duration(uptime)}\n\n• <b>Команд выполнено:</b> <code>{self._commands_executed}</code>\n\n• <b>Модулей загружено:</b> <code>{(len(self.loader.modules) if self.loader else 0)}</code>\n\n<b>💾 База данных:</b>\n\n• <b>JSON секций:</b> <code>{db_stats.get('json_sections', 0)}</code>\n\n• <b>Данных модулей:</b> <code>{db_stats.get('module_data_count', 0)}</code>\n\n• <b>Данных пользователей:</b> <code>{db_stats.get('user_data_count', 0)}</code>\n\n• <b>Размер БД:</b> <code>{self.utils.format_bytes(db_stats.get('json_size', 0) + db_stats.get('sqlite_size', 0))}</code>\n\n<b>🔬 GitHub:</b> {self.author}\n\n{platform_emoji}\n"
        await event.edit(info_text)

    async def _cmd_ping(self, event: events.NewMessage.Event, args: List[str]):
        start_time = time.time()
        await event.edit('🧪 <b>Анализ соединения...</b>')
        end_time = time.time()
        ping_ms = round((end_time - start_time) * 1000, 2)
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
        await event.edit(f'{emoji} <b>Результат анализа:</b>\n⏱️ <b>Задержка:</b> <code>{ping_ms}ms</code>\n📊 <b>Статус:</b> {status}')

    async def _cmd_modules(self, event: events.NewMessage.Event, args: List[str]):
        if not self.loader:
            await event.edit('❌ Module loader not initialized')
            return
        modules = self.loader.get_all_modules()
        if not modules:
            await event.edit('📦 <b>Модули не загружены</b>\n\n🔬 Поместите модули в папку <code>argent/modules/</code>')
            return
        modules_text = f'<b>🧪 Загруженные модули ({len(modules)}):</b>\n\n'
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
        await event.edit(modules_text)

    async def _cmd_load(self, event: events.NewMessage.Event, args: List[str]):
        if not args:
            await event.edit('❌ **Использование:** `.load <module_name>`')
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
            await event.edit('❌ **Использование:** `.unload <module_name>`')
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
            await event.edit('❌ **Использование:** `.reload <module_name>`')
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
        stats_text = f"\n\n<b>📊 {self.name} - Статистика</b>\n\n<b>⏱️ Время работы:</b>\n\n• <b>Запущен:</b> {self.utils.format_timestamp(int(self._start_time))}\n\n• <b>Работает:</b> {self.utils.format_duration(uptime)}\n\n• <b>Команд выполнено:</b> <code>{self._commands_executed}</code>\n\n<b>🧪 Модули:</b>\n\n• <b>Загружено:</b> <code>{(len(self.loader.modules) if self.loader else 0)}</code>\n\n• <b>Команд доступно:</b> <code>{(len(self.loader.commands) if self.loader else 0)}</code>\n\n<b>💾 База данных:</b>\n\n• <b>JSON секций:</b> <code>{db_stats.get('json_sections', 0)}</code>\n\n• <b>Записей модулей:</b> <code>{db_stats.get('module_data_count', 0)}</code>\n\n• <b>Записей пользователей:</b> <code>{db_stats.get('user_data_count', 0)}</code>\n\n• <b>Записей чатов:</b> <code>{db_stats.get('chat_data_count', 0)}</code>\n\n• <b>Размер JSON:</b> <code>{self.utils.format_bytes(db_stats.get('json_size', 0))}</code>\n\n• <b>Размер SQLite:</b> <code>{self.utils.format_bytes(db_stats.get('sqlite_size', 0))}</code>\n\n<b>🔬 Система:</b>\n\n• <b>Версия:</b> <code>{self.version}</code>\n\n• <b>Автор:</b> {self.author}\n\n"
        await event.edit(stats_text)

    async def run_until_disconnected(self):
        if not self.client:
            raise RuntimeError('❌ Client not initialized')
        await self.client.run_until_disconnected()

    async def stop(self):
        if self.client:
            await self.client.disconnect()
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
    finally:
        await bot.stop()
if __name__ == '__main__':
    asyncio.run(main())
