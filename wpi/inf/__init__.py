from . import loads
from . import utils


def loads_and_clean(file, platform=None):
    return utils.clean(loads.loads(file), platform)
