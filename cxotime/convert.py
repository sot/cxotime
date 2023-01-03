import datetime
import functools
import re
import sys

import erfa
import numpy as np
from astropy.time.formats import TimeYearDayTime, _parse_times

from .cxotime import CxoTime, TimeGreta, TimeMaude

__all__ = ["print_time_conversions", "convert_time_format"]


def print_time_conversions():
    """Interface to entry_point script ``cxotime`` to print time conversions"""
    date = None if len(sys.argv) == 1 else sys.argv[1]
    date = CxoTime(date)
    date.print_conversions()


def convert_time_format(val, fmt_out, *, fmt_in=None):
    """
    Convert a time to a different format.

    Parameters
    ----------
    val : CxoTimeLike
        Time value
    fmt_out : str
        Output format
    fmt_in : str
        Input format (default is to guess)

    Returns
    -------
    val_out : str
        Time string in output format
    """
    if fmt_in == fmt_out:
        return val

    if fmt_in is not None:
        jd1, jd2 = globals()[f"convert_{fmt_in}_to_jd1_jd2"](val)
        out = globals()[f"convert_jd1_jd2_to_{fmt_out}"](jd1, jd2)
        return out

    # Guess the input format. Returns None if guessing failed.
    fmt_in, jd1, jd2 = get_format(val, fmt_out)

    if fmt_in == fmt_out:
        return val

    # Try with the fast converters. If we don't have a fast converter then use CxoTime.
    out = None
    try:
        if jd1 is None:
            jd1, jd2 = globals()[f"convert_{fmt_in}_to_jd1_jd2"](val)
        out = globals()[f"convert_jd1_jd2_to_{fmt_out}"](jd1, jd2)
    except KeyError:
        tm = CxoTime(val, format=fmt_in)
        out = getattr(tm, fmt_out)

    return out


def get_format(val, fmt_out):
    fmt_in = None
    jd1 = None
    jd2 = None

    if val is None:
        return fmt_in, jd1, jd2

    val = np.asarray(val)

    # First check for a number or array of numbers, which implies CXC seconds
    if issubclass(val.dtype.type, np.number):
        fmt_in = "secs"
        if fmt_out != "secs":
            # Same code as _secs2date_scalar but inlined here for speed
            jd1 = val / 86400.0 + 2450814.5
            jd2 = 0.0
            jd1, jd2, _ = erfa.ufunc.tttai(jd1, jd2)
            jd1, jd2, _ = erfa.ufunc.taiutc(jd1, jd2)
        return fmt_in, jd1, jd2

    if val.dtype.kind not in ("U", "S"):
        # No clue, punt this back for generic conversion by CxoTime
        return fmt_in, jd1, jd2

    convert_funcs = [
        convert_date_to_jd1_jd2,
        convert_greta_to_jd1_jd2,
        convert_maude_to_jd1_jd2,
    ]
    for convert_func in convert_funcs:
        try:
            jd1, jd2 = convert_func(val)
            fmt_in = convert_func.__name__.split("_")[0]
            break
        except Exception:
            pass

    return fmt_in, jd1, jd2


def convert_date_to_secs(date):
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

    Parameters
    ----------
    date : str, list of str, bytes, list of bytes, np.ndarray
        Input date(s) in an allowed year-day-of-year date format

    Returns
    -------
    time : float, np.ndarray
        CXC seconds matching dimensions of input date(s)
    """
    # This code is adapted from the underlying code in astropy time, with some
    # of the general-purpose handling and validation removed.

    # Handle bytes or str input and convert to uint8.  We need to the
    # dtype _parse_times.dt_u1 instead of uint8, since otherwise it is
    # not possible to create a gufunc with structured dtype output.
    # See note about ufunc type resolver in pyerfa/erfa/ufunc.c.templ.
    jd1, jd2 = convert_date_to_jd1_jd2(date)
    secs = convert_jd1_jd2_to_secs(jd1, jd2)
    return secs


def convert_jd1_jd2_to_secs(jd1, jd2=None):
    if jd2 is None:
        jd2 = 0.0

    # Transform to TT via TAI
    jd1, jd2, _ = erfa.ufunc.utctai(jd1, jd2)
    jd1, jd2, _ = erfa.ufunc.taitt(jd1, jd2)

    # Fixed offsets taken from CxoTime(0.0).tt.jd1,2
    time_from_epoch1 = (jd1 - 2450814.0) * 86400.0
    time_from_epoch2 = (jd2 - 0.5) * 86400.0

    secs = time_from_epoch1 + time_from_epoch2
    return secs


def convert_date_to_jd1_jd2(date):
    # Performance note: using isinstance(date, np.ndarray) is a few times faster than
    # date = np.asarrray(date). (64 ns vs 226 ns).
    if not isinstance(date, np.ndarray):
        date = np.array(date)
    jd1, jd2 = convert_string_to_jd1_jd2(date, TimeYearDayTime)
    return jd1, jd2


def convert_greta_to_jd1_jd2(date):
    if not isinstance(date, np.ndarray):
        date = np.array(date)

    # Allow for numeric input but reformat as string
    if date.dtype.kind in ("f", "i"):
        date = np.array([f"{x:.9f}" for x in date.flat]).reshape(date.shape)

    jd1, jd2 = convert_string_to_jd1_jd2(date, TimeGreta)
    return jd1, jd2


def convert_maude_to_jd1_jd2(date):
    if not isinstance(date, np.ndarray):
        date = np.array(date)

    if date.dtype.kind == "i":
        date = date.astype("S")

    jd1, jd2 = convert_string_to_jd1_jd2(date, TimeMaude)
    return jd1, jd2


def convert_jd1_jd2_to_greta(jd1, jd2=None):
    date = convert_jd1_jd2_to_date(jd1, jd2)
    # Convert '1997:365:23:58:57.816' to '1997365.235857816'
    #          012345678901234567890
    if isinstance(date, np.ndarray):
        out = np.array(
            [
                x[:4] + x[5:8] + "." + x[9:11] + x[12:14] + x[15:17] + x[18:21]
                for x in date.flat
            ]
        )
        out.shape = date.shape
    else:
        x = date  # 15 ns
        out = x[:4] + x[5:8] + "." + x[9:11] + x[12:14] + x[15:17] + x[18:21]  # 660 ns
    return out


def convert_jd1_jd2_to_maude(jd1, jd2=None):
    date = convert_jd1_jd2_to_date(jd1, jd2)
    if isinstance(date, np.ndarray):
        out = np.array(
            [
                x[:4] + x[5:8] + x[9:11] + x[12:14] + x[15:17] + x[18:21]
                for x in date.flat
            ]
        )
        out = out.astype("i8")
        out.shape = date.shape
    else:
        x = date
        out = int(x[:4] + x[5:8] + x[9:11] + x[12:14] + x[15:17] + x[18:21])
    return out


def convert_jd1_jd2_to_jd(jd1, jd2=None):
    if jd2 is None:
        jd2 = 0.0
    jd = jd1 + jd2
    return jd


def convert_jd_to_jd1_jd2(jd):
    jd1 = jd
    jd2 = 0.0
    return jd1, jd2


def convert_string_to_jd1_jd2(date, time_format_cls):
    if date.dtype.kind == "U":
        # This assumes the input is pure ASCII.
        val1_uint32 = date.view((np.uint32, date.dtype.itemsize // 4))
        chars = val1_uint32.astype(_parse_times.dt_u1)
    else:
        chars = date.view((_parse_times.dt_u1, date.dtype.itemsize))

    # Call the fast parsing ufunc.
    time_struct = time_format_cls._fast_parser(chars)

    # In these ERFA calls ignore the return value since we know jd1, jd2 are OK.
    # Checking the return value via np.any nearly doubles the function time.

    # Convert time ISO date to jd1, jd2
    jd1, jd2, _ = erfa.ufunc.dtf2d(
        b"UTC",
        time_struct["year"],
        time_struct["month"],
        time_struct["day"],
        time_struct["hour"],
        time_struct["minute"],
        time_struct["second"],
    )

    return jd1, jd2


def convert_secs_to_date(secs):
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
    jd1, jd2 = convert_secs_to_jd1_jd2(secs)
    out = convert_jd1_jd2_to_date(jd1, jd2)

    return out


def convert_jd1_jd2_to_date(jd1, jd2=None):
    if jd2 is None:
        jd2 = np.zeros_like(jd1)
    iys, ims, ids, ihmsfs = erfa.d2dtf(b"TT", 3, jd1, jd2)
    ihrs = ihmsfs["h"]
    imins = ihmsfs["m"]
    isecs = ihmsfs["s"]
    ifracs = ihmsfs["f"]

    if isinstance(jd1, np.ndarray):
        dates = []
        for iy, im, id, ihr, imin, isec, ifracsec in np.nditer(
            [iys, ims, ids, ihrs, imins, isecs, ifracs], flags=["zerosize_ok"]
        ):
            yday = datetime.datetime(iy, im, id).timetuple().tm_yday
            date = f"{iy:4d}:{yday:03d}:{ihr:02d}:{imin:02d}:{isec:02d}.{ifracsec:03d}"
            dates.append(date)

        out = np.array(dates).reshape(jd1.shape)
    else:
        yday = datetime.datetime(iys, ims, ids).timetuple().tm_yday
        out = f"{iys:4d}:{yday:03d}:{ihrs:02d}:{imins:02d}:{isecs:02d}.{ifracs:03d}"

    return out


def convert_secs_to_jd1_jd2(secs):
    jd2 = 0.0
    try:
        jd1 = secs / 86400.0 + 2450814.5
    except TypeError:
        # For a list input
        jd1 = np.array(secs, dtype=np.float64) / 86400.0 + 2450814.5

    # In these ERFA calls ignore the return value since we know jd1, jd2 are OK.
    # Checking the return value via np.any is quite slow.
    # Transform TT to UTC via TAI
    jd1, jd2, _ = erfa.ufunc.tttai(jd1, jd2)
    jd1, jd2, _ = erfa.ufunc.taiutc(jd1, jd2)
    return jd1, jd2


from astropy.time.formats import TIME_FORMATS


def make_docstring(fmt_in, fmt_out):
    import textwrap

    fmt_in_cls = TIME_FORMATS[fmt_in]
    doc_in = fmt_in_cls.convert_doc
    fmt_out_cls = TIME_FORMATS[fmt_out]
    doc_out = fmt_out_cls.convert_doc
    equiv = f"CxoTime({doc_in['input_name']}, format='{fmt_in_cls.name}').{fmt_out_cls.name}"
    out = f"""\
    Convert {doc_in['descr_short']} to {doc_out['descr_short']}.

    This is equivalent to ``{equiv}`` but potentially 10x faster.

    Format in: {doc_in['input_format']}
    Format out: {doc_out['output_format']}

    Parameters
    ----------
    {doc_in['input_name']} : {doc_in['input_type']}
        {doc_in['descr_short']}

    Returns
    -------
    {doc_out['input_name']} : {doc_out['output_type']}
        {doc_out['descr_short']}
    """
    return textwrap.dedent(out)


# Define shortcuts for converters like date2secs or greta2date.
# Accept each value of globals if it matches the pattern convert_jd1_jd2_to_...
_formats = [
    m.group(1)
    for fmt in list(globals())
    if (m := re.match(r"convert_jd1_jd2_to_(\w+)", fmt))
]


for fmt1 in _formats:
    input_name = TIME_FORMATS[fmt1].convert_doc["input_name"]
    for fmt2 in _formats:
        if fmt1 != fmt2:
            name = f"{fmt1}2{fmt2}"
            func_str = (
                f"lambda {input_name}: "
                f"convert_time_format({input_name}, fmt_in='{fmt1}', fmt_out='{fmt2}')"
            )
            func = globals()[name] = eval(func_str)
            func.__doc__ = make_docstring(fmt1, fmt2)
            __all__.append(name)
