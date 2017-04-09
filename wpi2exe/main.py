import os
import sys
import tempfile
import logging

from subprocess import Popen

import wpi.version


def set_logging():
    from wpi.log import set_stream_handler

    set_stream_handler()


def cur_file_dir():
    path = sys.path[0]
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)

c_ = cur_file_dir()
p_ = os.path.realpath(os.path.join(cur_file_dir(), '..'))


def build(script, distpath, name=None, console=True, upx_dir=None, binarys=None,  output_specpath=None):
    import shutil
    binarys = binarys or []

    workpath = tempfile.mkdtemp()

    cmd = 'pyinstaller "{}" '.format(script)

    if name:
        cmd += '--name "{}" '.format(name)

    cmd += '--onefile '

    if output_specpath:
        cmd += '--specpath "{}" '.format(output_specpath)

    cmd += '--workpath "{}" '.format(workpath)
    cmd += '--distpath "{}" '.format(distpath)

    if upx_dir:
        cmd += '--upx-dir "{}" '.format(upx_dir)

    if console:
        cmd += '--console '
    else:
        cmd += '--windowed '

    cmd += '--uac-admin '

    for src, dest in binarys:
        cmd += '--add-binary "{}";"{}" '.format(src, dest)

    print('\npyinstaller cmd: \n', cmd, '\n')

    Popen(cmd, shell=True).wait()

    shutil.rmtree(workpath)


def run_verpatch(exe_path, verpatch_path):
    sys.path.append(p_)

    cmd = '{} {} ' \
          '{version} ' \
          '/va /pv {version} '\
          '/s description "Windows Printer Installer" '\
          '/s product "Windows Printer Installer" '\
          '/s copyright "Chen Meng, 2017" '\
          .format(verpatch_path, exe_path, version=wpi.version.__version__ + '.0', )

    print('\nverpathc cmd: \n', cmd, '\n')

    Popen(cmd, shell=True).wait()


def find_7z_path():
    regkeys = (r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
               r'SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall')
    from wpi.reg import Node

    for one in regkeys:
        n = Node(one)
        for k, subn in n.items():
            if k == '7-Zip':
                print(subn.tips['InstallLocation'])


def bundle_files():
    from wpi import ps_sample
    from wpi.env import get_szip_dir, SZIP_EXE, SZIP_DLL
    return (
        os.path.join(get_szip_dir(), SZIP_EXE),
        os.path.join(get_szip_dir(), SZIP_DLL),
        ps_sample.__file__,
    )


def main():
    import wpi.main

    from wpi import env
    from wpi import load_module

    from wpi2exe import config_

    os.chdir(tempfile.gettempdir())

    set_logging()

    config_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'wpi2exe')
    os.makedirs(config_dir, exist_ok=True)

    config__filename = os.path.split(config_.__file__)[1]
    user_config__path = os.path.join(config_dir, config__filename)
    user_config_path = os.path.join(config_dir, 'config.py')

    wpi.main.copy_text_file(config_.__file__, user_config__path, even_exists=True)
    wpi.main.copy_text_file(config_.__file__, user_config_path, even_exists=False)

    config = load_module(user_config_path)

    verpatch_path = getattr(config, 'verpathc_path', None)
    upx_dir = getattr(config, 'upx_dir', None)

    if getattr(config, 'output_dir', None) is None:
        def_out_put = os.path.join(config_dir, 'exe')
        logging.warning('output_dir is None, use: {}'.format(def_out_put))
        output_dir = def_out_put
    else:
        output_dir = getattr(config, 'output_dir', None)

    output_filename = getattr(config, 'output_filename', None) or 'wpi'

    def do_build(console_, output_filename_):
        build(
            script=os.path.join(wpi.main.__file__),
            distpath=output_dir,
            name=output_filename_,
            console=console_,
            upx_dir=upx_dir,
            binarys=[(path, env.BUNDLE_DATA_FOLDER) for path in bundle_files() if path is not None]
        )

        if verpatch_path is not None:
            run_verpatch(verpatch_path=verpatch_path, exe_path=os.path.join(output_dir, output_filename_ + '.exe'))

    do_build(True, '{}-{}'.format(output_filename, wpi.version.__version__))
    # (do_build(False, '{}_nw-{}'.format(output_filename, wpi.version.__version__))


if __name__ == '__main__':
    main()
