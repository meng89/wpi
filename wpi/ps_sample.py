
from wpi.des import ep, Printer, Driver, RAWPort, SMBPort, LPR

from wpi import add_credential

from wpi.env import CUR_BIT

# HP LaserJet 1020
# HP LaserJet 1022
# HP LaserJet 1022n
# HP LaserJet 1022nw
# HP LaserJet 1018


# pa1 和 pa2 除了安装好后打印机列表里显示的名字不同，打印机端口和驱动都是一样的。
# ep 的意思是 easy printer， ep 其实是一个函数，返回一个 Printer 实例。
pa1 = ep('172.17.0.11', 'HP LaserJet 1022n', 'hp 1022n 1')

pa2 = Printer(
    port=RAWPort(address='172.17.0.11', port=9100, name='172.17.0.11_9100', enable_snmp=False),
    driver=Driver(name='HP LaserJet 1022n'),
    name='hp 1022n 2'
)


# pb1 和 pb2 也是除了显示的打印机名不一样，其它都一样。
# 现在使用的端口是 Windows 共享资源形式，姑且称之为 smb 端口吧。
pb1 = ep(r'\\Printer-Server\HP LaserJet 1020', 'HP LaserJet 1020', 'hp 1020 1')

pb2 = Printer(
    port=SMBPort(r'\\Printer-Server\HP LaserJet 1020'),
    driver=Driver(name='HP LaserJet 1020'),
    name='hp 1020 2'
)

# 如果使用共享打印机需要提供账户密码才能使用，应该使用下面的函数添加凭据。
add_credential(host='Printer-Server', user='administrator', password='123456')


# 可以手动指定使用哪个包裹和在包裹里的哪个 inf 文件。
# archive 不是绝对路径时，程序寻找包裹时会自动拼接配置文件里定义的 drivers_dir。如果没有定义，则使用程序同目录下的 drivers 目录。
pc1 = ep('172.17.0.11', 'HP LaserJet 1022n', name='hp 1022n 3',
         archive='{bit}\lj1018_1020_1022-HB-pnp-win{bit}-sc.exe'.format(bit=CUR_BIT), inf='HPLJ1020.INF')


# 如果想使用以已不在包裹里的 inf 文件
pc2 = ep('172.17.0.11', 'HP LaserJet 1022n', name='hp 1022n 4',
         inf=r'{bit}\lj1018_1020_1022-HB-pnp-win{bit}-sc\HPLJ1020.INF'.format(bit=CUR_BIT))


# LPR 端口打印机
pd1 = ep('172.17.0.11', 'HP LaserJet 1022n', name='hp 1022n 5', protocol=LPR)


# 打印机集合文件里需要有一个名为 'printers' 的对象。
printers = [pa1, pa2, pb1, pb2, pc1, pc2, pd1]
