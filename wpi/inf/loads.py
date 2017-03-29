import io


def loads(strings: str):
    lines = [l.strip() for l in io.StringIO(strings).readlines()]
    lines = [l for l in lines if l != '']

    ls = []

    last_part = ''
    for line in lines:
        if line == '':
            continue

        if line.endswith('\\'):
            last_part += line
        else:
            ls.append(last_part+line)
            last_part = ''
            
    return _analyse(lines)


def _analyse(lines):
    data = {}

    sec = None

    for line in lines:
        if line[0] == ';':
            continue

        elif line[0] == '[':
            sec = _read_sec(line)
            data[sec] = []

        else:
            data[sec].append(_read_entry(line))
            
    return data


def _read_sec(line):
    start = line.index('[')
    end = line.rindex(']')

    v = line[start+1:end]
    return v


def _quote_handle(chars):
    v = ''
    in_quote = False

    i = 0
    for i in range(len(chars)):
        v += chars[i]

        if chars[i] == '"':
            if in_quote is True:
                _ = chars[i+1:].strip()
                if _ == '' or _[0] in (',', ';', '='):
                    break
            else:
                in_quote = True

    if v[0] != '"' or v[-1] != '"':
        raise Exception

    v = v[1:-1]
    while v != v.replace('""', '"'):
        v = v.replace()

    return v, chars[i+1:]


def _token_handle(chars):
    i = 0
    v = ''
    in_token = False

    for i in range(len(chars)):
        v += chars[i]

        if chars[i] == '%':
            if in_token is True:
                _ = chars[i+1:].strip()
                if _ == '' or _[0] in (',', ';', '='):
                    break
            else:
                in_token = True

    return v, chars[i+1:]


def _normal_handle(chars):
    i = 0
    v = ''

    for i in range(len(chars)):
        v += chars[i]

        _ = chars[i+1:].strip()
        if _ == '' or _[0] in (',', ';', '='):
            break

    return v, chars[i+1:]


def _read_entry(line):

    line = line.strip()

    v = None

    is_v_is_list = False
    v_list = []

    is_lr = False
    lv = None
    rv = None

    # is_lv_is_list = False
    lv_list = []

    is_rv_is_list = False
    rv_list = []

    while True:
        if line == '':
            break

        if line[0] == '"':
            quote_v, part_line = _quote_handle(line)
            line = part_line.strip()

            if is_lr:
                if is_rv_is_list:
                    rv_list[-1] += quote_v
                else:
                    rv = quote_v
            else:
                if is_v_is_list:
                    v_list[-1] += quote_v
                else:
                    v = quote_v

        elif line[0] == '%':
            token_v, part_line = _token_handle(line)
            line = part_line.strip()

            if is_lr:
                if is_rv_is_list:
                    rv_list[-1] += token_v
                else:
                    rv = token_v
            else:
                if is_v_is_list:
                    v_list[-1] += token_v
                else:
                    v = token_v

        elif line[0] == ';':
            break

        elif line[0] == ',':

            if is_lr:
                is_rv_is_list = True
                if len(rv_list) == 0:
                    rv_list = [rv, '']
                else:
                    rv_list.append('')
                rv = None

            else:
                is_v_is_list = True
                if len(v_list) == 0:
                    v_list = [v, '']
                else:
                    v_list.append('')
                v = None

            line = line[1:].strip()

        elif line[0] == '=':
            is_lr = True

            if is_v_is_list:
                lv_list = v_list
                del v_list

            else:
                lv = v
                v = None

            line = line[1:].strip()

        else:
            normal_v, part_line = _normal_handle(line)
            line = part_line.strip()

            if is_lr:
                if is_rv_is_list:
                    rv_list[-1] += normal_v
                else:
                    rv = normal_v
            else:
                if is_v_is_list:
                    v_list[-1] += normal_v
                else:
                    v = normal_v

    if is_lr:
        return (lv_list or lv), (rv_list or rv)

    elif is_v_is_list:
        return v_list

    else:
        return v
