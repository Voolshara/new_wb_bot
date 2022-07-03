from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import re, requests
from src.db.database import DB_new, DB_get

# keboards
first_keyboard = ["Добавить аккаунт", "Удалить аккаунт", "Посмотреть добавленные аккаунты", "Меню"]
repeat_sms_keyboard = ["Отправить код заново"]

# states
class Authorization(StatesGroup):
    choose_command_below = State()

    add_account = State()
    wait_code = State()

    delete_account = State()
    
    look_account = State()

# database
DBN = DB_new()
DBG = DB_get()

# start auth state
async def auth_start(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for code in first_keyboard:
        keyboard.add(code)
    await message.answer("Выберите нужную команду (см. ниже):", reply_markup=keyboard)
    await Authorization.choose_command_below.set()


# chosse key in keyboard
async def auth_chosen(message: types.Message, state: FSMContext):
    if message.text not in first_keyboard:
        await message.answer("Пожалуйста, воспользуйтесь командой, используя клавиатуру ниже")
        return
    if message.text.lower() == "добавить аккаунт":
        #if check_queue:
        if True:
            await message.answer("Отлично, давайте добавим новый аккаунт")
            await message.answer("Введите номер телефона без кода страны \nПример: 9371111111", reply_markup=types.ReplyKeyboardRemove())
            await Authorization.add_account.set()
        else:
            await message.answer("Повторите попытку позже")
            await state.finish()
    elif message.text.lower() == "удалить аккаунт":
        list_of_cookies = DBG.get_all_cookies(message.from_user.id)
        if len(list_of_cookies) == 0:
            await message.answer('У вас нет добавленных аккаунтов')
            await Authorization.choose_command_below.set()
            return
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for account in list_of_cookies:
            keyboard.add(account)
        await message.answer("Какой аккаунт вы хотите удалить?", reply_markup=keyboard)
        await Authorization.delete_account.set()
    elif message.text.lower() == "посмотреть добавленные аккаунты":
        list_of_cookies = DBG.get_all_cookies(message.from_user.id)
        if len(list_of_cookies) > 0:
            out = "Добавленные аккануты:\n"
            for el in list_of_cookies:
                out += "Тел: " + el + "\n"
            await message.answer(out)
            await Authorization.choose_command_below.set()
            return
        await message.answer('У вас нет добавленных аккаунтов')
        await Authorization.choose_command_below.set()
        # await Authorization.look_account.set()
    elif message.text.lower() == "меню":
        await message.answer(
            "Список команда: \n" + 
            "/start - Начало работы \n" +
            "/authorization - Добавить аккаунт WB \n" +
            "/smart_click - Умный кликер \n" +
            "/fiks - Фиксированное место \n" +
            "/output - Вкл/Выкл логирование \n",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer("Пожалуйста, воспользуйтесь командой, используя клавиатуру ниже")


# add new account
async def new_accound(message: types.Message, state: FSMContext):
    phone_number = message.text
    # check line in DB
    phone_reg = re.compile("\d{3}\d{3}\d{4}")
    if len(phone_reg.findall(phone_number)) == 0 or len(phone_number) != 10:
        await message.answer("Неверный номер телефона (см Пример) \nПопоробуйте ещё раз", reply_markup=types.ReplyKeyboardRemove())
        return 
    await message.answer("Телефон принят, подождите немного", reply_markup=types.ReplyKeyboardRemove())

    data = requests.post("http://localhost:4600/new_user", json={
        "status" : "phone",
        "mes" : phone_number
    }).json()

    print(data)

    if data["status"]:
        if await DBN.set_driver(message.from_user.id, data["name_of_driver"]) and  await DBN.set_phone(message.from_user.id, phone_number):
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for code in repeat_sms_keyboard:
                keyboard.add(code)
            await message.answer("Введите код из смс для входа в учётную запись", reply_markup=keyboard)
            await Authorization.wait_code.set()
        else:
            await message.answer("Вас нет в нашей Базе Данных, попробуйте /start", reply_markup=types.ReplyKeyboardRemove())
            await state.finish()
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for code in first_keyboard:
            keyboard.add(code)
        await message.answer(f"Ошибка со стороны WB \nСообщение от WB: {data['mes']}", reply_markup=keyboard)
        await Authorization.choose_command_below.set()


# get code from sms
async def get_sms(message: types.Message, state: FSMContext):
    code = message.text
    if code == "Отправить код заново":
        driver = DBG.get_driver(message.from_user.id)
        data = requests.post("http://localhost:4600/new_user", json={
            "status" : "repeat_sms",
            "driver_code" : driver,
        }).json()
        if data["status"]:
            await message.answer("Код отправлен")
            return
        await message.answer("Ещё нет возможности отправить код заново \nНужно подождать около минуты")
        return
    code_reg = re.compile("\d{6}")
    if len(code_reg.findall(code)) == 0 or len(code) != 6:
        await message.answer("Неверный код изи смс\nВведите ещё раз")
        return
    await message.answer("Код принят, подождите немного", reply_markup=types.ReplyKeyboardRemove())

    driver = DBG.get_driver(message.from_user.id)
    phone = DBG.get_phone(message.from_user.id)
    
    data = requests.post("http://localhost:4600/new_user", json={
        "status" : "sms",
        "driver_code" : driver,
        "phone" : phone,
        "sms" : code,
    }).json()

    print(data)

    if data["status"]:
        await DBN.add_cookie(message.from_user.id, phone, f"cookie{phone}")
        await message.answer("Готово, аккаунт добавлен", reply_markup=types.ReplyKeyboardRemove())
        await Authorization.choose_command_below.set()
    else:
        if data["mes"] == "Неверный СМС код" or data["mes"] == "Неверные данные доступа":
            await message.answer(f"Ошибка\nСообщение от WB: {data['mes']}", reply_markup=types.ReplyKeyboardRemove())
            await message.answer(f"Проверьте смс код и отправьте его снова", reply_markup=types.ReplyKeyboardRemove())
            return
        await message.answer(f"Ошибка\nСообщение от WB: {data['mes']}", reply_markup=types.ReplyKeyboardRemove())
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for code in first_keyboard:
            keyboard.add(code)
        await message.answer("Начните сначала", reply_markup=keyboard)
        await Authorization.choose_command_below.set()


async def delete_account(message: types.Message, state: FSMContext):
    list_of_cookies = DBG.get_all_cookies(message.from_user.id)
    cookie = message.text
    if cookie not in list_of_cookies:
        await message.answer("Пожалуйста выберите аккаунт используя клавиатуру ниже", reply_markup=types.ReplyKeyboardRemove())
        return
    await DBN.delete_account(cookie)
    await message.answer(f"Готово. Аккаунт {cookie} удалён", reply_markup=types.ReplyKeyboardRemove())
    await Authorization.choose_command_below.set()



def register_handlers_auth(dp: Dispatcher):
    dp.register_message_handler(auth_start, commands="authorization", state="*")
    dp.register_message_handler(auth_chosen, state=Authorization.choose_command_below)
    dp.register_message_handler(new_accound, state=Authorization.add_account)
    dp.register_message_handler(delete_account, state=Authorization.delete_account)
    dp.register_message_handler(get_sms, state=Authorization.wait_code)
