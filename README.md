# cxotime

Time class for Chandra analysis that is based on astropy.time.Time.

The CXO-specific time formats are shown in the table below.  The
CxoTime class default is to interpret any numerical values as `secs`
(aka `cxcsec` in the native Time class).


 Format     | Description                                  |  System
----------- | -------------------------------------------- | --------
secs        | Seconds since 1998-01-01T00:00:00 (float)    |   tt
date        | YYYY:DDD:hh:mm:ss.ss..                       |   utc

Important differences:

- In CxoTime the date '2000:001' is '2000:001:00:00:00' instead of
  '2000:001:12:00:00' in DateTime.  In most cases this interpretation is more
  rational and expected.
- In CxoTime the date '2001-01-01T00:00:00' is UTC, while in DateTime
  that is interpreted as TT.

The standard built-in Time formats that are available in CxoTime are:


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
