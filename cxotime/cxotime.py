# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
from copy import copy

from astropy.time import Time, TimeCxcSec, TimeYearDayTime, TimeDecimalYear
from astropy.utils import iers

# For working in Chandra operations, possibly with no network access, we cannot
# allow auto downloads.
iers.conf.auto_download = False


class CxoTime(Time):
    """Time class for Chandra analysis that is based on ``astropy.time.Time``.

    The CXO-specific time formats which are added to the astropy ``Time`` class
    are shown in the table below.  Like ``DateTime``, the ``CxoTime`` class
    default is to interpret any numerical values as ``secs`` (aka ``cxcsec`` in
    the native ``Time`` class).

    All of these formats use the UTC scale.

    ========= ===========================================
     Format   Description
    ========= ===========================================
    secs      Seconds since 1998-01-01T00:00:00 (TT)
    date      YYYY:DDD:hh:mm:ss.ss..
    frac_year YYYY.ffffff = date as a floating point year
    greta     YYYYDDD.hhmmsssss
    ========= ===========================================

    Important differences:

    - In ``CxoTime`` the date '2000:001' is '2000:001:00:00:00' instead of
      '2000:001:12:00:00' in ``DateTime``.  In most cases this interpretation
      is more rational and expected.

    - In ``CxoTime`` the date '2001-01-01T00:00:00' is UTC by default, while in
      ``DateTime`` that is interpreted as TT by default.  This is triggered by
      the ``T`` in the middle.  A date like '2001-01-01 00:00:00' defaults
      to UTC in both ``CxoTime`` and ``DateTime``.

    The standard built-in Time formats that are available in ``CxoTime`` are:

    ===========  ==============================
    Format       Example
    ===========  ==============================
    byear        1950.0
    byear_str    'B1950.0'
    cxcsec       63072064.184
    datetime     datetime(2000, 1, 2, 12, 0, 0)
    decimalyear  2000.45
    fits         '2000-01-01T00:00:00.000(TAI)'
    gps          630720013.0
    iso          '2000-01-01 00:00:00.000'
    isot         '2000-01-01T00:00:00.000'
    jd           2451544.5
    jyear        2000.0
    jyear_str    'J2000.0'
    mjd          51544.0
    plot_date    730120.0003703703
    unix         946684800.0
    yday         2000:001:00:00:00.000
    ===========  ==============================

    """
    def __new__(cls, *args, **kwargs):
        # Handle the case of `CxoTime()` which returns the current time. This is
        # for compatibility with DateTime.
        if not args:
            if not kwargs:
                args = (None, )
            else:
                raise ValueError('cannot supply keyword arguments with no time value')
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        if args:
            if args[0].__class__.__name__ == 'DateTime':
                if len(args) > 1:
                    raise ValueError('only one positional arg when DateTime is supplied')
                args = (args[0].date,)
                if kwargs.setdefault('scale', 'utc') != 'utc':
                    raise ValueError("must use scale 'utc' for DateTime input")
                if kwargs.setdefault('format', 'date') != 'date':
                    raise ValueError("must use format 'date' for DateTime input")
        else:
            # For `CxoTime()`` return the current time in `date` format.
            args = (Time.now().yday, )

        # If format is supplied and is a DateTime format then require scale='utc'.
        fmt = kwargs.get('format')

        # Define special formats and the type of vals that are accepted
        fmts_datetime = ('greta', 'secs', 'date', 'frac_year')
        fmt_dtypes = (np.character, np.number, np.character, np.number)

        # Check that scale=UTC for special formats
        if fmt in fmts_datetime and kwargs.setdefault('scale', 'utc') != 'utc':
            raise ValueError(f"must use scale 'utc' for format '{fmt}''")

        # If format is not supplied and one arg (val) supplied then guess format
        # in DateTime-compatibility mode. That means forcing scale to UTC.
        if fmt is None and len(args) == 1:
            kwargs_orig = copy(kwargs)
            kwargs['scale'] = 'utc'
            # Do not make a copy unless specifically set by user
            kwargs.setdefault('copy', False)
            # Convert to np.array at this point to get dtype
            val = np.asarray(args[0])

            for fmt, fmt_dtype in zip(fmts_datetime, fmt_dtypes):
                if not issubclass(val.dtype.type, fmt_dtype):
                    continue

                kwargs['format'] = fmt
                try:
                    super(CxoTime, self).__init__(*args, **kwargs)
                except Exception:
                    pass
                else:
                    if kwargs_orig.get('scale', 'utc') != 'utc':
                        raise ValueError(f"must use scale 'utc' for format '{fmt}''")
                    return
            kwargs = kwargs_orig

        super(CxoTime, self).__init__(*args, **kwargs)

    @classmethod
    def now(cls):
        return cls()

    now.__doc__ = Time.now.__doc__


class TimeSecs(TimeCxcSec):
    """
    Chandra X-ray Center seconds from 1998-01-01 00:00:00 TT.
    For example, 63072064.184 is midnight on January 1, 2000.
    """
    name = 'secs'


class TimeDate(TimeYearDayTime):
    """
    Year, day-of-year and time as "YYYY:DOY:HH:MM:SS.sss..." in UTC.

    The day-of-year (DOY) goes from 001 to 365 (366 in leap years).
    For example, 2000:001:00:00:00.000 is midnight on January 1, 2000.

    Time value in this format is always UTC regardless of the time scale
    of the time object.  For example::

      >>> t = CxoTime('2000-01-01', scale='tai')
      >>> t.iso
      '2000-01-01 00:00:00.000'
      >>> t.date
      '1999:365:23:59:28.000'

    The allowed subformats are:

    - 'date_hms': date + hours, mins, secs (and optional fractional secs)
    - 'date_hm': date + hours, mins
    - 'date': date
    """
    name = 'date'

    def to_value(self, parent=None, **kwargs):
        if self.scale == 'utc':
            return super().value
        else:
            return parent.utc._time.value

    value = property(to_value)


class TimeFracYear(TimeDecimalYear):
    """
    Time as a decimal year, with integer values corresponding to midnight
    of the first day of each year.  For example 2000.5 corresponds to the
    ISO time '2000-07-02 00:00:00'.

    Time value is always in UTC regardless of time object scale.
    """
    name = 'frac_year'

    def to_value(self, parent=None, **kwargs):
        if self.scale == 'utc':
            return super().value
        else:
            return parent.utc._time.value

    value = property(to_value)


class TimeGreta(TimeDate):
    """
    Date in format YYYYDDD.hhmmsssss, where sssss is number of milliseconds.

    Time value is always in UTC regardless of time object scale.
    """
    name = 'greta'

    subfmts = (('date_hms',
                '%Y%j%H%M%S',
                '{year:d}{yday:03d}{hour:02d}{min:02d}{sec:02d}'),)

    def _check_val_type(self, val1, val2):
        # Note: don't care about val2 for these classes
        if val1.dtype.kind not in ('S', 'U', 'i', 'f'):
            raise TypeError('Input values for {0} class must be strings or numbers'
                            .format(self.name))
        return val1, None

    def set_jds(self, val1, val2):
        """
        Remake the input to a form that standard parsing will work with.
        """
        shape = val1.shape

        # Allow for float input
        if val1.dtype.kind in ('f', 'i'):
            val1 = np.array(['{:.9f}'.format(x) for x in val1.flat])

        # Reformat from YYYYDDD.HHMMSSsss to YYYYDDDHHMMSS.sss
        val1 = np.array([x[:7] + x[8:14] + '.' + x[14:] for x in val1.flat])

        super(TimeGreta, self).set_jds(val1.reshape(shape), val2)

    def to_value(self, parent=None, **kwargs):
        if self.scale == 'utc':
            out1 = super().value
        else:
            out1 = parent.utc._time.value
        out = np.array([x[:7] + '.' + x[7:13] + x[14:] for x in out1.flat])
        out.shape = out1.shape
        return out

    value = property(to_value)
