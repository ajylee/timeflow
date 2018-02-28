# This file follows tips from
# https://stackoverflow.com/questions/43918933/pytest-specify-log-level-from-the-cli-command-running-the-tests

import pytest
import logging
import inspect


logging.basicConfig(format='{name:26} - {levelname} - {message}', style='{')


try:
    name_to_level = logging._nameToLevel
except AttributeError:
    # we shouldn't depend on reading a private var
    name_to_level = {'CRITICAL': 50,
                     'DEBUG': 10,
                     'ERROR': 40,
                     'INFO': 20,
                     'NOTSET': 0,
                     'WARN': 30,
                     'WARNING': 30}


def pytest_addoption(parser):
    parser.addoption('--log', action='store', default='WARNING', help='set log level')


@pytest.fixture
def log_level():
    level_name = pytest.config.getoption('log')
    level = name_to_level.get(level_name, 0)
    return level
