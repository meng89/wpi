import logging


logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s %(name)s %(filename)s %(funcName)s line:%(lineno)d %(levelname)s]: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='myapp.log',
    filemode='w'
)

console = logging.StreamHandler()

console.setLevel(logging.WARNING)
