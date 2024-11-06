import astropy.units as u
import numpy as np
import pytest

from cxotime import CxoTime


def run_linspace_step_test(start, stop, dt_max, expected_len, expected_values):
    """General test function for CxoTime.linspace with step_max."""

    result = CxoTime.linspace(start, stop, step_max=dt_max)

    # Confirm that the first interval duration matches the expected value
    assert abs(result[1] - result[0]) <= min(
        dt_max, abs(CxoTime(stop) - CxoTime(start))
    )

    # Confirm that all the intervals are the basically the same duration
    interval1 = result[1] - result[0]
    assert all(np.isclose((result[1:] - result[:-1]).sec, interval1.sec))

    # And that they are all less than or equal to dt_max
    assert all((result[1:] - result[:-1]) <= dt_max)

    # Confirm that the time range is covered
    assert result[0] == start
    assert result[-1] == stop

    # And confirm that the result is as expected
    assert len(result) == expected_len
    assert np.allclose(CxoTime(result).secs, CxoTime(expected_values).secs)


def test_linspace_step_bug():
    """Test that the steps are equal to or less than the maximum step for one case
    described in https://github.com/sot/cxotime/issues/45 . For this case, the
    maximum step is 1 minute and the range is 30 minutes. One would expect 30
    intervals, but due to tiny numeric issues with np.linspace, we need an extra
    interval to avoid having any intervals just over the step_max."""
    run_linspace_step_test(
        "2023:001:00:00:01.000",
        "2023:001:00:30:01.000",
        1 * u.min,
        32,
        [
            "2023:001:00:00:01.000",
            "2023:001:00:00:59.065",
            "2023:001:00:01:57.129",
            "2023:001:00:02:55.194",
            "2023:001:00:03:53.258",
            "2023:001:00:04:51.323",
            "2023:001:00:05:49.387",
            "2023:001:00:06:47.452",
            "2023:001:00:07:45.516",
            "2023:001:00:08:43.581",
            "2023:001:00:09:41.645",
            "2023:001:00:10:39.710",
            "2023:001:00:11:37.774",
            "2023:001:00:12:35.839",
            "2023:001:00:13:33.903",
            "2023:001:00:14:31.968",
            "2023:001:00:15:30.032",
            "2023:001:00:16:28.097",
            "2023:001:00:17:26.161",
            "2023:001:00:18:24.226",
            "2023:001:00:19:22.290",
            "2023:001:00:20:20.355",
            "2023:001:00:21:18.419",
            "2023:001:00:22:16.484",
            "2023:001:00:23:14.548",
            "2023:001:00:24:12.613",
            "2023:001:00:25:10.677",
            "2023:001:00:26:08.742",
            "2023:001:00:27:06.806",
            "2023:001:00:28:04.871",
            "2023:001:00:29:02.935",
            "2023:001:00:30:01.000",
        ],
    )


def test_linspace_step_with_zero_range():
    """Test that the result is correct when start==stop."""
    run_linspace_step_test(
        "2000:001", "2000:001", 1 * u.day, 2, ["2000:001", "2000:001"]
    )


def test_linspace_step_with_zero_range_and_bigger_step():
    """Test that the result is correct when the step is larger than the range."""
    run_linspace_step_test(
        "2000:001", "2000:001", 1.5 * u.day, 2, ["2000:001", "2000:001"]
    )


def test_linspace_step_with_float_range():
    """Test that the result is correct when the step is smaller than the range and more float-like."""
    run_linspace_step_test(
        "2024:001",
        "2023:364",
        12.5 * u.hour,
        5,
        [
            "2024:001:00:00:00.000",
            "2023:365:12:00:00.000",
            "2023:365:00:00:00.000",
            "2023:364:12:00:00.000",
            "2023:364:00:00:00.000",
        ],
    )


def test_linspace_step_odd_minutes():
    """Test that the result is correct when the step is just some weird float of minutes."""
    run_linspace_step_test(
        "2020:020:00:12:00.000",
        "2020:020:00:13:00.000",
        23.5 * u.min,
        2,
        ["2020:020:00:12:00.000", "2020:020:00:13:00.000"],
    )


def test_linspace_negative_range():
    """Test that the result is correct when stop < start"""
    start = CxoTime("2000:005")
    stop = CxoTime("2000:001")
    dt_max = 24 * u.hour
    result = CxoTime.linspace(start, stop, step_max=dt_max)
    assert len(result) == 5
    expected_values = ["2000:005", "2000:004", "2000:003", "2000:002", "2000:001"]
    assert np.all(result == CxoTime(expected_values))


def test_linspace_big_step():
    """Test that the result is correct when the step is larger than the range."""
    start = CxoTime("2020:001")
    stop = CxoTime("2020:005")
    dt_max = 30 * u.day
    result = CxoTime.linspace(start, stop, step_max=dt_max)
    assert len(result) == 2
    assert np.all(result == CxoTime(["2020:001", "2020:005"]))


def test_linspace_zero_step():
    """Test that an error is raised if step_max is zero."""
    start = CxoTime("2020:001")
    stop = CxoTime("2020:005")
    dt_max = 0 * u.day
    with pytest.raises(ValueError, match="step_max must be positive nonzero"):
        CxoTime.linspace(start, stop, step_max=dt_max)


def test_linspace_negative_step():
    """Test that an error is raised if step_max is negative."""
    start = CxoTime("2020:001")
    stop = CxoTime("2020:005")
    dt_max = -1 * u.day
    with pytest.raises(ValueError, match="step_max must be positive nonzero"):
        CxoTime.linspace(start, stop, step_max=dt_max)


def test_linspace_num_0():
    """Test that an error is raised if num is zero."""
    start = CxoTime("2000:001")
    stop = CxoTime("2000:005")
    num = 0
    with pytest.raises(ValueError, match="num must be positive nonzero"):
        CxoTime.linspace(start, stop, num=num)


def test_linspace_num_neg():
    """Test that an error is raised if num is negative."""
    start = CxoTime("2000:001")
    stop = CxoTime("2000:005")
    num = -1
    with pytest.raises(ValueError, match="num must be positive nonzero"):
        CxoTime.linspace(start, stop, num=num)


def test_linspace_num_1():
    start = CxoTime("2000:001")
    stop = CxoTime("2000:005")
    num = 2
    result = CxoTime.linspace(start, stop, num=num)
    assert len(result) == num + 1
    expected = ["2000:001", "2000:003", "2000:005"]
    assert np.all(result == CxoTime(expected))


def test_linspace_num_2():
    start = "2000:001"
    stop = "2024:001"
    num = 12
    result = CxoTime.linspace(start, stop, num=num)
    assert len(result) == num + 1
    expected = [
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
    ]
    # There are very small numerical differences between the expected and actual values
    # so this test uses allclose instead of ==.
    assert np.allclose(CxoTime(result).secs, CxoTime(expected).secs)


def test_linspace_num_3():
    start = "2010:001"
    stop = "2011:001"
    num = 12
    result = CxoTime.linspace(start, stop, num=num)
    assert len(result) == num + 1
    expected = [
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
    ]
    # There are very small numerical differences between the expected and actual values
    # so this test uses allclose instead of ==.
    assert np.allclose(CxoTime(result).secs, CxoTime(expected).secs)


def test_missing_args():
    start = "2015:001"
    stop = "2015:002"
    with pytest.raises(
        ValueError, match="exactly one of num and step_max must be defined"
    ):
        CxoTime.linspace(start, stop)


def test_too_many_args():
    start = "2015:001"
    stop = "2015:002"
    with pytest.raises(
        ValueError, match="exactly one of num and step_max must be defined"
    ):
        CxoTime.linspace(start, stop, 1, 2)
