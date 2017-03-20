import collections

import winreg

from hooky import Dict


ERROR_NO_MORE_ITEMS = 259


def _recommend_type(v):
    if isinstance(v, int):
        if 0 <= v <= 2**32-1:
            return winreg.REG_DWORD
        elif 2**32 <= v <= 2**64-1:
            return winreg.REG_QWORD
        else:
            return None

    elif isinstance(v, str):
        if v.startswith('%') and v.endswith('%'):
            return winreg.REG_EXPAND_SZ
        else:
            return winreg.REG_SZ

    elif isinstance(v, collections.Iterable):
        return winreg.REG_MULTI_SZ


def _analyze_path(path):
    if isinstance(path, (tuple, list)):
        return tuple(path)

    else:
        if isinstance(path, str):
            return tuple(path.split('\\'))
        else:
            raise Exception


class Node(Dict):
    def __init__(self, path=None, skip_error=True):
        super().__init__()

        if path:
            self.tips, self.data = self._load(path, skip_error)

        else:
            self.tips = Tips()

    @staticmethod
    def _load(path, skip_error=True):
        path = _analyze_path(path)

        tips = Tips(path, skip_error)

        subs = {}

        try:
            my_key = winreg.OpenKey(getattr(winreg, path[0]),
                                    '\\'.join(path[1:]),
                                    0,
                                    winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY)
        except Exception as e:
            if skip_error:
                return tips, subs
            else:
                raise e

        i = 0
        while True:
            try:
                k = winreg.EnumKey(my_key, i)
            except Exception as E:
                if isinstance(E, OSError) and E.winerror == ERROR_NO_MORE_ITEMS:
                    break
                elif skip_error:
                    continue
                else:
                    raise E

            subs[k] = Node(path + (k,), skip_error)
            i += 1

        my_key.Close()

        return tips, subs

    def save_to(self, path, skip_error=True):
        path = _analyze_path(path)

        try:
            my_key = winreg.CreateKeyEx(getattr(winreg, path[0]),
                                        '\\'.join(path[1:]),
                                        0,
                                        winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY)
        except Exception as E:
            if skip_error:
                return
            else:
                raise E

        # Tips
        self.tips.save_to(path, skip_error)

        # Subs
        reg_keys = set()

        i = 0
        while True:
            try:
                sub_key = winreg.EnumKey(my_key, i)
            except Exception as E:
                if isinstance(E, OSError) and E.winerror == ERROR_NO_MORE_ITEMS:
                    break
                elif skip_error:
                    i += 1
                    continue
                else:
                    raise E

            i += 1
            reg_keys.add(sub_key)

        # keys_to_add = set(self.keys()) - reg_keys
        keys_to_del = reg_keys - set(self.keys())

        for k in keys_to_del:
            winreg.DeleteKey(my_key, k)

        my_key.Close()

        # save Subs
        for k, v in self.items():
            v.save_to(path+(k,))

    def __setitem__(self, key, value):
        if not isinstance(value, Node):
            raise TypeError

        k_to_del = None
        for k in self.keys():
            if k.lower() == key.lower():
                k_to_del = k
                break
        if k_to_del:
            del self[k_to_del]

        self.data[key] = value


class Tips(Dict):
    def __init__(self, path=None, skip_error=True):
        super().__init__()

        if path:
            self.data, self.types = self._load(path, skip_error)
        else:
            self.types = {}

    @staticmethod
    def _load(path, skip_error=True):
        path = _analyze_path(path)

        data = {}
        types = {}

        try:
            my_key = winreg.OpenKey(getattr(winreg, path[0]),
                                    '\\'.join(path[1:]),
                                    0,
                                    winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY)
        except Exception as E:
            if skip_error:
                return data, types
            else:
                raise E

        i = 0
        while True:
            try:
                name, value, type_ = winreg.EnumValue(my_key, i)
            except Exception as E:
                if isinstance(E, OSError) and E.winerror == ERROR_NO_MORE_ITEMS:
                    break
                elif skip_error:
                    i += 1
                    continue
                else:
                    raise E
            i += 1
            data[name] = value
            types[name] = type_

        my_key.Close()

        return data, types

    def save_to(self, path, skip_error=True):
        path = _analyze_path(path)
        try:
            my_key = winreg.CreateKeyEx(getattr(winreg, path[0]),
                                        '\\'.join(path[1:]),
                                        0,
                                        winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY)
        except Exception as e:
            if skip_error:
                return
            else:
                raise e

        reg_data, reg_types = self._load(path)

        keys_to_del = set(reg_data.keys()) - set(self.keys())
        keys_to_add = set(self.keys()) - set(reg_data.keys())

        keys_to_update = set([k for k in (set(self.keys()) & set(reg_data.keys())) if self[k] != reg_data[k]])

        # Add and Update
        for k in (keys_to_add | keys_to_update):
            v, type_ = self.get_value(k)
            try:
                winreg.SetValueEx(my_key, k, 0, type_, v)
            except Exception as e:
                if skip_error:
                    return
                else:
                    raise e
        # Del
        for k in keys_to_del:
            try:
                winreg.DeleteValue(my_key, k)
            except Exception as e:
                if skip_error:
                    return
                else:
                    raise e

        my_key.Close()

    def get_value(self, key):
        try:
            _type = self.types[key]
        except KeyError:
            _type = _recommend_type(self[key])
        return self[key], _type

    def set_value(self, key, type_, value):
        try:
            del self[key]
        except KeyError:
            pass
        try:
            del self.types[key]
        except KeyError:
            pass

        self[key] = value
        self.types[key] = type_
