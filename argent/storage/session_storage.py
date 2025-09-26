import os
import json
import logging
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime
import hashlib
import base64
logger = logging.getLogger(__name__)

class SessionStorage:

    def __init__(self, data_dir: str='.argent_data'):
        self.data_dir = Path(data_dir)
        self.sessions_dir = self.data_dir / 'sessions'
        self.data_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
        self.sessions_index_path = self.sessions_dir / 'index.json'
        self._sessions_index = {}
        self._load_sessions_index()

    def _load_sessions_index(self):
        try:
            if self.sessions_index_path.exists():
                with open(self.sessions_index_path, 'r', encoding='utf-8') as f:
                    self._sessions_index = json.load(f)
            else:
                self._sessions_index = {'sessions': {}, 'default_session': None, 'created_at': datetime.now().isoformat()}
                self._save_sessions_index()
        except Exception as e:
            logger.error(f'❌ Ошибка загрузки индекса сессий: {e}')
            self._sessions_index = {'sessions': {}, 'default_session': None, 'created_at': datetime.now().isoformat()}

    def _save_sessions_index(self):
        try:
            with open(self.sessions_index_path, 'w', encoding='utf-8') as f:
                json.dump(self._sessions_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'❌ Ошибка сохранения индекса сессий: {e}')

    def _generate_session_id(self, phone: str, user_id: int=None) -> str:
        data = f"{phone}_{user_id or 'unknown'}_{datetime.now().isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()[:16]

    def _get_session_file_path(self, session_id: str, preferred_name: str=None) -> Path:
        if preferred_name:
            base = preferred_name
            if not base.endswith('.session'):
                base += '.session'
        else:
            base = f'{session_id}.session'
        return self.sessions_dir / base

    def save_session(self, session_string: str, phone: str=None, user_id: int=None, username: str=None, first_name: str=None) -> str:
        try:
            session_id = self._generate_session_id(phone, user_id)
            preferred_name = None
            if user_id:
                preferred_name = f'Argent_{user_id}'
            elif username:
                preferred_name = f'Argent_{username}'
            elif first_name:
                preferred_name = f'Argent_{first_name}'
            else:
                preferred_name = f'Argent_{session_id[:8]}'
            session_file = self._get_session_file_path(session_id, preferred_name)
            if session_file.exists():
                i = 1
                while True:
                    alt = self._get_session_file_path(session_id, f'{preferred_name}_{i}')
                    if not alt.exists():
                        session_file = alt
                        break
                    i += 1
            with open(session_file, 'w', encoding='utf-8') as f:
                f.write(session_string)
            session_info = {'session_id': session_id, 'user_id': user_id, 'username': username, 'first_name': first_name, 'created_at': datetime.now().isoformat(), 'last_used': datetime.now().isoformat(), 'file_path': str(session_file), 'file_name': session_file.name}
            self._sessions_index['sessions'][session_id] = session_info
            if not self._sessions_index['default_session']:
                self._sessions_index['default_session'] = session_id
            self._save_sessions_index()
            logger.info(f'✅ Сессия сохранена: {session_id} ({phone})')
            return session_id
        except Exception as e:
            logger.error(f'❌ Ошибка сохранения сессии: {e}')
            raise

    def load_session(self, session_id: str=None) -> Optional[str]:
        try:
            if session_id is None:
                session_id = self._sessions_index.get('default_session')
            if not session_id or session_id not in self._sessions_index['sessions']:
                return None
            session_info = self._sessions_index['sessions'][session_id]
            session_file = Path(session_info['file_path'])
            if not session_file.exists():
                logger.warning(f'⚠️ Файл сессии не найден: {session_file}')
                return None
            with open(session_file, 'r', encoding='utf-8') as f:
                session_string = f.read().strip()
            session_info['last_used'] = datetime.now().isoformat()
            self._save_sessions_index()
            logger.info(f'✅ Сессия загружена: {session_id}')
            return session_string
        except Exception as e:
            logger.error(f'❌ Ошибка загрузки сессии: {e}')
            return None

    def get_session_info(self, session_id: str=None) -> Optional[Dict]:
        if session_id is None:
            session_id = self._sessions_index.get('default_session')
        if not session_id or session_id not in self._sessions_index['sessions']:
            return None
        return self._sessions_index['sessions'][session_id].copy()

    def list_sessions(self) -> List[Dict]:
        return list(self._sessions_index['sessions'].values())

    def delete_session(self, session_id: str) -> bool:
        try:
            if session_id not in self._sessions_index['sessions']:
                return False
            session_info = self._sessions_index['sessions'][session_id]
            session_file = Path(session_info['file_path'])
            if session_file.exists():
                session_file.unlink()
            del self._sessions_index['sessions'][session_id]
            if self._sessions_index['default_session'] == session_id:
                remaining_sessions = list(self._sessions_index['sessions'].keys())
                self._sessions_index['default_session'] = remaining_sessions[0] if remaining_sessions else None
            self._save_sessions_index()
            logger.info(f'✅ Сессия удалена: {session_id}')
            return True
        except Exception as e:
            logger.error(f'❌ Ошибка удаления сессии: {e}')
            return False

    def set_default_session(self, session_id: str) -> bool:
        if session_id not in self._sessions_index['sessions']:
            return False
        self._sessions_index['default_session'] = session_id
        self._save_sessions_index()
        logger.info(f'✅ Сессия по умолчанию установлена: {session_id}')
        return True

    def get_default_session(self) -> Optional[str]:
        return self._sessions_index.get('default_session')

    def has_sessions(self) -> bool:
        return len(self._sessions_index['sessions']) > 0

    def cleanup_invalid_sessions(self):
        invalid_sessions = []
        for session_id, session_info in self._sessions_index['sessions'].items():
            session_file = Path(session_info['file_path'])
            if not session_file.exists():
                invalid_sessions.append(session_id)
        for session_id in invalid_sessions:
            logger.warning(f'⚠️ Удаление недействительной сессии: {session_id}')
            del self._sessions_index['sessions'][session_id]
        if invalid_sessions:
            default_session = self._sessions_index.get('default_session')
            if default_session in invalid_sessions:
                remaining_sessions = list(self._sessions_index['sessions'].keys())
                self._sessions_index['default_session'] = remaining_sessions[0] if remaining_sessions else None
            self._save_sessions_index()
            logger.info(f'🧹 Очищено недействительных сессий: {len(invalid_sessions)}')

    def backup_sessions(self, backup_path: str=None) -> str:
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = self.data_dir / f'sessions_backup_{timestamp}.json'
            else:
                backup_path = Path(backup_path)
            backup_data = {'index': self._sessions_index, 'sessions': {}, 'backup_created': datetime.now().isoformat()}
            for session_id, session_info in self._sessions_index['sessions'].items():
                session_file = Path(session_info['file_path'])
                if session_file.exists():
                    with open(session_file, 'r', encoding='utf-8') as f:
                        backup_data['sessions'][session_id] = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            logger.info(f'✅ Резервная копия создана: {backup_path}')
            return str(backup_path)
        except Exception as e:
            logger.error(f'❌ Ошибка создания резервной копии: {e}')
            raise
