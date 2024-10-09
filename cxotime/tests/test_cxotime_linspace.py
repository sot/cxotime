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
def test_get_range_in_chunks(start, stop, dt_max, expected_len, expected_values):
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
def test_get_range_in_chunks_negative():
    start = CxoTime("2000:005")
    stop = CxoTime("2000:001")
    dt_max = 24 * u.hour
    result = CxoTime.linspace(start, stop, step_max=dt_max)
    assert len(result) == 5
    expected_values = ["2000:005", "2000:004", "2000:003", "2000:002", "2000:001"]
    assert all(a == CxoTime(b) for a, b in zip(result, expected_values, strict=False))


# Add a test that shows that the time range is covered even if the time range is less than dt_max
def test_get_range_in_chunks_small():
    start = CxoTime("2020:001")
    stop = CxoTime("2020:005")
    dt_max = 30 * u.day
    result = CxoTime.linspace(start, stop, step_max=dt_max)
    assert len(result) == 2
    assert all(
        a == CxoTime(b) for a, b in zip(result, ["2020:001", "2020:005"], strict=False)
    )


# Add a test that shows we get an error if dt_max is zero
def test_get_range_in_chunks_zero():
    start = CxoTime("2020:001")
    stop = CxoTime("2020:005")
    dt_max = 0 * u.day
    with pytest.raises(ValueError) as excinfo:
        CxoTime.linspace(start, stop, step_max=dt_max)
    assert "step_max must be positive nonzero" in str(excinfo.value)


# Add a test that shows we get an error if dt_max is negative
def test_get_range_in_chunks_negative_dt():
    start = CxoTime("2020:001")
    stop = CxoTime("2020:005")
    dt_max = -1 * u.day
    with pytest.raises(ValueError) as excinfo:
        CxoTime.linspace(start, stop, step_max=dt_max)
    assert "step_max must be positive nonzero" in str(excinfo.value)
