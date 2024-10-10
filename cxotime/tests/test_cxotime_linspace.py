import astropy.units as u
import numpy as np
import pytest

from cxotime import CxoTime


@pytest.mark.parametrize(
    "start, stop, dt_max, expected_len, expected_values",
    [
        ("2000:001", "2000:001", 1 * u.day, 2, ["2000:001", "2000:001"]),
        (
            "2000:001",
            "2000:005",
            24 * u.hour,
            5,
            ["2000:001", "2000:002", "2000:003", "2000:004", "2000:005"],
        ),
        (
            "2000:001",
            "2000:005",
            2880 * u.minute,
            3,
            ["2000:001", "2000:003", "2000:005"],
        ),
        ("2000:001", "2000:005", 10 * 86400 * u.second, 2, ["2000:001", "2000:005"]),
    ],
)
def test_linspace_step(start, stop, dt_max, expected_len, expected_values):
    result = CxoTime.linspace(start, stop, step_max=dt_max)

    # Confirm that the time intervals are uniform if there is any interval
    if len(result) > 2:
        assert all(
            np.isclose((result[1:] - result[:-1]).sec, dt_max.to(u.second).value)
        )

    # Confirm that the time range is covered
    assert result[0] == start
    assert result[-1] == stop

    # And confirm that the result is as expected
    assert len(result) == expected_len
    assert all(a == CxoTime(b) for a, b in zip(result, expected_values, strict=False))


# Add a test of a negative time range
def test_linspace_negative_range():
    start = CxoTime("2000:005")
    stop = CxoTime("2000:001")
    dt_max = 24 * u.hour
    result = CxoTime.linspace(start, stop, step_max=dt_max)
    assert len(result) == 5
    expected_values = ["2000:005", "2000:004", "2000:003", "2000:002", "2000:001"]
    assert all(a == CxoTime(b) for a, b in zip(result, expected_values, strict=False))


# Add a test that shows that the time range is covered even if the time range is less than dt_max
def test_linspace_big_step():
    start = CxoTime("2020:001")
    stop = CxoTime("2020:005")
    dt_max = 30 * u.day
    result = CxoTime.linspace(start, stop, step_max=dt_max)
    assert len(result) == 2
    assert all(
        a == CxoTime(b) for a, b in zip(result, ["2020:001", "2020:005"], strict=False)
    )


# Add a test that shows we get an error if dt_max is zero
def test_linspace_zero_step():
    start = CxoTime("2020:001")
    stop = CxoTime("2020:005")
    dt_max = 0 * u.day
    with pytest.raises(ValueError) as excinfo:
        CxoTime.linspace(start, stop, step_max=dt_max)
    assert "step_max must be positive nonzero" in str(excinfo.value)


# Add a test that shows we get an error if dt_max is negative
def test_linspace_negative_step():
    start = CxoTime("2020:001")
    stop = CxoTime("2020:005")
    dt_max = -1 * u.day
    with pytest.raises(ValueError) as excinfo:
        CxoTime.linspace(start, stop, step_max=dt_max)
    assert "step_max must be positive nonzero" in str(excinfo.value)


def test_linspace_num_0():
    start = CxoTime("2000:001")
    stop = CxoTime("2000:005")
    num = 0
    with pytest.raises(ValueError) as excinfo:
        CxoTime.linspace(start, stop, num=num)
    assert "num must be positive nonzero" in str(excinfo.value)


def test_linspace_num_neg():
    start = CxoTime("2000:001")
    stop = CxoTime("2000:005")
    num = -1
    with pytest.raises(ValueError) as excinfo:
        CxoTime.linspace(start, stop, num=num)
    assert "num must be positive nonzero" in str(excinfo.value)


def test_linspace_num_1():
    start = CxoTime("2000:001")
    stop = CxoTime("2000:005")
    num = 2
    result = CxoTime.linspace(start, stop, num=num)
    assert len(result) == num + 1
    assert all(
        a == CxoTime(b)
        for a, b in zip(result, ["2000:001", "2000:003", "2000:005"], strict=False)
    )


def test_linspace_num_2():
    start = "2000:001"
    stop = "2024:001"
    num = 12
    result = CxoTime.linspace(start, stop, num=num)
    assert len(result) == num + 1
    for a, b in zip(
        result,
        [
            "2000:001:00:00:00.000",
            "2001:365:12:00:00.417",
            "2004:001:00:00:00.833",
            "2005:365:12:00:01.250",
            "2008:001:00:00:00.667",
            "2009:365:12:00:00.083",
            "2012:001:00:00:00.500",
            "2013:365:11:59:59.917",
            "2015:365:23:59:59.333",
            "2017:365:11:59:58.750",
            "2019:365:23:59:59.167",
            "2021:365:11:59:59.583",
            "2024:001:00:00:00.000",
        ],
        strict=False,
    ):
        assert np.isclose(a.secs, CxoTime(b).secs)


def test_linspace_num_3():
    start = "2010:001"
    stop = "2011:001"
    num = 12
    result = CxoTime.linspace(start, stop, num=num)
    assert len(result) == num + 1
    for a, b in zip(
        result,
        [
            "2010:001:00:00:00.000",
            "2010:031:10:00:00.000",
            "2010:061:20:00:00.000",
            "2010:092:06:00:00.000",
            "2010:122:16:00:00.000",
            "2010:153:02:00:00.000",
            "2010:183:12:00:00.000",
            "2010:213:22:00:00.000",
            "2010:244:08:00:00.000",
            "2010:274:18:00:00.000",
            "2010:305:04:00:00.000",
            "2010:335:14:00:00.000",
            "2011:001:00:00:00.000",
        ],
        strict=False,
    ):
        assert np.isclose(a.secs, CxoTime(b).secs)
