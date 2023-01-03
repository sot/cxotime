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


Examples
--------

Basic initialization
^^^^^^^^^^^^^^^^^^^^
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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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


Fast conversion between Date and CXC seconds
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For fast conversion of an input date or dates in Year Day-of-Year date format,
the function :func:`~cxotime.cxotime.date2secs` can be used.

This is a specialized function similar to the legacy ``Chandra.Time.date2secs``
that allows for fast conversion of a single date or an array of dates to CXC
seconds.  It is intended to be used ONLY when the input date is known to be in
the correct Year Day-of-Year format.

The main use case is for a single date or a few dates. For a single date this
function is about 10 times faster than the equivalent call to
``CxoTime(date).secs``. For a large array of dates (more than about 100) this
function  is not significantly faster.

This function will raise an exception if the input date is not in one of
these allowed formats:

- YYYY:DDD
- YYYY:DDD:HH:MM
- YYYY:DDD:HH:MM:SS
- YYYY:DDD:HH:MM:SS.sss

Conversely, for fast conversion from CXC seconds to Year Day-of-Year date, the
function :func:`~cxotime.cxotime.secs2date` can be used. For scalar inputs this
is 15-20 times faster than the equivalent call to ``CxoTime(secs).date``.

API docs
--------

.. automodule:: cxotime.cxotime
   :members:

.. automodule:: cxotime.convert
   :members:
