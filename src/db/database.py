import os
import sqlalchemy as sa
from contextlib import contextmanager
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from typing import Optional


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


class Place(Base):
    __tablename__ = 'Place'
    id = sa.Column(sa.Integer, primary_key=True)
    telegram_id = sa.Column(sa.String(50))
    phone = sa.Column(sa.String(10))
    url = sa.Column(sa.String(1000))
    place = sa.Column(sa.Integer)
    wait_place = sa.Column(sa.Boolean())
    status = sa.Column(sa.Boolean())


class DB_get:
    def get_all_places_to_w8(self, telegram_id:str) -> Optional[list[str]]:
        with create_session() as session:
            resp = session.query(Place).filter(Place.telegram_id == telegram_id, Place.wait_place == True).all()
            if resp is not None:
                return [i.id for i in resp]
            return None

    def get_all_places(self, telegram_id:str) -> Optional[list[str]]:
        with create_session() as session:
            resp = session.query(Place).filter(Place.telegram_id == telegram_id, Place.wait_place == False, Place.status == True).all()
            if resp is not None:
                return [[i.phone, i.url] for i in resp]
            return None

    def get_all_cookies(self, telegram_id:str) -> Optional[list[str]]:
        with create_session() as session:
            resp = session.query(Cookies).filter(Cookies.telegram_id == telegram_id, Cookies.status).all()
            if resp is not None:
                return [i.phone for i in resp]
            return None

    def get_user_id(self, telegram_id:str) -> Optional[str]:
        with create_session() as session:
            resp = session.query(Users).filter(Users.telegram_id == telegram_id).one_or_none()
            if resp is not None:
                return resp.id
            return None
    
    def get_phone(self, telegram_id:str) -> Optional[str]:
        with create_session() as session:
            resp = session.query(Users).filter(Users.telegram_id == telegram_id).one_or_none()
            if resp is not None:
                return resp.phone
            return None

    def get_driver(self, telegram_id:str) -> Optional[str]:
        with create_session() as session:
            resp = session.query(Users).filter(Users.telegram_id == telegram_id).one_or_none()
            if resp is not None:
                return resp.now_driver
            return None

class DB_new:
    def __init__(self) -> None:
        self.DBG = DB_get()

    async def delete_some_links(self, telegram_id:str, phone:str):
        with create_session() as session:
            session.query(Place).filter(Place.telegram_id == telegram_id, Place.phone == phone).update({Place.status: False})

    async def delete_all_links(self, telegram_id:str):
        with create_session() as session:
            session.query(Place).filter(Place.telegram_id == telegram_id).update({Place.status: False})

    async def set_place_link(self, telegram_id:str, link:str):
        with create_session() as session:
            session.query(Place).filter(Place.telegram_id == telegram_id, Place.wait_place == True, Place.status == True).update({Place.url: link})

    async def set_place_position(self, telegram_id:str, position:str):
        with create_session() as session:
            session.query(Place).filter(Place.telegram_id == telegram_id, Place.wait_place == True, Place.status == True).update({Place.place: position, Place.wait_place: False})

    async def new_place_data(self, telegram_id:str, phone:str, url : Optional[str] = None, place : Optional[str] = None, wait_place :Optional[bool] = True):
        place_ids_to_w8 = self.DBG.get_all_places_to_w8(telegram_id)
        # print(place_ids_to_w8)
        with create_session() as session:
            if len(place_ids_to_w8) == 0:
                session.add(Place(
                    telegram_id = str(telegram_id),
                    phone = phone[2:],
                    url = url,
                    place = place,
                    wait_place = True,
                    status = True
                ))
                return
            session.query(Place).filter(Place.id == place_ids_to_w8[0]).update({Place.phone : phone[2:]})

     # происходит наложение телефонов, если сбросить 1 регистрацию и продолжить с другой, то линк запишется на другой телефон

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
