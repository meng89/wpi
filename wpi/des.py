from wpi.port import TCPIPPort, RAW, LPR, LocalPort


class ParameterError(Exception):
    pass


class RAWPort(TCPIPPort):
    def __init__(self, address, port=9100, name=None, enable_snmp=False, snmp_dev_index=None, snmp_comunity=None):
        super().__init__()
        self.__dict__['name'] = name or address + '_' + str(port)

        self.protocol = RAW
        self.address = address
        self.port = port

        self.enable_snmp = enable_snmp
        self.snmp_dev_index = snmp_dev_index
        self.snmp_comunity = snmp_comunity


class LPRPort(TCPIPPort):
    def __init__(self, address, port=515, name=None,  enable_snmp=False, snmp_dev_index=None, snmp_comunity=None,
                 queue_name=None, is_enable_byte_count=False):
        super().__init__()
        self.__dict__['name'] = name or address + '_' + str(port)

        self.protocol = LPR
        self.address = address
        self.port = port

        self.enable_snmp = enable_snmp
        self.snmp_dev_index = snmp_dev_index
        self.snmp_comunity = snmp_comunity

        self.queue_name = queue_name
        self.is_enable_byte_count = is_enable_byte_count


class SMBPort(LocalPort):
    def __init__(self, name, value=None):
        super().__init__(value)
        self.name = name


class Driver:
    def __init__(self, name, archive=None, inf_in_archive=None, inf_path=None):
        if bool(archive) and bool(inf_path):
            raise ParameterError

        self.name = name
        self.archive = archive
        self.inf_in_archive = inf_in_archive
        self.inf_path = inf_path


class Printer:
    def __init__(self, port, driver, name=None):
        self.port = port
        self.driver = driver
        self.name = name or driver


def ep(address, driver, name=None, protocol=None, ipport=None, archive=None, inf=None):

    if address.startswith('\\\\'):
        port = SMBPort(address)

    else:
        if protocol == 'raw':
            port = RAWPort(address, ipport)
        elif protocol == 'lpr':
            port = LPRPort(address, ipport)

        elif protocol is None:

            if ipport is None:
                port = RAWPort(address)
            elif ipport >= 9100:
                port = RAWPort(address, ipport)
            else:
                port = LPRPort(address, ipport)

        else:
            raise ParameterError

    if archive:
        driver_obj = Driver(driver, archive, inf_in_archive=inf)
    else:
        driver_obj = Driver(driver, inf_path=inf)

    return Printer(port, driver_obj, name)
