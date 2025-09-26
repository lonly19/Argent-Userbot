import os
import io
import json
import base64
import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, FloodWaitError, PhoneCodeInvalidError
try:
    import qrcode
except Exception:
    qrcode = None

def validate_bot_token(token: str) -> bool:
    if not token or ':' not in token:
        return False
    left, right = token.split(':', 1)
    return left.isdigit() and len(right) >= 10

class AuthError(Exception):
    pass

@dataclass
class SessionStore:
    base_dir: str = '.argent_data'
    _qr_sessions: Dict[str, TelegramClient] = field(default_factory=dict)
    _sms_sessions: Dict[str, Dict] = field(default_factory=dict)

    def __post_init__(self):
        os.makedirs(self.base_dir, exist_ok=True)

    @property
    def config_path(self) -> str:
        return os.path.join(self.base_dir, 'config.json')

    def save_install(self, user_session: str, bot_token: str, api_id: int, api_hash: str) -> None:
        data = {'bot_token': bot_token, 'api_id': api_id, 'api_hash': api_hash, 'user_session': user_session, 'version': 1}
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_install(self) -> Optional[dict]:
        if not os.path.exists(self.config_path):
            return None
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def put_qr_client(self, token: str, client: TelegramClient):
        self._qr_sessions[token] = client

    def get_qr_client(self, token: str) -> Optional[TelegramClient]:
        return self._qr_sessions.get(token)

    def pop_qr_client(self, token: str) -> Optional[TelegramClient]:
        return self._qr_sessions.pop(token, None)

    def put_sms_flow(self, token: str, data: dict):
        data['ts'] = time.time()
        self._sms_sessions[token] = data

    def get_sms_flow(self, token: str) -> Optional[dict]:
        d = self._sms_sessions.get(token)
        if not d:
            return None
        if time.time() - d.get('ts', 0) > 900:
            self._sms_sessions.pop(token, None)
            return None
        return d

    def pop_sms_flow(self, token: str) -> Optional[dict]:
        return self._sms_sessions.pop(token, None)

class TelethonAuthFlow:

    def __init__(self, api_id: int, api_hash: str, store: SessionStore):
        self.api_id = api_id
        self.api_hash = api_hash
        self.store = store

    async def _build_client(self) -> TelegramClient:
        return TelegramClient(StringSession(), self.api_id, self.api_hash)

    async def start_qr_login(self) -> Tuple[str, str, TelegramClient]:
        if qrcode is None:
            raise AuthError("QRCode библиотека не установлена. Установите 'qrcode[pil]'.")
        client = await self._build_client()
        await client.connect()
        qr_login = await client.qr_login()
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(qr_login.url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode()
        token = base64.urlsafe_b64encode(os.urandom(18)).decode()
        self.store.put_qr_client(token, client)

        async def _wait_login():
            try:
                await qr_login.wait()
            except Exception:
                pass
        asyncio.create_task(_wait_login())
        return (f'data:image/png;base64,{b64}', token, client)

    async def poll_qr_login(self, token: str) -> Tuple[bool, Optional[str]]:
        client = self.store.get_qr_client(token)
        if not client:
            raise AuthError('QR сессия не найдена или истекла')
        if await client.is_user_authorized():
            session_string = client.session.save()
            self.store.pop_qr_client(token)
            await client.disconnect()
            return (True, session_string)
        return (False, None)

    async def start_sms_login(self, phone: str) -> str:
        client = await self._build_client()
        await client.connect()
        sent = await client.send_code_request(phone)
        token = base64.urlsafe_b64encode(os.urandom(18)).decode()
        self.store.put_sms_flow(token, {'client': client, 'phone': phone, 'sent': sent})
        return token

    async def finish_sms_login(self, token: str, code: Optional[str], password: Optional[str]) -> str:
        data = self.store.get_sms_flow(token)
        if not data:
            raise AuthError('Сессия входа не найдена или истекла')
        client: TelegramClient = data['client']
        phone = data['phone']
        try:
            if code:
                await client.sign_in(phone=phone, code=code)
            elif password:
                await client.sign_in(password=password)
            else:
                raise AuthError('Не указан код или пароль 2FA')
        except SessionPasswordNeededError:
            if not password:
                raise AuthError('Требуется пароль 2FA')
            await client.sign_in(password=password)
        except PhoneCodeInvalidError:
            raise AuthError('Неверный код')
        except FloodWaitError as e:
            raise AuthError(f'Подождите {int(e.seconds)} секунд и повторите попытку')
        session_string = client.session.save()
        self.store.pop_sms_flow(token)
        await client.disconnect()
        return session_string
