.. cxotime documentation master file, created by
   sphinx-quickstart on Sat Nov 14 12:35:27 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _Time: http://docs.astropy.org/en/stable/api/astropy.time.Time.html#astropy.time.Time
.. _TimeDelta: http://docs.astropy.org/en/stable/time/index.html#time-deltas
.. _astropytime: http://docs.astropy.org/en/stable/time/index.html
.. _DateTime: http://cxc.harvard.edu/mta/ASPECT/tool_doc/pydocs/Chandra.Time.html
.. |CxoTime| replace:: :class:`~cxotime.cxotime.CxoTime`

Chandra-specific astropy Time class
===================================

The ``cxotime`` package provides a |CxoTime| class which provides Chandra-specific
functionality while deriving from the Time_ class of the astropytime_ package.
The astropytime_ package provides robust 128-bit time representation,
arithmetic, and comparisons.

The Chandra-specific time formats which are added to the astropy Time_ class
are shown in the table below.  Like DateTime_, the |CxoTime| class
default is to interpret any numerical values as ``secs`` (aka ``cxcsec`` in
the native Time_ class).

========= ===========================================  =======
 Format   Description                                  System
========= ===========================================  =======
secs      Seconds since 1998-01-01T00:00:00 (TT)       utc
date      YYYY:DDD:hh:mm:ss.ss..                       utc
frac_year YYYY.ffffff = date as a floating point year  utc
greta     YYYYDDD.hhmmsssss (string)                   utc
maude     YYYYDDDhhmmsssss (integer)                   utc
========= ===========================================  =======

The standard built-in Time formats that are available in |CxoTime| are:

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


Basic initialization
--------------------
::

  >>> from cxotime import CxoTime
  >>> t = CxoTime(100.0)
  >>> t.date
  '1998:001:00:00:36.816'
  >>> t.format
  'secs'
  >>> t.scale
  'utc'

  >>> import astropy.units as u
  >>> t2 = t + [1, 2] * u.day + [10, 20] * u.s
  >>> t2.date
  array(['1998:002:00:00:46.816', '1998:003:00:00:56.816'], dtype='<U21')

  >>> t = CxoTime([['1998:001:00:00:01.000', '1998:001:00:00:02.000'],
                   ['1998:001:00:00:03.000', '1998:001:00:00:04.000']])
  >>> t.secs
  array([[ 64.184,  65.184],
         [ 66.184,  67.184]])

  >>> t.format
  'date'

Guessing and specifying the format
----------------------------------

Generally speaking ``CxoTime`` will successfully guess the format for
string-based times. However this requires some time, so if you know the
format in advance then it is recommended to provide this via the ``format``
argument.
::

  >>> t = CxoTime('2020001223344555', format='maude')
  >>> t.date
  '2020:001:22:33:44.555'

.. toctree::
   :maxdepth: 2


Fast conversion between formats
-------------------------------

Converting between time formats (e.g. from CXC seconds to Year Day-of-Year) is
easily done with the |CxoTime| class, but this involves some overhead and is
relatively slow for scalar values or small arrays (less than around 100
elements). For applications where this conversion time ends up being significant,
the `cxotime` package provides a different interface that is typically at least
10x faster for scalar values or small arrays.

For fast conversion of an input date or dates to a different format there are
two options that are described in the next two sections.

``convert_time_format``
^^^^^^^^^^^^^^^^^^^^^^^

The first option is a generalized time format conversion function
:func:`~cxotime.convert.convert_time_format` that can be used to convert between
any of the supported *fast* formats:

- `secs`: CXC seconds
- `date`: Year Day-of-Year
- `greta`: GRETA format (input can be string, float or int)
- `maude`: MAUDE format (input can be string or int)
- `jd`: Julian Day (requires `fmt_in="jd"` to identity this format)

For example::

    >>> from cxotime import convert_time_format
    >>> convert_time_format("2022:001:00:00:00.123", "greta")
    '2022001.000000123'
    >>> convert_time_format(100.123, "date")
    '1998:001:00:00:36.939'
    >>> convert_time_format(2459580.5, "date", fmt_in="jd")
    '2022:001:00:00:00.000'

Note that this function can be used to convert between any of the supported |CxoTime|
formats, but it will internally use a |CxoTime| object so the performance will not be
improved. For example::

    >>> convert_time_format(2022.123, fmt_out="date", fmt_in="frac_year")
    '2022:045:21:28:48.000'

    # Exactly equivalent to:
    >>> CxoTime(2022.123, format="frac_year").date
    '2022:045:21:28:48.000'

Convenience functions like ``secs2date``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For historical compatibility and for succinct code, direct conversion between any two
of the "fast" formats is also available via convenience functions. These have the name
``<fmt_in>2<fmt_out>`` where ``fmt_in`` and ``fmt_out`` are the input and output formats.
Examples include :func:`~cxotime.convert.date2secs`, :func:`~cxotime.convert.secs2greta`,
and :func:`~cxotime.convert.greta2jd`.

::
    >>> from cxotime import secs2greta
    >>> secs2greta([100, 1000])
    array(['1998001.000036816', '1998001.001536816'], dtype='<U17')


Print common time conversions
-----------------------------

The `cxotime` package has functionality to convert a time betweeen a variety of common
time formats. This convenience function is available in two ways, either as a
command line script or as class method :meth:`~cxotime.CxoTime.print_conversions`::

    $ cxotime 2022:002:12:00:00
    local       2022 Sun Jan 02 07:00:00 AM EST
    iso_local   2022-01-02T07:00:00-05:00
    date        2022:002:12:00:00.000
    cxcsec      757512069.184
    decimalyear 2022.00411
    iso         2022-01-02 12:00:00.000
    unix        1641124800.000

::

    $ cxotime  # Print current time
    local       2023 Tue Jan 10 01:41:02 PM EST
    iso_local   2023-01-10T13:41:02.603000-05:00
    date        2023:010:18:41:02.603
    cxcsec      789763331.787
    decimalyear 2023.02679
    iso         2023-01-10 18:41:02.603
    unix        1673376062.603

or in python::

    >>> from cxotime import CxoTime
    >>> tm = CxoTime("2022-01-02 12:00:00.000")
    >>> tm.print_conversions()
    local       2022 Sun Jan 02 07:00:00 AM EST
    iso_local   2022-01-02T07:00:00-05:00
    date        2022:002:12:00:00.000
    cxcsec      757512069.184
    decimalyear 2022.00411
    iso         2022-01-02 12:00:00.000
    unix        1641124800.000

CxoTime.NOW sentinel
--------------------

The |CxoTime| class has a special sentinel value ``CxoTime.NOW`` which can be used
to specify the current time.  This is useful for example when defining a function that
has accepts a CxoTime-like argument that defaults to the current time.

.. note:: Prior to introduction of ``CxoTime.NOW``, the standard idiom was to specify
    ``None`` as the argument default to indicate the current time.  This is still
    supported but is strongly discouraged for new code.

For example::

    >>> from cxotime import CxoTime
    >>> def my_func(stop=CxoTime.NOW):
    ...     stop = CxoTime(stop)
    ...     print(stop)
    ...
    >>> my_func()
    2024:006:11:37:41.930

This can also be used in a `dataclass
<https://docs.python.org/3/library/dataclasses.html>`_ to specify an attribute that is
optional and defaults to the current time when the object is created::

    >>> import time
    >>> from dataclasses import dataclass
    >>> from cxotime import CxoTime, CxoTimeDescriptor
    >>> @dataclass
    ... class MyData:
    ...     start: CxoTime = CxoTimeDescriptor(required=True)
    ...     stop: CxoTime = CxoTimeDescriptor(default=CxoTime.NOW)
    ...
    >>> obj1 = MyData("2022:001")
    >>> print(obj1.start)
    2022:001:00:00:00.000
    >>> time.sleep(2)
    >>> obj2 = MyData("2022:001")
    >>> dt = obj2.stop - obj1.stop
    >>> round(dt.sec, 2)
    2.0

Compatibility with DateTime
---------------------------

The key differences between |CxoTime| and DateTime_ are:

- In |CxoTime| the date '2000:001' is '2000:001:00:00:00' instead of
  '2000:001:12:00:00' in DateTime_ (prior to version 4.0).  In most cases this
  interpretation is more rational and expected.

- In |CxoTime| the date '2001-01-01T00:00:00' is UTC by default, while in
  DateTime_ that is interpreted as TT by default.  This is triggered by
  the ``T`` in the middle.  A date like '2001-01-01 00:00:00' defaults
  to UTC in both |CxoTime| and DateTime_.

- In |CxoTime| the difference of two dates is a TimeDelta_ object
  which is transformable to any time units.  In DateTime_ the difference
  of two dates is a floating point value in days.

- Conversely, starting with |CxoTime| one can add or subtract a TimeDelta_ or
  any quantity with time units.

API docs
--------

Cxotime
^^^^^^^

.. automodule:: cxotime.cxotime
   :members:

Converters
^^^^^^^^^^

.. automodule:: cxotime.convert
   :members:
