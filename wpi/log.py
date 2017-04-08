import logging


_is_file_handler_setted = False
_is_stream_handler_setted = False


def set_file_handler(filename):
    global _is_file_handler_setted
    if _is_file_handler_setted:
        return
    else:
        _is_file_handler_setted = True

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.NOTSET)

    fh = logging.FileHandler(filename, 'w')
    fh_formatter = logging.Formatter(
        '[%(asctime)s %(filename)s fun:%(funcName)s line:%(lineno)d]: %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    fh.setFormatter(fh_formatter)
    fh.setLevel(logging.NOTSET)
    root_logger.addHandler(fh)


def set_stream_handler():
    global _is_stream_handler_setted
    if _is_stream_handler_setted:
        return
    else:
        _is_stream_handler_setted = True

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.NOTSET)

    ch = logging.StreamHandler()
    ch_formatter = logging.Formatter('  %(levelname)s: [%(filename)s:%(lineno)d]: %(message)s')
    ch.setFormatter(ch_formatter)
    ch.setLevel(logging.WARNING)
    root_logger.addHandler(ch)
