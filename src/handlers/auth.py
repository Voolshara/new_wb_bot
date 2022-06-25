from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup


# keboards
first_keyboard = ["Добавить аккаунт", "Удалить аккаунт", "Посмотреть добавленные аккаунты"]


# states
class Authorization(StatesGroup):
    choose_command_below = State()
    add_account = State()
    delete_account = State()
    look_account = State()


# start auth state
async def auth_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for code in first_keyboard:
        keyboard.add(code)
    await message.answer("Выберите нужную команду (см. ниже):", reply_markup=keyboard)
    await Authorization.choose_command_below.set()


# chosse key in keyboard
async def auth_chosen(message: types.Message):
    print(message.text.lower())
    if message.text not in first_keyboard:
        await message.answer("Пожалуйста, воспользуйтесь командой, используя клавиатуру ниже")
        return
    if message.text.lower() == "добавить аккаунт":
        #if check_queue:
        if True:
            await Authorization.add_account.set()
        else:
            await message.answer("Повторите попытку позже")
            await state.finish()
    elif message.text.lower() == "удалить аккаунт":
        # await message.answer("2")
        await Authorization.delete_account.set()
    elif message.text.lower() == "посмотреть добавленные аккаунты":
        # await message.answer("3")
        await Authorization.look_account.set()
    else:
        await message.answer("Пожалуйста, воспользуйтесь командой, используя клавиатуру ниже")


def register_handlers_auth(dp: Dispatcher):
    dp.register_message_handler(auth_start, commands="authorization", state="*")
    dp.register_message_handler(auth_chosen, state=Authorization.choose_command_below)
    # dp.register_message_handler(food_size_chosen, state=OrderFood.waiting_for_food_size)


    
