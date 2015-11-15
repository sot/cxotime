from copy import copy

from astropy.time import Time, TimeCxcSec, TimeYearDayTime


class CxoTime(Time):
    """Time class for Chandra analysis that is based on astropy.time.Time.

    The CXO-specific time formats which are added to the astroy ``Time`` class
    are shown in the table below.  Like ``DateTime``, the ``CxoTime`` class
    default is to interpret any numerical values as ``secs`` (aka ``cxcsec`` in
    the native ``Time`` class).

    ============ ==============================================  =======
     Format      Description                                     System
    ============ ==============================================  =======
    secs         Seconds since 1998-01-01T00:00:00 (float)       tt
    date         YYYY:DDD:hh:mm:ss.ss..                          utc
    ============ ==============================================  =======
        
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
    def __init__(self, *args, **kwargs):
        # If format is not supplied then start off guessing with 'secs' and 'date'
        # formats.  For both of those default to UTC scale.  In particular for
        # 'secs' the default scale would be TT, which then produces surprising
        # results (for DateTime users) when converting to most other formats which
        # default to UTC scale.
        if kwargs.get('format') is None:
            kwargs_orig = copy(kwargs)
            if 'scale' not in kwargs:
                kwargs['scale'] = 'utc'

            for kwargs['format'] in ('secs', 'date'):
                try:
                    super(CxoTime, self).__init__(*args, **kwargs)
                    return
                except:
                    pass

            kwargs = kwargs_orig

        super(CxoTime, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.date


class TimeSecs(TimeCxcSec):
    """
    Chandra X-ray Center seconds from 1998-01-01 00:00:00 TT.
    For example, 63072064.184 is midnight on January 1, 2000.
    """
    name = 'secs'


class TimeDate(TimeYearDayTime):
    """
    Year, day-of-year and time as "YYYY:DOY:HH:MM:SS.sss...".
    The day-of-year (DOY) goes from 001 to 365 (366 in leap years).
    For example, 2000:001:00:00:00.000 is midnight on January 1, 2000.

    The allowed subformats are:

    - 'date_hms': date + hours, mins, secs (and optional fractional secs)
    - 'date_hm': date + hours, mins
    - 'date': date
    """
    name = 'date'
