from aiogram import Bot
from aiogram.types import BotCommand
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from config import dp, bot
from loguru import logger
import handlers


dp.middleware.setup(LoggingMiddleware())


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Начать 🚀"),
    ]
    await bot.set_my_commands(commands)


if __name__ == "__main__":
    from logger_config import setup_logger
    from aiogram import executor

    async def on_startup(dp):
        setup_logger()
        logger.info('Bot started ✅')
        await set_commands(bot)

    executor.start_polling(dp, on_startup=on_startup)
