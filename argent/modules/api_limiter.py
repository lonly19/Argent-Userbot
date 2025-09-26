import asyncio
import io
import json
import logging
import random
import time
import typing
from typing import List, Dict, Any, Optional
from telethon.tl import functions
from telethon.tl.tlobject import TLRequest
from telethon.tl.types import Message
from telethon.utils import is_list_like
from argent.core.loader import ArgentModule
try:
    from argent.config.api_limiter_defaults import API_LIMITER_CONFIG, PROTECTION_PROFILES
except ImportError:
    API_LIMITER_CONFIG = {'time_sample': 15, 'threshold': 100, 'local_floodwait': 30, 'min_delay': 0.01, 'max_delay': 0.05, 'forbidden_methods': ['joinChannel', 'importChatInvite'], 'monitored_modules': ['messages', 'account', 'channels']}
    PROTECTION_PROFILES = {}
logger = logging.getLogger(__name__)
GROUPS = ['auth', 'account', 'users', 'contacts', 'messages', 'updates', 'photos', 'upload', 'help', 'channels', 'bots', 'payments', 'stickers', 'phone', 'langpack', 'folders', 'stats']
CONSTRUCTORS = {}
try:
    for group in GROUPS:
        if hasattr(functions, group):
            group_obj = getattr(functions, group)
            for entity_name in dir(group_obj):
                if hasattr(group_obj, entity_name):
                    cur_entity = getattr(group_obj, entity_name)
                    if hasattr(cur_entity, '__bases__') and hasattr(cur_entity, 'CONSTRUCTOR_ID') and (TLRequest in cur_entity.__bases__):
                        constructor_name = (entity_name[0].lower() + entity_name[1:]).rsplit('Request', 1)[0]
                        CONSTRUCTORS[constructor_name] = cur_entity.CONSTRUCTOR_ID
except Exception as e:
    logger.warning(f'Failed to build constructors map: {e}')

class APILimiterModule(ArgentModule):
    __version__ = '1.2.0'
    __author__ = 'Argent UserBot Team'
    __category__ = 'core'

    def __init__(self):
        super().__init__()
        self.description = '🛡️ Защита от блокировок через умное ограничение API запросов'
        self._ratelimiter: List[tuple] = []
        self._suspend_until = 0
        self._lock = False
        self._protection_enabled = True
        self._original_call = None
        self._installed = False
        self._config = API_LIMITER_CONFIG.copy()
        self.register_command('apilimit', self.cmd_apilimit, '🛡️ Управление API лимитером')
        self.register_command('apiconfig', self.cmd_apiconfig, '⚙️ Конфигурация API лимитера')
        self.register_command('apistats', self.cmd_apistats, '📊 Статистика API запросов')
        self.register_command('apisuspend', self.cmd_apisuspend, '⏸️ Временно отключить защиту')
        self.register_command('apiprofile', self.cmd_apiprofile, '📋 Профили защиты')
        self.register_command('apistatus', self.cmd_apistatus, '🔍 Детальный статус защиты')

    async def on_load(self):
        try:
            logger.info('🔄 Инициализация API Limiter...')
            await asyncio.sleep(1)
            saved_config = self.db.get('modules', 'api_limiter_config')
            if saved_config:
                self._config.update(saved_config)
                logger.info('📋 Конфигурация загружена из БД')
            else:
                self.db.set('modules', 'api_limiter_config', self._config)
                logger.info('📋 Создана дефолтная конфигурация')
            protection_enabled = self.db.get('modules', 'api_limiter_enabled')
            if protection_enabled is not None:
                self._protection_enabled = protection_enabled
            logger.info('⏳ Запуск установки защиты через 3 секунды...')
            await asyncio.sleep(3)
            asyncio.create_task(self._install_protection())
            logger.info('🛡️ API Limiter module loaded successfully')
        except Exception as e:
            logger.error(f'❌ Failed to initialize API Limiter: {e}')

    async def on_unload(self):
        await self._uninstall_protection()
        logger.info('🛡️ API Limiter module unloaded')

    async def _install_protection(self):
        try:
            logger.info('🔄 Ожидание инициализации клиента...')
            for attempt in range(15):
                await asyncio.sleep(2)
                if self.client and hasattr(self.client, '_call'):
                    break
                if attempt % 5 == 0:
                    logger.info(f'⏳ Ожидание клиента... попытка {attempt + 1}/15')
            if not self.client or not hasattr(self.client, '_call'):
                logger.error('❌ Client not ready for API protection after 30s')
                return
            if hasattr(self.client._call, '_argent_api_protected'):
                logger.warning('⚠️ API protection already installed')
                return
            logger.info('🛡️ Подготовка к установке защиты...')
            await asyncio.sleep(3)
            self._original_call = self.client._call

            async def protected_call(sender, request: TLRequest, ordered: bool=False, flood_sleep_threshold: int=None):
                base_delay = self._config.get('base_safety_delay', 0.05)
                if not self._installed:
                    base_delay = random.uniform(0.1, 0.2)
                else:
                    base_delay = random.uniform(base_delay, base_delay * 2)
                await asyncio.sleep(base_delay)
                if self._protection_enabled:
                    extra_delay = random.uniform(self._config['min_delay'], self._config['max_delay'])
                    await asyncio.sleep(extra_delay)
                req_list = (request,) if not is_list_like(request) else request
                for req in req_list:
                    if await self._should_monitor_request(req):
                        await self._process_request(req)
                return await self._original_call(sender, request, ordered, flood_sleep_threshold)
            logger.info('🔧 Установка API защиты...')
            await asyncio.sleep(1)
            self.client._call = protected_call
            self.client._call._argent_api_protected = True
            self._installed = True
            await asyncio.sleep(2)
            logger.info('✅ API protection installed successfully with safety limits')
        except Exception as e:
            logger.error(f'Failed to install API protection: {e}')

    async def _uninstall_protection(self):
        try:
            if self._original_call and hasattr(self.client, '_call'):
                self.client._call = self._original_call
                if hasattr(self.client._call, '_argent_api_protected'):
                    delattr(self.client._call, '_argent_api_protected')
                self._installed = False
                logger.info('✅ API protection uninstalled')
        except Exception as e:
            logger.error(f'Failed to uninstall API protection: {e}')

    async def _should_monitor_request(self, request: TLRequest) -> bool:
        if not self._protection_enabled:
            return False
        if time.perf_counter() <= self._suspend_until:
            return False
        module_name = request.__module__.rsplit('.', maxsplit=1)[-1]
        return module_name in self._config['monitored_modules']

    async def _process_request(self, request: TLRequest):
        try:
            current_time = time.perf_counter()
            request_name = type(request).__name__
            if await self._is_critical_request(request):
                min_delay = self._config.get('critical_delay_min', 0.1)
                max_delay = self._config.get('critical_delay_max', 0.3)
                critical_delay = random.uniform(min_delay, max_delay)
                await asyncio.sleep(critical_delay)
                logger.debug(f'🚨 Critical request detected: {request_name}, added {critical_delay:.2f}s delay')
            self._ratelimiter.append((request_name, current_time))
            time_threshold = current_time - self._config['time_sample']
            self._ratelimiter = [(name, req_time) for name, req_time in self._ratelimiter if req_time > time_threshold]
            threshold = self._config['threshold']
            if not self._installed:
                installation_threshold = self._config.get('installation_threshold', 25)
                threshold = min(threshold // 2, installation_threshold)
            if len(self._ratelimiter) > threshold and (not self._lock):
                await self._handle_rate_limit()
        except Exception as e:
            logger.error(f'Error processing request: {e}')

    async def _is_critical_request(self, request: TLRequest) -> bool:
        try:
            request_name = type(request).__name__
            critical_methods = ['JoinChannelRequest', 'ImportChatInviteRequest', 'SendMessageRequest', 'SendMediaRequest', 'CreateChannelRequest', 'InviteToChannelRequest', 'EditChatAdminRequest', 'BanChatMemberRequest']
            return request_name in critical_methods
        except Exception:
            return False

    async def _handle_rate_limit(self):
        try:
            self._lock = True
            report_data = {'timestamp': time.time(), 'requests_count': len(self._ratelimiter), 'time_window': self._config['time_sample'], 'threshold': self._config['threshold'], 'requests': [{'name': name, 'time': req_time} for name, req_time in self._ratelimiter[-50:]]}
            self.db.set('modules', 'api_limiter_last_trigger', report_data)
            logger.warning(f"🚨 API rate limit triggered! Requests: {len(self._ratelimiter)}/{self._config['threshold']} in {self._config['time_sample']}s")
            await asyncio.sleep(self._config['local_floodwait'])
            self._lock = False
        except Exception as e:
            logger.error(f'Error handling rate limit: {e}')
            self._lock = False

    async def cmd_apilimit(self, event, args):
        if not args:
            status = '🟢 Включен' if self._protection_enabled else '🔴 Выключен'
            installed = '✅ Установлена' if self._installed else '❌ Не установлена'
            await event.edit(f"\n🛡️ <b>API Limiter Status</b>\n\n<b>📊 Состояние:</b> {status}\n<b>🔧 Защита:</b> {installed}\n<b>📈 Запросов в буфере:</b> <code>{len(self._ratelimiter)}</code>\n<b>🎯 Порог:</b> <code>{self._config['threshold']}</code>\n<b>⏱️ Окно времени:</b> <code>{self._config['time_sample']}s</code>\n\n<b>💡 Команды:</b>\n• <code>.apilimit on/off</code> - включить/выключить\n• <code>.apiconfig</code> - настройки\n• <code>.apistats</code> - статистика\n")
            return
        action = args[0].lower()
        if action == 'on':
            self._protection_enabled = True
            self.db.set('modules', 'api_limiter_enabled', True)
            await event.edit('✅ <b>API Limiter включен</b>')
        elif action == 'off':
            self._protection_enabled = False
            self.db.set('modules', 'api_limiter_enabled', False)
            await event.edit('🔴 <b>API Limiter выключен</b>')
        elif action == 'reset':
            self._ratelimiter.clear()
            self._lock = False
            self._suspend_until = 0
            await event.edit('🔄 <b>Статистика API Limiter сброшена</b>')
        else:
            await event.edit('❌ <b>Неизвестная команда</b>\n\n<b>Доступно:</b> on, off, reset')

    async def cmd_apiconfig(self, event, args):
        if not args:
            config_text = '\n'.join([f'<b>{key}:</b> <code>{value}</code>' for key, value in self._config.items()])
            await event.edit(f'\n⚙️ <b>Конфигурация API Limiter</b>\n\n{config_text}\n\n<b>💡 Изменение:</b>\n<code>.apiconfig &lt;параметр&gt; &lt;значение&gt;</code>\n\n<b>📋 Примеры:</b>\n• <code>.apiconfig threshold 150</code>\n• <code>.apiconfig time_sample 20</code>\n')
            return
        if len(args) < 2:
            await event.edit('❌ <b>Использование:</b> <code>.apiconfig &lt;параметр&gt; &lt;значение&gt;</code>')
            return
        param = args[0]
        value = args[1]
        if param not in self._config:
            await event.edit(f'❌ <b>Неизвестный параметр:</b> <code>{param}</code>')
            return
        try:
            if isinstance(self._config[param], int):
                value = int(value)
            elif isinstance(self._config[param], float):
                value = float(value)
            elif isinstance(self._config[param], list):
                value = value.split(',') if ',' in value else [value]
            self._config[param] = value
            self.db.set('modules', 'api_limiter_config', self._config)
            await event.edit(f'✅ <b>Параметр обновлен:</b>\n<code>{param} = {value}</code>')
        except ValueError:
            await event.edit(f'❌ <b>Неверный тип значения для параметра:</b> <code>{param}</code>')

    async def cmd_apistats(self, event, args):
        try:
            current_time = time.perf_counter()
            recent_requests = [(name, req_time) for name, req_time in self._ratelimiter if current_time - req_time < self._config['time_sample']]
            request_types = {}
            for name, req_time in recent_requests:
                request_types[name] = request_types.get(name, 0) + 1
            last_trigger = self.db.get('modules', 'api_limiter_last_trigger')
            stats_text = f"\n📊 <b>Статистика API Limiter</b>\n\n<b>📈 Текущее состояние:</b>\n• Запросов в буфере: <code>{len(recent_requests)}</code>\n• Порог срабатывания: <code>{self._config['threshold']}</code>\n• Заблокирован до: <code>{('Да' if current_time < self._suspend_until else 'Нет')}</code>\n\n<b>🔥 Топ запросов:</b>\n"
            sorted_types = sorted(request_types.items(), key=lambda x: x[1], reverse=True)
            for i, (req_type, count) in enumerate(sorted_types[:5], 1):
                stats_text += f'{i}. <code>{req_type}</code>: {count}\n'
            if last_trigger:
                trigger_time = self.utils.format_timestamp(int(last_trigger['timestamp']))
                stats_text += f'\n<b>🚨 Последнее срабатывание:</b>\n<code>{trigger_time}</code>'
            await event.edit(stats_text)
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка получения статистики:</b> <code>{e}</code>')

    async def cmd_apisuspend(self, event, args):
        if not args or not args[0].isdigit():
            await event.edit('❌ <b>Использование:</b> <code>.apisuspend &lt;секунды&gt;</code>')
            return
        seconds = int(args[0])
        if seconds > 3600:
            await event.edit('❌ <b>Максимальное время приостановки:</b> 3600 секунд (1 час)')
            return
        self._suspend_until = time.perf_counter() + seconds
        await event.edit(f'\n⏸️ <b>API защита приостановлена</b>\n\n<b>⏱️ Время:</b> <code>{seconds}</code> секунд\n<b>🔄 Возобновится:</b> <code>{self.utils.format_timestamp(int(time.time() + seconds))}</code>\n\n<b>⚠️ Внимание:</b> Используйте осторожно!\n')

    async def cmd_apiprofile(self, event, args):
        if not args:
            if not PROTECTION_PROFILES:
                await event.edit('❌ <b>Профили защиты недоступны</b>\n\n<i>Конфигурационный файл не найден</i>')
                return
            profiles_text = '\n'.join([f"<b>{name}:</b> {info['description']}" for name, info in PROTECTION_PROFILES.items()])
            await event.edit(f'\n📋 <b>Доступные профили защиты</b>\n\n{profiles_text}\n\n<b>💡 Использование:</b>\n<code>.apiprofile &lt;имя_профиля&gt;</code>\n\n<b>📋 Примеры:</b>\n• <code>.apiprofile conservative</code>\n• <code>.apiprofile balanced</code>\n• <code>.apiprofile performance</code>\n')
            return
        profile_name = args[0].lower()
        if profile_name not in PROTECTION_PROFILES:
            available = ', '.join(PROTECTION_PROFILES.keys())
            await event.edit(f'❌ <b>Неизвестный профиль:</b> <code>{profile_name}</code>\n\n<b>Доступные:</b> {available}')
            return
        try:
            profile = PROTECTION_PROFILES[profile_name]
            self._config.update(profile['config'])
            self.db.set('modules', 'api_limiter_config', self._config)
            self._ratelimiter.clear()
            self._lock = False
            await event.edit(f"\n✅ <b>Профиль применен:</b> <code>{profile_name}</code>\n\n<b>📝 Описание:</b> {profile['description']}\n\n<b>⚙️ Новые настройки:</b>\n• Порог: <code>{self._config['threshold']}</code>\n• Окно времени: <code>{self._config['time_sample']}s</code>\n• Время блокировки: <code>{self._config['local_floodwait']}s</code>\n• Задержки: <code>{self._config['min_delay']}-{self._config['max_delay']}s</code>\n\n<b>🔄 Статистика сброшена</b>\n")
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка применения профиля:</b> <code>{e}</code>')

    async def cmd_apistatus(self, event, args):
        try:
            current_time = time.perf_counter()
            install_status = '✅ Установлена' if self._installed else '❌ Не установлена'
            protection_status = '🟢 Включена' if self._protection_enabled else '🔴 Выключена'
            lock_status = '🔒 Заблокирована' if self._lock else '🔓 Активна'
            base_delay = self._config.get('base_safety_delay', 0.05)
            min_delay = self._config['min_delay']
            max_delay = self._config['max_delay']
            critical_min = self._config.get('critical_delay_min', 0.1)
            critical_max = self._config.get('critical_delay_max', 0.3)
            recent_requests = len([req for req in self._ratelimiter if current_time - req[1] < self._config['time_sample']])
            suspend_time = ''
            if current_time < self._suspend_until:
                remaining = int(self._suspend_until - current_time)
                suspend_time = f'\n<b>⏸️ Приостановлена на:</b> <code>{remaining}s</code>'
            await event.edit(f"\n🔍 <b>Детальный статус API Limiter</b>\n\n<b>🛡️ Состояние защиты:</b>\n• Установка: {install_status}\n• Защита: {protection_status}\n• Блокировка: {lock_status}{suspend_time}\n\n<b>⚙️ Текущие лимиты:</b>\n• Порог: <code>{self._config['threshold']}</code> запросов\n• Окно времени: <code>{self._config['time_sample']}s</code>\n• Время блокировки: <code>{self._config['local_floodwait']}s</code>\n\n<b>⏱️ Задержки (секунды):</b>\n• Базовая: <code>{base_delay}</code>\n• Обычная: <code>{min_delay}-{max_delay}</code>\n• Критическая: <code>{critical_min}-{critical_max}</code>\n\n<b>📊 Текущая активность:</b>\n• Запросов в буфере: <code>{recent_requests}</code>\n• Всего в истории: <code>{len(self._ratelimiter)}</code>\n\n<b>🔧 Мониторинг:</b>\n• Модули: <code>{', '.join(self._config['monitored_modules'])}</code>\n• Запрещенные методы: <code>{len(self._config['forbidden_methods'])}</code>\n\n<b>💡 Статус:</b> {('🟢 Все системы в норме' if not self._lock else '🚨 Активна защита от перегрузки')}\n")
        except Exception as e:
            await event.edit(f'❌ <b>Ошибка получения статуса:</b> <code>{e}</code>')
module = APILimiterModule()
