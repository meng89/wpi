import os
import sys
import tempfile
from subprocess import Popen, PIPE

from wpi import version


def cur_file_dir():
    path = sys.path[0]
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)

c_ = cur_file_dir()
p_ = os.path.realpath(os.path.join(cur_file_dir(), '..'))


def build():
    # {} --distpath {}
    pyinstaller_p = Popen('pyinstaller {} --workpath {} --distpath {} --upx-dir {}'.format(
        os.path.join(c_, 'wpi.spec'),
        os.path.join(c_, '_build'),
        os.path.realpath(os.path.join(cur_file_dir(), '_dist')),
        c_,

    ), shell=True, stdout=PIPE)

    pyinstaller_p.wait()


def build2(script, distpath, name=None, console=True, upx_dir=None, binarys=None,  output_specpath=None):
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
        cmd += '--add-binary "{}:{}" '.format(src, dest)

    Popen(cmd, shell=True).wait()


def verpath():
    sys.path.append(p_)
    # print(os.path.realpath(os.path.join(cur_file_dir(), '../dist/wpi.exe')))
    verpath_p = Popen('{} {} '
                      '{version} '
                      '/va /pv {version} '
                      '/s description "Windows Printer Installer" '
                      '/s product "Windows Printer Installer" '
                      '/s copyright "Chen Meng, 2017" '
                      '/s comment "fixed this and that" '
                      .format(os.path.realpath(os.path.join(cur_file_dir(), 'verpatch.exe')),
                              os.path.realpath(os.path.join(cur_file_dir(), '_dist/wpi.exe')),
                              version=version.__version__,
                              )
                      )

    verpath_p.wait()


def sha256():
    pass


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
    build()

    verpath()
    sha256()


if __name__ == '__main__':
    main()
