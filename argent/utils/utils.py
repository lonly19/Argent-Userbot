import re
import time
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import hashlib
import random
import string
logger = logging.getLogger(__name__)

class ArgentUtils:

    def __init__(self, client=None):
        self.client = client

    @staticmethod
    def escape_html(text: str) -> str:
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')

    @staticmethod
    def escape_markdown(text: str) -> str:
        chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in chars:
            text = text.replace(char, f'\\{char}')
        return text

    @staticmethod
    def format_bytes(bytes_count: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f'{bytes_count:.1f} {unit}'
            bytes_count /= 1024.0
        return f'{bytes_count:.1f} PB'

    @staticmethod
    def format_duration(seconds: float) -> str:
        if seconds < 60:
            return f'{seconds:.1f}s'
        elif seconds < 3600:
            return f'{seconds / 60:.1f}m'
        elif seconds < 86400:
            return f'{seconds / 3600:.1f}h'
        else:
            return f'{seconds / 86400:.1f}d'

    @staticmethod
    def generate_id(length: int=8) -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def hash_text(text: str, algorithm: str='md5') -> str:
        if algorithm == 'md5':
            return hashlib.md5(text.encode()).hexdigest()
        elif algorithm == 'sha1':
            return hashlib.sha1(text.encode()).hexdigest()
        elif algorithm == 'sha256':
            return hashlib.sha256(text.encode()).hexdigest()
        else:
            raise ValueError(f'Unsupported algorithm: {algorithm}')

    @staticmethod
    def get_timestamp() -> int:
        return int(time.time())

    @staticmethod
    def format_timestamp(timestamp: int, format_str: str='%Y-%m-%d %H:%M:%S') -> str:
        return datetime.fromtimestamp(timestamp).strftime(format_str)

    @staticmethod
    def parse_duration(duration_str: str) -> Optional[int]:
        pattern = '(\\d+)([smhd])'
        matches = re.findall(pattern, duration_str.lower())
        if not matches:
            return None
        total_seconds = 0
        for value, unit in matches:
            value = int(value)
            if unit == 's':
                total_seconds += value
            elif unit == 'm':
                total_seconds += value * 60
            elif unit == 'h':
                total_seconds += value * 3600
            elif unit == 'd':
                total_seconds += value * 86400
        return total_seconds

    async def get_chat_info(self, chat_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        try:
            entity = await self.client.get_entity(chat_id)
            return {'id': entity.id, 'title': getattr(entity, 'title', None), 'username': getattr(entity, 'username', None), 'type': entity.__class__.__name__, 'participants_count': getattr(entity, 'participants_count', None)}
        except Exception as e:
            logger.error(f'❌ Get chat info error: {e}')
            return None

    async def get_user_info(self, user_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        try:
            entity = await self.client.get_entity(user_id)
            return {'id': entity.id, 'first_name': getattr(entity, 'first_name', None), 'last_name': getattr(entity, 'last_name', None), 'username': getattr(entity, 'username', None), 'phone': getattr(entity, 'phone', None), 'is_bot': getattr(entity, 'bot', False)}
        except Exception as e:
            logger.error(f'❌ Get user info error: {e}')
            return None

    async def download_media(self, message, path: str=None) -> Optional[str]:
        if not self.client or not message.media:
            return None
        try:
            if not path:
                path = f'downloads/{self.generate_id()}'
            file_path = await self.client.download_media(message, path)
            return file_path
        except Exception as e:
            logger.error(f'❌ Download media error: {e}')
            return None

    @staticmethod
    def is_url(text: str) -> bool:
        url_pattern = re.compile('^https?://(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\\.)+[A-Z]{2,6}\\.?|localhost|\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3})(?::\\d+)?(?:/?|[/?]\\S+)$', re.IGNORECASE)
        return url_pattern.match(text) is not None

    @staticmethod
    def is_email(text: str) -> bool:
        email_pattern = re.compile('^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$')
        return email_pattern.match(text) is not None

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        url_pattern = re.compile('https?://(?:[-\\w.])+(?:[:\\d]+)?(?:/(?:[\\w/_.])*(?:\\?(?:[\\w&=%.])*)?(?:#(?:[\\w.])*)?)?')
        return url_pattern.findall(text)

    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        mention_pattern = re.compile('@(\\w+)')
        return mention_pattern.findall(text)

    @staticmethod
    def format_scientific_number(number: float, precision: int=2) -> str:
        return f'{number:.{precision}e}'

    @staticmethod
    def format_percentage(value: float, total: float, precision: int=1) -> str:
        if total == 0:
            return '0.0%'
        percentage = value / total * 100
        return f'{percentage:.{precision}f}%'

    @staticmethod
    def format_chemical_formula(formula: str) -> str:
        subscripts = str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉')
        return re.sub('(\\d+)', lambda m: m.group(1).translate(subscripts), formula)

    @staticmethod
    async def run_sync(func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)

    @staticmethod
    async def sleep_random(min_seconds: float, max_seconds: float):
        duration = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(duration)
    SCIENTIFIC_EMOJIS = {'atom': '⚛️', 'molecule': '🧬', 'test_tube': '🧪', 'flask': '⚗️', 'microscope': '🔬', 'dna': '🧬', 'crystal': '💎', 'fire': '🔥', 'lightning': '⚡', 'gear': '⚙️', 'magnet': '🧲', 'battery': '🔋', 'satellite': '🛰️', 'rocket': '🚀', 'telescope': '🔭'}

    @classmethod
    def get_emoji(cls, name: str) -> str:
        return cls.SCIENTIFIC_EMOJIS.get(name, '🔬')
