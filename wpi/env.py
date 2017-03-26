import os
import sys
import platform
import shutil

from wpi import load_module, config_sample, set_sample


bundle_data_folder = '_data'

archive_exts = ['.zip', '.7z', '.rar', '.exe']

Z7_folder = '7z'
Z7_exe_filename = '7z.exe'
Z7_dll_filename = '7z.dll'


def is_exe():
    if getattr(sys, 'frozen', False) is not False:
        return True
    else:
        return False


def meipass_path():
    return getattr(sys, '_MEIPASS')


def load_config():
    if is_exe():
        config_sample_path = os.path.join(meipass_path(), bundle_data_folder, 'config_sample.py')
    else:
        config_sample_path = config_sample.__file__

    config_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'wpi')
    os.makedirs(config_dir, exist_ok=True)

    user_config_sample_path = os.path.join(config_dir, 'config_sample.py')
    user_config_path = os.path.join(config_dir, 'config.py')

    if not os.path.exists(user_config_sample_path) or \
            open(config_sample_path, 'rb').read() != open(user_config_sample_path, 'rb').read():
        shutil.copyfile(config_sample_path, user_config_sample_path)

    if not os.path.exists(user_config_path):
        shutil.copyfile(user_config_sample_path, user_config_path)
        print('"config.py" not found, copied. you may want to edit {} and rerun this again'.format(user_config_path))

    return load_module(user_config_path)


config = load_config()
_config_z7_dir = getattr(config, 'z7_dir', None)
_config_drivers_dir = getattr(config, 'dirvers_dir', None)


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
    if platform.system() == 'Windows':

        if _config_z7_dir is not None:
            return _config_drivers_dir

        elif is_exe():
            return os.path.join(meipass_path(), bundle_data_folder, Z7_exe_filename)

        else:
            for _7z_path in [os.path.join(one,  Z7_exe_filename) for one in find_7z_in_reg()]:
                if os.path.isfile(_7z_path):
                    return _7z_path

        raise FileNotFoundError

    else:
        return '7z'


def drivers_dir():
    if _config_drivers_dir is not None:
        return _config_drivers_dir

    elif is_exe():
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
    os.path.join(os.path.split(path_of_7z())[0], Z7_dll_filename),
    config_sample.__file__,
    set_sample.__file__,
)
