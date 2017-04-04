import os
import platform
import sys
from wpi import load_module, config_sample


bundle_data_folder = '_data'

Z7_FOLDER = '7z'
Z7_EXE = '7z.exe'
Z7_DLL = '7z.dll'

config_sample_filename = 'config_sample.py'
config_filename = 'config.py'

def_ps_filename = '_.py'

def_drivers_dirname = 'drivers'

user_config_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'wpi')
user_config_sample_path = os.path.join(user_config_dir, 'config_sample.py')
user_config_path = os.path.join(user_config_dir, config_filename)

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


def find_7z_in_reg():
    regkeys = (r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
               r'HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall')

    from wpi.reg import Node

    b32_location = None
    b64_location = None

    for one in regkeys:
        n = Node(one)
        for k, sub in n.items():
            if k == '7-Zip':
                if sub.tips['DisplayName'].endswith('(x64)'):
                    b64_location = sub.tips['InstallLocation']
                else:
                    b32_location = sub.tips['InstallLocation']

    return b32_location, b64_location


def path_of_7z():
    if is_exe():
        return os.path.join(meipass_path(), bundle_data_folder, Z7_EXE)

    else:
        for _7z_path in [os.path.join(one, Z7_EXE) for one in find_7z_in_reg()]:
            if os.path.isfile(_7z_path):
                return _7z_path

    raise FileNotFoundError


def bundle_files():
    from wpi import ps_sample
    return (
        path_of_7z(),
        os.path.join(os.path.split(path_of_7z())[0], Z7_DLL),
        config_sample.__file__,
        ps_sample.__file__,
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

    c.z7_path = c.z7_path or path_of_7z()

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


def ps_sample_filename():
    from wpi import ps_sample
    return os.path.splitext(os.path.split(ps_sample.__file__)[1])[0] + '.py'
