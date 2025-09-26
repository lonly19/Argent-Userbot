import os
import sys
import logging
from typing import Optional
from .owner_manager import OwnerManager
logger = logging.getLogger(__name__)

class StartupSecurity:

    def __init__(self, config_dir: str='.argent_data'):
        try:
            self.owner_manager = OwnerManager(config_dir)
        except Exception as e:
            logger.error(f'Ошибка инициализации OwnerManager: {e}')
            self.owner_manager = OwnerManager(config_dir)
        self.config_dir = config_dir

    def check_owner_setup(self) -> bool:
        return self.owner_manager.has_primary_owner()

    def get_owner_info(self) -> dict:
        return {'has_owner': self.owner_manager.has_primary_owner(), 'primary_owner_id': self.owner_manager.get_primary_owner(), 'total_owners': len(self.owner_manager.get_all_owners()), 'setup_completed': self.owner_manager.is_setup_completed()}

    def require_owner_setup(self, app_name: str='Argent UserBot') -> bool:
        if not self.check_owner_setup():
            print(f'\n🔐 {app_name} - Система безопасности')
            print('=' * 50)
            print('❌ Владелец не настроен!')
            print('\n📋 Для запуска необходимо:')
            print('1. Запустить веб-установщик: python run.py')
            print('2. Ввести токен бота')
            print('3. Нажать /start в Telegram боте')
            print('4. Стать владельцем бота')
            print('\n🔒 Это защищает ваш userbot от несанкционированного доступа')
            print('💡 После настройки владельца можно запускать userbot')
            print('\n⚠️  ВНИМАНИЕ: Первый пользователь, нажавший /start, станет владельцем!')
            print('🔐 Убедитесь, что это делаете именно вы!')
            return False
        owner_info = self.get_owner_info()
        print(f'\n✅ {app_name} - Проверка безопасности пройдена')
        print('=' * 50)
        print(f"👑 Основной владелец: {owner_info['primary_owner_id']}")
        print(f"👥 Всего владельцев: {owner_info['total_owners']}")
        print(f"🔐 Настройка завершена: {('Да' if owner_info['setup_completed'] else 'Нет')}")
        print('🚀 Запуск разрешен!\n')
        return True

    def show_security_warning(self, app_name: str='Argent UserBot') -> None:
        print(f'\n⚠️  {app_name} - Предупреждение безопасности')
        print('=' * 50)
        print('🔐 Этот userbot защищен системой владельцев')
        print('👑 Только авторизованные пользователи могут управлять ботом')
        print('🚫 Неавторизованные пользователи получат отказ в доступе')
        print('\n💡 Для управления владельцами используйте inline бот')
        print('📱 Команда: /start в боте')
        print('⚙️  Настройки -> Управление владельцами')

    def validate_environment(self) -> bool:
        issues = []
        config_path = os.path.join(self.config_dir, 'owner_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    f.read(1)
            except PermissionError:
                issues.append('❌ Нет доступа к файлу конфигурации владельцев')
            except Exception as e:
                issues.append(f'❌ Ошибка чтения конфигурации: {e}')
        try:
            os.makedirs(self.config_dir, exist_ok=True)
        except PermissionError:
            issues.append(f'❌ Нет прав на создание директории {self.config_dir}')
        except Exception as e:
            issues.append(f'❌ Ошибка создания директории: {e}')
        if issues:
            print('\n🔒 Проблемы безопасности:')
            for issue in issues:
                print(f'  {issue}')
            return False
        return True

    def emergency_reset(self) -> bool:
        try:
            self.owner_manager.reset_config()
            print('⚠️  ВНИМАНИЕ: Конфигурация владельцев сброшена!')
            print('🔄 Необходимо заново настроить владельца через веб-установщик')
            return True
        except Exception as e:
            print(f'❌ Ошибка сброса конфигурации: {e}')
            return False

def check_startup_security(app_name: str='Argent UserBot', config_dir: str='.argent_data') -> bool:
    security = StartupSecurity(config_dir)
    if not security.validate_environment():
        print('❌ Проверка окружения не пройдена')
        return False
    security.show_security_warning(app_name)
    return security.require_owner_setup(app_name)
