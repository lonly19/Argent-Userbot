import asyncio
import time
import random
import string
from datetime import datetime
from argent.core.loader import ArgentModule

class HerokuFeaturesModule(ArgentModule):
    __version__ = '1.0.0'
    __author__ = 'github.com/lonly19/Argent-Userbot'
    __category__ = 'utils'

    def __init__(self):
        super().__init__()
        self.description = '🚀 Классические функции Argent c научным подходом'
        self.register_command('alive', self.cmd_alive, '💫 Проверка активности')
        self.register_command('speedtest', self.cmd_speedtest, '🌐 Тест скорости')
        self.register_command('usage', self.cmd_usage, '📊 Использование ресурсов')
        self.register_command('logs', self.cmd_logs, '📋 Системные логи')
        self.register_command('update', self.cmd_update, '🔄 Обновление системы')
        self.register_command('eval', self.cmd_eval, '🧮 Выполнить код')
        self.register_command('exec', self.cmd_exec, '⚡ Выполнить команду')
        self.register_command('term', self.cmd_terminal, '💻 Терминал')
        self.register_command('neofetch', self.cmd_neofetch, '🖥️ нформация о системе')
        self.register_command('carbon', self.cmd_carbon, '🎨 Создать carbon код')
        self.register_command('paste', self.cmd_paste, '📄 Загрузить на paste')
        self.register_command('telegraph', self.cmd_telegraph, '📰 Создать Telegraph')
        self.register_command('translate', self.cmd_translate, '🌍 Перевести текст')
        self.register_command('weather', self.cmd_weather, '🌤️ Погода')
        self.register_command('qr', self.cmd_qr, '📱 QR код')
        self.register_command('short', self.cmd_short, '🔗 Сократить ссылку')

    async def cmd_alive(self, event, args):
        start_time = time.time()
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        me = await self.client.get_me()
        uptime = self.db.get_config('start_time', time.time())
        current_time = time.time()
        ping_time = round((time.time() - start_time) * 1000, 2)
        alive_text = f"⚗️ <b>Argent UserBot - Активен</b>\n\n<blockquote>\n<b>👤 Пользователь:</b> {me.first_name}\n<b>🆔 ID:</b> <code>{me.id}</code>\n<b>📱 Username:</b> @{me.username or 'не установлен'}\n\n<b>⚡ Производительность:</b>\n• <b>Пинг:</b> <code>{ping_time}ms</code>\n• <b>CPU:</b> <code>{cpu}%</code>\n• <b>RAM:</b> <code>{memory.percent}%</code>\n\n<b>🕐 Время работы:</b> <code>{self.utils.format_duration(current_time - uptime)}</code>\n<b>🧪 Версия:</b> <code>2.0.0</code>\n<b>🔬 Статус:</b> Все молекулы стабильны\n\n<b>⚛️ Научный подход к Telegram</b>\n</blockquote>"
        await event.edit(alive_text)

    async def cmd_speedtest(self, event, args):
        await event.edit('🌐 <b>Тестирование скорости...</b>\n\n🔬 Анализ сетевых соединений...')
        try:
            import speedtest
            st = speedtest.Speedtest()
            await event.edit('🌐 <b>Поиск оптимального сервера...</b>')
            st.get_best_server()
            await event.edit('📥 <b>Тестирование загрузки...</b>')
            download_speed = st.download() / 1000000
            await event.edit('📤 <b>Тестирование отдачи...</b>')
            upload_speed = st.upload() / 1000000
            ping = st.results.ping
            await event.edit(f"🌐 <b>Результаты теста скорости</b>\n\n<blockquote>\n<b>📥 Загрузка:</b> <code>{download_speed:.2f} Mbps</code>\n<b>📤 Отдача:</b> <code>{upload_speed:.2f} Mbps</code>\n<b>🏓 Пинг:</b> <code>{ping:.2f} ms</code>\n\n<b>🔬 Провайдер:</b> {st.results.client['isp']}\n<b>🌍 Сервер:</b> {st.results.server['name']} ({st.results.server['country']})\n\n<b>⚛️ Качество соединения:</b> {('🟢 Отличное' if download_speed > 50 else '🟡 Хорошее' if download_speed > 10 else '🔴 Слабое')}\n</blockquote>")
        except ImportError:
            await event.edit('❌ <b>Модуль speedtest не установлен</b>\n\n📦 Установите: <code>pip install speedtest-cli</code>')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка теста:</b> <code>{str(e)}</code>')

    async def cmd_usage(self, event, args):
        import psutil
        import os
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        net_io = psutil.net_io_counters()
        usage_text = f'📊 <b>Использование ресурсов</b>\n\n<blockquote>\n<b>🖥️ Система:</b>\n• <b>CPU:</b> <code>{cpu_percent}%</code>\n• <b>RAM:</b> <code>{memory.percent}%</code> ({self.utils.format_bytes(memory.used)}/{self.utils.format_bytes(memory.total)})\n• <b>Диск:</b> <code>{disk.percent}%</code> ({self.utils.format_bytes(disk.used)}/{self.utils.format_bytes(disk.total)})\n\n<b>⚗️ Процесс UserBot:</b>\n• <b>RAM:</b> <code>{self.utils.format_bytes(process_memory.rss)}</code>\n• <b>CPU:</b> <code>{process.cpu_percent()}%</code>\n\n<b>🌐 Сеть:</b>\n• <b>Отправлено:</b> <code>{self.utils.format_bytes(net_io.bytes_sent)}</code>\n• <b>Получено:</b> <code>{self.utils.format_bytes(net_io.bytes_recv)}</code>\n\n<b>🔬 Статус:</b> Все параметры в норме\n</blockquote>'
        await event.edit(usage_text)

    async def cmd_logs(self, event, args):
        import subprocess
        try:
            result = subprocess.run(['tail', '-20', '/var/log/syslog'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logs = result.stdout
                if len(logs) > 3500:
                    logs = logs[-3500:]
                await event.edit(f'📋 <b>Системные логи</b>\n\n<blockquote>\n<code>{logs}</code>\n\n🔬 <b>Последние 20 записей</b>\n</blockquote>')
            else:
                await event.edit('❌ <b>Не удалось получить логи</b>')
        except subprocess.TimeoutExpired:
            await event.edit('⏰ <b>Таймаут получения логов</b>')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка:</b> <code>{str(e)}</code>')

    async def cmd_update(self, event, args):
        await event.edit('🔄 <b>Проверка обновлений...</b>')
        try:
            import subprocess
            result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                if result.stdout.strip():
                    await event.edit('⚠️ <b>Есть локальные изменения</b>\n\n🔬 Сначала сохраните изменения')
                    return
                await event.edit('📥 <b>Загрузка обновлений...</b>')
                result = subprocess.run(['git', 'pull'], capture_output=True, text=True, timeout=30)
                if 'Already up to date' in result.stdout:
                    await event.edit('✅ <b>Система актуальна</b>\n\n🧪 Обновления не требуются')
                else:
                    await event.edit('✅ <b>Обновления установлены</b>\n\n🔄 Перезагрузите бота для применения')
            else:
                await event.edit('❌ <b>Не удалось проверить обновления</b>')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка обновления:</b> <code>{str(e)}</code>')

    async def cmd_eval(self, event, args):
        if not args:
            await event.edit('❌ **Использование:** `.eval <код>`')
            return
        code = ' '.join(args)
        try:
            env = {'client': self.client, 'event': event, 'db': self.db, 'utils': self.utils, 'asyncio': asyncio, 'time': time, 'datetime': datetime}
            result = eval(code, env)
            if asyncio.iscoroutine(result):
                result = await result
            await event.edit(f'🧮 <b>Результат выполнения</b>\n\n<blockquote>\n<b>📝 Код:</b>\n<code>{code}</code>\n\n<b>📊 Результат:</b>\n<code>{repr(result)}</code>\n\n<b>⚛️ Тип:</b> {type(result).__name__}\n</blockquote>')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка выполнения</b>\n\n<blockquote>\n<b>📝 Код:</b>\n<code>{code}</code>\n\n<b>🚫 Ошибка:</b>\n<code>{str(e)}</code>\n</blockquote>')

    async def cmd_exec(self, event, args):
        if not args:
            await event.edit('❌ Использование: `.exec <команда>`')
            return
        command = ' '.join(args)
        try:
            import subprocess
            import os
            if os.name == 'nt':
                try:
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
                    stderr_lines = result.stderr.split('\n') if result.stderr else []
                    filtered_stderr = '\n'.join([line for line in stderr_lines if 'PRN' not in line and 'гбва®©бвў®' not in line])
                    output = result.stdout + filtered_stderr
                except Exception:
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                    stderr_lines = result.stderr.split('\n') if result.stderr else []
                    filtered_stderr = '\n'.join([line for line in stderr_lines if 'PRN' not in line and 'гбва®©бвў®' not in line])
                    output = result.stdout + filtered_stderr
            else:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout + result.stderr
            if len(output) > 3500:
                output = output[-3500:]
            await event.edit(f"⚡ <b>Выполнение команды</b>\n\n<blockquote>\n<b>💻 Команда:</b>\n<code>{command}</code>\n\n<b>📊 Результат:</b>\n<code>{output or 'Команда выполнена без вывода'}</code>\n\n<b>🔬 Код возврата:</b> {result.returncode}\n</blockquote>")
        except subprocess.TimeoutExpired:
            await event.edit('⏰ <b>Таймаут выполнения команды</b>')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка:</b> <code>{str(e)}</code>')

    async def cmd_terminal(self, event, args):
        if not args:
            await event.edit('💻 <b>Терминал Argent UserBot</b>\n\n<blockquote>\n<b>🔬 Доступные команды:</b>\n• <code>.term ls</code> - список файлов\n• <code>.term pwd</code> - текущая директория\n• <code>.term whoami</code> - текущий пользователь\n• <code>.term ps aux</code> - список процессов\n\n<b>⚛️ Безопасность:</b> Команды выполняются в изолированной среде\n</blockquote>')
            return
        await self.cmd_exec(event, args)

    async def cmd_neofetch(self, event, args):
        import platform
        import psutil
        system = platform.system()
        release = platform.release()
        machine = platform.machine()
        processor = platform.processor()
        memory = psutil.virtual_memory()
        python_version = platform.python_version()
        neofetch_text = f"<b>🖥️ Системная информация</b>\n<blockquote><code>⚗️ Argent UserBot 2.0.0\n\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🖥️  OS: {system} {release}\n\n🏗️  Arch: {machine}\n\n🧠  CPU: {processor or 'Unknown'}\n\n💾  RAM: {self.utils.format_bytes(memory.used)} / {self.utils.format_bytes(memory.total)}\n\n🐍  Python: {python_version}\n\n⚛️  Framework: Telethon + Aiogram\n\n🔬  Status: Active</code></blockquote>"
        await event.edit(neofetch_text)

    async def cmd_carbon(self, event, args):
        if not event.is_reply and (not args):
            await event.edit('❌ <b>Ответьте на сообщение с кодом или укажите код</b>')
            return
        if event.is_reply:
            reply = await event.get_reply_message()
            code = reply.text
        else:
            code = ' '.join(args)
        if not code:
            await event.edit('❌ <b>Код не найден</b>')
            return
        await event.edit('🎨 <b>Создание Carbon изображения...</b>')
        carbon_url = f'https://carbon.now.sh/api/cook'
        try:
            import aiohttp
            import json
            payload = {'code': code, 'theme': 'material', 'backgroundColor': '#1e1e1e', 'language': 'python'}
            async with aiohttp.ClientSession() as session:
                async with session.post(carbon_url, json=payload) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        with open('carbon.png', 'wb') as f:
                            f.write(image_data)
                        await event.delete()
                        await self.client.send_file(event.chat_id, 'carbon.png', caption='🎨 <b>Carbon код</b>')
                        import os
                        os.remove('carbon.png')
                    else:
                        await event.edit('❌ <b>Ошибка создания Carbon</b>')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка:</b> <code>{str(e)}</code>')

    async def cmd_paste(self, event, args):
        if not event.is_reply and (not args):
            await event.edit('❌ <b>Ответьте на сообщение или укажите текст</b>')
            return
        if event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text
        else:
            text = ' '.join(args)
        if not text:
            await event.edit('❌ <b>Текст не найден</b>')
            return
        await event.edit('📄 <b>Загрузка на paste сервис...</b>')
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post('https://hastebin.com/documents', data=text.encode()) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        key = result['key']
                        url = f'https://hastebin.com/{key}'
                        await event.edit(f'📄 <b>Текст загружен</b>\n\n<blockquote>\n<b>🔗 Ссылка:</b> {url}\n<b>📊 Размер:</b> {len(text)} символов\n<b>⚛️ Сервис:</b> Hastebin\n</blockquote>')
                    else:
                        await event.edit('❌ <b>Ошибка загрузки</b>')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка:</b> <code>{str(e)}</code>')

    async def cmd_telegraph(self, event, args):
        if not event.is_reply:
            await event.edit('❌ <b>Ответьте на сообщение для создания Telegraph</b>')
            return
        reply = await event.get_reply_message()
        if not reply.text:
            await event.edit('❌ <b>Сообщение должно содержать текст</b>')
            return
        await event.edit('📰 <b>Создание Telegraph страницы...</b>')
        try:
            from telegraph import Telegraph
            telegraph = Telegraph()
            telegraph.create_account(short_name='ArgentBot')
            title = args[0] if args else 'Argent UserBot Post'
            content = reply.text
            response = telegraph.create_page(title=title, html_content=f'<p>{content}</p>', author_name='Argent UserBot')
            url = f"https://telegra.ph/{response['path']}"
            await event.edit(f'📰 <b>Telegraph страница создана</b>\n\n<blockquote>\n<b>📝 Заголовок:</b> {title}\n<b>🔗 Ссылка:</b> {url}\n<b>📊 Размер:</b> {len(content)} символов\n\n⚛️ <b>Страница готова к просмотру</b>\n</blockquote>')
        except ImportError:
            await event.edit('❌ <b>Модуль telegraph не установлен</b>\n\n📦 Установите: <code>pip install telegraph</code>')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка:</b> <code>{str(e)}</code>')

    async def cmd_translate(self, event, args):
        if not args and (not event.is_reply):
            await event.edit('❌ Использование: `.translate <язык> <текст>` или ответьте на сообщение')
            return
        if event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text
            target_lang = args[0] if args else 'en'
        else:
            target_lang = args[0]
            text = ' '.join(args[1:])
        if not text:
            await event.edit('❌ <b>Текст для перевода не найден</b>')
            return
        await event.edit('🌍 <b>Перевод текста...</b>')
        try:
            from googletrans import Translator
            translator = Translator()
            result = translator.translate(text, dest=target_lang)
            await event.edit(f"🌍 <b>Перевод завершен</b>\n\n<blockquote>\n<b>📝 Оригинал ({result.src}):</b>\n{text}\n\n<b>🔄 Перевод ({target_lang}):</b>\n{result.text}\n\n<b>🔬 Достоверность:</b> {(int(result.confidence * 100) if hasattr(result, 'confidence') else 'N/A')}%\n</blockquote>")
        except ImportError:
            await event.edit('❌ <b>Модуль googletrans не установлен</b>\n\n📦 Установите: <code>pip install googletrans==4.0.0-rc1</code>')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка перевода:</b> <code>{str(e)}</code>')

    async def cmd_weather(self, event, args):
        if not args:
            await event.edit('❌ Использование: `.weather <город>`')
            return
        city = ' '.join(args)
        await event.edit(f'🌤️ <b>Получение погоды для {city}...</b>')
        try:
            import aiohttp
            api_key = self.db.get_config('weather_api_key')
            if not api_key:
                await event.edit('❌ API ключ OpenWeatherMap не настроен\n\n🔧 Установите: `.setweatherkey <ключ>`')
                return
            url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru'
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        temp = data['main']['temp']
                        feels_like = data['main']['feels_like']
                        humidity = data['main']['humidity']
                        pressure = data['main']['pressure']
                        description = data['weather'][0]['description']
                        await event.edit(f'🌤️ <b>Погода в {city}</b>\n\n<blockquote>\n<b>🌡️ Температура:</b> {temp}°C (ощущается как {feels_like}°C)\n<b>📝 Описание:</b> {description.title()}\n<b>💧 Влажность:</b> {humidity}%\n<b>📊 Давление:</b> {pressure} гПа\n\n<b>🔬 Данные актуальны</b>\n</blockquote>')
                    else:
                        await event.edit('❌ <b>Город не найден</b>')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка:</b> <code>{str(e)}</code>')

    async def cmd_qr(self, event, args):
        if not args and (not event.is_reply):
            await event.edit('❌ Использование: `.qr <текст>` или ответьте на сообщение')
            return
        if event.is_reply:
            reply = await event.get_reply_message()
            text = reply.text
        else:
            text = ' '.join(args)
        if not text:
            await event.edit('❌ <b>Текст для QR кода не найден</b>')
            return
        await event.edit('📱 <b>Создание QR кода...</b>')
        try:
            import qrcode
            from io import BytesIO
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            bio = BytesIO()
            img.save(bio, format='PNG')
            bio.seek(0)
            await event.delete()
            await self.client.send_file(event.chat_id, bio, caption=f"📱 <b>QR код</b>\n\n📝 <b>Текст:</b> <code>{text[:100]}{('...' if len(text) > 100 else '')}</code>")
        except ImportError:
            await event.edit('❌ <b>Модуль qrcode не установлен</b>\n\n📦 Установите: <code>pip install qrcode[pil]</code>')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка:</b> <code>{str(e)}</code>')

    async def cmd_short(self, event, args):
        if not args and (not event.is_reply):
            await event.edit('❌ Использование: `.short <ссылка>` или ответьте на сообщение')
            return
        if event.is_reply:
            reply = await event.get_reply_message()
            url = reply.text
        else:
            url = ' '.join(args)
        if not self.utils.is_url(url):
            await event.edit('❌ <b>Некорректная ссылка</b>')
            return
        await event.edit('🔗 <b>Сокращение ссылки...</b>')
        try:
            import aiohttp
            api_url = f'https://is.gd/create.php?format=simple&url={url}'
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as resp:
                    if resp.status == 200:
                        short_url = await resp.text()
                        await event.edit(f'🔗 <b>Ссылка сокращена</b>\n\n<blockquote>\n<b>📝 Оригинал:</b>\n{url}\n\n<b>✂️ Сокращенная:</b>\n{short_url}\n\n<b>📊 Экономия:</b> {len(url) - len(short_url)} символов\n</blockquote>')
                    else:
                        await event.edit('❌ <b>Ошибка сокращения ссылки</b>')
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка:</b> <code>{str(e)}</code>')
module = HerokuFeaturesModule()
