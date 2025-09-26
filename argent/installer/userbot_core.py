import asyncio
import logging
from typing import Dict, List, Optional
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from .telethon_manager import SessionStore
logger = logging.getLogger(__name__)

class ArgentUserBot:

    def __init__(self, store: SessionStore):
        self.store = store
        self.client: Optional[TelegramClient] = None
        self.modules: Dict[str, object] = {}
        self.commands: Dict[str, callable] = {}
        self._running = False

    async def start(self):
        config = self.store.load_install()
        if not config:
            raise RuntimeError('Установка не найдена. Запустите веб-установщик.')
        api_id = config['api_id']
        api_hash = config['api_hash']
        user_session = config['user_session']
        self.client = TelegramClient(StringSession(user_session), api_id, api_hash)
        await self.client.start()
        self._register_builtin_commands()
        self.client.add_event_handler(self._handle_message, events.NewMessage(outgoing=True))
        self._running = True
        logger.info('Argent UserBot запущен')
        me = await self.client.get_me()
        logger.info(f"Вошли как: {me.first_name} (@{me.username or 'без username'})")

    def _register_builtin_commands(self):
        self.commands['.help'] = self._cmd_help
        self.commands['.info'] = self._cmd_info
        self.commands['.ping'] = self._cmd_ping
        self.commands['.modules'] = self._cmd_modules

    async def _handle_message(self, event: events.NewMessage.Event):
        text = event.raw_text
        if not text or not text.startswith('.'):
            return
        cmd_parts = text.split()
        cmd = cmd_parts[0].lower()
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        if cmd in self.commands:
            try:
                await self.commands[cmd](event, args)
            except Exception as e:
                await event.edit(f'❗ Ошибка команды: {e}')
                logger.exception(f'Command error: {cmd}')

    async def _cmd_help(self, event: events.NewMessage.Event, args: List[str]):
        help_text = '\n\n<b>🔧 Argent UserBot — Помощь</b>\n\n<b>📦 Основные команды:</b>\n\n• <code>.help</code> — это меню\n\n• <code>.info</code> — информация о боте\n\n• <code>.ping</code> — проверка работы\n\n• <code>.modules</code> — список модулей\n\n<b>🧰 Утилиты:</b>\n\n• (модули будут добавлены позже)\n\n<b>⚙️ Система:</b>\n\n• (системные команды скоро)\n\n<i>Совет: команды работают только в исходящих сообщениях</i>\n\n        '
        await event.edit(help_text, parse_mode='html')

    async def _cmd_info(self, event: events.NewMessage.Event, args: List[str]):
        me = await self.client.get_me()
        config = self.store.load_install()
        info_text = f"\n\n<b>⚙️ Argent UserBot</b>\n\n<b>Пользователь:</b> {me.first_name}\n\n<b>Username:</b> @{me.username or 'не установлен'}\n\n<b>ID:</b> <code>{me.id}</code>\n\n<b>Версия:</b> 1.0.0\n\n<b>Модулей:</b> {len(self.modules)}\n\n<b>Команд:</b> {len(self.commands)}\n\n<b>Статус:</b> ✅ Активен\n\n<b>API ID:</b> <code>{config.get('api_id', 'N/A')}</code>\n\n<b>GitHub:</b> github.com/lonly19/Argent-Userbot\n\n        "
        await event.edit(info_text, parse_mode='html')

    async def _cmd_ping(self, event: events.NewMessage.Event, args: List[str]):
        import time
        start = time.time()
        await event.edit('🏓 Понг!')
        end = time.time()
        ping_ms = round((end - start) * 1000, 2)
        await event.edit(f'🏓 <b>Понг!</b>\n⚡ <code>{ping_ms}ms</code>', parse_mode='html')

    async def _cmd_modules(self, event: events.NewMessage.Event, args: List[str]):
        if not self.modules:
            await event.edit('📦 <b>Модули не загружены</b>\n\n<i>Система модулей будет добавлена в следующих версиях</i>', parse_mode='html')
        else:
            module_list = '\n'.join([f'• {name}' for name in self.modules.keys()])
            await event.edit(f'📦 <b>Загруженные модули:</b>\n\n{module_list}', parse_mode='html')

    async def run_until_disconnected(self):
        if not self.client:
            raise RuntimeError('Клиент не инициализирован')
        await self.client.run_until_disconnected()

    async def stop(self):
        if self.client:
            await self.client.disconnect()
        self._running = False
        logger.info('Argent UserBot остановлен')

async def main():
    import os
    store = SessionStore(base_dir=os.getenv('ARGENT_DATA_DIR', '.argent_data'))
    bot = ArgentUserBot(store)
    try:
        await bot.start()
        print('✅ Argent UserBot запущен. Нажмите Ctrl+C для остановки.')
        await bot.run_until_disconnected()
    except KeyboardInterrupt:
        print('\n🛑 Остановка...')
    except Exception as e:
        print(f'❗ Ошибка: {e}')
    finally:
        await bot.stop()
if __name__ == '__main__':
    asyncio.run(main())
