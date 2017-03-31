Windows Printer Installer
=========================

WPI 是一个使用 Python 3 编写的安装非本地打印机 （包括驱动，端口） 的工具。


安装
====

先安装 `Python 3 <https://www.python.org/downloads/windows/>`_ (建议选择的 32位 3.4 版)，安装时注意勾选 pip 组件。

然后手动下载安装相应版本的 `pywin32 <https://sourceforge.net/projects/pywin32/files/pywin32/>`_

再以管理员管理员权限运行：
::

    pip install wpi


完成安装后，wpi 应该就可以直接在命令行下运行了。

注：为了解压在压缩包里的驱动，应当下载安装 `7-Zip <http://www.7-zip.org/download.html>`_
如果想把 wpi 打包成可以多系统下可执行的独立程序，应当安装32位的 7-Zip

打包为独立的程序
========

如果想在没有 Python 环境的系统下运行，得把 Python 环境和 wpi 依赖的模块打包在一起。
先安装 Pyinstaller, 以管理员打开 cmd 执行：
::

    pip install pyinstaller


然后运行 wpi 的打包命令:
::

   wpi2exe


这样会生成单一的 exe 文件， wpi2exe 使用 %LOCALAPPDATA%\\wpi2exe\\config.py 作为配置文件，如果此文件不存在，wpi2exe 会自动创建它。
可以编辑它以设置输出目录等。正如后缀名所示，此配置文件是一个 Python 脚本。


参数用法
====

命令行参数的定义类似 Python 函数，如果把 wpi 当成一个函数看待，那么 wpi 的定义就是 wpi(ps=None, config=None)
具名参数运行例子:
::

    wpi ps=my_printers.py config=my_config.py


非具名参数运行例子：
::

    wpi my_printers.py my_conifg.py


非具名参数运行时，参数的顺序是有意义的。

参数 ps
-----

ps 是一个定义了打印机列表的文件。


参数 config
---------

config 是 配置文件。


模块脚本运行和独立 exe 运行时行为的不同
======================

虽然两种方式运行时参数一样，当时当参数不全时，或 config 里的某些项目在缺省时，程序的行为不一样。


以模块脚本方式运行时的行为
-------------

默认的配置，和 dirvers 目录所在的位置是 %LOCALAPPDATA%\\wpi；

如果没有 ps 参数，会进入交互式模式；

如果没有 config 参数，会使用 %LOCALAPPDATA%\\wpi\\config.py

如果 config 中没有配置 drivers_dir，就会使用 %LOCALAPPDATA%\\wpi\\drivers


以独立 exe 方式运行时的行为
----------------

默认的配置，和 dirvers 目录所在的位置是程序同目录

如果没有 ps 参数，会查找程序同目录有没有 _.py 如有，就使用它作为 ps。如无，就会进入交互模式

如果没有 config 参数，会使用同目录下的 config.py

如果 config 中没有配置 drivers_dir，就会使用同目录下的 drivers。


问：打印机集合文件怎么编写？
--------------
以无参数运行独立的 wpi.exe 时，会自动把名为 ps_sample.py 的打印机集合样例文件复制到程序同目录。
应该查看 ps_sample.py 以确定怎么定义打印机列表。此文件同模块 wpi.ps_sample 一样。


问：从打印机官网下载的驱动应该放在哪里？
--------------------
以无参数运行独立的 wpi.exe 时，也会自动在程序同目录下创建名为 drivers 的文件夹。打开此文件夹看看里面的结构，就能明白怎么放置驱动程序。
驱动程序包裹可放置在特定的系统版本目录下，也可放置在上一级，这样就表示这个驱动是可用于多系统的。

下载的文件只要是 7-Zip 可以解包（解压）的文件就无需手动解包。程序会自动寻找包裹里的 inf 文件并比较在打印机集合文件里给定的驱动名，符合就会使用此包裹里的这个 inf 文件。
包裹里的 inf 文件只能在第一级包裹里，举个反例: 把 inf 打包为包裹1，然后把包裹1再打包成包裹2。这样的情况下程序就找不到 inf 文件了，因为包裹2的文件列表里无 inf 文件！


问：怎么运行一下程序就安装好打印机？
------------------
必须使用打包好的单一的 wpi.exe，并且需要把定义好的打印机文件以 _.py 命名后放置在程序同目录下。


问：我有多个打印机集合文件，怎么选择安装？
---------------------
直接把集合文件拖到 wpi.exe 上，Windows 系统就会自动以一个参数的方式运行程序，那一个参数就是拖动的集合的文件名。
