# Licensed under a 3-clause BSD style license - see LICENSE.rst
import astropy.units as u
import numpy as np

from cxotime import CxoTime, CxoTimeLike


def get_range_in_chunks(start: CxoTimeLike, stop: CxoTimeLike, dt_max: u.Quantity):
    """
    Get uniform time chunks for a given time range.

    Output times are spaced uniformly spaced by up to ``dt_max`` and cover the time
    range from ``start`` to ``stop``.

    Parameters
    ----------
    start : CxoTime
        Start time of the time range.
    stop : CxoTime
        Stop time of the time range.
    dt_max : u.Quantity (timelike)
        Maximum time interval for each chunk.

    Returns
    -------
    CxoTime
        CxoTime with time bin edges for each chunk.
    """
    start = CxoTime(start)
    stop = CxoTime(stop)

    # Require that dt_max is a positive nonzero quantity
    if dt_max <= 0 * u.s:
        raise ValueError("dt_max must be positive nonzero")

    # Let this work if start > stop, but flip the sign of dt_max
    if start > stop:
        dt_max = -dt_max

    # Calculate chunks to cover time range, handling edge case of start == stop
    n_chunk = max(np.ceil(float((stop - start) / dt_max)), 1)
    dt = (stop - start) / n_chunk
    times = start + np.arange(n_chunk + 1) * dt
    return times
