import logging
import os
import platform
import sys

BUNDLE_DATA_FOLDER = '_data'

SZIP_EXE = '7z.exe'
SZIP_DLL = '7z.dll'


def is_exe():
    if getattr(sys, 'frozen', False) is not False:
        return True
    else:
        return False


def meipass_path():
    return getattr(sys, '_MEIPASS')


def exe_path():
    if is_exe():
        return sys.executable
    elif __file__:
        return __file__


def exe_dir():
    return os.path.dirname(exe_path())


def _find_7z_in_reg():
    from wpi.reg import Node

    b32_location = None
    b64_location = None

    n = Node(r'HKEY_LOCAL_MACHINE\SOFTWARE\7-Zip')
    for k, v in n.tips.items():
        if k == 'Path32':
            b32_location = v
        elif k == 'Path64':
            b64_location = v

    return b32_location, b64_location


def get_szip_dir():
    if is_exe():
        z7_dir = os.path.join(meipass_path(), BUNDLE_DATA_FOLDER, SZIP_EXE)
        if os.path.isfile(z7_dir):
            return z7_dir

    szip_32_dir, szip_64_dir = _find_7z_in_reg()

    if szip_32_dir and os.path.isfile(os.path.join(szip_32_dir, SZIP_EXE)):
        return szip_32_dir

    elif szip_64_dir and os.path.isfile(os.path.join(szip_64_dir, SZIP_EXE)):
        return szip_64_dir

    else:
        logging.warning('7-Zip cannot be found.')
        return None


def get_szip_path():
    return os.path.join(get_szip_dir(), SZIP_EXE)


class Config:
    __slots__ = ['z7_path', 'drivers_dir', 'archive_exts']

    def __init__(self, obj=None):
        for k in self.__slots__:
            setattr(self, k, getattr(obj, k, None))


def load_config(path):
    from wpi import load_module

    return Config(load_module(path))


def supply_config(config=None):
    c = Config(config)

    c.z7_path = c.z7_path or get_szip_path()

    c.archive_exts = c.archive_exts or ['.zip', '.7z', '.rar', '.exe']

    return c


ARCHIVE_EXTS = ['.zip', '.7z', '.rar', '.exe']


CUR_OS = platform.release().lower()
ALL_OS = {'xp', '7', '10'} | {CUR_OS}


B32 = '32'
B64 = '64'
ALL_BITS = {'32', '64'}


if platform.machine().endswith('64'):
    CUR_BIT = '64'
elif platform.machine().endswith('86'):
    CUR_BIT = '32'
else:
    raise Exception


PYTHON_BIT = platform.architecture()[0][0:2]
