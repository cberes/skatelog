from collections.abc import Iterator
from datetime import date
import pytest
from skatelog.cli_util import find_by_startswith, find_disciplines, date_range
from skatelog.models import Discipline

def test_date_range_returns_min_max_as_default() -> None:
    start, end = date_range(None, None)
    assert start == date.min
    assert end == date.max

def test_date_range_with_month() -> None:
    start, end = date_range("2026-04", None)
    assert start == date(2026, 4, 1)
    assert end == date(2026, 5, 1)

def test_date_range_with_year() -> None:
    start, end = date_range(None, "2026")
    assert start == date(2026, 1, 1)
    assert end == date(2027, 1, 1)

def test_find_by_startswith_returns_none_when_value_is_dash() -> None:
    found = find_by_startswith("-", ["a"], lambda x: None)
    assert found is None

@pytest.mark.parametrize("test_input,expected", [
    ("a", "APPLE"),
    ("aP", "APPLE"),
    ("aPp", "APPLE"),
    ("aPpL", "APPLE"),
    ("aPpLe", "APPLE"),
    ("b", "BANANA"),
    ("c", "CHERRY"),
    ("ch", "CHERRY"),
    ("ca", "CAKE"),
])
def test_find_by_startswith_with_known_inputs(test_input: str, expected: str) -> None:
    marker = []
    found = find_by_startswith(test_input, ["APPLE", "BANANA", "CHERRY", "CAKE"], lambda x: marker.append(x))
    assert found == expected
    assert marker == []

def test_find_by_startswith_with_unknown_inputs() -> None:
    marker = []
    found = find_by_startswith("orAnge", ["APPLE", "BANANA", "CHERRY"], lambda x: marker.append(x))
    assert found == "orAnge"
    assert marker == ["orAnge"]

@pytest.mark.parametrize("test_input", ["  a  ,Ba, H, rA,t ", "a,ba,h,ra,t"])
def test_find_disciplines_with_valid_disciplines(test_input: str) -> None:
    marker = []
    found = find_disciplines("  a  ,Ba, H, rA,t ", lambda x: marker.append(x))
    assert found == {"a_frame": True, "bank": True, "hip": True, "rail": True, "transition": True}
    assert marker == []

def test_find_disciplines_with_none() -> None:
    marker = []
    found = find_disciplines(None, lambda x: marker.append(x))
    assert found == {}
    assert marker == []

# TODO IDK if this is good, but it's how it works :shrug:
@pytest.mark.parametrize("test_input", ["-", "c"])
def test_find_disciplines_with_unknown_inputs(test_input: str) -> None:
    marker = []
    found = find_disciplines(test_input, lambda x: marker.append(x))
    assert found == {}
    assert marker == []

@pytest.mark.parametrize("test_input", ["", ",", ",,,,", " , ,\n\n,\t\t"])
def test_find_disciplines_with_space_inputs(test_input: str) -> None:
    marker = []
    found = find_disciplines(test_input, lambda x: marker.append(x))
    assert found == {}
    assert marker == []

def test_find_disciplines_with_ambiguous_inputs() -> None:
    marker = []
    found = find_disciplines("a,bo,m,f", lambda x: marker.append(x))
    assert found == {"a_frame": True, "manual": True}
    assert marker == ["bo", "f"]

