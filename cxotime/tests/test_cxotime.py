# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Simple test of CxoTime.  The base Time object is extremely well
tested, so this simply confirms that the add-on in CxoTime works.
"""
import pytest
import numpy as np

from .. import CxoTime, conf
from astropy.time import Time
from Chandra.Time import DateTime
import astropy.units as u


@pytest.fixture(scope='module', params=['True', 'False', 'force'])
def use_fast_parser(request):
    conf.use_fast_parser = request.param
    yield
    conf.use_fast_parser = 'True'


def test_cxotime_basic(use_fast_parser):
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


# @pytest.mark.parmetrize('use_fast_parser', ['True', 'False', 'force'])
# @pytest.mark.parametrize('now_method', [CxoTime, CxoTime.now])
# def test_cxotime_now(use_fast_parser, now_method):
#     with conf.set_temp('use_fast_parser', use_fast_parser):
#         _test_cxotime_basic(now_method)


@pytest.mark.parametrize('now_method', [CxoTime, CxoTime.now])
def test_cxotime_now(use_fast_parser, now_method):
    ct_now = now_method()
    t_now = Time.now()
    assert t_now >= ct_now
    assert (ct_now - t_now) < 10 * u.s

    with pytest.raises(ValueError,
                       match='cannot supply keyword arguments with no time value'):
        CxoTime(scale='utc')


def test_cxotime_from_datetime(use_fast_parser):
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


def test_cxotime_vs_datetime(use_fast_parser):
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


def test_secs(use_fast_parser):
    """
    Test a problem fixed in https://github.com/astropy/astropy/pull/4312.
    This test would pass for ``t = CxoTime(1, scale='tt')`` or if
    comparing t.secs to 1.0.
    """
    t = CxoTime(1)
    assert t.scale == 'utc'
    assert np.allclose(t.value, 1.0, atol=1e-10, rtol=0)


def test_date(use_fast_parser):
    t = CxoTime('2001:002:03:04:05.678')
    assert t.format == 'date'
    assert t.scale == 'utc'

    # During leap second
    assert CxoTime('2015-06-30 23:59:60.5').date == '2015:181:23:59:60.500'


def test_arithmetic(use_fast_parser):
    """Very basic test of arithmetic"""
    t1 = CxoTime(0.0)
    t2 = CxoTime(86400.0)
    dt = t2 - t1
    assert np.allclose(dt.jd, 1.0)

    t3 = t2 + dt
    assert np.allclose(t3.secs, 172800.0)
    assert isinstance(t3, CxoTime)


def test_frac_year(use_fast_parser):
    t = CxoTime(2000.5, format='frac_year')
    assert t.date == '2000:184:00:00:00.000'
    t = CxoTime('2000:184:00:00:00.000')
    assert t.frac_year == 2000.5


def test_greta(use_fast_parser):
    """Test greta format"""
    t_in = [['2001002.030405678', '2002002.030405678'],
            ['2003002.030405678', '2004002.030405678']]
    t = CxoTime(t_in)
    assert t.format == 'greta'
    assert t.scale == 'utc'
    assert t.shape == (2, 2)
    assert np.all(t.yday == [['2001:002:03:04:05.678', '2002:002:03:04:05.678'],
                             ['2003:002:03:04:05.678', '2004:002:03:04:05.678']])
    assert np.all(t.value == t_in)

    # Input from float
    t = CxoTime(np.array(t_in, dtype=np.float), format='greta')
    assert np.all(t.value == t_in)

    # During leap second
    assert CxoTime('2015-06-30 23:59:60.5').greta == '2015181.235960500'
    assert CxoTime('2015181.235960500').date == '2015:181:23:59:60.500'


def test_scale_exception(use_fast_parser):
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
