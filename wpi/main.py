import ctypes
import sys
import os
import platform

import chardet

from wpi import load_module, archivelib, ALL_BITS, ALL_OS, MY_BIT, MY_OS, version


def app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    elif __file__:
        return os.path.dirname(__file__)


def meipass_path():
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = getattr(sys, '_MEIPASS')
    except AttributeError:
        base_path = os.path.abspath(".")

    return base_path


def drivers_dir():
    if getattr(sys, 'frozen', False):
        return os.path.realpath(os.path.join(app_path(), 'drivers'))

    else:
        for _ in (r'Z:\printer_drivers', ):
            if os.path.exists(_) and os.path.isdir(_):
                return _
        raise FileNotFoundError


archive_exts = ['.zip', '.7z', '.rar', '.exe']


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


Z7_folder = '7z'
Z7_exe_filename = '7z.exe'
Z7_dll_filename = '7z.dll'


def path_of_7z():
    if platform.system() == 'Windows':
        try:
            _7z_meipass = os.path.join(getattr(sys, '_MEIPASS'), Z7_folder, Z7_exe_filename)
            if os.path.isfile(_7z_meipass):
                return _7z_meipass

        except AttributeError:
            for _7z_path in [os.path.join(one, Z7_exe_filename) for one in find_7z_in_reg()]:
                if os.path.isfile(_7z_path):
                    return _7z_path
        else:
            raise FileNotFoundError
    else:
        return '7z'


def split_all(path):
    names = []
    while True:
        path, name = os.path.split(path)

        if name != '':
            names.append(name)
        else:
            if path != '':
                names.append(path)
            break

    names.reverse()
    return names


def check_dirs_names(names: set, must_have: set, must_have_no: set, case_sensitive=False):
    if case_sensitive:
        if not names & must_have_no:
            if names >= must_have:
                return True
    else:
        if not (set([_.lower() for _ in names]) & set([_.lower() for _ in must_have_no])):
            if set([_.lower() for _ in names]) >= set([_.lower() for _ in must_have]):
                return True

    return False


def get_all_files(d):
    all_files = []

    for root, dirs, files in os.walk(d):
        for file in files:
            all_files.append(os.path.join(root, file))

    return all_files


def is_match(inf_bytes, driver):
    import wpi.inf

    inf_data = wpi.inf.loads.loads(inf_bytes.decode(chardet.detect(inf_bytes)['encoding']))
    models = wpi.inf.clean.get_models(inf_data)

    for model, namek_files_hids in models.items():
        if driver in namek_files_hids.keys():
            return True

    return False


def match_infs(inf_files, driver):
    legal_files = []

    for file in inf_files:
        if is_match(open(file, 'rb').read(), driver):
            legal_files.append(file)

    return legal_files


def get_legal_archive_infs_list(best_archives, driver):
    legal_archives = []
    for archive in best_archives:

        legal_infs = []
        for name in archivelib.list_names(archive, path_of_7z()):
            if os.path.splitext(name)[1].lower() == '.inf':
                inf_bytes = archivelib.read(archive, name, path_of_7z())
                if is_match(inf_bytes, driver):
                    legal_infs.append(name)

            if legal_infs:
                legal_archives.append((archive, legal_infs))

    return legal_archives


def get_legal_infs_list(archive, driver):
    legal_infs = []
    for name in archivelib.list_names(archive, path_of_7z()):
        if os.path.splitext(name)[1].lower() == '.inf':
            inf_bytes = archivelib.read(archive, name, path_of_7z())
            if is_match(inf_bytes, driver):
                legal_infs.append(name)
    return legal_infs


def filter_by_exts(files, exts, case_sensitive=False):
    new_files = []
    if case_sensitive:
        for file in files:
            if os.path.splitext(file)[1] in exts:
                new_files.append(file)
    else:
        for file in files:
            if os.path.splitext(file)[1].lower() in [ext.lower() for ext in exts]:
                new_files.append(file)
    return new_files


def filter_by_isarchive(files):
    files = [file for file in files if archivelib.is_can_handle(file, path_of_7z())]
    return files


def filter_by_dirs(files, must_have, must_have_no):
    new_files = []

    delete_root = drivers_dir()

    for path in files:
        if not path.startswith(delete_root):
            raise Exception

        _part_path = path[len(delete_root):]
        part_path = os.path.split(_part_path)[0]

        if check_dirs_names(set(split_all(part_path)), must_have=must_have, must_have_no=must_have_no):
            new_files.append(path)

    return new_files


def _get_archive_infs_list(driver, must_have):

    archives = filter_by_isarchive(
                filter_by_dirs(
                    filter_by_exts(get_all_files(drivers_dir()), archive_exts),
                    must_have,
                    (ALL_BITS | ALL_OS) - must_have
                )
            )

    legal_archive_infs_list = []

    for archive in archives:
        legal_infs = get_legal_infs_list(archive, driver)
        if legal_infs:
            legal_archive_infs_list.append([archive, legal_infs])

    return legal_archive_infs_list


def get_best_archive_infs_list(driver):
    must_have = {MY_BIT, MY_OS}
    return _get_archive_infs_list(driver, must_have)


def get_compatible_archive_infs_list(driver):
    must_have = {MY_BIT}
    return _get_archive_infs_list(driver, must_have)


def _get_infs_list(driver, must_have):

    infs = filter_by_dirs(
               filter_by_exts(get_all_files(drivers_dir()), ['.inf']),
               must_have,
               (ALL_BITS | ALL_OS) - must_have
    )

    legal_infs = []
    for inf in infs:
        if is_match(open(inf, 'rb').read(), driver):
            legal_infs.append(inf)

    return legal_infs


def get_best_infs_list(driver):
    must_have = {MY_BIT, MY_OS}
    return _get_infs_list(driver, must_have)


def get_compatible_infs_list(driver):
    must_have = {MY_BIT}
    return _get_infs_list(driver, must_have)


class PortInstallError(Exception):
    pass


class PortInstallAbort(PortInstallError):
    pass


def install_port(des_port, del_printer_if_necessary=True):
    print('  installing port: ', des_port.name, 'type:', type(des_port))
    from wpi.port import Ports, TCPIPPort, LocalPort

    from wpi.des import RAWPort, LPRPort, SMBPort

    from wpi.printer import Printers

    sysports = Ports()

    if des_port.name is None:
        raise Exception

    def install_it():
        if isinstance(des_port, (RAWPort, LPRPort)):
            sysports[des_port.name] = des_port

        elif isinstance(des_port, SMBPort):
            sysports[des_port.name] = des_port

        sysports.save()

    if des_port.name in sysports.keys():
        print('    port ' + repr(des_port.name) + ' exists')
        if isinstance(des_port, SMBPort) and isinstance(sysports[des_port.name], LocalPort):
            pass

        elif isinstance(des_port, (RAWPort, LPRPort)) and isinstance(sysports[des_port.name], TCPIPPort):
            print('      update port')
            sysports[des_port.name].update(des_port)
            sysports.save()

        else:
            print('      types are not same')
            if del_printer_if_necessary:
                print('        ')
                sysprinters = Printers()
                sysprinters_to_del = []

                for name, sysprinter in sysprinters.items():
                    if sysprinter.port.lower() == des_port.name:
                        sysprinters_to_del.append(name)

                for name in sysprinters_to_del:
                    print(name, ' to del')
                    del sysprinters[name]
                    sysprinters.save()

                del sysports[des_port.name]

                install_it()

            else:
                print('        abort')
                raise PortInstallAbort

    else:
        install_it()


def install_driver(des_driver):
    import tempfile

    from wpi.driver import Drivers

    # archive=None, inf_in_archive=None, inf_path=None
    inf_path = None

    tempdir = None

    if des_driver.archive:
        iia = des_driver.inf_in_archive
        if iia is None:
            infs = get_legal_infs_list(des_driver.archive, des_driver.name)
            if infs:
                tempdir = tempfile.mkdtemp()
                archivelib.extract_all(des_driver.archive, tempdir, path_of_7z())
                inf_path = os.path.join(tempdir, infs[0])
        else:
            tempdir = tempfile.mkdtemp()
            archivelib.extract_all(des_driver.archive, tempdir, path_of_7z())
            inf_path = os.path.join(tempdir, iia)

    elif des_driver.inf_path:
        inf_path = des_driver.inf_path

    else:
        best_archive_infs = get_best_archive_infs_list(driver=des_driver.name)
        if best_archive_infs:
            tempdir = tempfile.mkdtemp()
            archivelib.extract_all(best_archive_infs[0][0], tempdir, path_of_7z())
            inf_path = os.path.join(tempdir, best_archive_infs[0][1][0])
        else:
            best_infs = get_best_infs_list(des_driver.name)
            if best_infs:
                pass
            else:
                compatible_archive_infs = get_compatible_archive_infs_list(des_driver.name)
                if compatible_archive_infs:
                    tempdir = tempfile.mkdtemp()
                    archivelib.extract_all(compatible_archive_infs[0][0], tempdir, path_of_7z())
                    inf_path = os.path.join(tempdir, compatible_archive_infs[0][1][0])
                else:
                    compatible_infs = get_compatible_infs_list(des_driver.name)
                    if compatible_infs:
                        pass

    sysdrivers = Drivers()
    print(inf_path, des_driver.name)
    sysdrivers.add_by_inf(inf_path, des_driver.name)

    if tempdir is not None:
        try:
            os.removedirs(tempdir)
        except OSError:
            pass


def install(module):
    from wpi.printer import Printers

    for p in module.printers:

        try:
            print('try install driver')
            install_driver(p.driver)
            print('try install port')
            install_port(p.port)

        except PortInstallAbort:
            print('skip install printer ' + repr(p.name))
            continue

        else:
            print('try install printer')
            sysprinters = Printers()
            print('here1')
            if p.name not in sysprinters.keys():
                print('here2')
                printer = sysprinters.make_new(p.name)
                printer.driver_name = p.driver.name
                printer.port_name = p.port.name

                sysprinters.save()


def print_head():
    print(
        '###################################################\n'
        '#                                                 #\n'
        '#            Windows Printer Installer            #\n'
        '#                                                 #\n'
        '# Version: {}'.format(version.__version__) + ' ' * (51 - 11 - len(version.__version__) - 1) + '#\n'
        '# Author: Chen Meng                               #\n'
        '# HomePage: https://github.com/meng89/wpi         #\n'
        '###################################################'
    )


def main():
    import tempfile

    os.chdir(tempfile.gettempdir())
    print_head()
    if getattr(sys, 'frozen', False) is not False:
        make_driver_dir()
        copy_set_sample()

    if not ctypes.windll.shell32.IsUserAnAdmin():
        print('Not Administrator!')
        exit()
    try:
        sysinput = sys.argv[1]
    except Exception:
        sysinput = None

    while True:
        print('\nPlease input a set of printers, q to quit')
        print('>', end='')
        if sysinput is not None:
            user_input = sysinput
            print(sysinput)
            sysinput = None
        else:
            user_input = None

        if user_input is None:
            user_input = input()

        if user_input.strip().lower() in ('q', 'quit', 'e', 'exit'):
            break

        elif user_input.strip().lower().endswith('.py'):
            profile = load_module(user_input.strip())
            install(profile)


def make_driver_dir():
    from wpi import ALL_BITS, ALL_OS
    for bit in ALL_BITS:
        for os_ in ALL_OS:
            try:
                os.makedirs(os.path.realpath(os.path.join(app_path(), 'drivers', bit, os_)))
            except Exception:
                pass


def copy_set_sample():
    import shutil
    from wpi import set_sample
    set_sample_filename = os.path.splitext(os.path.split(set_sample.__file__)[1])[0] + '.py'
    set_sample_target = os.path.join(app_path(), set_sample_filename)
    if not os.path.exists(set_sample_target):
        try:
            shutil.copy(os.path.join(meipass_path(), set_sample_filename), set_sample_target)
        except Exception:
            pass


if __name__ == '__main__':
    main()
