import copy
import time
import logging

import win32serviceutil
from win32com.client import GetObject
from wpi import reg

import hooky

# import win32serviceutil

# Name -> 端口名

# HostAddress -> 主机名
# PortNumber -> 端口号, 一般为 9100/515 (lpr 强制)

# Queue -> 队列名称, 只限 lpr
# ByteCount -> 启用了 LPR 字节计数, 只限 lpr

# SNMPEnabled -> 启用了 SNMP 状态, True/False
# SNMPDevIndex -> SNMP 设备索引
# SNMPCommunity -> 社区名称, public（默认）/None,

# Protocol -> 协议 1(raw)/2(lpr)

# Put_() 保存
# Delete_() 删除

RAW = 1
LPR = 2

_LOCAL_PORT_REG_KEY = r'HKEY_LOCAL_MACHINE\Software\Microsoft\Windows NT\CurrentVersion\Ports'


class Ports(hooky.Dict):
    def __init__(self, computer=None, account=None):
        super(Ports, self).__init__()

        self._tcpipobj = GetObject('winmgmts:/root/cimv2').Get('Win32_TCPIPPrinterPort')
        self._localregtips = reg.Tips(_LOCAL_PORT_REG_KEY)
        self._old_localregtips = copy.deepcopy(self._localregtips)

        self._tcpipobjs_to_del = []

        self._tcpipobjs = {}
        for _ in self._tcpipobj.instances_():
            self.data[_.Name] = TCPIPPort(_)
            self._tcpipobjs[_.Name] = _

        for _, v in self._localregtips.items():
            self.data[_] = LocalPort(v)

    def make_a_tcpipport(self, name):
        if name in [_.lower() for _ in self.keys()]:
            raise KeyError

        win32obj = self._tcpipobj.SpawnInstance_()
        p = TCPIPPort(win32obj)
        self._tcpipobjs[name] = win32obj
        self[name] = p
        return p

    def make_a_localport(self, name):
        p = LocalPort()
        self[name] = p
        return p

    def save(self):
        for k, v in self.data.items():
            for one in self._tcpipobjs_to_del:
                one.Delete_()

            if isinstance(v, TCPIPPort):
                win32obj = self._tcpipobjs[k]
                win32obj.Name = k
                v.save_to(win32obj)
                win32obj.Put_()

            elif isinstance(v, LocalPort):
                self._localregtips[k] = v.value or ''

        if self._localregtips != self._old_localregtips:
            self._localregtips.save_to(_LOCAL_PORT_REG_KEY)
            self._old_localregtips = copy.deepcopy(self._localregtips)

            logging.info('restart print spooler')
            _ = 'Print Spooler'
            win32serviceutil.RestartService('Print Spooler')
            sec = 0
            while win32serviceutil.QueryServiceStatus(_)[1] != 4 and sec < 10:
                time.sleep(0.2)
                sec += 0.2

            print(sec)

    def __getitem__(self, key):
        for name, obj in self.data.items():
            if name.lower() == key.lower():
                return obj

    def __setitem__(self, key, value):
        if not isinstance(value, (TCPIPPort, LocalPort)):
            raise TypeError
        try:
            del self[key]
        except KeyError:
            pass

        try:
            del self._tcpipobjs[key]
        except KeyError:
            pass

        self.data[key] = value
        if isinstance(value, TCPIPPort):
            self._tcpipobjs[key] = self._tcpipobj.SpawnInstance_()

    def __delitem__(self, key):
        k_to_del = None
        for k, v in self.data.items():
            if k.lower() == key:
                k_to_del = key
                break

        if k_to_del is None:
            raise KeyError

        else:
            v = self.data[k_to_del]

            if isinstance(v, TCPIPPort):
                try:
                    self._tcpipobjs_to_del.append(self._tcpipobjs[key])
                    del self._tcpipobjs[key]
                except KeyError:
                    pass

            elif isinstance(v, LocalPort):
                del self._localregtips[key]

            del self.data[k_to_del]


class TCPIPPort:
    def __init__(self, win32obj=None):
        self.__dict__['_map'] = (
            ('protocol', 'Protocol', RAW),
            ('address', 'HostAddress', None),
            ('port', 'PortNumber', 9100),
            ('enable_snmp', 'SNMPEnabled', False),
            ('snmp_dev_index', 'SNMPDevIndex', 1),
            ('snmp_comunity', 'SNMPCommunity', 'public'),
            ('queue_name', 'Queue', '_'),
            ('is_enable_byte_count', 'ByteCount', False)
        )
        if win32obj:
            self.__dict__['data'] = self._load(win32obj)
        else:
            self.__dict__['data'] = {}
            for k, win32_k, default in self._map:
                setattr(self, k, default)

    def _load(self, win32obj):
        data = {}
        for k, win32_k, _ in self._map:
            data[k] = getattr(win32obj, win32_k)
        return data

    def save_to(self, win32obj):
        for k, win32_k, _ in self._map:
            setattr(win32obj, win32_k, getattr(self, k))

    def __getattr__(self, key):
        return self.data[key]

    def __setattr__(self, key, value):
        if key not in [one[0] for one in self._map]:
            raise AttributeError

        self.data[key] = value

    def __eq__(self, other):
        if self.protocol != other.protocol:
            return False
        if self.address != other.address or self.port != other.port:
            return False
        if self.enable_snmp != other.enable_snmp:
            return False
        if self.enable_snmp:
            if self.snmp_dev_index != other.snmp_dev_index or self.snmp_comunity != other.snmp_comunity:
                return False
        if self.protocol is LPR:
            if self.queue_name != other.queue_name or self.is_enable_byte_count != other.is_enable_byte_count:
                return False

        return True

    def update(self, other):
        if isinstance(other, TCPIPPort) or issubclass(type(other), TCPIPPort):
            self.data.update(other.data)
        else:
            self.data.update(other)


class LocalPort:
    def __init__(self, value=None):
        self.value = value
