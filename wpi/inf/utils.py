

def is_token(string):
    try:
        if string[0] == '%' and string[-1] == '%':
            return True
        else:
            return False
    except IndexError:
        return False


def get_entries(infdata, section):
    for k, v in infdata.items():
        if k.lower() == section.lower():
            return v


def get_option(entries, option):
    for entry in entries:
        if entry[0].lower() == option.lower():
            return entry[1]


def get_models(infdata):
    old_models_heads = []
    for entry in get_entries(infdata, 'manufacturer'):
        v = entry[1]

        old_models_heads.append((v[0], None, None))

        for t in v[1:]:
            try:
                platform, osversion = t.split('.', 1)
            except ValueError:
                platform = t
                osversion = None

            old_models_heads.append((v[0], platform, osversion))

    new_models = {}
    for model in old_models_heads:
        sec = ''
        sec += model[0]
        if model[1] is not None:
            sec += '.' + model[1]
        if model[2] is not None:
            sec += '.' + model[2]

        entries = get_entries(infdata, sec)
        if entries is None:
            continue

        d2 = {}

        for entry in entries:
            d2[entry[0]] = entry[1][0], entry[1][1:]

        new_models[model] = d2

    return new_models


def get_provider(infdata):
    provider = get_option(get_entries(infdata, 'Version'), 'provider')
    if is_token(provider):
        provider = get_option(get_entries(infdata, 'Strings'), provider[1:-1])
    return provider


def get_driver_version(infdata):
    driverver = get_option(get_entries(infdata, 'version'), 'driverver')

    date = driverver[0]
    try:
        ver = driverver[1]
    except ValueError:
        ver = None
    return date, ver


def keep_platform(models, platform):
    platform = platform or (None, 'NTx86', 'NTamd64')
    new_models = {}
    for k, name_fh in models.items():
        if k[1] in platform:
            new_models[k] = name_fh

    return new_models


def clean(infdata, platform):
    models = get_models(infdata)

    models = keep_platform(models, platform)

    new_models = {}
    for k, name_fhs in models.items():
        new_name_fhs = {}
        for name, files_hids in name_fhs.items():
            new_name_fhs[name] = tuple(files_hids[1])

        new_models[k] = new_name_fhs

    return get_provider(infdata), get_driver_version(infdata), new_models
