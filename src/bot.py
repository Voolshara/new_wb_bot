import logging, asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from typer import Typer

from src.handlers.food import register_handlers_food
from src.handlers.common import register_handlers_common
from src.handlers.auth import register_handlers_auth
from src.handlers.fiks import register_handlers_fiks


logger = logging.getLogger(__name__)
run = Typer()

# Регистрация команд, отображаемых в интерфейсе Telegram
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/authorization", description="Добавить новый аккаунт WB"),
        BotCommand(command="/fiks", description="Фиксированное место"),
        BotCommand(command="/cancel", description="Отменить текущее действие")
    ]
    await bot.set_my_commands(commands)


async def main():
    # Настройка логирования в stdout
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger.error("Starting bot")

    # Объявление и инициализация объектов бота и диспетчера
    bot = Bot(token="5585095304:AAFYsfIoTD29QSln36yfVpwKVhodzIRlaKs")
    dp = Dispatcher(bot, storage=MemoryStorage())

    # Регистрация хэндлеров
    register_handlers_common(dp)
    register_handlers_food(dp)
    register_handlers_auth(dp)
    register_handlers_fiks(dp)

    # Установка команд бота
    await set_commands(bot)

    # Запуск поллинга
    await dp.skip_updates()  # пропуск накопившихся апдейтов (необязательно)
    await dp.start_polling()


@run.command()
def bot_runner():
    asyncio.run(main())