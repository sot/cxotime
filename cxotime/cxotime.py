# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
from copy import copy
from pathlib import Path
import warnings
import datetime

import numpy.ctypeslib as npct
from ctypes import c_int

from astropy.time import Time, TimeCxcSec, TimeYearDayTime, TimeDecimalYear
from astropy.time.utils import day_frac
from astropy.utils import iers
# in astropy versions < 4.2, erfa was an astropy private package:
try:
    import erfa
except ModuleNotFoundError:
    from astropy import _erfa as erfa

# Globally ignore the ERFA dubious year warning that gets emitted for UTC dates
# either before around 1950 or well after the last known leap second. This
# warning is conservatively indicating that UTC is not well-defined in those
# regimes, but we don't care.
warnings.filterwarnings('ignore', category=erfa.ErfaWarning, message=r'.*dubious year')

# For working in Chandra operations, possibly with no network access, we cannot
# allow auto downloads.
iers.conf.auto_download = False

# Input types in the parse_times.c code
array_1d_char = npct.ndpointer(dtype=np.uint8, ndim=1, flags='C_CONTIGUOUS')
array_1d_double = npct.ndpointer(dtype=np.double, ndim=1, flags='C_CONTIGUOUS')
array_1d_int = npct.ndpointer(dtype=np.intc, ndim=1, flags='C_CONTIGUOUS')

# load the library, using numpy mechanisms
libpt = npct.load_library("parse_times", Path(__file__).parent)

# Set up the return types and argument types for parse_ymdhms_times()
# int parse_ymdhms_times(char *times, int n_times, int max_str_len,
#                    char *delims, int *starts, int *stops, int *break_allowed,
#                    int *years, int *months, int *days, int *hours,
#                    int *minutes, double *seconds)
libpt.parse_ymdhms_times.restype = c_int
libpt.parse_ymdhms_times.argtypes = [array_1d_char, c_int, c_int, c_int,
                                     array_1d_char, array_1d_int, array_1d_int, array_1d_int,
                                     array_1d_int, array_1d_int, array_1d_int,
                                     array_1d_int, array_1d_int, array_1d_double]
libpt.check_unicode.restype = c_int

# Set up returns types and args for the unicode checker
libpt.check_unicode.argtypes = [array_1d_char, c_int]


def date2secs(date):
    """Fast conversion from Year Day-of-Year date(s) to CXC seconds

    This is a specialized function that allows for fast conversion of a single
    date or an array of dates to CXC seconds.  It is intended to be used ONLY
    when the input date is known to be in the correct Year Day-of-Year format.

    The main use case is for a single date or a few dates. For a single date
    this function is about 10 times faster than the equivalent call to
    ``CxoTime(date).secs``. For a large array of dates (more than about 100)
    this function is not significantly faster.

    This function will raise an exception if the input date is not in one of
    these allowed formats:

    - YYYY:DDD
    - YYYY:DDD:HH:MM
    - YYYY:DDD:HH:MM:SS
    - YYYY:DDD:HH:MM:SS.sss

    :param date: str, list of str, bytes, list of bytes, np.ndarray Input
        date(s) in an allowed year-day-of-year date format
    :returns: float, np.ndarray CXC seconds matching dimensions of input date(s)
    """
    # This code is adapted from the underlying code in astropy time, with some
    # of the general-purpose handling and validation removed.
    from astropy.time.formats import TimeYearDayTime
    from astropy.time import _parse_times

    # Handle bytes or str input and convert to uint8.  We need to the
    # dtype _parse_times.dt_u1 instead of uint8, since otherwise it is
    # not possible to create a gufunc with structured dtype output.
    # See note about ufunc type resolver in pyerfa/erfa/ufunc.c.templ.
    date = np.asarray(date)
    if date.dtype.kind == 'U':
        # This assumes the input is pure ASCII.
        val1_uint32 = date.view((np.uint32, date.dtype.itemsize // 4))
        chars = val1_uint32.astype(_parse_times.dt_u1)
    else:
        chars = date.view((_parse_times.dt_u1, date.dtype.itemsize))

    # Call the fast parsing ufunc.
    time_struct = TimeYearDayTime._fast_parser(chars)

    # In these ERFA calls ignore the return value since we know jd1, jd2 are OK.
    # Checking the return value via np.any nearly doubles the function time.

    # Convert time ISO date to jd1, jd2
    jd1, jd2, _ = erfa.ufunc.dtf2d(
        b'UTC',
        time_struct['year'],
        time_struct['month'],
        time_struct['day'],
        time_struct['hour'],
        time_struct['minute'],
        time_struct['second'])

    # Transform to TT via TAI
    jd1, jd2, _ = erfa.ufunc.utctai(jd1, jd2)
    jd1, jd2, _ = erfa.ufunc.taitt(jd1, jd2)

    # Fixed offsets taken from CxoTime(0.0).tt.jd1,2
    time_from_epoch1 = (jd1 - 2450814.0) * 86400.0
    time_from_epoch2 = (jd2 - 0.5) * 86400.0

    return time_from_epoch1 + time_from_epoch2


def secs2date(secs):
    """Fast conversion from CXC seconds to Year Day-of-Year date(s)

    This is a specialized function that allows for fast conversion of one or
    more CXC seconds times to Year Day-of-Year format.

    The main use case is for a single date or a few dates. For a single date
    this function is about 15-20 times faster than the equivalent call to
    ``CxoTime(secs).date``. For a large array of dates (more than about 100)
    this function is not significantly faster.

    :param secs: float, list of float, np.ndarray
        Input time(s) in CXC seconds
    :returns: str, np.ndarray of str
        Year Day-of-Year dates matching dimensions of input time(s)
    """
    # This code is adapted from the underlying code in astropy time, with some
    # of the general-purpose handling and validation removed.

    # For scalars use a specialized version that is about 30% faster.
    if (isinstance(secs, float)
            or isinstance(secs, np.ndarray) and secs.shape == ()):
        return _secs2date_scalar(secs)

    secs = np.asarray(secs, dtype=np.float64)
    jd1 = secs / 86400.0 + 2450814.5
    jd2 = 0.0

    # In these ERFA calls ignore the return value since we know jd1, jd2 are OK.
    # Checking the return value via np.any is quite slow.
    # Transform TT to UTC via TAI
    jd1, jd2, _ = erfa.ufunc.tttai(jd1, jd2)
    jd1, jd2, _ = erfa.ufunc.taiutc(jd1, jd2)

    dates = []
    iys, ims, ids, ihmsfs = erfa.d2dtf(b'TT', 3, jd1, jd2)
    ihrs = ihmsfs['h']
    imins = ihmsfs['m']
    isecs = ihmsfs['s']
    ifracs = ihmsfs['f']
    for iy, im, id, ihr, imin, isec, ifracsec in np.nditer(
            [iys, ims, ids, ihrs, imins, isecs, ifracs],
            flags=['zerosize_ok']):
        yday = datetime.datetime(iy, im, id).timetuple().tm_yday
        date = f'{iy:4d}:{yday:03d}:{ihr:02d}:{imin:02d}:{isec:02d}.{ifracsec:03d}'
        dates.append(date)

    out = np.array(dates).reshape(secs.shape)
    return out


def _secs2date_scalar(secs):
    """Internal version of secs2date for scalar input

    Same as secs2date but with the array handling removed. This is around 30%
    faster.
    """
    jd1 = secs / 86400.0 + 2450814.5
    jd2 = 0.0

    jd1, jd2, _ = erfa.ufunc.tttai(jd1, jd2)
    jd1, jd2, _ = erfa.ufunc.taiutc(jd1, jd2)

    iy, im, id, ihmsfs = erfa.d2dtf(b'TT', 3, jd1, jd2)
    ihr = ihmsfs['h']
    imin = ihmsfs['m']
    isec = ihmsfs['s']
    ifracsec = ihmsfs['f']
    yday = datetime.datetime(iy, im, id).timetuple().tm_yday
    date = f'{iy:4d}:{yday:03d}:{ihr:02d}:{imin:02d}:{isec:02d}.{ifracsec:03d}'

    return date


class CxoTime(Time):
    """Time class for Chandra analysis that is based on ``astropy.time.Time``.

    The CXO-specific time formats which are added to the astropy ``Time`` class
    are shown in the table below.  Like ``DateTime``, the ``CxoTime`` class
    default is to interpret any numerical values as ``secs`` (aka ``cxcsec`` in
    the native ``Time`` class).

    All of these formats use the UTC scale.

    ========= ==============================================
     Format   Description
    ========= ==============================================
    secs      Seconds since 1998-01-01T00:00:00 (TT) (float)
    date      YYYY:DDD:hh:mm:ss.ss.. (string)
    frac_year YYYY.ffffff = date as a floating point year
    greta     YYYYDDD.hhmmsss (string)
    muade     YYYDDDhhmmsss (integer)
    ========= ==============================================

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
        if not args or (len(args) == 1 and args[0] is None):
            if not kwargs:
                # Stub in a value for `val` so super()__new__ can run since `val`
                # is a required positional arg.
                args = (None, )
            else:
                raise ValueError('cannot supply keyword arguments with no time value')
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and args[0] is None:
            # Compatibility with DateTime and allows kwarg default of None with
            # input casting like `date = CxoTime(date)`.
            args = ()

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

        # Define special formats for guessing and type of accepted vals
        fmts_datetime = ('greta', 'secs', 'date', 'maude')
        fmt_dtypes = (np.character, np.number, np.character, np.character)

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

        elif fmt == 'maude':
            args = (np.asarray(args[0], dtype='S'),) + args[1:]

        super(CxoTime, self).__init__(*args, **kwargs)

    @classmethod
    def now(cls):
        return cls()

    now.__doc__ = Time.now.__doc__


class FastDateParserMixin:

    def set_jds_fast(self, val1):
        """Use fast C parser to parse time strings in val1 and set jd1, jd2"""
        # Handle bytes or str input and flatten down to a single array of uint8.
        char_size = 4 if val1.dtype.kind == 'U' else 1
        val1_str_len = int(val1.dtype.itemsize // char_size)
        chars = val1.ravel().view(np.uint8)

        if char_size == 4:
            # Check that this is pure ASCII
            status = libpt.check_unicode(chars, len(chars) // 4)
            if status != 0:
                raise ValueError('input is not pure ASCII')
            # It might be possible to avoid this copy with cleverness in
            # parse_times.c but leave that for another day.
            chars = chars[::4]
        chars = np.ascontiguousarray(chars)

        # Pre-allocate output components
        n_times = len(chars) // val1_str_len
        year = np.zeros(n_times, dtype=np.intc)
        month = np.zeros(n_times, dtype=np.intc)
        day = np.zeros(n_times, dtype=np.intc)
        hour = np.zeros(n_times, dtype=np.intc)
        minute = np.zeros(n_times, dtype=np.intc)
        second = np.zeros(n_times, dtype=np.double)

        # Set up parser parameters as numpy arrays for passing to C parser
        delims = np.array(self.delims, dtype=np.uint8)
        starts = np.array(self.starts, dtype=np.intc)
        stops = np.array(self.stops, dtype=np.intc)
        break_allowed = np.array(self.break_allowed, dtype=np.intc)

        # Call C parser
        status = libpt.parse_ymdhms_times(chars, n_times, val1_str_len, self.has_day_of_year,
                                          delims, starts, stops, break_allowed,
                                          year, month, day, hour, minute, second)
        if status == 0:
            # All went well, finish the job
            jd1, jd2 = erfa.dtf2d(self.scale.upper().encode('ascii'),
                                  year, month, day, hour, minute, second)
            jd1.shape = val1.shape
            jd2.shape = val1.shape
            self.jd1, self.jd2 = day_frac(jd1, jd2)
        else:
            msgs = {1: 'time string ends at beginning of component where break is not allowed',
                    2: 'time string ends in middle of component',
                    3: 'required delimiter character not found',
                    4: 'non-digit found where digit (0-9) required',
                    5: 'bad day of year (1 <= doy <= 365 or 366 for leap year'}
            raise ValueError(f'fast C time string parser failed: {msgs[status]}')


class TimeSecs(TimeCxcSec):
    """
    Chandra X-ray Center seconds from 1998-01-01 00:00:00 TT.
    For example, 63072064.184 is midnight on January 1, 2000.
    """
    name = 'secs'


class TimeDate(TimeYearDayTime, FastDateParserMixin):
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

    # Class attributes for fast C-parsing
    delims = (0, 0, ord(':'), ord(':'), ord(':'), ord(':'), ord('.'))
    starts = (0, -1, 4, 8, 11, 14, 17)
    stops = (3, -1, 7, 10, 13, 16, -1)
    # Break before:  y  m  d  h  m  s  f
    break_allowed = (0, 0, 0, 1, 0, 1, 1)
    has_day_of_year = 1

    def to_value(self, parent=None, **kwargs):
        if self.scale == 'utc':
            return super().value
        else:
            return parent.utc._time.value

    value = property(to_value)

    def set_jds(self, val1, val2):
        """Parse the time strings contained in val1 and set jd1, jd2"""
        if val2 is not None:
            raise ValueError(f'cannot supply val2 for {self.name} format')
        self.set_jds_fast(val1)


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


class TimeGreta(TimeDate, FastDateParserMixin):
    """
    Date as a string in format 'YYYYDDD.hhmmsssss', where sssss is number of
    milliseconds.

    This can be input as a float, integer or string, but the output is always
    string.

    Time value is always in UTC regardless of time object scale.
    """
    name = 'greta'

    subfmts = (('date_hms',
                '%Y%j%H%M%S',
                '{year:d}{yday:03d}{hour:02d}{min:02d}{sec:02d}'),)

    # Define positions and starting delimiter for year, month, day, hour,
    # minute, seconds components of an ISO time. This is used by the fast
    # C-parser parse_ymdhms_times()
    #
    #  "2000123.131415678"
    #   01234567890123456
    #   yyyyddd.hhmmssfff
    # Parsed as ('yyyy', 'ddd', '.hh', 'mm', 'ss', 'fff')
    #
    # delims: character at corresponding `starts` position (0 => no character)
    # starts: position where component starts (including delimiter if present)
    # stops: position where component ends (-1 => continue to end of string)

    # Before: yr mon  doy     hour      minute    second    frac
    delims = (0, 0, 0, ord('.'), 0, 0, 0)
    starts = (0, -1, 4, 7, 10, 12, 14)
    stops = (3, -1, 6, 9, 11, 13, -1)
    # Break before:  y  m  d  h  m  s  f
    break_allowed = (0, 0, 0, 1, 0, 1, 1)
    has_day_of_year = 1

    def _check_val_type(self, val1, val2):
        if val2 is not None:
            raise ValueError(f'cannot supply val2 for {self.name} format')

        if val1.dtype.kind not in ('S', 'U', 'i', 'f'):
            raise TypeError('Input values for {0} class must be string or number'
                            .format(self.name))
        return val1, None

    def set_jds(self, val1, val2):
        """Parse the time strings contained in val1 and set jd1, jd2"""
        # If specific input subformat is required then use the Python parser.
        # Also do this if Time format class does not define `use_fast_parser`
        # or if the fast parser is entirely disabled.
        # Allow for float input
        if val1.dtype.kind in ('f', 'i'):
            val1 = np.array(['{:.9f}'.format(x) for x in val1.flat]).reshape(val1.shape)

        self.set_jds_fast(val1)

    def to_value(self, parent=None, **kwargs):
        if self.scale == 'utc':
            out1 = super().value
        else:
            out1 = parent.utc._time.value
        out = np.array([x[:7] + '.' + x[7:13] + x[14:] for x in out1.flat])
        out.shape = out1.shape
        return out

    value = property(to_value)


class TimeMaude(TimeDate, FastDateParserMixin):
    """
    Date as a 64-bit integer in format YYYYDDDhhmmsss, where sss is number of
    milliseconds.

    This can be input as an integer or string, but the output is always integer.

    Time value is always in UTC regardless of time object scale.
    """
    name = 'maude'

    subfmts = (('date_hms',
                '%Y%j%H%M%S',
                '{year:d}{yday:03d}{hour:02d}{min:02d}{sec:02d}'),)

    # Define positions and starting delimiter for year, month, day, hour,
    # minute, seconds components of an ISO time. This is used by the fast
    # C-parser parse_ymdhms_times()
    #
    #  "2000123131415678"
    #   0123456789012345
    #   yyyydddhhmmssfff
    # Parsed as ('yyyy', 'ddd', 'hh', 'mm', 'ss', 'fff')
    #
    # delims: character at corresponding `starts` position (0 => no character)
    # starts: position where component starts (including delimiter if present)
    # stops: position where component ends (-1 => continue to end of string)

    # Before: yr mon  doy     hour      minute    second    frac
    use_fast_parser = True
    delims = (0, 0, 0, 0, 0, 0, 0)
    starts = (0, -1, 4, 7, 9, 11, 13)
    stops = (3, -1, 6, 8, 10, 12, -1)
    # Break before:  y  m  d  h  m  s  f
    break_allowed = (0, 0, 0, 1, 0, 1, 1)
    has_day_of_year = 1

    def _check_val_type(self, val1, val2):
        if val2 is not None:
            raise ValueError(f'cannot supply val2 for {self.name} format')

        if val1.dtype.kind not in ('S', 'U', 'i'):
            raise TypeError('Input values for {0} class must be string or int'
                            .format(self.name))

        if val1.dtype.kind == 'i':
            val1 = val1.astype('S')

        return val1, None

    def set_jds(self, val1, val2):
        """Parse the time strings contained in val1 and set jd1, jd2"""
        self.set_jds_fast(val1)

    def to_value(self, parent=None, **kwargs):
        if self.scale == 'utc':
            out = super().value
        else:
            out = parent.utc._time.value
        out = np.array([x[:13] + x[14:] for x in out.flat]).reshape(out.shape)
        out = out.astype('i8')

        return out

    value = property(to_value)
