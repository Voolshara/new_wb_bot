import os
from datetime import datetime
import stat
import sqlalchemy as sa
from contextlib import contextmanager
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.schema import *
from typing import Optional



engine = sa.create_engine(
    'mysql+pymysql://{}:{}@{}:{}/{}'.format(
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
    is_send_auth = sa.Column(sa.Boolean())
    link_for_fiks = sa.Column(sa.String(500))

class Drivers(Base):
    __tablename__ = 'Drivers'
    id = sa.Column(sa.Integer, primary_key=True)
    telegram_id = sa.Column(sa.String(50))
    driver = sa.Column(sa.String(16))
    get_phone_status = sa.Column(sa.Integer)
    # 0 - phone not ready
    # 1 - phone ready
    # 2 - state start in auth (auth_chosen)
    code_send_time = sa.Column(sa.DateTime, server_default=func.now())
    is_active = sa.Column(sa.Boolean())


class Cookies(Base):
    __tablename__ = 'Cookies'
    id = sa.Column(sa.Integer, primary_key=True)
    telegram_id = sa.Column(sa.String(50))
    phone = sa.Column(sa.String(15), unique=True)
    file_name = sa.Column(sa.String(50))
    status = sa.Column(sa.Integer) 
    # (0) - wait sms 
    # (1) - ready to use
    # (-1) - deleted  
    # (-2) - not fully registered


class Place(Base):
    __tablename__ = 'Place'
    id = sa.Column(sa.Integer, primary_key=True)
    telegram_id = sa.Column(sa.String(50))
    phone = sa.Column(sa.String(15))
    url = sa.Column(sa.String(500))
    last_url = sa.Column(sa.String(500))
    place = sa.Column(sa.Integer)
    wait_place = sa.Column(sa.Boolean())
    status = sa.Column(sa.Boolean())


class DB_get:
    def get_cookie_from_url(self, url):
        with create_session() as session:
            resp = session.query(Place).filter(Place.url == url, Place.status == 1).one_or_none()
            if resp is None:
                return None
            phone, place = "+7" + resp.phone, resp.place
            # phone = "+79781248490"
            resp = session.query(Cookies).filter(Cookies.phone == phone, Cookies.status == 1).one_or_none()
            if resp is None:
                return
            return url, place, resp.file_name


    def get_place_to_w8(self, telegram_id:str, link:str) -> Optional[list[str]]:
        with create_session() as session:
            resp = session.query(Place).filter(Place.telegram_id == telegram_id, Place.url == link, Place.wait_place == True).one_or_none()
            if resp is not None:
                return resp.id
            return None

    def get_all_places_with_link(self, telegram_id:str, link:str) -> Optional[list[str]]:
        with create_session() as session:
            resp = session.query(Place).filter(Place.telegram_id == telegram_id, Place.link == link).one_or_none()
            if resp is not None:
                return [i.id for i in resp]
            return None

    def get_fiks_link(self, telegram_id:str) -> None:
        with create_session() as session:
            resp = session.query(Users).filter(Users.telegram_id == telegram_id).one()
            return resp.link_for_fiks

    def get_all_places(self, telegram_id:str) -> Optional[list[str]]:
        with create_session() as session:
            resp = session.query(Place).filter(Place.telegram_id == telegram_id, Place.wait_place == False, Place.status == True).all()
            if resp is not None:
                return [[i.phone, i.url] for i in resp]
            return None

    def get_all_cookies(self, telegram_id:str) -> Optional[list[str]]:
        with create_session() as session:
            resp = session.query(Cookies).filter(Cookies.telegram_id == telegram_id, Cookies.status == 1).all()
            if resp is not None:
                return [i.phone for i in resp]
            return None

    def get_user_id(self, telegram_id:str) -> Optional[str]:
        with create_session() as session:
            resp = session.query(Users).filter(Users.telegram_id == telegram_id).one_or_none()
            if resp is not None:
                return resp.id
            return None

    def get_user_sms_status(self, telegram_id:str) -> bool:
        with create_session() as session:
            resp = session.query(Users).filter(Users.telegram_id == telegram_id).one_or_none()
            return resp.is_send_auth
    
    def get_phone(self, telegram_id:str) -> Optional[str]:
        with create_session() as session:
            resp = session.query(Cookies).filter(Cookies.telegram_id == telegram_id, Cookies.status == 0).one_or_none()
            return resp.phone

    def get_driver(self, telegram_id:str) -> Optional[str]:
        with create_session() as session:
            resp = session.query(Drivers).filter(Drivers.telegram_id == telegram_id, Drivers.is_active == True).one_or_none()
            if resp is not None:
                return resp.driver
            return None

    def is_resend_not_ready(self, telegram_id:str) -> bool:
        with create_session() as session:
            resp = session.query(Drivers).filter(Drivers.telegram_id == telegram_id, Drivers.is_active == True).one_or_none()
            if (datetime.now() - resp.code_send_time).total_seconds() >= 65:
                return False
            return True

    def get_ready_for_sms_status(self, telegram_id:str) -> bool:
        with create_session() as session:
            resp = session.query(Drivers).filter(Drivers.telegram_id == telegram_id, Drivers.is_active == True).one_or_none()
            if resp is None:
                return 0
            return resp.get_phone_status
# ------------------------------------------------------ Authorization ---------------------------------------


class DB_new:
    def __init__(self) -> None:
        self.DBG = DB_get()

    async def delete_some_links(self, telegram_id:str, phone:str) -> bool:
        with create_session() as session:
            req = session.query(Place).filter(Place.telegram_id == telegram_id, Place.phone == phone).all()
            if len(req) == 0:
                return False
            session.query(Place).filter(Place.telegram_id == telegram_id, Place.phone == phone).update({Place.status: False})
            return True

    async def delete_all_links(self, telegram_id:str):
        with create_session() as session:
            session.query(Place).filter(Place.telegram_id == telegram_id).update({Place.status: False})

    async def set_place_link(self, telegram_id:str, link:str):
        with create_session() as session:
            session.query(Place).filter(Place.telegram_id == telegram_id, Place.wait_place == True, Place.status == True).update({Place.url: link})

    async def set_place_position(self, telegram_id:str, position:str):
        with create_session() as session:
            session.query(Place).filter(Place.telegram_id == telegram_id, Place.wait_place == True, Place.status == True).update({Place.place: position, Place.wait_place: False})

    async def set_fiks_link(self, telegram_id:str, link:str) -> None:
        with create_session() as session:
            session.query(Users).filter(Users.telegram_id == telegram_id).update({Users.link_for_fiks: link})

    
    async def new_place_data(self, telegram_id:str, phone:str, url : Optional[str] = None, place : Optional[str] = None, wait_place :Optional[bool] = True):
        if self.DBG.get_all_places_with_link(telegram_id, url) is None:
            place_to_w8 = self.DBG.get_place_to_w8(telegram_id, url)
            with create_session() as session:
                if len(place_to_w8) == 0:
                    session.add(Place(
                        telegram_id = str(telegram_id),
                        phone = phone[2:],
                        url = url,
                        place = place,
                        wait_place = True,
                        status = True
                    ))
                    return
                session.query(Place).filter(Place.id == place_to_w8).update({Place.phone : phone[2:]})

        else:
            session.query(Place).filter(Place.url == url).update({Place.phone : phone[2:], Place.wait_place : True, Place.status: False})


# ------------------------------------------------------ Authorization ---------------------------------------
    async def set_user_send(self, telegram_id:str) -> None:
        with create_session() as session:
            session.query(Users).filter(Users.telegram_id == telegram_id).update({Users.is_send_auth: True})

    async def set_user_send_f(self, telegram_id:str) -> None:
        with create_session() as session:
            session.query(Users).filter(Users.telegram_id == telegram_id, Users.is_send_auth == True).update({Users.is_send_auth: False})

    
    async def delete_account(self, phone:str) -> None:
        with create_session() as session:
            session.query(Cookies).filter(Cookies.phone == phone).update({Cookies.status: -1})

    async def set_status_of_sms(self, telegram_id:str) -> None:
        with create_session() as session:
            session.query(Drivers).filter(Drivers.telegram_id == telegram_id, Drivers.is_active == True).update({
                Drivers.get_phone_status : 1, 
            })

    async def set_status_of_auth_start(self, telegram_id:str) -> None:
        with create_session() as session:
            session.query(Drivers).filter(Drivers.telegram_id == telegram_id, Drivers.is_active == True).update({
                Drivers.get_phone_status : 2, 
            })
    
    async def clean_empty_cookies(self, telegram_id:str) -> None:
        with create_session() as session:
            session.query(Cookies).filter(Cookies.telegram_id == telegram_id, Cookies.status == 0).update({
                Cookies.status: -2, 
                })

    async def clean_empty_drivers(self, telegram_id:str) -> None:
        with create_session() as session:
            session.query(Drivers).filter(Drivers.telegram_id == telegram_id, Drivers.is_active == True).update({
                Drivers.is_active : False, 
                })
    
    async def add_cookie_file(self, telegram_id:str, phone:str, file_name:str) -> None:
        with create_session() as session:
            session.query(Cookies).filter(Cookies.phone == phone).update({
                Cookies.status: 1, 
                Cookies.file_name : file_name
                })


    async def new_cookie(self, telegram_id:str, phone:str) -> None:
        with create_session() as session:
            req = session.query(Cookies).filter(Cookies.phone == phone).one_or_none()
            if req is None:
                session.add(Cookies(
                    telegram_id = telegram_id,
                    phone = phone,
                    file_name = "",
                    status = 0,
                ))
            else:
                session.query(Cookies).filter(Cookies.phone == phone).update({
                    Cookies.telegram_id : telegram_id,
                    Cookies.status : 0,
                    })

    async def set_driver(self, telegram_id:str, driver_code:str) -> None:
        with create_session() as session:
            session.add(Drivers(
            telegram_id = telegram_id,
            driver = driver_code,
            get_phone_status = 0,
            code_send_time = datetime.now(),
            is_active = True
        ))

    async def add_user(self, telegram_id:str, full_name:str) -> None:
        if self.DBG.get_user_id(telegram_id) is None:
            with create_session() as session:
                session.add(Users(
                    telegram_id = str(telegram_id),
                    full_name = full_name,
                    blocked = False,
                    is_output = False,
                    is_send_auth = False,
                    link_for_fiks = ""
            ))

# ------------------------------------------------------ Authorization ---------------------------------------

    def create_all_tables(self) -> None:
        Base.metadata.create_all(engine)


# DBN = DB_new()
# DBN.create_all_tables()
