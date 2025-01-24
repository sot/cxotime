.. cxotime documentation master file, created by
   sphinx-quickstart on Sat Nov 14 12:35:27 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _Time: http://docs.astropy.org/en/stable/time/index.html
.. _TimeDelta: http://docs.astropy.org/en/stable/time/index.html#time-deltas
.. _DateTime: http://cxc.harvard.edu/mta/ASPECT/tool_doc/pydocs/Chandra.Time.html
.. _astropy.time: http://docs.astropy.org/en/stable/time/index.html
.. |CxoTime| replace:: :class:`~cxotime.cxotime.CxoTime`


.. toctree::
   :hidden:

Chandra Time
============

The ``cxotime`` package provides the |CxoTime| class to represent and manipulate times.
It also provides :mod:`fast converter functions <cxotime.converters>` for converting
between time formats.

The |CxoTime| class adds Chandra-specific functionality to the Time_ class of the
`astropy.time`_ package. The `astropy.time`_ package provides robust 128-bit time
representation, arithmetic, and comparisons.

Basics
------

The |CxoTime| class can be initialized with a variety of input formats, including
strings, floats, integers, and arrays of these.  The following examples show some
of the ways to create a |CxoTime| object.

>>> from cxotime import CxoTime
>>> t = CxoTime('2022:001:00:00:00.123')
>>> t
<CxoTime object: scale='utc' format='date' value=2022:001:00:00:00.123>
>>> print(t)
2022:001:00:00:00.123

Now you can convert to a different format:

>>> t.greta
'2022001.000000123'
>>> t.iso
'2022-01-01 00:00:00.123'
>>> t.secs
757382469.307

You can get the current time with the :meth:`~cxotime.CxoTime.now` class method:

>>> t = CxoTime.now()

String formatted inputs are unique and you do not need to specify the format when
creating a |CxoTime| object.  The format is automatically inferred from the input.

>>> t = CxoTime('2022001.000000123')
>>> t.format
'greta'

The ``greta`` format is a little special since it can be input as either a string or a
float. However, |CxoTime| will always return it as a string. By default |CxoTime|
always interprets a float number as CXC seconds, so if you have a ``greta`` float
then you can explicitly specify the format:

>>> t = CxoTime(2022001.000000123, format='greta')
>>> t.date
'2022:001:00:00:00.123'

You can also create a |CxoTime| object from a numpy array of strings, floats, or
integers. When possible, the format is inferred from the input. However, if performance
is an issue and you know the format in advance, you should specify it.

>>> import numpy as np
>>> t = CxoTime(np.array([2022001.000000123, 2022002.000000123]), format='greta')
>>> t.date
array(['2022:001:00:00:00.123', '2022:002:00:00:00.123'], dtype='<U21')

Time arithmetic
---------------

You can add and subtract times using the standard arithmetic operators and astropy
units and `Quantity <https://docs.astropy.org/en/latest/units/quantity.html>`_ objects:

>>> import astropy.units as u
>>> t0 = CxoTime("2025:001")
>>> dt = [1, 2] * u.day + [10, 20] * u.s  # Quantity with time units (day)
>>> t1 = t0 + dt
>>> print(t1)
['2025:002:00:00:10.000' '2025:003:00:00:20.000']

If you subtract two times you get a TimeDelta_ object:

>>> dt = t1 - t0
>>> dt.sec
array([ 86410., 172820.])
>>> dt.jd  # days
array([1.00011574, 2.00023148])

You can convert the TimeDelta_ object to a float type with any time unit:

>>> dt.to_value(u.ks)
array([ 86.41, 172.82])

Available time formats
----------------------

The Chandra-specific time formats which are added to the astropy Time_ class
are shown in the table below.  Like DateTime_, the |CxoTime| class
default is to interpret any numerical values as ``secs`` (aka ``cxcsec`` in
the native Time_ class).

========= ===========================================
 Format   Description
========= ===========================================
secs      Seconds since 1998-01-01T00:00:00 (TT)
date      YYYY:DDD:hh:mm:ss.ss..
frac_year YYYY.ffffff = date as a floating point year
greta     YYYYDDD.hhmmsssss (string)
maude     YYYYDDDhhmmsssss (integer)
========= ===========================================

Some of more useful built-in Time_ formats that are also available in |CxoTime| are:

=========== ======================== ==============================
Format       Description             Example
=========== ======================== ==============================
datetime    Python datetime class    datetime(2000, 1, 2, 12, 0, 0)
datetime64  Numpy datetime64 class   np.datetime64('2000-01-02')
decimalyear Same as frac_year        2000.45
iso         ISO time with a space    '2000-01-01 00:00:00.000'
isot        ISO time with a T        '2000-01-01T00:00:00.000'
jd          Julian Date              2451544.5
plot_date   Matplotlib date          730120.0003703703
unix        Unix time (approx)       946684800.0
=========== ======================== ==============================

Fast format conversion
----------------------

Converting between time formats (e.g. from CXC seconds to Year Day-of-Year) is
easily done with the |CxoTime| class, but this involves some overhead and is
relatively slow for scalar values or small arrays (less than around 100
elements). For applications where this conversion time ends up being significant,
the ``cxotime`` package provides a different interface that is typically at least
10x faster for scalar values or small arrays.

For fast conversion of an input date or dates to a different format there are
two options that are described in the next two sections.

``convert_time_format``
^^^^^^^^^^^^^^^^^^^^^^^

The first option is a generalized time format conversion function
:func:`~cxotime.convert.convert_time_format` that can be used to convert between
any of the supported *fast* formats:

- ``secs``: CXC seconds
- ``date``: Year Day-of-Year
- ``greta``: GRETA format (input can be string, float or int)
- ``maude``: MAUDE format (input can be string or int)
- ``jd``: Julian Day (requires ``fmt_in="jd"`` to identity this format)

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

The full list of available functions is shown in :mod:`cxotime.converters`.

Examples include :func:`~cxotime.convert.date2secs`, :func:`~cxotime.convert.secs2greta`,
and :func:`~cxotime.convert.greta2jd`.

>>> from cxotime import secs2greta
>>> secs2greta([100, 1000])
array(['1998001.000036816', '1998001.001536816'], dtype='<U17')

Common time conversions
-----------------------

The `cxotime` package has functionality to convert a time betweeen a variety of common
time formats. This convenience function is available in two ways, either as a
command line script or as class method :meth:`~cxotime.CxoTime.get_conversions`::

    $ cxotime 2022:002:12:00:00
    local       2022 Sun Jan 02 07:00:00 AM EST
    iso_local   2022-01-02T07:00:00-05:00
    date        2022:002:12:00:00.000
    cxcsec      757512069.184
    decimalyear 2022.00411
    iso         2022-01-02 12:00:00.000
    unix        1641124800.000

If you do not provide an argument then it will use the current time.

From Python you can do the same using the :meth:`~cxotime.CxoTime.get_conversions`
method:

>>> from cxotime import CxoTime
>>> tm = CxoTime("2022-01-02 12:00:00.000")
>>> tm.get_conversions()
{'cxcsec': 757512069.184,
 'date': '2022:002:12:00:00.000',
 'decimalyear': 2022.004109589041,
 'iso': '2022-01-02 12:00:00.000',
 'iso_local': '2022-01-02T07:00:00-05:00',
 'local': '2022 Sun Jan 02 07:00:00 AM EST',
 'unix': 1641124800.0}

CxoTime.NOW
-----------

The |CxoTime| class has a special value ``CxoTime.NOW`` which signifies the current time
when used to initialize a |CxoTime| object.  This is commonly useful for example when
defining a function that has accepts a CxoTime-like argument that defaults to the
current time.

.. note:: Prior to introduction of ``CxoTime.NOW``, the standard idiom was to specify
    ``None`` as the argument default to indicate the current time.  This is still
    supported but is strongly discouraged for new code.

For example:

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

The key differences between |CxoTime| and DateTime_ relate to the handling of time
deltas:

- In |CxoTime| the difference of two dates is a TimeDelta_ object
  which is transformable to any time units.  In DateTime_ the difference
  of two dates is a floating point value in days.

- In |CxoTime| you can add or subtract with a TimeDelta_ or a `Quantity
  <https://docs.astropy.org/en/latest/units/quantity.html>`_ like ``500 * u.s``. If you
  add or subtract a float number it is interpreted as days but a warning is issued. In
  DateTime_ you can only add or subtract with a float number which is interpreted as
  days.

A less common difference is that in |CxoTime| the date '2001-01-01T00:00:00' is UTC by
default, while in DateTime_ that is interpreted as TT by default.  This is triggered by
the ``T`` in the middle.  A date like '2001-01-01 00:00:00' defaults to UTC in both
|CxoTime| and DateTime_.
