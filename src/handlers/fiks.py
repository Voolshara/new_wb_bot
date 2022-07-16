from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from src.db.database import DB_new, DB_get
import re

from src.handlers.auth import delete_account
from src.func.behavior_decorators import check_start
from src.func.stavki import place_setup_from_tg

DBG = DB_get()
DBN = DB_new()

# keboards
fiks_keyboard = ["Добавить новую ссылку", "Посмотреть добавленные ссылки", "Удалить ссылку(и)"]

# states
class Fiks(StatesGroup):
    choose_command_below = State()
    choose_one_phone = State()
    w8_link = State()
    w8_position = State()
    delete_link = State()


# start auth state
@check_start
async def fiks_start(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for code in fiks_keyboard:
        keyboard.add(code)
    await message.answer("Выберите нужную команду (см. ниже):", reply_markup=keyboard)
    await Fiks.choose_command_below.set()


@check_start
async def fiks_chosen(message: types.Message, state: FSMContext):
    if message.text not in fiks_keyboard:
        await message.answer("Пожалуйста, воспользуйтесь командой, используя клавиатуру ниже")
        return
    if message.text.lower() == "добавить новую ссылку":
        list_of_cookies = DBG.get_all_cookies(message.from_user.id)
        if len(list_of_cookies) == 0:
            await message.answer("У вас нет ни одного привязанного аккаунта")
            await message.answer("Сначала авторизирйутесь /authorization", reply_markup=types.ReplyKeyboardRemove())
            await Fiks.choose_command_below.set()
        else:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for account in list_of_cookies:
                keyboard.add(account)   
            await message.answer(f"Выберите аккаунт, к которому надо привязать ссылку", reply_markup=keyboard)
            await Fiks.choose_one_phone.set()
        # list_of_cookies = ["9969498308"]
        # keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        # for account in list_of_cookies:
        #     keyboard.add("+7" + account)   
        # await message.answer(f"Выберите аккаунт, к которому надо привязать ссылку", reply_markup=keyboard)
        # await Fiks.choose_one_phone.set()
    elif message.text.lower() == "посмотреть добавленные ссылки":
        all_links = DBG.get_all_places(message.from_user.id)
        if len(all_links) == 0:
            await message.answer("У вас нет аккаунтов")
        else:
            s = "Добавленные аккаунты: "
            for phone, link in all_links:
                s += f"Тел {phone} ({link})\n"
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for code in fiks_keyboard:
                keyboard.add(code)
            await message.answer(s, reply_markup=keyboard)
    elif message.text.lower() == "удалить ссылку(и)":
        all_links = DBG.get_all_places(message.from_user.id)
        if len(all_links) == 0:
            await message.answer("У вас нет аккаунтов")
        else:
            n = 1
            s = "Добавленные аккаунты: "
            for phone, link in all_links:
                s += f"{n})  Тел {phone} [{link}]\n"
                n += 1
            await message.answer(s, reply_markup=types.ReplyKeyboardRemove())
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for phone, link in all_links:
                keyboard.add(f"+7{phone} {n}")
            keyboard.add(f"Удалить все ссылки")
            await message.answer("Выберете сслыку, которую надо удалить", reply_markup=keyboard)
            await Fiks.delete_link.set()


@check_start
async def delete_link(message: types.Message, state: FSMContext):
    delete_link = message.text
    if delete_link == "Удалить все ссылки":
        await DBN.delete_all_links(message.from_user.id)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for code in fiks_keyboard:
            keyboard.add(code)
        await message.answer("Удалены все записи", reply_markup=keyboard)
        await Fiks.choose_command_below.set()
        return
    phone = delete_link[2:13]
    if DBN.delete_some_links(message.from_user.id, phone):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for code in fiks_keyboard:
            keyboard.add(code)
        await message.answer(f"Удалён: {phone}", reply_markup=keyboard)
        await Fiks.choose_command_below.set()
        return
    await message.answer(f"Такого аккаунта не существует", reply_markup=types.ReplyKeyboardRemove())


@check_start
async def phone_chosen(message: types.Message, state: FSMContext):
    phone_number = message.text
    phone_reg = re.compile("^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$")
    if len(phone_reg.findall(phone_number)) == 0:
        list_of_cookies = DBG.get_all_cookies(message.from_user.id)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for account in list_of_cookies:
            keyboard.add(account)
        await message.answer("Неверный номер телефона\nПопоробуйте ещё раз", reply_markup=keyboard)
        return 
    await DBN.new_place_data(message.from_user.id, phone_number)
    await message.answer(
        f"Укажите ссылку, на которой находится ваш продукт"
        f"Пример: "
        f"https://seller.wildberries.ru/cmp/campaigns/list/active/edit/carousel-auction/1664683", reply_markup=types.ReplyKeyboardRemove()
    )
    await Fiks.w8_link.set()


@check_start
async def set_link(message: types.Message, state: FSMContext):
    link_re = re.compile(r"https://seller.wildberries.ru/cmp/campaigns/list/active/edit/.*")
    link = message.text
    if len(link_re.findall(link)) == 0:
        await message.answer("Неверная сслыка, попробуйте ещё раз", reply_markup=types.ReplyKeyboardRemove())
        return
    await DBN.set_place_link(message.from_user.id, link)
    await DBN.set_fiks_link(message.from_user.id, link)
    await message.answer(
        f"Укажите позицию, на которой должен встать продукт"
        f"Введите просто число"
    )
    await Fiks.w8_position.set()
    

@check_start
async def set_position(message: types.Message, state: FSMContext):
    flag = False
    try:
        pos = int(message.text) 
    except:
        flag = True
    if flag:
        await message.answer("Введённая позиция не является чмслом, попробуйте ещё раз", reply_markup=types.ReplyKeyboardRemove())
        return
    await DBN.set_place_position(message.from_user.id, pos)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for code in fiks_keyboard:
        keyboard.add(code)
    await message.answer(f"Готово", reply_markup=keyboard)
    await place_setup_from_tg(DBG.get_fiks_link(message.from_user.id), message.from_user.id)
    await Fiks.choose_command_below.set()

    

def register_handlers_fiks(dp: Dispatcher):
    dp.register_message_handler(fiks_chosen, state=Fiks.choose_command_below)
    dp.register_message_handler(phone_chosen, state=Fiks.choose_one_phone)
    dp.register_message_handler(set_link, state=Fiks.w8_link)
    dp.register_message_handler(set_position, state=Fiks.w8_position)
    dp.register_message_handler(delete_link, state=Fiks.delete_link)