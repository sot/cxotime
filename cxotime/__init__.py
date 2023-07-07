# Licensed under a 3-clause BSD style license - see LICENSE.rst
import ska_helpers
from astropy import units  # noqa
from astropy.time import TimeDelta  # noqa

from .convert import *  # noqa
from .cxotime import CxoTime, CxoTimeLike  # noqa: F401

__version__ = ska_helpers.get_version(__package__)


def test(*args, **kwargs):
    """
    Run py.test unit tests.
    """
    import testr

    return testr.test(*args, **kwargs)
