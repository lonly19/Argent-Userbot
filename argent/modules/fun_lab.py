import random
import asyncio
from argent.core.loader import ArgentModule

class FunLabModule(ArgentModule):
    __version__ = '1.0.0'
    __author__ = 'github.com/lonly19/Argent-Userbot'
    __category__ = 'fun'

    def __init__(self):
        super().__init__()
        self.description = '🎭 Лаборатория развлечений и экспериментов'
        self.register_command('dice', self.cmd_dice, '🎲 Бросить кубик')
        self.register_command('coin', self.cmd_coin, '🪙 Подбросить монету')
        self.register_command('random', self.cmd_random, '🔀 Случайное число')
        self.register_command('choose', self.cmd_choose, '🎯 Выбрать вариант')
        self.register_command('reverse', self.cmd_reverse, '🔄 Перевернуть текст')
        self.register_command('mock', self.cmd_mock, '🤡 МоКиНг ТеКсТ')
        self.register_command('chemistry', self.cmd_chemistry, '⚗️ Химическая реакция')
        self.register_command('experiment', self.cmd_experiment, '🧪 Научный эксперимент')

    async def cmd_dice(self, event, args):
        sides = 6
        count = 1
        if args:
            try:
                if len(args) == 1:
                    if 'd' in args[0]:
                        count, sides = map(int, args[0].split('d'))
                    else:
                        sides = int(args[0])
                elif len(args) == 2:
                    count, sides = (int(args[0]), int(args[1]))
            except ValueError:
                await event.edit('❌ <b>Использование:</b> <code>.dice [количество] [граней]</code> или <code>.dice 2d6</code>')
                return
        if count > 10 or sides > 100:
            await event.edit('❌ <b>Лимит:</b> максимум 10 кубиков по 100 граней')
            return
        results = [random.randint(1, sides) for _ in range(count)]
        total = sum(results)
        dice_emoji = '🎲' * min(count, 5)
        result_text = f"\n\n{dice_emoji} <b>Результат броска</b>\n\n<b>🎯 Кубиков:</b> <code>{count}</code> по <code>{sides}</code> граней\n\n<b>📊 Результаты:</b> <code>{', '.join(map(str, results))}</code>\n\n<b>🧮 Сумма:</b> <code>{total}</code>\n\n<b>📈 Среднее:</b> <code>{total / count:.1f}</code>\n\n"
        await event.edit(result_text)

    async def cmd_coin(self, event, args):
        count = 1
        if args:
            try:
                count = int(args[0])
                if count > 20:
                    count = 20
            except ValueError:
                pass
        results = []
        heads = 0
        tails = 0
        for _ in range(count):
            result = random.choice(['Орел', 'Решка'])
            results.append(result)
            if result == 'Орел':
                heads += 1
            else:
                tails += 1
        coin_emoji = '🪙' * min(count, 5)
        result_text = f"\n\n{coin_emoji} <b>Подбрасывание монеты</b>\n\n<b>🎯 Бросков:</b> <code>{count}</code>\n\n<b>📊 Результаты:</b> <code>{', '.join(results)}</code>\n\n<b>📈 Статистика:</b>\n\n• 🦅 <b>Орел:</b> <code>{heads}</code> ({self.utils.format_percentage(heads, count)}%)\n\n• 🏛️ <b>Решка:</b> <code>{tails}</code> ({self.utils.format_percentage(tails, count)}%)\n\n"
        await event.edit(result_text)

    async def cmd_random(self, event, args):
        min_val = 1
        max_val = 100
        if len(args) == 1:
            try:
                max_val = int(args[0])
            except ValueError:
                pass
        elif len(args) == 2:
            try:
                min_val, max_val = (int(args[0]), int(args[1]))
            except ValueError:
                pass
        if min_val >= max_val:
            await event.edit('❌ <b>Минимум должен быть меньше максимума</b>')
            return
        result = random.randint(min_val, max_val)
        await event.edit(f'\n\n🔀 <b>Случайное число</b>\n\n<b>📊 Диапазон:</b> <code>{min_val}</code> - <code>{max_val}</code>\n\n<b>🎯 Результат:</b> <code>{result}</code>\n\n<b>🧪 Вероятность:</b> <code>1/{max_val - min_val + 1}</code>\n\n')

    async def cmd_choose(self, event, args):
        if not args:
            await event.edit('❌ <b>Использование:</b> <code>.choose вариант1 вариант2 вариант3...</code>')
            return
        choice = random.choice(args)
        await event.edit(f'\n\n🎯 <b>Научный выбор</b>\n\n<b>🧪 Варианты:</b> <code>{len(args)}</code>\n\n<b>⚛️ Выбор:</b> <b>{choice}</b>\n\n<b>🔬 Метод:</b> Квантовая случайность\n\n')

    async def cmd_reverse(self, event, args):
        if not args:
            await event.edit('❌ **Использование:** `.reverse <текст>`')
            return
        text = ' '.join(args)
        reversed_text = text[::-1]
        await event.edit(f'\n\n🔄 <b>Обращение текста</b>\n\n<b>📝 Оригинал:</b> <code>{text}</code>\n\n<b>🔄 Обращенный:</b> <code>{reversed_text}</code>\n\n<b>🧬 Длина:</b> <code>{len(text)}</code> символов\n\n')

    async def cmd_mock(self, event, args):
        if not args:
            await event.edit('❌ **Использование:** `.mock <текст>`')
            return
        text = ' '.join(args)
        mocked = ''
        for i, char in enumerate(text):
            if char.isalpha():
                mocked += char.upper() if i % 2 == 0 else char.lower()
            else:
                mocked += char
        await event.edit(f'\n\n🤡 <b>МоКиНг ТеКсТ</b>\n\n<b>📝 Оригинал:</b> {text}\n\n<b>🤡 МоКиНг:</b> {mocked}\n\n<b>🧪 Алгоритм:</b> Чередование регистра\n\n')

    async def cmd_chemistry(self, event, args):
        reactions = [('H₂ + Cl₂', '2HCl', 'Синтез хлороводорода'), ('2H₂ + O₂', '2H₂O', 'Образование воды'), ('CH₄ + 2O₂', 'CO₂ + 2H₂O', 'Горение метана'), ('CaCO₃', 'CaO + CO₂', 'Разложение карбоната кальция'), ('Fe + S', 'FeS', 'Синтез сульфида железа'), ('2Na + Cl₂', '2NaCl', 'Образование поваренной соли'), ('Mg + 2HCl', 'MgCl₂ + H₂', 'Реакция магния с кислотой'), ('C + O₂', 'CO₂', 'Горение углерода')]
        reactants, products, description = random.choice(reactions)
        await event.edit(f"\n\n⚗️ <b>Химическая реакция</b>\n\n<b>🧪 Реагенты:</b> <code>{reactants}</code>\n\n<b>➡️ Продукты:</b> <code>{products}</code>\n\n<b>📋 Описание:</b> {description}\n\n<b>🔬 Тип:</b> {random.choice(['Синтез', 'Разложение', 'Замещение', 'Обмен'])}\n\n<b>🌡️ Условия:</b> {random.choice(['Нормальные', 'Нагревание', 'Катализатор', 'Высокое давление'])}\n\n")

    async def cmd_experiment(self, event, args):
        experiments = [{'name': 'Определение pH раствора', 'materials': ['Лакмусовая бумага', 'сследуемый раствор', 'Эталонная шкала'], 'result': f'pH = {random.uniform(1, 14):.1f}', 'conclusion': random.choice(['Кислая среда', 'Щелочная среда', 'Нейтральная среда'])}, {'name': 'змерение плотности вещества', 'materials': ['Весы', 'Мерный цилиндр', 'сследуемое вещество'], 'result': f'ρ = {random.uniform(0.5, 5.0):.2f} г/см³', 'conclusion': random.choice(['Легче воды', 'Тяжелее воды', 'Близко к воде'])}, {'name': 'Анализ спектра поглощения', 'materials': ['Спектрофотометр', 'Образец', 'Кювета'], 'result': f'λmax = {random.randint(400, 700)} нм', 'conclusion': random.choice(['Синий спектр', 'Красный спектр', 'Зеленый спектр'])}]
        experiment = random.choice(experiments)
        await event.edit(f"\n\n🧪 <b>Научный эксперимент</b>\n\n<b>📋 Название:</b> {experiment['name']}\n\n<b>🔬 Материалы:</b>\n\n{chr(10).join([f'• {material}' for material in experiment['materials']])}\n\n<b>📊 Результат:</b> <code>{experiment['result']}</code>\n\n<b>🎯 Вывод:</b> {experiment['conclusion']}\n\n<b>⚛️ Статус:</b> Эксперимент завершен успешно\n\n")
module = FunLabModule()
