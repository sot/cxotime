"""
Simple test of CxoTime.  The base Time object is extremely well
tested, so this simply confirms that the add-on in CxoTime works.
"""

import pytest
import numpy as np

from cxotime import CxoTime

try:
    from Chandra.Time import DateTime
    HAS_DATETIME = True
except ImportError:
    HAS_DATETIME = False


def test_cxotime_basic():
    t = CxoTime(1)
    assert t.format == 'secs'
    assert t.scale == 'utc'
    assert np.allclose(t.secs, 1.0, rtol=1e-10, atol=0)
    assert t.tt.date == '1998:001:00:00:01.000'

    # Multi-dim input
    t = CxoTime([[1, 2], [3, 4]])
    assert t.shape == (2, 2)
    assert np.all(t.tt.date == [['1998:001:00:00:01.000', '1998:001:00:00:02.000'],
                                ['1998:001:00:00:03.000', '1998:001:00:00:04.000']])

    t = CxoTime('1998:001:00:00:01.000', scale='tt')
    assert t.scale == 'tt'
    assert np.allclose(t.secs, 1.0, atol=1e-10, rtol=0)


@pytest.mark.skipif('not HAS_DATETIME')
def test_cxotime_vs_datetime():
    dates = ('2015-06-30 23:59:60.5', '2015:180:01:02:03.456')
    for date in dates:
        assert np.allclose(CxoTime(date).secs, DateTime(date).secs,
                           atol=1e-4, rtol=0)
        assert CxoTime(CxoTime(date).secs).date == DateTime(DateTime(date).secs).date
