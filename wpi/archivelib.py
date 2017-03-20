import zipfile
import io
from subprocess import Popen, PIPE

import chardet


def is_can_handle(filename, path_of_7z=None):
    if zipfile.is_zipfile(filename):
        return True

    elif path_of_7z is not None:
        for bytes_line in io.BytesIO(
                Popen('{} t {}'.format(path_of_7z, filename), shell=True, stdout=PIPE).communicate()[0])\
                .readlines():

            if bytes_line.decode().strip() == 'Everything is Ok':
                return True

    return False


def list_names(archive, path_of_7z=None):

    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            return z.namelist()

    if path_of_7z is None:
        raise Exception

    list_head = '   Date      Time    Attr         Size   Compressed  Name'
    list_cut = '------------------- ----- ------------ ------------  ------------------------'

    _b = Popen('{} l -so {}'.format(path_of_7z, archive), shell=True, stdout=PIPE).communicate()[0]
    _code = chardet.detect(_b)['encoding']
    bytes_file = io.BytesIO(_b)
    lines = [line.decode(_code).rstrip() for line in bytes_file.readlines()]

    start_pos = None
    end_pos = None
    i = 0
    for line in lines:
        if line.startswith(list_head):
            start_pos = i + 2

        elif line.startswith(list_cut) and i > start_pos + 2:
            end_pos = i
            break

        i += 1

    return [line[53:] for line in lines[start_pos:end_pos]]


def read(archive, filename, path_of_7z=None):
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            return io.BytesIO(z.read(filename))

    if path_of_7z is None:
        raise Exception

    return Popen('{} e -so {} {}'.format(path_of_7z, archive, filename), shell=True, stdout=PIPE).communicate()[0]


def extract_all(archive, path, path_of_7z=None):
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            z.extractall(path)
            return

    elif path_of_7z:
        Popen('{} x {} -o{}'.format(path_of_7z, archive, path), shell=True, stdout=PIPE).communicate()
    else:
        print(path_of_7z)
        raise Exception
