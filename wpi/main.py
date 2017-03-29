import ctypes
import os
import sys

import shutil

import chardet

from wpi import load_module, archivelib, version

import wpi.inf

from wpi.env import is_exe, app_path, meipass_path, bundle_data_folder, ALL_BITS, CUR_BIT, CUR_OS, ALL_OS

supplied_config = None


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

    inf_data = wpi.inf.loads.loads(inf_bytes.decode(chardet.detect(inf_bytes)['encoding']))
    models = wpi.inf.utils.get_models(inf_data)

    for model, namek_files_hids in models.items():
        if CUR_BIT == '32' and model[1].lower() not in (None, 'ntx86'):
            continue
        elif CUR_BIT == '64' and model[1].lower() != 'ntamd64':
            continue

        if driver in namek_files_hids.keys():
            return True

    return False


def match_infs(inf_files, driver):
    legal_files = []

    for file in inf_files:
        if is_match(open(file, 'rb').read(), driver):
            legal_files.append(file)

    return legal_files


def get_legal_archive_infs_list(best_archives, driver, z7_path):
    legal_archives = []
    for archive in best_archives:

        legal_infs = []
        for name in archivelib.list_names(archive, z7_path):
            if os.path.splitext(name)[1].lower() == '.inf':
                inf_bytes = archivelib.read(archive, name, z7_path)
                if is_match(inf_bytes, driver):
                    legal_infs.append(name)

            if legal_infs:
                legal_archives.append((archive, legal_infs))

    return legal_archives


def get_legal_infs_list(archive, driver, z7_path):
    legal_infs = []
    for name in archivelib.list_names(archive, z7_path):
        if os.path.splitext(name)[1].lower() == '.inf':
            inf_bytes = archivelib.read(archive, name, z7_path)
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


def filter_by_isarchive(files, z7_path):
    files = [file for file in files if archivelib.is_can_handle(file, z7_path)]
    return files


def filter_by_dirs(files, must_have, must_have_no, drivers_dir):
    new_files = []

    delete_root = drivers_dir

    for path in files:
        if not path.startswith(delete_root):
            raise Exception

        _part_path = path[len(delete_root):]
        part_path = os.path.split(_part_path)[0]

        if check_dirs_names(set(split_all(part_path)), must_have=must_have, must_have_no=must_have_no):
            new_files.append(path)

    return new_files


def _get_archive_infs_list(driver, must_have, drivers_dir, archive_exts, z7_path):

    archives = filter_by_isarchive(
                filter_by_dirs(
                    filter_by_exts(get_all_files(drivers_dir), archive_exts),
                    must_have,
                    (ALL_BITS | ALL_OS) - must_have,
                    drivers_dir
                ),
                z7_path
            )

    legal_archive_infs_list = []

    for archive in archives:
        legal_infs = get_legal_infs_list(archive, driver, z7_path)

        if legal_infs:
            legal_archive_infs_list.append([archive, legal_infs])

    return legal_archive_infs_list


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


def install_driver(des_driver, sc):
    import tempfile
    import shutil

    from wpi.driver import Drivers

    # archive=None, inf_in_archive=None, inf_path=None
    inf_path = None

    tempdir = tempfile.mkdtemp()

    if des_driver.inf_path:
        if os.path.isabs(des_driver.inf_path):
            inf_path = des_driver.inf_path
        else:
            inf_path = os.path.join(sc.drivers_dir, des_driver.inf_path)

    elif des_driver.archive:
        if des_driver.inf_in_archive:
            iia = des_driver.inf_in_archive
        else:
            infs = get_legal_infs_list(des_driver.archive, des_driver.name, sc.z7_path)
            iia = infs[0]

        if os.path.isabs(des_driver.archive):
            archive = des_driver.archive
        else:
            archive = os.path.join(sc.drivers_dir, des_driver.archive)

        archivelib.extract_all(archive, tempdir, sc.z7_path)

        inf_path = os.path.join(tempdir, iia)

    else:
        archive = None
        iia = None
        inf_path_ = None

        best_archive_infs = _get_archive_infs_list(des_driver.name, {CUR_BIT, CUR_OS}, sc.drivers_dir,
                                                   sc.archive_exts, sc.z7_path)

        if best_archive_infs:
            archive = best_archive_infs[0][0]
            iia = best_archive_infs[0][1][0]

        else:
            compatible_archive_infs = _get_archive_infs_list(des_driver.name, {CUR_BIT}, sc.drivers_dir,
                                                             sc.archive_exts, sc.z7_path)
            if compatible_archive_infs:
                archive = best_archive_infs[0][0]
                iia = best_archive_infs[0][1][0]

        if archive and iia:
            archivelib.extract_all(archive, tempdir, sc.z7_path)
            inf_path = os.path.join(tempdir, iia)
        elif inf_path_:
            inf_path = inf_path_
        else:
            pass

    sysdrivers = Drivers()
    print(inf_path, des_driver.name)
    sysdrivers.add_by_inf(inf_path, des_driver.name)

    try:
        shutil.rmtree(tempdir)
    except OSError:
        pass


def install(printers, sc):
    from wpi.printer import Printers

    for p in printers:

        try:
            print('try install driver')
            install_driver(p.driver, sc)
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
    from wpi.env import load_config, Config, supply_config, user_config_path

    os.chdir(tempfile.gettempdir())

    copy_2config()

    if len(sys.argv) > 3:
        raise TypeError

    if not ctypes.windll.shell32.IsUserAnAdmin():
        print('Not run as Administrator!')
        exit()

    if len(sys.argv) > 1:
        module_ = load_module(sys.argv[1])
        
        if len(sys.argv) > 2:
            config = supply_config(load_config(sys.argv[2]))
        else:
            config = supply_config(Config())

        install(module_.printers, config)

        exit()

    elif len(sys.argv) == 1:
        module_file = os.path.join(app_path(), '_.py')

        config = supply_config(load_config(user_config_path))

        if config.drivers_dir:
            make_driver_dir_structure(config.drivers_dir)

        if os.path.exists(module_file):
            module_ = load_module(module_file.strip())
            install(module_.printers, config)

            exit()

        elif is_exe():
            make_driver_dir_structure(os.path.join(app_path(), 'drivers'))
            copy_set_sample()

        os.system('cls')
        print_head()

        while True:
            print('\nPlease input a set of printers, q to quit.')
            print('>', end='')

            user_input = input()

            if user_input.strip().lower() in ('q', 'quit', 'e', 'exit'):
                break

            elif user_input.strip().lower().endswith('.py'):
                module_ = load_module(user_input.strip())
                install(module_.printers, config)


def make_driver_dir_structure(drivers_dir):
    for bit in ALL_BITS:
        for os_ in ALL_OS:
            try:
                os.makedirs(os.path.realpath(os.path.join(drivers_dir, bit, os_)), exist_ok=True)
            except OSError:
                pass


def copy_file(source, target, even_exists=False):

    def _copy():
        os.makedirs(os.path.split(target)[0], exist_ok=True)
        shutil.copyfile(source, target)

    if os.path.exists(target):
        if even_exists and open(source, 'rb').read() != open(target, 'rb').read():
            _copy()
    else:
        _copy()


def copy_set_sample():
    from wpi import set_sample

    set_sample_filename = os.path.splitext(os.path.split(set_sample.__file__)[1])[0] + '.py'
    set_sample_target = os.path.join(app_path(), set_sample_filename)

    copy_file(os.path.join(meipass_path(), bundle_data_folder, set_sample_filename),
              set_sample_target,
              even_exists=True)


def copy_2config():
    from wpi.env import user_config_sample_path, user_config_path

    if is_exe():
        config_sample_path = os.path.join(meipass_path(), bundle_data_folder, 'config_sample.py')
    else:
        from wpi import config_sample
        config_sample_path = config_sample.__file__

    copy_file(config_sample_path, user_config_sample_path, even_exists=True)
    copy_file(config_sample_path, user_config_path, even_exists=False)


if __name__ == '__main__':
    main()
