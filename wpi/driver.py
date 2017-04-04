from win32com.client import GetObject
import hooky

_OBJ_NAME = 'Win32_PrinterDriver'

B32 = 'Windows NT x86'
B64 = 'Windows x64'


class Drivers(hooky.Dict):
    def __init__(self):
        super().__init__()
        self._Driver = GetObject('winmgmts:/root/cimv2').Get('Win32_PrinterDriver')

    def __iter__(self):
        for _ in self._Driver.instances_():
            yield tuple(_.name.rsplit(',', 2))

    def __setitem__(self, key, value):
        raise TypeError('not support this yet!')

    def add_by_inf(self, inf_path, name, platform=None):
        if inf_path is None:
            raise ValueError

        self._Driver.Name = name
        self._Driver.InfName = inf_path

        # default is os platform
        if platform is not None:
            self._Driver.SupportedPlatform = platform

        method = self._Driver.Methods_('AddPrinterDriver')
        in_parms = method.InParameters
        in_parms.DriverInfo = self._Driver

        self._Driver.ExecMethod_('AddPrinterDriver', in_parms)

    def __delitem__(self, key):

        wmi = GetObject('winmgmts:/root/cimv2')

        drivers = wmi.InstancesOf(_OBJ_NAME)

        for driver in drivers:
            if key == driver.name.rsplit(',', 2):
                driver.Delete_()
                return

        raise Exception


if __name__ == '__main__':
    pass
