import time
import asyncio
from argent.core.loader import ArgentModule

class CoreUtilsModule(ArgentModule):
    __version__ = '1.0.0'
    __author__ = 'github.com/lonly19/Argent-Userbot'
    __category__ = 'core'

    def __init__(self):
        super().__init__()
        self.description = '🧪 Базовые научные утилиты для повседневного использования'
        self.register_command('test', self.cmd_test, '🧪 Тестовая команда')
        self.register_command('echo', self.cmd_echo, '📢 Повторить сообщение')
        self.register_command('calc', self.cmd_calc, '🧮 Калькулятор')
        self.register_command('time', self.cmd_time, '🕐 Текущее время')
        self.register_command('uptime', self.cmd_uptime, '⏱️ Время работы')
        self.register_command('setprefix', self.cmd_setprefix, '🔧 Изменить префикс команд')

    async def on_load(self):
        self.start_time = time.time()

    async def cmd_test(self, event, args):
        await event.edit('⚗️ <b>Тест успешен!</b>\n🔬 Все системы работают нормально')

    async def cmd_echo(self, event, args):
        if not args:
            await event.edit('❌ **Использование:** `.echo <текст>`')
            return
        text = ' '.join(args)
        await event.edit(f'📢 <b>Эхо:</b> {text}')

    async def cmd_calc(self, event, args):
        if not args:
            await event.edit('❌ **Использование:** `.calc <выражение>`')
            return
        expression = ' '.join(args)
        try:
            allowed_chars = '0123456789+-*/.() '
            if not all((c in allowed_chars for c in expression)):
                await event.edit('❌ <b>Ошибка:</b> Недопустимые символы в выражении')
                return
            result = eval(expression)
            await event.edit(f'\n\n🧮 <b>Калькулятор</b>\n\n<b>📝 Выражение:</b> <code>{expression}</code>\n\n<b>🔢 Результат:</b> <code>{result}</code>\n\n<b>🔬 Тип:</b> <code>{type(result).__name__}</code>\n\n')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка вычисления:</b> <code>{str(e)}</code>')

    async def cmd_time(self, event, args):
        current_time = time.time()
        formatted_time = self.utils.format_timestamp(int(current_time), '%Y-%m-%d %H:%M:%S')
        await event.edit(f'\n\n🕐 <b>Временные данные</b>\n\n<b>📅 Дата и время:</b> <code>{formatted_time}</code>\n\n<b>⏰ Unix timestamp:</b> <code>{int(current_time)}</code>\n\n<b>🌍 Часовой пояс:</b> <code>UTC+3</code>\n\n')

    async def cmd_uptime(self, event, args):
        if not hasattr(self, 'start_time'):
            self.start_time = time.time()
        uptime_seconds = time.time() - self.start_time
        uptime_str = self.utils.format_duration(uptime_seconds)
        await event.edit(f'\n\n⏱️ <b>Время работы модуля</b>\n\n<b>🚀 Запущен:</b> {self.utils.format_timestamp(int(self.start_time))}\n\n<b>⏰ Работает:</b> <code>{uptime_str}</code>\n\n<b>🔬 Статус:</b> ✅ Активен\n\n')

    async def cmd_setprefix(self, event, args):
        if not args:
            current_prefix = getattr(self.client, 'command_prefix', '.')
            await event.edit(f'\n🔧 <b>Управление префиксом</b>\n\n<b>📝 Текущий префикс:</b> <code>{current_prefix}</code>\n\n<b>💡 Использование:</b> <code>.setprefix &lt;новый_префикс&gt;</code>\n\n<b>📋 Примеры:</b>\n• <code>.setprefix !</code>\n• <code>.setprefix /</code>\n• <code>.setprefix .</code>\n')
            return
        new_prefix = args[0]
        if len(new_prefix) > 3:
            await event.edit('❌ <b>Ошибка:</b> Префикс не может быть длиннее 3 символов')
            return
        if not new_prefix.strip():
            await event.edit('❌ <b>Ошибка:</b> Префикс не может быть пустым')
            return
        self.client.command_prefix = new_prefix
        await event.edit(f'\n✅ <b>Префикс изменен!</b>\n\n<b>🔧 Новый префикс:</b> <code>{new_prefix}</code>\n\n<b>💡 Пример использования:</b> <code>{new_prefix}help</code>\n\n<b>⚠️ Примечание:</b> Изменения действуют до перезапуска\n')
module = CoreUtilsModule()
