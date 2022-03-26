# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Simple test of CxoTime.  The base Time object is extremely well
tested, so this simply confirms that the add-on in CxoTime works.
"""

import pytest
import numpy as np

from .. import CxoTime, date2secs
from astropy.time import Time
from Chandra.Time import DateTime
import astropy.units as u


def test_cxotime_basic():
    t = CxoTime(1)
    assert t.format == 'secs'
    assert t.scale == 'utc'
    assert np.allclose(t.secs, 1.0, rtol=1e-10, atol=0)
    assert t.tt.yday == '1998:001:00:00:01.000'

    # Date is always UTC
    assert t.date == '1997:365:23:58:57.816'
    assert t.tt.date == '1997:365:23:58:57.816'

    # Multi-dim input
    t = CxoTime([[1, 2], [3, 4]], scale='utc')
    assert t.scale == 'utc'
    assert t.shape == (2, 2)
    t_tt_iso = [['1998-01-01 00:00:01.000', '1998-01-01 00:00:02.000'],
                ['1998-01-01 00:00:03.000', '1998-01-01 00:00:04.000']]
    assert np.all(t.tt.iso == t_tt_iso)
    assert np.all(t.date == t.yday)
    assert np.all(t.utc.iso == Time(t_tt_iso, format='iso', scale='tt').utc.iso)

    with pytest.raises(ValueError):
        t = CxoTime('1998:001:00:00:01.000', scale='tt')


@pytest.mark.parametrize('now_method', [CxoTime, CxoTime.now])
def test_cxotime_now(now_method):
    ct_now = now_method()
    t_now = Time.now()
    assert abs((ct_now - t_now).to_value(u.s)) < 0.1

    with pytest.raises(ValueError,
                       match='cannot supply keyword arguments with no time value'):
        CxoTime(scale='utc')


def test_cxotime_now_by_none():
    ct_now = CxoTime(None)
    t_now = Time.now()
    assert abs((ct_now - t_now).to_value(u.s)) < 0.1

    with pytest.raises(ValueError,
                       match='cannot supply keyword arguments with no time value'):
        CxoTime(None, scale='utc')


def test_cxotime_from_datetime():
    secs = DateTime(np.array(['2000:001', '2015:181:23:59:60.500', '2015:180:01:02:03.456'])).secs
    dts = DateTime(secs)
    ct = CxoTime(dts)
    assert ct.scale == 'utc'
    assert ct.format == 'date'

    for out_fmt in ('greta', 'secs', 'date', 'frac_year'):
        vals_out = getattr(ct, out_fmt)
        if vals_out.dtype.kind == 'U':
            assert np.all(vals_out == getattr(dts, out_fmt))
        else:
            assert np.allclose(vals_out, getattr(dts, out_fmt), atol=1e-4, rtol=0)


def test_cxotime_vs_datetime():
    # Note the bug (https://github.com/sot/Chandra.Time/issues/21), hence the odd first two lines
    # >>> DateTime('2015:181:23:59:60.500').date
    # '2015:182:00:00:00.500'
    secs = DateTime(np.array(['2000:001', '2015:181:23:59:60.500', '2015:180:01:02:03.456'])).secs
    dts = DateTime(secs)
    vals = dict(date=dts.date,
                secs=dts.secs,
                greta=dts.greta,
                frac_year=dts.frac_year)

    fmts = list(vals.keys())
    for in_fmt in fmts:
        ct = CxoTime(vals[in_fmt], format=in_fmt)
        assert ct.scale == 'utc'
        for out_fmt in fmts:
            vals_out = getattr(ct, out_fmt)
            if vals_out.dtype.kind == 'U':
                assert np.all(vals_out == vals[out_fmt])
            else:
                assert np.allclose(vals_out, vals[out_fmt], atol=1e-4, rtol=0)


def test_secs():
    """
    Test a problem fixed in https://github.com/astropy/astropy/pull/4312.
    This test would pass for ``t = CxoTime(1, scale='tt')`` or if
    comparing t.secs to 1.0.
    """
    t = CxoTime(1)
    assert t.scale == 'utc'
    assert np.allclose(t.value, 1.0, atol=1e-10, rtol=0)


def test_date():
    t = CxoTime('2001:002:03:04:05.678')
    assert t.format == 'date'
    assert t.scale == 'utc'

    # During leap second
    assert CxoTime('2015-06-30 23:59:60.5').date == '2015:181:23:59:60.500'


def test_arithmetic():
    """Very basic test of arithmetic"""
    t1 = CxoTime(0.0)
    t2 = CxoTime(86400.0)
    dt = t2 - t1
    assert np.allclose(dt.jd, 1.0)

    t3 = t2 + dt
    assert np.allclose(t3.secs, 172800.0)
    assert isinstance(t3, CxoTime)


def test_frac_year():
    t = CxoTime(2000.5, format='frac_year')
    assert t.date == '2000:184:00:00:00.000'
    t = CxoTime('2000:184:00:00:00.000')
    assert t.frac_year == 2000.5


@pytest.mark.parametrize('fmt', ['maude', 'greta'])
@pytest.mark.parametrize('number', [True, False])
@pytest.mark.parametrize('bytestr', [True, False])
def test_maude_and_greta(fmt, number, bytestr):
    """Test maude and greta formats"""
    def mg(val):
        """Munge greta-style string input to desired type for CxoTime init"""
        if fmt == 'greta':
            out = float(val) if number else val
        else:
            val = val[:7] + val[8:]
            out = int(val) if number else val
        if bytestr and isinstance(out, str):
            out = out.encode('ascii')
        return out

    def mgo(val):
        """Munge output to expected type for CxoTime output"""
        if fmt == 'greta':
            return val
        elif fmt == 'maude':
            return int(val[:7] + val[8:])

    t_in = [[mg('2001002.030405678'), mg('2002002.030405678')],
            [mg('2003002.030405678'), mg('2004002.030405678')]]
    val_out = [[mgo('2001002.030405678'), mgo('2002002.030405678')],
               [mgo('2003002.030405678'), mgo('2004002.030405678')]]
    t = CxoTime(t_in, format=fmt)
    assert t.format == fmt
    assert t.scale == 'utc'
    assert t.shape == (2, 2)
    assert np.all(t.yday == [['2001:002:03:04:05.678', '2002:002:03:04:05.678'],
                             ['2003:002:03:04:05.678', '2004:002:03:04:05.678']])
    assert np.all(t.value == val_out)

    # During leap second
    assert getattr(CxoTime('2015-06-30 23:59:60.5'), fmt) == mgo('2015181.235960500')
    assert CxoTime(mg('2015181.235960500'), format=fmt).date == '2015:181:23:59:60.500'


def test_scale_exception():
    with pytest.raises(ValueError, match="must use scale 'utc' for format 'secs'"):
        CxoTime(1, scale='tt')

    with pytest.raises(ValueError, match="must use scale 'utc' for format 'secs'"):
        CxoTime(1, format='secs', scale='tt')

    with pytest.raises(ValueError, match="must use scale 'utc' for format 'greta'"):
        CxoTime('2019123.123456789', scale='tt')

    with pytest.raises(ValueError, match="must use scale 'utc' for format 'greta'"):
        CxoTime('2019123.123456789', format='greta', scale='tt')

    with pytest.raises(ValueError, match="must use scale 'utc' for format 'date'"):
        CxoTime('2019:123', scale='tt')

    with pytest.raises(ValueError, match="must use scale 'utc' for format 'date'"):
        CxoTime('2019:123:12:13:14', format='date', scale='tt')


def test_strict_parsing():
    """Python strptime parsing allows single digits for mon, day, etc.

    CxoTime is stricter in the format requirements.
    """
    CxoTime('2000:001:1:2:3', format='yday')
    with pytest.raises(ValueError, match='Input values did not match the format class date'):
        CxoTime('2000:001:1:2:3', format='date')

    with pytest.raises(ValueError, match='Input values did not match the format class greta'):
        CxoTime('2000001.123', format='greta')


@pytest.mark.parametrize(
    'date',
    ['2001:002',
     '2001:002:03:04',
     '2001:002:03:04:05',
     '2001:002:03:04:05.678'])
def test_date2secs(date):
    t = CxoTime(date)
    t_secs = t.secs
    assert t_secs == date2secs(t.date)  # np.array U
    assert t_secs == date2secs(np.char.encode(t.date, 'ascii')) # np.array S
    assert t_secs == date2secs(date)  # str
    assert t_secs == date2secs(date.encode('ascii'))  # bytes

    date2 = str((t + 20 * u.s).date)
    date3 = str((t + 40 * u.s).date)
    dates = [[date, date2], [date3, date2]]
    t = CxoTime(dates)
    t_secs = t.secs
    assert np.all(t_secs == date2secs(t.date))  # np.array U
    assert np.all(t_secs == date2secs(np.char.encode(t.date, 'ascii')))  # np.array S
    assert np.all(t_secs == date2secs(dates))  # str
    assert np.all(t_secs == date2secs(np.char.encode(t.date, 'ascii')).tolist())  # bytes
    assert t_secs.shape == date2secs(dates).shape
