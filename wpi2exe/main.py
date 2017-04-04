import os
import sys
import tempfile
from subprocess import Popen

import wpi.version


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


def main():
    import shutil
    import wpi.main
    import wpi.env
    from wpi import load_module

    from wpi2exe import config_sample

    config_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'wpi2exe')
    os.makedirs(config_dir, exist_ok=True)

    user_config_sample_path = os.path.join(config_dir, 'config_sample.py')
    user_config_path = os.path.join(config_dir, 'config.py')

    print(user_config_path)

    if not os.path.exists(user_config_sample_path) or \
            open(config_sample.__file__, 'rb').read() != open(user_config_sample_path, 'rb').read():
        shutil.copyfile(config_sample.__file__, user_config_sample_path)

    if not os.path.exists(user_config_path):
        shutil.copyfile(user_config_sample_path, user_config_path)
        print('"config.py" not found, copied. you may want to edit {} and rerun this again'.format(user_config_path))
        exit()

    config = load_module(user_config_path)

    verpatch_path = getattr(config, 'verpathc_path', None)
    upx_dir = getattr(config, 'upx_dir', None)

    output_dir = getattr(config, 'output_dir', None) or os.path.expanduser('~')

    output_filename = getattr(config, 'output_filename', None) or 'wpi'

    def do_build(console_, output_filename_):
        build(
            script=os.path.join(wpi.main.__file__),
            distpath=output_dir,
            name=output_filename_,
            console=console_,
            upx_dir=upx_dir,
            binarys=[(path, wpi.env.bundle_data_folder) for path in wpi.env.bundle_files()]
        )

        if verpatch_path is not None:
            run_verpatch(verpatch_path=verpatch_path, exe_path=os.path.join(output_dir, output_filename_ + '.exe'))

    do_build(True, output_filename)
    do_build(False, output_filename + '_nw')

if __name__ == '__main__':
    main()
