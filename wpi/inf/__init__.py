from . import loads
from . import clean


def loads_and_clean(file, platform=None):
    return clean.clean(loads.loads(file), platform)
