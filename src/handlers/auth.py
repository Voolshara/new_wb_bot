from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import re

# keboards
first_keyboard = ["Добавить аккаунт", "Удалить аккаунт", "Посмотреть добавленные аккаунты"]


# states
class Authorization(StatesGroup):
    choose_command_below = State()

    add_account = State()
    wait_code = State()

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
    if message.text not in first_keyboard:
        await message.answer("Пожалуйста, воспользуйтесь командой, используя клавиатуру ниже")
        return
    if message.text.lower() == "добавить аккаунт":
        #if check_queue:
        if True:
            await message.answer("Отлично, давайте добавим новый аккаунт")
            await message.answer("Введите номер телефона без кода страны \n Пример: 9371111111")
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


# add new account
async def new_accound(message: types.Message):
    phone_number = message.text
    phone_reg = re.compile("\d{3}\d{3}\d{4}")
    if len(phone_reg.findall(phone_number)) == 0:
        await message.answer("Неверный номер телефона (см Пример) \nПопоробуйте ещё раз")
        return 
    await message.answer("Телефон принят, подождите немного")
    # send_phone
    await message.answer("Введите код из смс для входа в учётную запись")
    await Authorization.wait_code.set()


# get code from sms
async def get_sms(message: types.Message):
    code = message.text
    code_reg = re.compile("\d{6}")
    if len(code_reg.findall(code)) == 0:
        await message.answer("Неверный код изи смс\n Введите ещё раз")
        return
    await message.answer("Код принят, подождите немного")
    # send_sms
    await message.answer("Готово, аккаунт добавлен")


def register_handlers_auth(dp: Dispatcher):
    dp.register_message_handler(auth_start, commands="authorization", state="*")
    dp.register_message_handler(auth_chosen, state=Authorization.choose_command_below)
    dp.register_message_handler(new_accound, state=Authorization.add_account)
    dp.register_message_handler(get_sms, state=Authorization.wait_code)
