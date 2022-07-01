from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, IDFilter
from src.db.database import DB_new


DBN = DB_new()


async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "Привет, этот бот создан для работы с рекламой Wildberries",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await message.answer(
        "Список команда: \n" + 
        "/start - Начало работы \n" +
        "/authorization - Добавить аккаунт WB \n" +
        "/smart_click - Умный кликер \n" +
        "/fiks - Фиксированное место \n" +
        "/output - Вкл/Выкл логирование \n",
        reply_markup=types.ReplyKeyboardRemove()
    )
    global DBN
    await DBN.add_user(telegram_id=str(message.from_user.id), full_name=message.from_user.full_name)


async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено", reply_markup=types.ReplyKeyboardRemove())


async def secret_command(message: types.Message):
    await message.answer("Поздравляю! Эта команда доступна только администратору бота.")



def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands="start", state="*")
    dp.register_message_handler(cmd_cancel, commands="cancel", state="*")
    dp.register_message_handler(cmd_cancel, Text(equals="отмена", ignore_case=True), state="*")
    # dp.register_message_handler(secret_command, IDFilter(user_id=admin_id), commands="abracadabra")