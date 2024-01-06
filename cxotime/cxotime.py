# Licensed under a 3-clause BSD style license - see LICENSE.rst
import sys
import warnings
from copy import copy
from typing import Union

import erfa
import numpy as np
import numpy.typing as npt
from astropy.time import Time, TimeCxcSec, TimeDecimalYear, TimeJD, TimeYearDayTime
from astropy.utils import iers
from ska_helpers.utils import TypedDescriptor

__all__ = ["CxoTime", "CxoTimeLike", "CxoTimeDescriptor"]


# TODO: use npt.NDArray with numpy 1.21
CxoTimeLike = Union["CxoTime", str, float, int, np.ndarray, npt.ArrayLike, None]

# Globally ignore the ERFA dubious year warning that gets emitted for UTC dates
# either before around 1950 or well after the last known leap second. This
# warning is conservatively indicating that UTC is not well-defined in those
# regimes, but we don't care.
warnings.filterwarnings("ignore", category=erfa.ErfaWarning, message=r".*dubious year")

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

    # Sentinel object for CxoTime(CxoTime.NOW) to return the current time. See e.g.
    # https://python-patterns.guide/python/sentinel-object/.
    NOW = object()

    def __new__(cls, *args, **kwargs):
        # Handle the case of `CxoTime()`, `CxoTime(None)`, or `CxoTime(CxoTime.NOW)`,
        # all of which return the current time. This is for compatibility with DateTime.
        if not args or (len(args) == 1 and (args[0] is None or args[0] is CxoTime.NOW)):
            if not kwargs:
                # Stub in a value for `val` so super()__new__ can run since `val`
                # is a required positional arg. NOTE that this change to args here does
                # not affect the args in the call to __init__() below.
                args = (None,)
            else:
                raise ValueError("cannot supply keyword arguments with no time value")

        if len(args) == 1 and isinstance(args[0], CxoTime) and not kwargs:
            # If input is already a CxoTime instance and no other kwargs just return
            # the instance. Note that copy=False is the default.
            return args[0]

        return super().__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], CxoTime) and not kwargs:
            # If input is already a CxoTime instance and no other kwargs (which
            # implies copy=False) then no other initialization is needed.
            return

        if len(args) == 1 and (args[0] is None or args[0] is CxoTime.NOW):
            # Compatibility with DateTime and allows kwarg default of None with
            # input casting like `date = CxoTime(date)`.
            args = ()

        if args:
            if args[0].__class__.__name__ == "DateTime":
                if len(args) > 1:
                    raise ValueError(
                        "only one positional arg when DateTime is supplied"
                    )
                args = (args[0].date,)
                if kwargs.setdefault("scale", "utc") != "utc":
                    raise ValueError("must use scale 'utc' for DateTime input")
                if kwargs.setdefault("format", "date") != "date":
                    raise ValueError("must use format 'date' for DateTime input")
        else:
            # For `CxoTime()`` return the current time in `date` format.
            args = (Time.now().yday,)

        # If format is supplied and is a DateTime format then require scale='utc'.
        fmt = kwargs.get("format")

        # Define special formats for guessing and type of accepted vals
        fmts_datetime = ("greta", "secs", "date", "maude")
        fmt_dtypes = (np.character, np.number, np.character, np.character)

        # Check that scale=UTC for special formats
        if fmt in fmts_datetime and kwargs.setdefault("scale", "utc") != "utc":
            raise ValueError(f"must use scale 'utc' for format '{fmt}''")

        # If format is not supplied and one arg (val) supplied then guess format
        # in DateTime-compatibility mode. That means forcing scale to UTC.
        if fmt is None and len(args) == 1:
            kwargs_orig = copy(kwargs)
            kwargs["scale"] = "utc"
            # Do not make a copy unless specifically set by user
            kwargs.setdefault("copy", False)
            # Convert to np.array at this point to get dtype
            val = np.asarray(args[0])

            for fmt, fmt_dtype in zip(fmts_datetime, fmt_dtypes):
                if not issubclass(val.dtype.type, fmt_dtype):
                    continue

                kwargs["format"] = fmt
                try:
                    super(CxoTime, self).__init__(*args, **kwargs)
                except Exception:
                    pass
                else:
                    if kwargs_orig.get("scale", "utc") != "utc":
                        raise ValueError(f"must use scale 'utc' for format '{fmt}''")
                    return
            kwargs = kwargs_orig

        elif fmt == "maude":
            args = (np.asarray(args[0], dtype="S"),) + args[1:]

        super(CxoTime, self).__init__(*args, **kwargs)

    @classmethod
    def now(cls):
        return cls()

    now.__doc__ = Time.now.__doc__

    def print_conversions(self, file=sys.stdout):
        """
        Print a table of conversions to a standard set of formats.

        Example::

           >>> from cxotime import CxoTime
           >>> t = CxoTime('2010:001:00:00:00')
           >>> t.print_conversions()
           local       2009 Thu Dec 31 07:00:00 PM EST
           iso_local   2009-12-31T19:00:00-05:00
           date        2010:001:00:00:00.000
           cxcsec      378691266.184
           decimalyear 2010.00000
           iso         2010-01-01 00:00:00.000
           unix        1262304000.000

        :param file: file-like, optional
            File-like object to write output (default=sys.stdout).
        """
        from astropy.table import Table

        formats = {
            "cxcsec": ".3f",
            "decimalyear": ".5f",
            "unix": ".3f",
        }

        conversions = self.get_conversions()

        # Format numerical values as strings with specified precision
        for name, fmt in formats.items():
            conversions[name] = format(conversions[name], fmt)

        formats = list(conversions)
        values = list(conversions.values())
        out = Table([formats, values], names=["format", "value"])
        out["format"].info.format = "<s"
        out["value"].info.format = "<s"

        # Remove the header and print
        lines = out.pformat_all()[2:]
        print("\n".join(lines), file=file)

    def get_conversions(self):
        """
        Get a dict of conversions to a standard set of formats.

        Example::

           >>> from cxotime import CxoTime
           >>> t = CxoTime('2010:001:00:00:00')
           >>> t.get_conversions()
           {'local': '2009 Thu Dec 31 07:00:00 PM EST',
           'iso_local': '2009-12-31T19:00:00-05:00',
           'date': '2010:001:00:00:00.000',
           'cxcsec': 378691266.184,
           'decimalyear': 2010.0,
           'iso': '2010-01-01 00:00:00.000',
           'unix': 1262304000.0}
        """
        from datetime import timezone

        out = {}

        dt_local = self.datetime.replace(tzinfo=timezone.utc).astimezone(tz=None)
        out["local"] = dt_local.strftime("%Y %a %b %d %I:%M:%S %p %Z")
        out["iso_local"] = dt_local.isoformat()

        for name in ["date", "cxcsec", "decimalyear", "iso", "unix"]:
            out[name] = getattr(self, name)

        return out


TimeJD.convert_doc = {
    "input_name": "jd",
    "descr_short": "Julian Date",
    "input_format": "Julian Date (numeric)",
    "output_format": "Julian Date (numeric)",
    "input_type": "float, int, list, ndarray",
    "output_type": "float, ndarray[float]",
}


class TimeSecs(TimeCxcSec):
    """Chandra X-ray Center seconds from 1998-01-01 00:00:00 TT.

    For example, 63072064.184 is midnight on January 1, 2000.
    """

    name = "secs"

    # Documentation inputs for convert functions
    convert_doc = {
        "input_name": "time",
        "descr_short": "CXC seconds",
        "input_format": "CXC seconds (numeric)",
        "output_format": "CXC seconds (numeric)",
        "input_type": "float, int, list, ndarray",
        "output_type": "float, ndarray[float]",
    }


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

    name = "date"

    # Documentation inputs for convert functions
    convert_doc = {
        "input_name": "date",
        "descr_short": "Date (Year, day-of-year, time)",
        "input_format": """
    - YYYY:DDD:HH:MM:SS.sss
    - YYYY:DDD:HH:MM:SS
    - YYYY:DDD:HH:MM
    - YYYY:DDD""",
        "output_format": "YYYY:DDD:HH:MM:SS.sss",
        "input_type": "str, bytes, float, list, ndarray",
        "output_type": "str, ndarray[str]",
    }

    def to_value(self, parent=None, **kwargs):
        if self.scale == "utc":
            return super().value
        else:
            return parent.utc._time.value

    value = property(to_value)

    def set_jds(self, val1, val2):
        """Parse the time strings contained in val1 and set jd1, jd2"""
        if val2 is not None:
            raise ValueError(f"cannot supply val2 for {self.name} format")
        self.jd1, self.jd2 = self.get_jds_fast(val1, val2)


class TimeFracYear(TimeDecimalYear):
    """Time as a decimal year.

    Integer values corresponding to midnight of the first day of each year.  For example
    2000.5 corresponds to the ISO time '2000-07-02 00:00:00'.

    Time value is always in UTC regardless of time object scale.
    """

    name = "frac_year"

    def to_value(self, parent=None, **kwargs):
        if self.scale == "utc":
            return super().value
        else:
            return parent.utc._time.value

    value = property(to_value)


class TimeGreta(TimeDate):
    """Date as string in format 'YYYYDDD.hhmmsssss'.

    Here sssss is the number of millisec.

    This can be input as a float, integer or string, but the output is always string.

    Time value is always in UTC regardless of time object scale.
    """

    name = "greta"

    # Documentation inputs for convert functions
    convert_doc = {
        "input_name": "date",
        "descr_short": "GRETA date",
        "input_format": "YYYYDDD.HHMMSSsss (str or float)",
        "output_format": "YYYYDDD.HHMMSSsss (str)",
        "input_type": "str, bytes, float, list, np.ndarray",
        "output_type": "str, np.ndarray[str]",
    }

    subfmts = (
        ("date_hms", "%Y%j%H%M%S", "{year:d}{yday:03d}{hour:02d}{min:02d}{sec:02d}"),
    )

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

    fast_parser_pars = {
        "delims": (0, 0, 0, ord("."), 0, 0, 0),
        "starts": (0, -1, 4, 7, 10, 12, 14),
        "stops": (3, -1, 6, 9, 11, 13, -1),
        # Break before:  y  m  d  h  m  s  f
        "break_allowed": (0, 0, 0, 1, 0, 1, 1),
        "has_day_of_year": 1,
    }

    def _check_val_type(self, val1, val2):
        if val2 is not None:
            raise ValueError(f"cannot supply val2 for {self.name} format")

        if val1.dtype.kind not in ("S", "U", "i", "f"):
            raise TypeError(
                "Input values for {0} class must be string or number".format(self.name)
            )

        if val1.dtype.kind in ("f", "i"):
            val1 = np.array(["{:.9f}".format(x) for x in val1.flat]).reshape(val1.shape)

        return val1, None

    def to_value(self, parent=None, **kwargs):
        if self.scale == "utc":
            out1 = super().value
        else:
            out1 = parent.utc._time.value
        out = np.array([x[:7] + "." + x[7:13] + x[14:] for x in out1.flat])
        out.shape = out1.shape
        return out

    value = property(to_value)


class TimeMaude(TimeDate):
    """Date as a 64-bit integer in format YYYYDDDHHMMSSsss.

    Here sss is number of milliseconds.

    This can be input as an integer or string, but the output is always integer.

    Time value is always in UTC regardless of time object scale.
    """

    name = "maude"
    convert_doc = {
        "input_name": "date",
        "descr_short": "MAUDE date",
        "input_format": "YYYYDDDHHMMSSsss (str or int)",
        "output_format": "YYYYDDD.HHMMSSsss (int)",
        "input_type": "str, bytes, int, list, ndarray",
        "output_type": "int, ndarray[int]",
    }

    subfmts = (
        ("date_hms", "%Y%j%H%M%S", "{year:d}{yday:03d}{hour:02d}{min:02d}{sec:02d}"),
    )

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
    fast_parser_pars = {
        "use_fast_parser": True,
        "delims": (0, 0, 0, 0, 0, 0, 0),
        "starts": (0, -1, 4, 7, 9, 11, 13),
        "stops": (3, -1, 6, 8, 10, 12, -1),
        # Break before:  y  m  d  h  m  s  f,
        "break_allowed": (0, 0, 0, 1, 0, 1, 1),
        "has_day_of_year": 1,
    }

    def _check_val_type(self, val1, val2):
        if val2 is not None:
            raise ValueError(f"cannot supply val2 for {self.name} format")

        if val1.dtype.kind not in ("S", "U", "i"):
            raise TypeError(
                "Input values for {0} class must be string or int".format(self.name)
            )

        if val1.dtype.kind == "i":
            val1 = val1.astype("S")

        return val1, None

    def to_value(self, parent=None, **kwargs):
        if self.scale == "utc":
            out = super().value
        else:
            out = parent.utc._time.value
        out = np.array([x[:13] + x[14:] for x in out.flat]).reshape(out.shape)
        out = out.astype("i8")

        return out

    value = property(to_value)


class CxoTimeDescriptor(TypedDescriptor):
    """Descriptor for an attribute that is CxoTime (in date format) or None if not set.

    This allows setting the attribute with any ``CxoTimeLike`` value.

    Note that setting this descriptor to ``None`` will set the attribute to ``None``,
    which is different than ``CxoTime(None)`` which returns the current time. To set
    an attribute to the current time, set it with ``CxoTime.now()``.

    Parameters
    ----------
    default : CxoTimeLike, optional
        Default value for the attribute which is provide to the ``CxoTime`` constructor.
        If not specified or ``None``, the default for the attribute is ``None``.
    required : bool, optional
        If ``True``, the attribute is required to be set explicitly when the object
        is created. If ``False`` the default value is used if the attribute is not set.

    Examples
    --------
    >>> from dataclasses import dataclass
    >>> from cxotime import CxoTime, CxoTimeDescriptor
    >>> @dataclass
    ... class MyClass:
    ...     start: CxoTime | None = CxoTimeDescriptor()
    ...     stop: CxoTime | None = CxoTimeDescriptor()
    ...
    >>> obj = MyClass("2023:100")
    >>> obj.start
    <CxoTime object: scale='utc' format='date' value=2023:100:00:00:00.000>
    >>> obj.stop is None
    True
    """

    cls = CxoTime
