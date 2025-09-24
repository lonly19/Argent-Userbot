# 🧪 Argent UserBot - Руководство разработчика модулей

---

## 🚀 Введение

Argent UserBot поддерживает модульную архитектуру, позволяющую разработчикам создавать собственные команды и функции. Модули загружаются динамически с помощью команды `.load <module_name>`.

### Основные возможности:
- ⚡ Динамическая загрузка/выгрузка модулей
- 🔄 Перезагрузка без перезапуска бота
- 📦 Категоризация модулей
- 🎯 Простая система регистрации команд

---

## 📁 Структура модуля

Все модули должны находиться в папке `argent/modules/` и иметь расширение `.py`.

### Минимальная структура модуля:

```python
from argent.core.loader import ArgentModule

class MyModule(ArgentModule):
    __version__ = "1.0.0"
    __author__ = "Ваше имя"
    __category__ = "misc"  # core, utils, admin, fun, misc
    
    def __init__(self):
        super().__init__()
        self.description = "Описание вашего модуля"
        # Регистрация команд
        self.register_command("hello", self.cmd_hello, "Приветствие")
    
    async def cmd_hello(self, event, args):
        await event.edit("👋 Привет из модуля!")

module = MyModule()
```

---

## 🏗️ Базовый класс ArgentModule

### Атрибуты класса:
- `__version__` - версия модуля (обязательно)
- `__author__` - автор модуля (обязательно)
- `__category__` - категория модуля (обязательно)
- `__doc__` - описание модуля (опционально)

### Доступные объекты:
- `self.client` - Telethon клиент
- `self.db` - База данных Argent
- `self.utils` - Утилиты Argent
- `self.name` - Имя модуля
- `self.commands` - Словарь зарегистрированных команд

### Категории модулей:
- `core` 🧪 - Основные системные модули
- `utils` 🔧 - Утилиты и инструменты
- `admin` 👑 - Административные функции
- `fun` 🎭 - Развлекательные модули
- `misc` 📦 - Прочие модули

---

## ⚡ Создание команд

### Регистрация команды:
```python
self.register_command("имя_команды", self.метод_команды, "Описание команды")
```

### Структура метода команды:
```python
async def cmd_example(self, event, args):
    """
    event - объект события Telethon
    args - список аргументов команды (без префикса и имени команды)
    """
    if not args:
        await event.edit("❌ **Использование:** `.example <аргумент>`")
        return
    
    # Ваша логика здесь
    result = " ".join(args)
    await event.edit(f"✅ Результат: {result}")
```

### Работа с аргументами:
```python
async def cmd_example(self, event, args):
    # Проверка наличия аргументов
    if not args:
        await event.edit("❌ Укажите аргументы")
        return
    
    # Первый аргумент
    first_arg = args[0]
    
    # Все аргументы как строка
    all_args = " ".join(args)
    
    # Определенное количество аргументов
    if len(args) < 2:
        await event.edit("❌ Нужно минимум 2 аргумента")
        return
```

---

## 🔄 Цикл модуля

### Методы цикла:
```python
async def on_load(self):
    """Вызывается при загрузке модуля"""
    # Инициализация ресурсов
    self.start_time = time.time()
    print(f"Модуль {self.name} загружен")

async def on_unload(self):
    """Вызывается при выгрузке модуля"""
    # Очистка ресурсов
    print(f"Модуль {self.name} выгружен")
```

---

## 🔌 Доступ к API

### Telethon клиент:
```python
async def cmd_info(self, event, args):
    # Получить информацию о пользователе
    me = await self.client.get_me()
    
    # Отправить сообщение
    await self.client.send_message('me', 'Тест')
    
    # Получить сообщения из чата
    messages = await self.client.get_messages(event.chat_id, limit=10)
```

### База данных:
```python
async def cmd_save(self, event, args):
    # Сохранить данные модуля
    self.db.set("modules", f"{self.name}_data", {"key": "value"})
    
    # Получить данные модуля
    data = self.db.get("modules", f"{self.name}_data", {})
    
    # Сохранить пользовательские данные
    user_id = event.sender_id
    self.db.set("users", str(user_id), {"setting": "value"})
```

### Утилиты:
```python
async def cmd_utils_example(self, event, args):
    # Форматирование времени
    timestamp = time.time()
    formatted = self.utils.format_timestamp(int(timestamp))
    
    # Форматирование длительности
    duration = self.utils.format_duration(3661)  # "1ч 1м 1с"
    
    # Форматирование размера файла
    size = self.utils.format_bytes(1024)  # "1.0 KB"
    
    await event.edit(f"Время: {formatted}\nДлительность: {duration}\nРазмер: {size}")
```

---

## 📚 Примеры модулей

### 1. Простой модуль с одной командой:
```python
from argent.core.loader import ArgentModule

class HelloModule(ArgentModule):
    __version__ = "1.0.0"
    __author__ = "Developer"
    __category__ = "fun"
    
    def __init__(self):
        super().__init__()
        self.description = "Модуль приветствий"
        self.register_command("hello", self.cmd_hello, "👋 Поприветствовать")
    
    async def cmd_hello(self, event, args):
        name = " ".join(args) if args else "Мир"
        await event.edit(f"👋 Привет, {name}!")

module = HelloModule()
```

### 2. Модуль с сохранением данных:
```python
from argent.core.loader import ArgentModule
import time

class CounterModule(ArgentModule):
    __version__ = "1.0.0"
    __author__ = "Developer"
    __category__ = "utils"
    
    def __init__(self):
        super().__init__()
        self.description = "Счетчик использований"
        self.register_command("count", self.cmd_count, "📊 Показать счетчик")
        self.register_command("reset", self.cmd_reset, "🔄 Сбросить счетчик")
    
    async def cmd_count(self, event, args):
        # Получаем текущий счетчик
        count = self.db.get("modules", f"{self.name}_count", 0)
        count += 1
        
        # Сохраняем обновленный счетчик
        self.db.set("modules", f"{self.name}_count", count)
        
        await event.edit(f"📊 **Счетчик:** {count}")
    
    async def cmd_reset(self, event, args):
        self.db.set("modules", f"{self.name}_count", 0)
        await event.edit("🔄 **Счетчик сброшен**")

module = CounterModule()
```

### 3. Модуль с внешними зависимостями:
```python
from argent.core.loader import ArgentModule

class WeatherModule(ArgentModule):
    __version__ = "1.0.0"
    __author__ = "Developer"
    __category__ = "utils"
    
    def __init__(self):
        super().__init__()
        self.description = "Модуль погоды"
        self.register_command("weather", self.cmd_weather, "🌤️ Узнать погоду")
    
    async def cmd_weather(self, event, args):
        if not args:
            await event.edit("❌ **Использование:** `.weather <город>`")
            return
        
        city = " ".join(args)
        
        try:
            # Попытка импорта внешней библиотеки
            import requests
        except ImportError:
            await event.edit("❌ **Ошибка:** Установите requests: `pip install requests`")
            return
        
        try:
            # Здесь был бы реальный API запрос
            await event.edit(f"🌤️ **Погода в {city}:** Солнечно, +25°C")
        except Exception as e:
            await event.edit(f"❌ **Ошибка:** {str(e)}")

module = WeatherModule()
```

---

## 💡 Лучшие практики

### 1. Обработка ошибок:
```python
async def cmd_example(self, event, args):
    try:
        # Ваш код
        result = some_operation()
        await event.edit(f"✅ Результат: {result}")
    except Exception as e:
        await event.edit(f"❌ **Ошибка:** {str(e)}")
```

### 2. Валидация входных данных:
```python
async def cmd_example(self, event, args):
    if not args:
        await event.edit("❌ **Использование:** `.example <аргумент>`")
        return
    
    if len(args[0]) > 100:
        await event.edit("❌ **Ошибка:** Аргумент слишком длинный")
        return
```

### 3. Использование HTML форматирования:
```python
async def cmd_example(self, event, args):
    text = f"""
<b>🧪 Заголовок модуля</b>

<b>📝 Параметр:</b> <code>{args[0]}</code>
<b>✅ Статус:</b> Успешно

<blockquote>
💡 Дополнительная информация
</blockquote>
"""
    await event.edit(text)
```

### 4. Работа с файлами:
```python
async def cmd_file_example(self, event, args):
    if not event.is_reply:
        await event.edit("❌ Ответьте на сообщение с файлом")
        return
    
    reply = await event.get_reply_message()
    if not reply.media:
        await event.edit("❌ В сообщении нет файла")
        return
    
    # Скачать файл
    file_path = await self.client.download_media(reply.media)
    
    # Обработать файл
    # ...
    
    await event.edit("✅ Файл обработан")
```

---

## 🐛 Отладка и тестирование

### 1. Логирование:
```python
import logging

logger = logging.getLogger(__name__)

async def cmd_debug(self, event, args):
    logger.info(f"Команда debug вызвана с аргументами: {args}")
    # Ваш код
```

### 2. Проверка модуля перед загрузкой:
```bash
# Проверка синтаксиса
python -m py_compile argent/modules/your_module.py

# Запуск тестов (если есть)
python -m pytest tests/test_your_module.py
```

### 3. Тестирование команд:
```python
# В конце модуля можно добавить тесты
if __name__ == "__main__":
    # Простые тесты
    module = YourModule()
    print(f"Модуль {module.name} создан успешно")
    print(f"Команды: {list(module.commands.keys())}")
```

---

## 📦 Установка и использование

### 1. Создание модуля:
1. Создайте файл `your_module.py` в папке `argent/modules/`
2. Реализуйте класс, наследующий от `ArgentModule`
3. Создайте экземпляр модуля в конце файла

### 2. Загрузка модуля:
```
.load {reply_to_your_module.py}
```

### 3. Управление модулями:
```
.modules          # Список всех модулей
.unload your_module  # Выгрузить модуль
.reload your_module  # Перезагрузить модуль
```

---

## 🔗 Полезные ссылки

- [Документация Telethon](https://docs.telethon.dev/)
- [Примеры модулей](argent/modules/)
- [API Reference](https://github.com/lonly19/Argent-Userbot)

---

## 📞 Поддержка

Если у вас возникли вопросы по разработке модулей:
1. Изучите существующие модули в папке `argent/modules/`
2. Проверьте логи на наличие ошибок
3. Обратитесь к сообществу разработчиков

---

**Удачи в разработке модулей для Argent UserBot! 🚀**
