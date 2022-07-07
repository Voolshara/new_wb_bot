from src import __version__
from src.func.drivers_server import test_driver_connection


def test_version():
    assert __version__ == '0.1.0'


def test_driver():
        assert test_driver_connection() is True
