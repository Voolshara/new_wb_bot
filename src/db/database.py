import os
from pydoc import tempfilepager
from xmlrpc.client import Boolean
import sqlalchemy as sa
from contextlib import contextmanager
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func


engine = sa.create_engine(
    'mariadb+pymysql://{}:{}@{}:{}/{}'.format(
        os.getenv('MySQL_NAME'),
        os.getenv('MySQL_PASSWORD'),
        os.getenv('MySQL_HOST'),
        os.getenv('MySQL_PORT'),
        os.getenv('MySQL_DB_NAME'),
    )
)


Session = sessionmaker(bind=engine)
Base = declarative_base()


@contextmanager
def create_session(**kwargs):
    new_session = Session(**kwargs)
    try:
        yield new_session
        new_session.commit()
    except Exception:
        new_session.rollback()
        raise
    finally:
        new_session.close()


class Users(Base):
    __tablename__ = 'Users'
    id = sa.Column(sa.Integer, primary_key=True)
    telegram_id = sa.Column(sa.String(50), unique=True)
    full_name = sa.Column(sa.String(50))
    blocked = sa.Column(sa.Boolean())
    is_output = sa.Column(sa.Boolean())
    phone = sa.Column(sa.String(10))
    now_driver = sa.Column(sa.String(16))


class Cookies(Base):
    __tablename__ = 'Cookies'
    id = sa.Column(sa.Integer, primary_key=True)
    telegram_id = sa.Column(sa.String(50))
    phone = sa.Column(sa.String(10))
    file_name = sa.Column(sa.String(50))
    status = sa.Column(sa.Boolean())


class DB_get:
    def get_all_cookies(self, telegram_id:str) -> list[str]|None:
        with create_session() as session:
            resp = session.query(Cookies).filter(Cookies.telegram_id == telegram_id, Cookies.status).all()
            if resp is not None:
                return [i.phone for i in resp]
            return None

    def get_user_id(self, telegram_id:str) -> str | None:
        with create_session() as session:
            resp = session.query(Users).filter(Users.telegram_id == telegram_id).one_or_none()
            if resp is not None:
                return resp.id
            return None
    
    def get_phone(self, telegram_id:str) -> str | None:
        with create_session() as session:
            resp = session.query(Users).filter(Users.telegram_id == telegram_id).one_or_none()
            if resp is not None:
                return resp.phone
            return None

    def get_driver(self, telegram_id:str) -> str | None:
        with create_session() as session:
            resp = session.query(Users).filter(Users.telegram_id == telegram_id).one_or_none()
            if resp is not None:
                return resp.now_driver
            return None

class DB_new:
    def __init__(self) -> None:
        self.DBG = DB_get()

    async def add_cookie(self, telegram_id:str, phone:str, file_name:str) -> None:
        with create_session() as session:
            session.add(Cookies(
                telegram_id = str(telegram_id),
                phone = phone,
                file_name = file_name,
                status = True
            ))

    async def delete_account(self, phone:str) -> None:
        with create_session() as session:
            session.query(Cookies).filter(Cookies.phone == phone).update({Cookies.status: False})

    async def set_phone(self, telegram_id:str, phone:str) -> bool:
        user_id = self.DBG.get_user_id(telegram_id)
        if user_id is None:
            print("Ошибка Пользователя нет")
            return False
        with create_session() as session:
            session.query(Users).filter(Users.id == user_id).update({Users.phone: phone})
            return True

    async def set_driver(self, telegram_id:str, driver_code:str) -> bool:
        user_id = self.DBG.get_user_id(telegram_id)
        if user_id is None:
            print("Ошибка Пользователя нет")
            return False
        with create_session() as session:
            session.query(Users).filter(Users.id == user_id).update({Users.now_driver: driver_code})
            return True

    async def add_user(self, telegram_id:str, full_name:str) -> None:
        if self.DBG.get_user_id(telegram_id) is None:
            with create_session() as session:
                session.add(Users(
                    telegram_id = str(telegram_id),
                    full_name = full_name,
                    blocked = False,
                    is_output = False,
                    now_driver = "",
            ))

    def create_all_tables(self) -> None:
        Base.metadata.create_all(engine)


# DBN = DB_new()
# DBN.create_all_tables()
