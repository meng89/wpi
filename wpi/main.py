import ctypes
import datetime
import logging
import os
import sys
import tempfile

import chardet

import wpi.inf

import wpi.log

from wpi import load_module, archivelib, version
from wpi.env import ALL_BITS, CUR_BIT, CUR_OS, ALL_OS, PYTHON_BIT

supplied_config = None

DEFAULT_PS_NAME = 'ps.py'

USER_SAMPLE_PS_NAME = '_ps.py'

DEFAULT_DIRIVERS_NAME = 'drivers'


# user_config_sample_path = os.path.join(user_wpi_dir, 'config.py')
# user_config_path = os.path.join(user_wpi_dir, def_config_filename)

logs_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'wpi_logs')


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
    try:
        inf_data = wpi.inf.loads.loads(inf_bytes.decode(chardet.detect(inf_bytes)['encoding']))
    except Exception:
        return False

    models = wpi.inf.utils.get_models(inf_data)

    for model, namek_files_hids in models.items():
        if CUR_BIT == '32' and model[1] is not None and model[1].lower() != 'ntx86':
            continue

        elif CUR_BIT == '64' and (model[1] is None or model[1].lower() != 'ntamd64'):
            continue

        if driver in namek_files_hids.keys():
            return True

    return False


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


class InstallationFailed(Exception):
    pass


def install_port(des_port):
    from wpi.port import Ports

    from wpi.des import RAWPort, LPRPort, SMBPort

    sysports = Ports()

    if des_port.name is None:
        raise Exception

    if des_port.name not in sysports.keys():
        if isinstance(des_port, (RAWPort, LPRPort)):
            sysports[des_port.name] = des_port

        elif isinstance(des_port, SMBPort):
            sysports[des_port.name] = des_port

        sysports.save()
    else:
        logging.warning('port: {} already existed, abort.'.format(des_port.name))


def install_driver(des_driver, drivers_dir):
    from wpi.driver import Drivers, B32, B64
    from wpi import env
    from wpi.env import ARCHIVE_EXTS, get_szip_path

    szip_path = get_szip_path()

    sysdrivers = Drivers()

    for one in sysdrivers:
        if one[0] == des_driver.name and (one[2], CUR_BIT) in ((B32, env.B32), (B64, env.B64)):
            logging.warning('driver: {} already existed, abort.'.format(des_driver.name))
            return None

    inf_path = None

    tempdir = tempfile.mkdtemp()

    def _full(_):
        if not os.path.isabs(_):
            return os.path.join(drivers_dir, _)
        return _

    if des_driver.inf_path:
        inf_path = _full(des_driver.inf_path)

    elif des_driver.archive:

        archive = _full(des_driver.archive)

        if des_driver.inf_in_archive:
            iia = des_driver.inf_in_archive
        else:
            infs = get_legal_infs_list(archive, des_driver.name, szip_path)
            iia = infs[0]

        logging.info('use archive: {}'.format(archive))

        archivelib.extract_all(archive, tempdir, szip_path)

        inf_path = os.path.join(tempdir, iia)

    else:
        for must_have in ({CUR_BIT, CUR_OS}, {CUR_BIT}):
            archive_infs = _get_archive_infs_list(des_driver.name, must_have, drivers_dir, ARCHIVE_EXTS, szip_path)

            if archive_infs:
                archive = archive_infs[0][0]
                logging.info('use matched archive: {}'.format(archive))
                iia = archive_infs[0][1][0]
                logging.info('inf_in_archive: {}'.format(iia))

                archivelib.extract_all(archive, tempdir, szip_path)
                inf_path = os.path.join(tempdir, iia)

    if inf_path and is_match(open(inf_path, 'rb').read(), des_driver.name):
        logging.info('use inf_path: {}, driver name: {}'.format(inf_path, des_driver.name))
        sysdrivers.add_by_inf(inf_path, des_driver.name)
        logging.info('done')
    else:
        logging.warning('bad driver -> name: {}, archive: {}, inf_path:{}'.format(des_driver.name,
                                                                                  des_driver.archive,
                                                                                  des_driver.inf_path))
        raise InstallationFailed


def install_printer(printer_name, driver_name, port_name):
    from wpi.printer import Printers
    sysprinters = Printers()

    if printer_name not in sysprinters.keys():
        printer = sysprinters.make_new(printer_name)
        printer.driver_name = driver_name
        printer.port_name = port_name
        sysprinters.save()
    else:
        logging.warning('printer: {} already existed, abord.'.format(printer_name))


def install(printers, drivers_dir):
    for p in printers:
        try:
            install_driver(p.driver, drivers_dir)
            install_port(p.port)
            install_printer(p.name, p.driver.name, p.port.name)

        except InstallationFailed:
            logging.error('install printer: {} failed.'.format(p.name))


def print_head():
    from shutil import get_terminal_size

    conlose_len = get_terminal_size()[0] - 2
    cl = conlose_len

    header_len = min([62, cl]) - 2
    hl = header_len

    item_left = 2

    def _(s):
        return s
        # return '{:^{}}'.format(s, cl)

    def sharp():
        s = '#' * hl
        return _(s)

    def _wpi():
        s = '{:^{}}'.format('Windows Printer Installer', hl)
        return _(s)

    def _item(k, v):
        s = '{}: {}'.format(k, v)
        s = (' ' * item_left) + s
        s += ' ' * (hl - len(s))
        return _(s)

    ss = [
        sharp(),
        '',
        _wpi(),
        '',
        _item('Version', version.__version__),
        _item('License', 'LGPL v3'),
        _item('Author', 'Chen Meng'),
        _item('HomePage', 'https://github.com/meng89/wpi'),
        sharp(),
    ]

    for _ in ss:
        print(_)


def main():
    from wpi.env import is_exe
    from wpi.log import set_file_handler, set_stream_handler

    if not ctypes.windll.shell32.IsUserAnAdmin():
        print('Not run as Administrator!')
        sys.exit()

    args = list()
    kwargs = dict()

    for _ in sys.argv[1:]:
        p_a = _.split('=', 1)
        if len(p_a) == 1:
            args.append(_)
        else:
            kwargs[p_a[0]] = p_a[1]

    log_filename = datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S_%f') + '.log.txt'
    os.makedirs(logs_dir, exist_ok=True)

    set_file_handler(os.path.join(logs_dir, log_filename))
    set_stream_handler()

    log_sys_info()

    os.chdir(tempfile.gettempdir())

    if is_exe():
        exe_main(*args, **kwargs)
    else:
        script_main(*args, **kwargs)


def exe_main(ps=None, drivers=None):
    from wpi.env import exe_dir

    if drivers is not None:
        drivers_dir = drivers
    else:
        drivers_dir = os.path.join(exe_dir(), DEFAULT_DIRIVERS_NAME)

    if ps is not None:
        module_ = load_module(ps)
    elif os.path.exists(os.path.join(exe_dir(), DEFAULT_PS_NAME)):
        module_ = load_module(os.path.join(exe_dir(), DEFAULT_PS_NAME))
    else:
        module_ = None

    if module_ is not None:
        install(module_.printers, drivers_dir)
        sys.exit()

    interactive_loop(drivers_dir, exe_dir())


def script_main(ps=None, drivers=None):
    user_wpi_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'wpi')

    if drivers is not None:
        drivers_dir = drivers
    else:
        drivers_dir = os.path.join(user_wpi_dir, DEFAULT_DIRIVERS_NAME)

    if ps is not None:
        module_ = load_module(ps)
    else:
        module_ = None

    if module_ is not None:
        install(module_.printers, drivers_dir)
        sys.exit()

    interactive_loop(drivers_dir, user_wpi_dir)


def interactive_loop(drivers_dir, m_target_dir):
    logging.info('m command target dir: '.format(m_target_dir))

    print_head()
    while True:
        print('\n')
        print('Please input a printers file or a command:\n' +
              '  m  Make sample of "ps" and make drivers structure directories.\n' +
              '  q  Quit.')
        print('"ps" file or cmd: ', end='')

        user_input = input()

        if user_input.strip().lower() == 'm':
            copy_text_file(original_ps_sample_path(), os.path.join(m_target_dir, USER_SAMPLE_PS_NAME), even_exists=True)
            target_drivers_dir = os.path.join(m_target_dir, DEFAULT_DIRIVERS_NAME)
            make_driver_dir_structure(target_drivers_dir)

        elif user_input.strip().lower() in ('q', 'quit', 'e', 'exit'):
            break

        elif user_input.strip().lower().endswith('.py'):
            module_ = load_module(user_input.strip())
            install(module_.printers, drivers_dir)


def make_driver_dir_structure(drivers_dir):
    for bit in ALL_BITS:
        for os_ in ALL_OS:
            try:
                os.makedirs(os.path.realpath(os.path.join(drivers_dir, bit, os_)), exist_ok=True)
            except OSError:
                pass


def copy_text_file(source, target, even_exists=False, lf2crlf=True):
    import io

    if lf2crlf:
        with io.StringIO(newline='\r\n') as s_strio:
            s_strio.writelines(open(source, 'r', encoding='utf8').readlines())
            s_strio.seek(0)
            s_bytes = bytes(s_strio.read(), encoding='utf8')
    else:
        s_bytes = open(source, 'rb').read()

    def _write_target():
        os.makedirs(os.path.split(target)[0], exist_ok=True)
        with open(target, 'wb') as f:
            f.write(s_bytes)

    if os.path.exists(target):
        if even_exists:
            if s_bytes != open(target, 'rb').read():
                _write_target()
        else:
            pass
    else:
        _write_target()


def original_ps_sample_path():
    from wpi.env import is_exe, meipass_path, BUNDLE_DATA_FOLDER
    from wpi.user_sample import ps

    if is_exe():
        return os.path.join(meipass_path(), BUNDLE_DATA_FOLDER,
                            os.path.splitext(os.path.split(ps.__file__)[1])[0] + '.py')
    else:
        from wpi.user_sample import ps
        return ps.__file__


def log_sys_info():
    logging.info('OS bit: {}'.format(CUR_BIT))
    logging.info('OS release: {}'.format(CUR_OS))
    logging.info('Python bit: {}'.format(PYTHON_BIT))
    logging.info('Python sys.version: {}'.format(sys.version))


if __name__ == '__main__':
    main()
