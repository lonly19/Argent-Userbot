import os
import sys
import importlib
import importlib.util
import logging
import traceback
from typing import Dict, List, Optional, Any, Type
from pathlib import Path
from ..storage.database import ArgentDatabase
from ..utils.utils import ArgentUtils
logger = logging.getLogger(__name__)

class ModuleInfo:

    def __init__(self, name: str, version: str='1.0.0', author: str='Unknown', description: str='', category: str='misc'):
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.category = category
        self.commands = []
        self.loaded = False
        self.instance = None

class ArgentModule:

    def __init__(self):
        self.name = self.__class__.__name__
        self.version = getattr(self, '__version__', '1.0.0')
        self.author = getattr(self, '__author__', 'Unknown')
        self.description = getattr(self, '__doc__', 'No description')
        self.category = getattr(self, '__category__', 'misc')
        self.commands = {}
        self.client = None
        self.db = None
        self.utils = None

    async def on_load(self):
        pass

    async def on_unload(self):
        pass

    def register_command(self, name: str, func: callable, description: str=''):
        self.commands[name] = {'func': func, 'description': description, 'module': self.name}

class ArgentLoader:

    def __init__(self, client, db: ArgentDatabase, utils: ArgentUtils):
        self.client = client
        self.db = db
        self.utils = utils
        self.modules: Dict[str, ModuleInfo] = {}
        self.commands: Dict[str, Dict] = {}
        self.modules_dir = Path('argent/modules')
        self.modules_dir.mkdir(exist_ok=True)

    async def load_all_modules(self):
        logger.info('🔬 Starting module discovery...')
        if not self.modules_dir.exists():
            logger.warning('📁 Modules directory not found, creating...')
            self.modules_dir.mkdir(exist_ok=True)
            return
        for file_path in self.modules_dir.glob('*.py'):
            if file_path.name.startswith('_'):
                continue
            module_name = file_path.stem
            try:
                await self.load_module(module_name)
            except Exception as e:
                logger.error(f'❌ Failed to load module {module_name}: {e}')
        logger.info(f'✅ Loaded {len(self.modules)} modules with {len(self.commands)} commands')

    async def load_module(self, module_name: str) -> bool:
        try:
            module_path = self.modules_dir / f'{module_name}.py'
            if not module_path.exists():
                logger.error(f'📄 Module file not found: {module_path}')
                return False
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if not spec or not spec.loader:
                logger.error(f'🚫 Invalid module spec: {module_name}')
                return False
            module = importlib.util.module_from_spec(spec)
            sys.modules[f'argent.modules.{module_name}'] = module
            spec.loader.exec_module(module)
            module_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, ArgentModule) and (attr != ArgentModule):
                    module_class = attr
                    break
            if not module_class:
                logger.error(f'🔍 No ArgentModule class found in {module_name}')
                return False
            instance = module_class()
            instance.client = self.client
            instance.db = self.db
            instance.utils = self.utils
            info = ModuleInfo(name=instance.name, version=instance.version, author=instance.author, description=instance.description, category=instance.category)
            info.instance = instance
            info.loaded = True
            for cmd_name, cmd_info in instance.commands.items():
                full_cmd = f'.{cmd_name}'
                self.commands[full_cmd] = cmd_info
                info.commands.append(full_cmd)
            self.modules[module_name] = info
            await instance.on_load()
            logger.info(f'✅ Loaded module: {instance.name} v{instance.version} by {instance.author}')
            return True
        except Exception as e:
            logger.error(f'❌ Error loading module {module_name}: {e}')
            logger.debug(traceback.format_exc())
            return False

    async def unload_module(self, module_name: str) -> bool:
        if module_name not in self.modules:
            return False
        try:
            info = self.modules[module_name]
            if info.instance:
                await info.instance.on_unload()
            for cmd in info.commands:
                self.commands.pop(cmd, None)
            sys.modules.pop(f'argent.modules.{module_name}', None)
            del self.modules[module_name]
            logger.info(f'🗑️ Unloaded module: {module_name}')
            return True
        except Exception as e:
            logger.error(f'❌ Error unloading module {module_name}: {e}')
            return False

    async def reload_module(self, module_name: str) -> bool:
        if module_name in self.modules:
            await self.unload_module(module_name)
        return await self.load_module(module_name)

    def get_module_info(self, module_name: str) -> Optional[ModuleInfo]:
        return self.modules.get(module_name)

    def get_all_modules(self) -> Dict[str, ModuleInfo]:
        return self.modules.copy()

    def get_commands_by_category(self) -> Dict[str, List[str]]:
        categories = {}
        for module_name, info in self.modules.items():
            if info.category not in categories:
                categories[info.category] = []
            categories[info.category].extend(info.commands)
        return categories

    async def execute_command(self, command: str, event, args: List[str]) -> bool:
        if command not in self.commands:
            return False
        try:
            cmd_info = self.commands[command]
            await cmd_info['func'](event, args)
            return True
        except Exception as e:
            logger.error(f'❌ Command execution error {command}: {e}')
            await event.edit(f'⚠️ <b>Ошибка команды:</b> <code>{e}</code>')
            return False
