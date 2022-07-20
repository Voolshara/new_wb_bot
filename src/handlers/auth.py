from cmath import log
from inspect import trace
import logging
from aiogram import Dispatcher, types, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import re, requests
from src.db.database import DB_new, DB_get
from src.func.behavior_decorators import check_start
import multiprocessing, asyncio
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

try:
    multiprocessing.set_start_method('spawn')
except:
    pass


# database
DBN = DB_new()
DBG = DB_get()


# clean decorator
def clean_empty_obj(handler):
    async def clean(message, state=None):

        if DBG.get_user_id(message.from_user.id) is not None:
            await DBN.clean_empty_cookies(message.from_user.id)
            await DBN.clean_empty_drivers(message.from_user.id)
            await DBN.set_user_send_f(message.from_user.id)
            # TODO :  realise close drivers on auth server
            return await handler(message, state)
        await message.answer("Перед началом работы зарегистрируйтесь\n/start")
    return clean
        


# start auth state
@clean_empty_obj
async def auth_start(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for code in first_keyboard:
        keyboard.add(code)
    await message.answer("Выберите нужную команду (см. ниже):", reply_markup=keyboard)
    await Authorization.choose_command_below.set()


# chosse key in keyboard
@check_start
async def auth_chosen(message: types.Message, state: FSMContext):
    if message.text not in first_keyboard:
        await message.answer("Пожалуйста, воспользуйтесь командой, используя клавиатуру ниже")
        return
    if message.text.lower() == "добавить аккаунт":
        #if check_queue:
        if True:
            await message.answer("Отлично, давайте добавим новый аккаунт")
            await message.answer("Введите номер телефона без кода страны \nПример: +79781248490", reply_markup=types.ReplyKeyboardRemove())
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

class Send_phone:
    def __init__(self):
        pass
    async def send_reply(self, data, phone_number, user_id): 
        bot = Bot(token="5585095304:AAFYsfIoTD29QSln36yfVpwKVhodzIRlaKs")
        if data["status"]:
            await DBN.set_driver(user_id, data["name_of_driver"])
            await DBN.new_cookie(user_id, phone_number)
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for code in repeat_sms_keyboard:
                keyboard.add(code)
            await bot.send_message(user_id, "Введите код из смс для входа в учётную запись", reply_markup=keyboard)
            # await self.Authorization_class.wait_code.set()
            await DBN.set_status_of_sms(user_id)
            return 
        else:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for code in first_keyboard:
                keyboard.add(code)
            await bot.send_message(user_id, f"Ошибка со стороны WB \nСообщение от WB: {data['mes']}\nПопробуйте сначала /authorization", reply_markup=keyboard)
            # await Authorization.choose_command_below.set()
            await DBN.set_driver(user_id, "")
            await DBN.set_status_of_auth_start(user_id)
            return

    async def new_account_procces(self, phone_number, user_id):
        bot = Bot(token="5585095304:AAFYsfIoTD29QSln36yfVpwKVhodzIRlaKs")
        try:
            data = requests.post("http://localhost:4600/new_user", json={
                "status" : "phone",
                "mes" : phone_number[2:]
            }).json()
            await self.send_reply(data, phone_number, user_id)
        except:
            await bot.send_message(user_id, f"Ошибка на стороне WB\nПопробуйте чуть позже", reply_markup=types.ReplyKeyboardRemove())
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for code in first_keyboard:
                keyboard.add(code)
            await bot.send_message(user_id, "Начните сначала", reply_markup=keyboard)
            await DBN.set_driver(user_id, "")
            await DBN.set_status_of_auth_start(user_id)
    
    async def check_message_send(self, user_id):
        bot = Bot(token="5585095304:AAFYsfIoTD29QSln36yfVpwKVhodzIRlaKs")
        await bot.send_message(user_id, "QU")
        
         
    def process(self, phone_number, user_id):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task = loop.create_task(self.new_account_procces(phone_number, user_id))
        loop.run_until_complete(task)
        # try:
        #     asyncio.run((user_id, state))
        #     # asyncio.run(self.new_account_procces(phone_number, user_id))
        # except RuntimeError as e:
        #     if e != "Event loop is closed":
        #         print(e)


# add new account
@check_start
async def new_account(message: types.Message, state: FSMContext):
    if DBG.get_ready_for_sms_status(message.from_user.id) == 1:
        await get_sms(message, state)
    elif DBG.get_ready_for_sms_status(message.from_user.id) == 2:
        await auth_chosen(message, state)
    else:
        if not DBG.get_user_sms_status(message.from_user.id):
            await DBN.set_user_send(message.from_user.id)
            phone_number = message.text
            # check line in DB
            # phone_reg = re.compile()
            if re.match(r"[+]7[0-9]{10}$", phone_number) is None:
                await message.answer("Неверный номер телефона (см Пример) \nПопоробуйте ещё раз", reply_markup=types.ReplyKeyboardRemove())
                return 
            await message.answer("Телефон принят, подождите немного", reply_markup=types.ReplyKeyboardRemove())
            p = multiprocessing.Process(target=Send_phone().process, args=(phone_number, message.from_user.id))
            p.start() 
        else:
            await message.answer("Ваш телефон уже в обработке, пожалуйста подождите", reply_markup=types.ReplyKeyboardRemove())


# get code from sms
@check_start
async def get_sms(message: types.Message, state: FSMContext):
    code = message.text
    
    if code == "Отправить код заново":
        if DBG.is_resend_not_ready(message.from_user.id):
            await message.answer("Ещё нет возможности отправить код заново \nНужно подождать около минуты")
            return

        try:
            data = requests.post("http://localhost:4600/new_user", json={
                "status" : "repeat_sms",
                "driver_code" : DBG.get_driver(message.from_user.id),
            }).json()
        except Exception as e:
            logging.warning(str(e))
            await message.answer(f"Ошибка на стороне WB\nПопробуйте чуть позже", reply_markup=types.ReplyKeyboardRemove())
            await DBN.clean_empty_cookies(message.from_user.id) # clean not used cookie
            await DBN.clean_empty_drivers(message.from_user.id) # clean not used driver
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for code in first_keyboard:
                keyboard.add(code)
            await message.answer("Начните сначала", reply_markup=keyboard)
            await Authorization.choose_command_below.set()
            return


        if data["status"]:
            await message.answer("Код отправлен")
            return
        await message.answer("Ещё нет возможности отправить код заново \nНужно подождать около минуты")
        return

    code_reg = re.compile("\d{6}")
    if len(code_reg.findall(code)) == 0 or len(code) != 6:
        await message.answer("Неверный код из смс\nВведите ещё раз")
        return
    await message.answer("Код принят, подождите немного", reply_markup=types.ReplyKeyboardRemove())

    driver = DBG.get_driver(message.from_user.id)
    phone = DBG.get_phone(message.from_user.id)
    
    try:
        data = requests.post("http://localhost:4600/new_user", json={
            "status" : "sms",
            "driver_code" : driver,
            "phone" : phone,
            "sms" : code,
        }).json()

    except exception as e:
        logging.wa
        await message.answer(f"Ошибка со стороны WB\nПопробуйте чуть позже", reply_markup=types.ReplyKeyboardRemove())
        await DBN.clean_empty_cookies(message.from_user.id) # clean not used cookie
        await DBN.clean_empty_drivers(message.from_user.id) # clean not used driver
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for code in first_keyboard:
            keyboard.add(code)
        await Authorization.choose_command_below.set()
        return 

    if data["status"]:
        await DBN.add_cookie_file(message.from_user.id, phone, f"cookie{phone}")
        await message.answer("Готово, аккаунт добавлен", reply_markup=types.ReplyKeyboardRemove())
        await Authorization.choose_command_below.set()
    else:
        if data["mes"] == "Неверный СМС код" or data["mes"] == "Неверные данные доступа":
            await message.answer(f"Ошибка\nСообщение от WB: {data['mes']}", reply_markup=types.ReplyKeyboardRemove())
            await message.answer(f"Проверьте смс код и отправьте его снова", reply_markup=types.ReplyKeyboardRemove())
            return
        await message.answer(f"Ошибка\nСообщение от WB: {data['mes']}", reply_markup=types.ReplyKeyboardRemove())
        await DBN.clean_empty_cookies(message.from_user.id) # clean not used cookie
        await DBN.clean_empty_drivers(message.from_user.id) # clean not used driver
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for code in first_keyboard:
            keyboard.add(code)
        await message.answer("Начните сначала", reply_markup=keyboard)
        await Authorization.choose_command_below.set()


@check_start
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
    dp.register_message_handler(auth_chosen, state=Authorization.choose_command_below)
    dp.register_message_handler(new_account, state=Authorization.add_account)
    dp.register_message_handler(delete_account, state=Authorization.delete_account)
    dp.register_message_handler(get_sms, state=Authorization.wait_code)
