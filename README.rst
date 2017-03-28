Windows Printer Installer
=========================

WPI 是一个使用 Python 3 编写的安装非本地打印机 （包括驱动，端口） 的工具。


安装
====

先安装 Python 3 (建议选择 32bit 的 3.4 版) 及 pip 组件

然后手动下载安装 `pywin32 <https://sourceforge.net/projects/pywin32/files/pywin32/>`_

再以管理员启动 cmd 后用 pip 安装 wpi：
::

    pip install wpi


wpi 怎么用？
========

分为以 Python 模块和脚本运行和以编译好的独立的 exe 运行两种情况。
如果你是开发者，可能对你来说，实用价值最大的是 wpi.reg 模块，此模块可以通过类似 dict 对象的方式处理注册表。


以独立的 exe 运行
-----------

如果想在没有 Python 环境的系统下运行，得把 Python 环境和 wpi 依赖的模块打包在一起。
先安装 Pyinstaller, 以管理员打开 cmd 执行：
::

    pip install pyinstaller

然后运行打包命令:
::

   wpi2exe

这样会生成单一的 exe 文件， wpi2exe 使用 %LOCALAPPDATA%\\wpi2exe\\config.py 作为配置脚本，如果不存在，wpi2exe 会自动创建它。
可以编辑它以设置输出目录等。正如后缀名所示，此配置文件是一个 Python 脚本文件。

现在我们可以运行 wpi.exe 了， 举例：
::

    wpi.exe D:\my_set.py D:\wpi_config.py

只有两个可选参数： 第一个参数是定义了打印机集合的脚本，第二个是配置脚本。 默认的配置脚本位置是 %LOCALAPPDATA%\\wpi\\config.py。
如果像例子中的命令这样以第二个参数指定了配置文件，默认配置文件则会被忽略。只有当以一个参数的方式运行 wpi.exe 时（既没有指定配置脚本），wpi.exe 才会使用默认的配置脚本。


第一个参数是打印机集合，wpi.exe 在运行时会自动把打印机集合样例文件复制到程序同目录。应该查看 set_sample.py 以确定怎么定义打印机集合。

以脚本运行
-----
通过 pip 安装 wpi 后，wpi 应该就可以直接在 cmd 下运行了。