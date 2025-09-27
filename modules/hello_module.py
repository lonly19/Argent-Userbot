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
