# Licensed under a 3-clause BSD style license - see LICENSE.rst
from .cxotime import CxoTime, date2secs, secs2date  # noqa
from astropy.time import TimeDelta  # noqa
from astropy import units  # noqa
import ska_helpers

__version__ = ska_helpers.get_version(__package__)


def test(*args, **kwargs):
    '''
    Run py.test unit tests.
    '''
    import testr
    return testr.test(*args, **kwargs)
