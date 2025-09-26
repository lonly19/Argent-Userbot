import json
import logging
from typing import Any, Dict, Optional, List
from pathlib import Path
import threading
logger = logging.getLogger(__name__)

class ArgentDatabase:

    def __init__(self, data_dir: str='.argent_data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.json_db_path = self.data_dir / 'database.json'
        self._json_data = {}
        self._lock = threading.RLock()
        self._init_json_db()

    def _init_json_db(self):
        try:
            if self.json_db_path.exists():
                with open(self.json_db_path, 'r', encoding='utf-8') as f:
                    self._json_data = json.load(f)
            else:
                self._json_data = {'config': {}, 'modules': {}, 'users': {}, 'chats': {}, 'misc': {}}
                self._save_json_db()
        except Exception as e:
            logger.error(f'❌ JSON DB init error: {e}')
            self._json_data = {'config': {}, 'modules': {}, 'users': {}, 'chats': {}, 'misc': {}}

    def _save_json_db(self):
        try:
            with self._lock:
                with open(self.json_db_path, 'w', encoding='utf-8') as f:
                    json.dump(self._json_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'❌ JSON DB save error: {e}')

    def get(self, section: str, key: str, default: Any=None) -> Any:
        with self._lock:
            return self._json_data.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any):
        with self._lock:
            if section not in self._json_data:
                self._json_data[section] = {}
            self._json_data[section][key] = value
            self._save_json_db()

    def delete(self, section: str, key: str) -> bool:
        with self._lock:
            if section in self._json_data and key in self._json_data[section]:
                del self._json_data[section][key]
                self._save_json_db()
                return True
            return False

    def get_section(self, section: str) -> Dict[str, Any]:
        with self._lock:
            return self._json_data.get(section, {}).copy()

    def get_module_config(self, module_name: str, key: str, default: Any=None) -> Any:
        return self.get('modules', f'{module_name}.{key}', default)

    def set_module_config(self, module_name: str, key: str, value: Any):
        self.set('modules', f'{module_name}.{key}', value)

    def get_user_data(self, user_id: int, key: str, default: Any=None) -> Any:
        with self._lock:
            users = self._json_data.setdefault('users', {})
            user_entry = users.setdefault(str(user_id), {})
            return user_entry.get(key, default)

    def set_user_data(self, user_id: int, key: str, value: Any):
        with self._lock:
            users = self._json_data.setdefault('users', {})
            user_entry = users.setdefault(str(user_id), {})
            user_entry[key] = value
            self._save_json_db()

    def get_chat_data(self, chat_id: int, key: str, default: Any=None) -> Any:
        with self._lock:
            chats = self._json_data.setdefault('chats', {})
            chat_entry = chats.setdefault(str(chat_id), {})
            return chat_entry.get(key, default)

    def set_chat_data(self, chat_id: int, key: str, value: Any):
        with self._lock:
            chats = self._json_data.setdefault('chats', {})
            chat_entry = chats.setdefault(str(chat_id), {})
            chat_entry[key] = value
            self._save_json_db()

    def get_config(self, key: str, default: Any=None) -> Any:
        return self.get('config', key, default)

    def set_config(self, key: str, value: Any):
        self.set('config', key, value)

    def get_stats(self) -> Dict[str, Any]:
        stats = {'json_sections': len(self._json_data), 'json_size': self.json_db_path.stat().st_size if self.json_db_path.exists() else 0, 'sqlite_size': 0}
        modules = self._json_data.get('modules', {})
        users = self._json_data.get('users', {})
        chats = self._json_data.get('chats', {})
        stats['module_data_count'] = sum((len([k for k in modules.keys() if k.startswith(f'{m}.')]) for m in set((k.split('.')[0] for k in modules.keys())))) if modules else 0
        stats['user_data_count'] = sum((len(v) for v in users.values())) if users else 0
        stats['chat_data_count'] = sum((len(v) for v in chats.values())) if chats else 0
        return stats
