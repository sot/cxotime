# cxotime

Time class for Chandra analysis that is based on `astropy.time.Time`.

The CXO-specific time formats are shown in the table below.  The
`CxoTime` class default is to interpret any numerical values as `secs`
(aka `cxcsec` in the native Time class).

All of these formats use the UTC scale.

 Format     | Description
----------- | ----------------------------------------
secs        | Seconds since 1998-01-01T00:00:00 (tt)
date        | YYYY:DDD:hh:mm:ss.ss..
greta       | YYYYDDD.hhmmsssss
frac_year   | YYYY.fffff

Important differences:

- In `CxoTime` the date '2000:001' is '2000:001:00:00:00' instead of
  '2000:001:12:00:00' in `DateTime` (prior to version 4.0).  In most cases this
  interpretation is more rational and expected.

- In `CxoTime` the date '2001-01-01T00:00:00' is UTC by default, while in
  `DateTime` that is interpreted as TT by default.  This is triggered by
  the ``T`` in the middle.  A date like '2001-01-01 00:00:00' defaults
  to UTC in both `CxoTime` and `DateTime`.

- In `CxoTime` the difference of two dates is a `TimeDelta` object
  which is transformable to any time units.  In `DateTime` the difference
  of two dates is a floating point value in days.

- Conversely, starting with `CxoTime` one can add or subtract a `TimeDelta` or
  any astropy `Quantity` with time units.

- To get the current time replace `DateTime()` with `CxoTime.now()`

The standard built-in Time formats that are available in `CxoTime` are:

Format      |  Example
----------- |  ------------------------
byear       |  1950.0
byear_str   |  'B1950.0'
cxcsec      |  63072064.184
datetime    |  datetime(2000, 1, 2, 12, 0, 0)
decimalyear |  2000.45
fits        |  '2000-01-01T00:00:00.000(TAI)'
gps         |  630720013.0
iso         |  '2000-01-01 00:00:00.000'
isot        |  '2000-01-01T00:00:00.000'
jd          |  2451544.5
jyear       |  2000.0
jyear_str   |  'J2000.0'
mjd         |  51544.0
plot_date   |  730120.0003703703
unix        |  946684800.0
yday        |  2000:001:00:00:00.000
