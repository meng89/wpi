import os
import platform
import sys
from wpi import load_module, config_sample, set_sample


bundle_data_folder = '_data'

Z7_FOLDER = '7z'
Z7_EXE = '7z.exe'
Z7_DLL = '7z.dll'


user_config_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'wpi')
user_config_sample_path = os.path.join(user_config_dir, 'config_sample.py')
user_config_path = os.path.join(user_config_dir, 'config.py')


def is_exe():
    if getattr(sys, 'frozen', False) is not False:
        return True
    else:
        return False


def meipass_path():
    return getattr(sys, '_MEIPASS')


def app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    elif __file__:
        return os.path.dirname(__file__)


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


def drivers_dir():
    if is_exe():
        return os.path.realpath(os.path.join(app_path(), 'drivers'))

    raise FileNotFoundError


def copy_config_sample():
    import shutil
    from wpi import set_sample
    set_sample_filename = os.path.splitext(os.path.split(set_sample.__file__)[1])[0] + '.py'
    set_sample_target = os.path.join(app_path(), set_sample_filename)
    if not os.path.exists(set_sample_target):
        try:
            shutil.copy(os.path.join(meipass_path(), set_sample_filename), set_sample_target)
        except OSError:
            pass


bundle_files = (
    path_of_7z(),
    os.path.join(os.path.split(path_of_7z())[0], Z7_DLL),
    config_sample.__file__,
    set_sample.__file__,
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

    if is_exe():
        c.drivers_dir = c.drivers_dir or os.path.realpath(os.path.join(app_path(), 'drivers'))

    return c


ALL_BITS = {'32', '64'}
CUR_BIT = platform.architecture()[0][0:2]
CUR_OS = platform.release().lower()
ALL_OS = {'xp', '7', '10'} | {CUR_OS}
