import logging
import os
import platform
import sys

from wpi import load_module

bundle_data_folder = '_data'

Z7_EXE = '7z.exe'
Z7_DLL = '7z.dll'


def get_ps__filename():
    from wpi.user_sample import ps_

    return os.path.splitext(os.path.split(ps_.__file__)[1])[0] + '.py'


def get_config__filename():
    from wpi.user_sample import config_

    return os.path.splitext(os.path.split(config_.__file__)[1])[0] + '.py'


def_config_filename = 'config.py'

def_ps_filename = '_.py'

def_drivers_dirname = 'drivers'

user_wpi_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'wpi')
user_config_sample_path = os.path.join(user_wpi_dir, 'config_.py')
user_config_path = os.path.join(user_wpi_dir, def_config_filename)

user_logs_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'wpi_logs')


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
    # regkeys = (r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
    #           r'HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall')

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


def get_7z_dir():
    if is_exe():
        z7_dir = os.path.join(meipass_path(), bundle_data_folder)
        if os.path.isfile(z7_dir):
            return z7_dir

    z7_32_dir, z7_64_dir = _find_7z_in_reg()

    if z7_32_dir and os.path.isfile(os.path.join(z7_32_dir, Z7_EXE)):
        return z7_32_dir

    elif z7_64_dir and os.path.isfile(os.path.join(z7_64_dir, Z7_EXE)):
        return z7_64_dir

    else:
        logging.warning('7-Zip cannot be found.')
        return None


def get_7z_path():
    return os.path.join(get_7z_dir(), Z7_EXE)


def bundle_files():
    from wpi.user_sample import config_, ps_
    return (
        os.path.join(get_7z_dir(), Z7_EXE),
        os.path.join(get_7z_dir(), Z7_DLL),
        config_.__file__,
        ps_.__file__,
    )


class Config:
    __slots__ = ['z7_path', 'drivers_dir', 'archive_exts']

    def __init__(self, obj=None):
        for k in self.__slots__:
            setattr(self, k, getattr(obj, k, None))


def load_config(path):
    return Config(load_module(path))


def supply_config(config=None):
    c = Config(config)

    c.z7_path = c.z7_path or get_7z_path()

    c.archive_exts = c.archive_exts or ['.zip', '.7z', '.rar', '.exe']

    return c


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
