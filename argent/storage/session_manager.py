import asyncio
import logging
from typing import Optional, Dict, Any
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneNumberInvalidError
from .session_storage import SessionStorage
logger = logging.getLogger(__name__)

class SessionManager:

    def __init__(self, storage: SessionStorage):
        self.storage = storage
        self._current_client: Optional[TelegramClient] = None
        self._current_session_id: Optional[str] = None

    async def create_session(self, api_id: int, api_hash: str, phone: str) -> Dict[str, Any]:
        try:
            temp_client = TelegramClient(StringSession(), api_id, api_hash)
            await temp_client.connect()
            sent_code = await temp_client.send_code_request(phone)
            return {'success': True, 'client': temp_client, 'phone': phone, 'phone_code_hash': sent_code.phone_code_hash, 'message': 'Код отправлен на телефон'}
        except PhoneNumberInvalidError:
            return {'success': False, 'error': 'Неверный номер телефона'}
        except Exception as e:
            logger.error(f'❌ Ошибка создания сессии: {e}')
            return {'success': False, 'error': str(e)}

    async def verify_code(self, client: TelegramClient, phone: str, phone_code_hash: str, code: str, password: str=None) -> Dict[str, Any]:
        try:
            try:
                user = await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            except SessionPasswordNeededError:
                if not password:
                    return {'success': False, 'need_password': True, 'message': 'Требуется пароль двухфакторной аутентификации'}
                user = await client.sign_in(password=password)
            session_string = client.session.save()
            session_id = self.storage.save_session(session_string=session_string, phone=phone, user_id=user.id, username=user.username, first_name=user.first_name)
            await client.disconnect()
            return {'success': True, 'session_id': session_id, 'user': {'id': user.id, 'username': user.username, 'first_name': user.first_name, 'phone': phone}, 'message': 'Сессия успешно создана и сохранена'}
        except PhoneCodeInvalidError:
            return {'success': False, 'error': 'Неверный код подтверждения'}
        except Exception as e:
            logger.error(f'❌ Ошибка подтверждения кода: {e}')
            return {'success': False, 'error': str(e)}

    async def load_session(self, api_id: int, api_hash: str, session_id: str=None) -> Optional[TelegramClient]:
        try:
            session_string = self.storage.load_session(session_id)
            if not session_string:
                logger.warning('⚠️ Сессия не найдена')
                return None
            client = TelegramClient(StringSession(session_string), api_id, api_hash)
            await client.connect()
            if not await client.is_user_authorized():
                logger.warning('⚠️ Сессия недействительна')
                await client.disconnect()
                return None
            self._current_client = client
            self._current_session_id = session_id or self.storage.get_default_session()
            logger.info('✅ Сессия успешно загружена')
            return client
        except Exception as e:
            logger.error(f'❌ Ошибка загрузки сессии: {e}')
            return None

    async def get_current_user(self) -> Optional[Dict[str, Any]]:
        if not self._current_client:
            return None
        try:
            me = await self._current_client.get_me()
            return {'id': me.id, 'username': me.username, 'first_name': me.first_name, 'last_name': me.last_name, 'phone': me.phone, 'is_premium': getattr(me, 'premium', False)}
        except Exception as e:
            logger.error(f'❌ Ошибка получения информации о пользователе: {e}')
            return None

    def get_current_client(self) -> Optional[TelegramClient]:
        return self._current_client

    def get_current_session_id(self) -> Optional[str]:
        return self._current_session_id

    async def switch_session(self, api_id: int, api_hash: str, session_id: str) -> bool:
        try:
            if self._current_client:
                await self._current_client.disconnect()
            client = await self.load_session(api_id, api_hash, session_id)
            if client:
                self.storage.set_default_session(session_id)
                return True
            return False
        except Exception as e:
            logger.error(f'❌ Ошибка переключения сессии: {e}')
            return False

    async def disconnect(self):
        if self._current_client:
            await self._current_client.disconnect()
            self._current_client = None
            self._current_session_id = None

    def list_sessions(self) -> list:
        return self.storage.list_sessions()

    def delete_session(self, session_id: str) -> bool:
        return self.storage.delete_session(session_id)

    def has_sessions(self) -> bool:
        return self.storage.has_sessions()

    async def validate_session(self, session_id: str=None) -> bool:
        try:
            session_info = self.storage.get_session_info(session_id)
            if not session_info:
                return False
            session_string = self.storage.load_session(session_id)
            if not session_string:
                return False
            temp_client = TelegramClient(StringSession(session_string), 0, '')
            await temp_client.connect()
            is_valid = await temp_client.is_user_authorized()
            await temp_client.disconnect()
            return is_valid
        except Exception as e:
            logger.error(f'❌ Ошибка проверки сессии: {e}')
            return False

    def cleanup_sessions(self):
        self.storage.cleanup_invalid_sessions()

    def backup_sessions(self, backup_path: str=None) -> str:
        return self.storage.backup_sessions(backup_path)
