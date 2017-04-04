import logging

import hooky


class Printers(hooky.Dict):
    def __init__(self):

        from win32com.client import GetObject
        self._Printer = GetObject('winmgmts:/root/cimv2').Get('Win32_Printer')

        super().__init__()
        for _ in self._Printer.instances_():
            p = Printer(_)
            self.data[_.DeviceID] = p

    def save(self):
        for name, printer in self.data.items():
            printer.save(name)

    def make_new(self, name):
        if name in [_.lower() for _ in self.keys()]:
            raise KeyError

        win32obj = self._Printer.SpawnInstance_()

        new_printer = Printer(win32obj)

        self.data[name] = new_printer
        return new_printer

    def __delitem__(self, key):
        self.data[key].win32obj.Delete_()
        del self.data[key]


class Printer:
    def __init__(self, win32obj):
        self.win32obj = win32obj

        self._old_driver_name, self._old_port_name, self._old_name = self._load()

    def _load(self):
        return self.win32obj.DriverName, self.win32obj.PortName, self.win32obj.DeviceID

    def save(self, name):
        if self._old_driver_name != self.driver_name \
                or self._old_port_name != self.port_name \
                or self._old_name != name:

            self.win32obj.DeviceID = name
            logging.info('name: {}, driver name: {}, port name: {}'.format(name, self.driver_name, self.port_name))
            self.win32obj.Put_()

    @property
    def driver_name(self):
        return self.win32obj.DriverName

    @driver_name.setter
    def driver_name(self, v):
        self.win32obj.DriverName = v

    @property
    def port_name(self):
        return self.win32obj.PortName

    @port_name.setter
    def port_name(self, v):
        self.win32obj.PortName = v
