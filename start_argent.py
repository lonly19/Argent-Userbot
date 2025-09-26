import asyncio
import sys
from argent.core.userbot import main
from argent.security import check_startup_security
if __name__ == '__main__':
    print('⚗️ Argent UserBot v2.0.0 - Scientific Framework')
    print('🧪 Initializing Argent UserBot userbot systems...')
    if not check_startup_security('Argent UserBot'):
        print('\n🛑 Запуск остановлен из соображений безопасности')
        print('📋 Следуйте инструкциям выше для настройки владельца')
        sys.exit(1)
    print('🔬 Loading molecular modules...')
    asyncio.run(main())
