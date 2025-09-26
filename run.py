import os
from argent.installer import create_app
from argent.security import StartupSecurity
if __name__ == '__main__':
    print('⚗️ Argent UserBot - Scientific Telegram Framework')
    print('🔬 Веб-установщик с улучшенной безопасностью')
    security = StartupSecurity()
    owner_info = security.get_owner_info()
    if owner_info['has_owner']:
        print(f'\n🔐 Статус безопасности:')
        print(f"👑 Основной владелец: {owner_info['primary_owner_id']}")
        print(f"👥 Всего владельцев: {owner_info['total_owners']}")
        print('✅ Владелец уже настроен')
        print('\n💡 Веб-установщик можно использовать для:')
        print('   • Переустановки бота')
        print('   • Смены токена')
        print('   • Сброса конфигурации')
    else:
        print('\n🔓 Владелец не настроен')
        print('⚠️  ВНИМАНИЕ: Первый пользователь, нажавший /start в боте, станет владельцем!')
        print('🔐 Убедитесь, что это будете именно вы!')
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    print(f'\n🚀 Starting web installer on http://{host}:{port}')
    print('🧪 После ввода токена бота вас перенаправит в Telegram для продолжения установки')
    print('🔬 Научный подход к разработке юзерботов')
    app.run(host=host, port=port, debug=debug)
