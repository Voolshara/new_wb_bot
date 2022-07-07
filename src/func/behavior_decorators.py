from src.db.database import DB_get, DB_new


DBG = DB_get()


def check_start(handler):
    async def accept_to_continue(message, state=None):
        if DBG.get_user_id(message.from_user.id) is not None:
            if state is None:
                return await handler(message)
            return await handler(message, state)
        await message.answer("Перед началом работы зарегистрируйтесь\n/start")
    return accept_to_continue
        