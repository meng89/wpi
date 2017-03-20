from wpi.des import ep

from wpi.des import Printer, Driver, RAWPort, LPRPort


p1 = ep('172.16.0.11', 'KONICA MINOLTA 423SeriesPCL-8', name='km283')

p2 = ep(r'\\Print-Server\HPLaserJ', 'HP LaserJet 1020', name='hp1020')

p3 = Printer(port=RAWPort('172.16.0.11'), driver=Driver('KONICA MINOLTA 423SeriesPCL-8'), name='km283')

p4 = ep('192.168.1.6', 'HP LaserJet 1020', name='hp1020_3', archive='xxx/xxx/xxx.zip', inf='a.inf')

p5 = ep('192.168.1.6', 'HP LaserJet 1020', name='hp1020_4', inf='xxx/xxx/xxx.inf')


printers = (p1, p2)
