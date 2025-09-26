import os
import json
import logging
import time
import threading
from typing import Optional, List
from pathlib import Path
logger = logging.getLogger(__name__)

class OwnerManager:

    def __init__(self, config_dir: str='.argent_data'):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / 'owner_config.json'
        self._lock = threading.Lock()
        self._config = self._load_config()

    def _load_config(self) -> dict:
        if not self.config_file.exists():
            return {}
        for attempt in range(3):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        if attempt == 0:
                            time.sleep(0.1)
                            continue
                        else:
                            return {}
                    config = json.loads(content)
                    return config
            except json.JSONDecodeError as e:
                logger.error(f'Ошибка JSON в конфигурации владельцев (попытка {attempt + 1}): {e}')
                if attempt == 2:
                    try:
                        self.config_file.unlink()
                    except:
                        pass
                    return {}
                time.sleep(0.1)
            except Exception as e:
                logger.error(f'Ошибка загрузки конфигурации владельцев (попытка {attempt + 1}): {e}')
                if attempt == 2:
                    return {}
                time.sleep(0.1)
        return {}

    def _save_config(self) -> None:
        try:
            self.config_dir.mkdir(exist_ok=True)
            temp_file = self.config_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.config_file)
        except Exception as e:
            logger.error(f'Ошибка сохранения конфигурации владельцев: {e}')
            try:
                temp_file = self.config_file.with_suffix('.tmp')
                if temp_file.exists():
                    temp_file.unlink()
            except:
                pass

    def set_primary_owner(self, user_id: int) -> bool:
        if not isinstance(user_id, int) or user_id <= 0:
            logger.error(f'Неверный user_id: {user_id}')
            return False
        if user_id < 1000:
            logger.error(f'Подозрительно маленький user_id: {user_id}')
            return False
        with self._lock:
            self._config = self._load_config()
            if self.has_primary_owner():
                logger.warning(f'Попытка установить основного владельца {user_id}, но он уже существует')
                return False
            self._config['primary_owner'] = user_id
            self._config['owners'] = [user_id]
            self._config['setup_completed'] = True
            self._save_config()
            return True

    def has_primary_owner(self) -> bool:
        return 'primary_owner' in self._config and self._config['primary_owner'] is not None

    def get_primary_owner(self) -> Optional[int]:
        return self._config.get('primary_owner')

    def is_owner(self, user_id: int) -> bool:
        owners = self._config.get('owners', [])
        return user_id in owners

    def add_owner(self, user_id: int, added_by: int) -> bool:
        if not self.is_owner(added_by):
            logger.warning(f'Пользователь {added_by} попытался добавить владельца {user_id} без прав')
            return False
        owners = self._config.get('owners', [])
        if user_id not in owners:
            owners.append(user_id)
            self._config['owners'] = owners
            self._save_config()
            return True
        return False

    def remove_owner(self, user_id: int, removed_by: int) -> bool:
        if user_id == self.get_primary_owner():
            logger.warning(f'Попытка удалить основного владельца {user_id}')
            return False
        if not self.is_owner(removed_by):
            logger.warning(f'Пользователь {removed_by} попытался удалить владельца {user_id} без прав')
            return False
        owners = self._config.get('owners', [])
        if user_id in owners:
            owners.remove(user_id)
            self._config['owners'] = owners
            self._save_config()
            return True
        return False

    def get_all_owners(self) -> List[int]:
        return self._config.get('owners', [])

    def is_setup_completed(self) -> bool:
        return self._config.get('setup_completed', False)

    def reset_config(self) -> None:
        self._config = {}
        if self.config_file.exists():
            self.config_file.unlink()

    def get_config_info(self) -> dict:
        return {'has_primary_owner': self.has_primary_owner(), 'primary_owner': self.get_primary_owner(), 'total_owners': len(self.get_all_owners()), 'setup_completed': self.is_setup_completed(), 'config_file_exists': self.config_file.exists()}
