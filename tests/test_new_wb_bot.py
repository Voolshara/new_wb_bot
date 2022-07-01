from src import __version__
from src.func.auth import set_phone


def test_version():
    assert __version__ == '0.1.0'


def test_wb_auth():
        phone = "9969498308"
        assert set_phone(phone)
