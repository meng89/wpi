Windows Printer Installer
=========================

WPI 是一个使用 Python 3 编写的安装打印机 （包括驱动，端口） 的工具。

想一下这样的情况：需要给很多台电脑安装同一台打印机。你不想使用微软

安装
---

先安装 Python 3 (建议选择 32bit 的 3.4 版) 及 pip 组件
然后手动下载安装 `pywin32 <https://sourceforge.net/projects/pywin32/files/pywin32/>`_
再以管理员启动 cmd
最后用 pip 安装 wpi：
::

    pip install wpi
现在，系统应该已有 wpi 命令。

如果想在没有 Python 环境的系统下运行，得把 Python 环境和 wpi 依赖的模块打包，执行:
::

   wpi2exe

会生成单一的 exe 文件，当前用户\AppData\Local\wpi2exe\config.py 这个文件是 wpi2exe 这个命令的配置文件，如果不存在，wpi2exe 会自动创建它。
如你所见，此配置文件纯粹是一个 Python 脚本文件。你可以编辑它以选择编译exe是的输出目录等。

wpi.exe 怎么使用？
-------------
举个例子:
::

    wpi.exe D:\my_set.py D:\wpi_config.py

就两个参数： 第一个是定义了打印机集合的脚本文件，第二个是配置脚本文件。它们也是纯粹的 Python 脚本文件。
