import json
import logging
import os
from typing import Any, Dict, Optional
from pathlib import Path
from .config_defaults import DEFAULT_CONFIG, DEFAULT_MODULE_CONFIG
logger = logging.getLogger(__name__)

class ConfigManager:

    def __init__(self, data_dir: str='.argent_data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.config_path = self.data_dir / 'config.json'
        self.user_config_path = self.data_dir / 'user_config.json'
        self._config = {}
        self._user_config = {}
        self._load_env()
        self._load_config()

    def _load_config(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception as e:
                logger.error(f'❌ Ошибка загрузки config.json: {e}')
                self._config = {}
        if self.user_config_path.exists():
            try:
                with open(self.user_config_path, 'r', encoding='utf-8') as f:
                    self._user_config = json.load(f)
            except Exception as e:
                logger.error(f'❌ Ошибка загрузки user_config.json: {e}')
                self._user_config = {}
        if not self._user_config:
            self._user_config = self._deep_copy_dict(DEFAULT_CONFIG)
            self._save_user_config()

    def _load_env(self):
        try:
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except Exception:
                pass
            api_id = os.getenv('TELEGRAM_API_ID') or os.getenv('API_ID')
            api_hash = os.getenv('TELEGRAM_API_HASH') or os.getenv('API_HASH')
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
            if api_id and api_hash:
                try:
                    self.set_system('api_id', int(api_id), save=False)
                except Exception:
                    self.set_system('api_id', api_id, save=False)
                self.set_system('api_hash', str(api_hash), save=False)
            if bot_token:
                self.set_system('bot_token', str(bot_token), save=False)
            if self._config:
                self._save_config()
        except Exception:
            pass

    def _save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'❌ Ошибка сохранения config.json: {e}')

    def _save_user_config(self):
        try:
            with open(self.user_config_path, 'w', encoding='utf-8') as f:
                json.dump(self._user_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'❌ Ошибка сохранения user_config.json: {e}')

    def _deep_copy_dict(self, d: Dict) -> Dict:
        return json.loads(json.dumps(d))

    def _get_nested_value(self, data: Dict, path: str, default: Any=None) -> Any:
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def _set_nested_value(self, data: Dict, path: str, value: Any):
        keys = path.split('.')
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def get(self, path: str, default: Any=None) -> Any:
        value = self._get_nested_value(self._user_config, path)
        if value is not None:
            return value
        value = self._get_nested_value(self._config, path)
        if value is not None:
            return value
        value = self._get_nested_value(DEFAULT_CONFIG, path)
        if value is not None:
            return value
        return default

    def set(self, path: str, value: Any, save: bool=True):
        self._set_nested_value(self._user_config, path, value)
        if save:
            self._save_user_config()

    def set_system(self, path: str, value: Any, save: bool=True):
        self._set_nested_value(self._config, path, value)
        if save:
            self._save_config()

    def delete_system(self, path: str, save: bool=True) -> bool:
        keys = path.split('.')
        current = self._config
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                return False
            current = current[key]
        if keys[-1] in current:
            del current[keys[-1]]
            if save:
                self._save_config()
            return True
        return False

    def delete(self, path: str, save: bool=True) -> bool:
        keys = path.split('.')
        current = self._user_config
        for key in keys[:-1]:
            if key not in current:
                return False
            current = current[key]
        if keys[-1] in current:
            del current[keys[-1]]
            if save:
                self._save_user_config()
            return True
        return False

    def reset_to_default(self, path: str=None, save: bool=True):
        if path is None:
            self._user_config = self._deep_copy_dict(DEFAULT_CONFIG)
        else:
            default_value = self._get_nested_value(DEFAULT_CONFIG, path)
            if default_value is not None:
                self._set_nested_value(self._user_config, path, default_value)
        if save:
            self._save_user_config()

    def get_api_credentials(self) -> Optional[Dict[str, Any]]:
        api_id = self.get('api_id')
        api_hash = self.get('api_hash')
        if api_id and api_hash:
            return {'api_id': int(api_id), 'api_hash': str(api_hash)}
        return None

    def set_api_credentials(self, api_id: int, api_hash: str):
        self.set_system('api_id', api_id)
        self.set_system('api_hash', api_hash)

    def get_session_string(self) -> Optional[str]:
        s = self.get('session_string')
        if s:
            return s
        argent = self.get('user_session')
        return argent

    def set_session_string(self, session_string: str):
        self.set_system('session_string', session_string)

    def clear_argent_session_key(self):
        try:
            removed1 = self.delete_system('user_session', save=False)
            removed2 = self.delete_system('session_string', save=True)
            return removed1 or removed2
        except Exception:
            return False

    def get_bot_token(self) -> Optional[str]:
        return self.get('bot_token')

    def set_bot_token(self, bot_token: str):
        self.set_system('bot_token', bot_token)

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        config = self.get(f'modules.{module_name}', {})
        default = DEFAULT_MODULE_CONFIG.get(module_name, {})
        result = self._deep_copy_dict(default)
        result.update(config)
        return result

    def set_module_config(self, module_name: str, config: Dict[str, Any]):
        self.set(f'modules.{module_name}', config)

    def is_first_run(self) -> bool:
        return not self.config_path.exists() or not self.get('setup_completed', False)

    def mark_setup_completed(self):
        self.set_system('setup_completed', True)

    def get_all_config(self) -> Dict[str, Any]:
        result = self._deep_copy_dict(DEFAULT_CONFIG)
        for key, value in self._config.items():
            if isinstance(value, dict) and key in result:
                result[key].update(value)
            else:
                result[key] = value
        for key, value in self._user_config.items():
            if isinstance(value, dict) and key in result:
                result[key].update(value)
            else:
                result[key] = value
        return result
