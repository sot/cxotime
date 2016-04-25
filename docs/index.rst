.. cxotime documentation master file, created by
   sphinx-quickstart on Sat Nov 14 12:35:27 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. |Time| replace:: `http://docs.astropy.org/en/stable/api/astropy.time.Time.html#astropy.time.Time <Time>`_
.. |TimeDelta| replace:: `http://docs.astropy.org/en/stable/time/index.html#time-deltas <TimeDelta>`_
.. |astropy.time| replace:: `http://docs.astropy.org/en/stable/time/index.html <astropy.time>`_
.. |CxoTime| replace:: :ref:`~cxotime.cxotime.CxoTime`
.. |DateTime| replace:: `http://cxc.harvard.edu/mta/ASPECT/tool_doc/pydocs/Chandra.Time.html <DateTime>`_

Chandra-specific astropy Time class
===================================

The ``cxotime`` package provides a |CxoTime| class which provides Chandra-specific
functionality while deriving from the |Time| class of the |astropy.time| package.
The |astropy.time| package provides robust 128-bit time representation,
arithmetic, and comparisons.

The Chandra-specific time formats which are added to the astropy |Time| class
are shown in the table below.  Like |DateTime|, the |CxoTime| class
default is to interpret any numerical values as ``secs`` (aka ``cxcsec`` in
the native |Time| class).

======== =======================================  =======
 Format  Description                              System
======== =======================================  =======
secs     Seconds since 1998-01-01T00:00:00 (TT)   utc
date     YYYY:DDD:hh:mm:ss.ss..                   utc
greta    YYYYDDD.hhmmsssss                        utc
======== =======================================  =======


Compatibility with DateTime
---------------------------

The key differences between |CxoTime| and |DateTime| are:

- In |CxoTime| the date '2000:001' is '2000:001:00:00:00' instead of
  '2000:001:12:00:00' in |DateTime|.  In most cases this interpretation
  is more rational and expected.

- In |CxoTime| the date '2001-01-01T00:00:00' is UTC by default, while in
  |DateTime| that is interpreted as TT by default.  This is triggered by
  the ``T`` in the middle.  A date like '2001-01-01 00:00:00' defaults
  to UTC in both |CxoTime| and |DateTime|.

- In |CxoTime| the difference of two dates is a |DeltaTime| object
  which is transformable to any time units.  In |DateTime| the difference
  of two dates is a floating point value in days.

- Conversely, starting with |CxoTime| one can add or subtract a |DeltaTime| or
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
::

  >>> t = CxoTime(1.0)
  >>> t.format
  'secs'

  >>> t.scale
  'utc'

  >>> t.tt.date
  '1998:001:00:00:01.000'

  >>> t = CxoTime([['1998:001:00:00:01.000', '1998:001:00:00:02.000'],
                   ['1998:001:00:00:03.000', '1998:001:00:00:04.000']])
  >>> t.secs
  array([[ 64.184,  65.184],
         [ 66.184,  67.184]])

  >>> t.format
  'date'

  >>> t.scale
  'utc'

.. toctree::
   :maxdepth: 2

API docs
========

.. automodule:: cxotime
   :members:

.. autoclass:: CxoTime

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

