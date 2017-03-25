
from setuptools import setup
from distutils.util import convert_path

import ssl

ssl._create_default_https_context = ssl._create_unverified_context


NAME = 'wpi'

main_ns = {}
ver_path = convert_path('{}/version.py'.format(NAME))
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

DESCRIPTION = 'Windows Printer Installer'


URL = 'https://github.com/meng89/' + NAME

CLASSIFIERS = [
    'Intended Audience :: Developers',
    'Intended Audience :: Information Technology',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
    'Operating System :: Microsoft :: Windows',
    'Programming Language :: Python :: 3',
    'Topic :: Software Development :: Libraries :: Python Modules',
]
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name=NAME,
      version=main_ns['__version__'],
      description=DESCRIPTION,
      include_package_data=True,
      author='Chen Meng',
      author_email='ObserverChan@gmail.com',
      license='LGPL',
      url=URL,
      packages=[
          'wpi',
          'wpi.inf',
          'wpi2exe',
      ],
      # scripts=[
      #    'main.py',
      # ],
      entry_points={
          'console_scripts': [
               'wpi=wpi.main:main',
               'wpi2exe=wpi2exe.main:main'
          ],
      },
      install_requires=requirements,
      classifiers=CLASSIFIERS)
