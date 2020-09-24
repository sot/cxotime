# Licensed under a 3-clause BSD style license - see LICENSE.rst
import ska_helpers
from astropy import config as _config

__version__ = ska_helpers.get_version(__package__)


class Conf(_config.ConfigNamespace):  # noqa
    """
    Configuration parameters for `astropy.table`.
    """

    use_fast_parser = _config.ConfigItem(
        ['True', 'False', 'force'],
        "Use fast C parser for supported time strings formats, including ISO, "
        "ISOT, and YearDayTime. Allowed values are the 'False' (use Python parser),"
        "'True' (use C parser and fall through to Python parser if fails), and "
        "'force' (use C parser and raise exception if it fails). Note that the"
        "options are all strings.")

conf = Conf()  # noqa

from .cxotime import CxoTime  # noqa


def test(*args, **kwargs):
    '''
    Run py.test unit tests.
    '''
    import testr
    return testr.test(*args, **kwargs)
