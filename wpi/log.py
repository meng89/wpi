import logging


_is_setted = False


def set_logging(filename):
    global _is_setted
    if _is_setted:
        raise Exception
    else:
        _is_setted = True

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.NOTSET)

    fh = logging.FileHandler(filename, 'w')
    fh_formatter = logging.Formatter(
        '[%(asctime)s %(filename)s fun:%(funcName)s line:%(lineno)d]: %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    fh.setFormatter(fh_formatter)
    fh.setLevel(logging.NOTSET)
    root_logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch_formatter = logging.Formatter('  --[%(filename)s:%(lineno)d]: %(levelname)s: %(message)s')
    ch.setFormatter(ch_formatter)
    ch.setLevel(logging.WARNING)
    root_logger.addHandler(ch)

    return root_logger
