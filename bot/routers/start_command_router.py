from aiogram import Router
from aiogram.filters import CommandStart

from app.bot.scenes.start_scene import StartScene

start_command_router: Router = Router(name=__name__)

start_command_router.message.register(
    StartScene.as_handler(),
    CommandStart()
)
