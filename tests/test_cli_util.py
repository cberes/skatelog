from datetime import date
import pytest
from skatelog.cli_util import date_range, find_by_startswith, find_disciplines, new_tricks, streak
from skatelog.models import Session, Stance, Trick

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
    result = find_by_startswith("-", ["a"])
    assert result.found is None
    assert not result.found

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
    result = find_by_startswith(test_input, ["APPLE", "BANANA", "CHERRY", "CAKE"])
    assert result.found == expected
    assert not result.new

def test_find_by_startswith_with_unknown_inputs() -> None:
    result = find_by_startswith("orAnge", ["APPLE", "BANANA", "CHERRY"])
    assert result.found == "orAnge"
    assert result.new

@pytest.mark.parametrize("test_input", ["  a  ,Ba, H, rA,t ", "a,ba,h,ra,t"])
def test_find_disciplines_with_valid_disciplines(test_input: str) -> None:
    result = find_disciplines("  a  ,Ba, H, rA,t ")
    assert result.found == {"a_frame": True, "bank": True, "hip": True, "rail": True, "transition": True}
    assert result.ambiguous == []
    assert result.unknown == []

def test_find_disciplines_with_none() -> None:
    result = find_disciplines(None)
    assert result.found == {}
    assert result.ambiguous == []
    assert result.unknown == []

@pytest.mark.parametrize("test_input", ["-", "c"])
def test_find_disciplines_with_unknown_inputs(test_input: str) -> None:
    result = find_disciplines(test_input)
    assert result.found == {}
    assert result.ambiguous == []
    assert result.unknown == [test_input]

@pytest.mark.parametrize("test_input", ["", ",", ",,,,", " , ,\n\n,\t\t"])
def test_find_disciplines_with_space_inputs(test_input: str) -> None:
    result = find_disciplines(test_input)
    assert result.found == {}
    assert result.ambiguous == []
    assert result.unknown == []

def test_find_disciplines_with_ambiguous_inputs() -> None:
    result = find_disciplines("a,bo,m,f")
    assert result.found == {"a_frame": True, "manual": True}
    assert result.ambiguous == ["bo", "f"]
    assert result.unknown == []

def test_streak_when_empty() -> None:
    assert streak([]) == (0, [])

def test_streak_when_not_skated() -> None:
    days = (date(2026, 1, i) for i in range(1, 10))
    sessions = (Session(day=d) for d in days)
    assert streak(sessions) == (0, [])

def test_streak_when_skated_every_day() -> None:
    days = [date(2026, 1, i) for i in range(1, 10)]
    sessions = (Session(day=d, flat=True) for d in days)
    assert streak(sessions) == (9, [(days[i], i + 1) for i in range(0, len(days))])

def test_streak_sorts_sessions() -> None:
    days = [date(2026, 1, i) for i in range(1, 10)]
    sessions = (Session(day=d, flat=True) for d in reversed(days))
    assert streak(sessions) == (9, [(days[i], i + 1) for i in range(0, len(days))])

def test_streak_detects_breaks() -> None:
    sessions = [
        Session(day=date(2026, 1, 1), flat=True),
        Session(day=date(2026, 1, 2), flat=True),
        Session(day=date(2026, 1, 3), flat=True),
        Session(day=date(2026, 1, 6), flat=True),
    ]
    expected = [
        (date(2026, 1, 1), 1),
        (date(2026, 1, 2), 2),
        (date(2026, 1, 3), 3),
        (date(2026, 1, 4), 0),
        (date(2026, 1, 5), 0),
        (date(2026, 1, 6), 1),
    ]
    assert streak(sessions) == (3, expected)

def test_streak_updates_best_streak() -> None:
    sessions = [
        Session(day=date(2026, 1, 1), flat=True),
        Session(day=date(2026, 1, 2), flat=True),
        Session(day=date(2026, 1, 3), flat=True),
        Session(day=date(2026, 1, 6), flat=True),
        Session(day=date(2026, 1, 7), flat=True),
        Session(day=date(2026, 1, 8), flat=True),
        Session(day=date(2026, 1, 9), flat=True),
    ]
    expected = [
        (date(2026, 1, 1), 1),
        (date(2026, 1, 2), 2),
        (date(2026, 1, 3), 3),
        (date(2026, 1, 4), 0),
        (date(2026, 1, 5), 0),
        (date(2026, 1, 6), 1),
        (date(2026, 1, 7), 2),
        (date(2026, 1, 8), 3),
        (date(2026, 1, 9), 4),
    ]
    assert streak(sessions) == (4, expected)

def test_new_tricks_when_empty() -> None:
    assert list(new_tricks([])) == []

def test_new_tricks_ignores_count() -> None:
    tricks = [
        Trick(day=date(2026, 1, 1), name="kickflip", count=10),
        Trick(day=date(2026, 1, 2), name="kickflip", count=100),
        Trick(day=date(2026, 1, 3), name="kickflip", count=1),
    ]
    assert list(new_tricks(tricks)) == tricks[:1]

def test_new_tricks_ignores_id() -> None:
    tricks = [
        Trick(day=date(2026, 1, 1), name="kickflip", id=10),
        Trick(day=date(2026, 1, 2), name="kickflip", id=100),
        Trick(day=date(2026, 1, 3), name="kickflip", id=1),
    ]
    assert list(new_tricks(tricks)) == tricks[:1]

def test_new_tricks_considers_stance() -> None:
    tricks = [
        Trick(day=date(2026, 1, 1), name="kickflip", stance=Stance.REGULAR),
        Trick(day=date(2026, 1, 2), name="kickflip", stance=Stance.SWITCH),
        Trick(day=date(2026, 1, 3), name="kickflip", stance=Stance.NOLLIE),
    ]
    assert list(new_tricks(tricks)) == tricks

def test_new_tricks_considers_surface() -> None:
    tricks = [
        Trick(day=date(2026, 1, 1), name="kickflip", surface="A-frame"),
        Trick(day=date(2026, 1, 2), name="kickflip", surface="hip"),
        Trick(day=date(2026, 1, 3), name="kickflip", surface="euro gap"),
    ]
    assert list(new_tricks(tricks)) == tricks

def test_new_tricks_excludes_surfaceless_trick_when_surface_trick_present() -> None:
    tricks = [
        Trick(day=date(2026, 1, 1), name="kickflip", surface="A-frame"),
        Trick(day=date(2026, 1, 2), name="kickflip"),
    ]
    assert list(new_tricks(tricks)) == tricks[:1]

def test_new_tricks_includes_surface_trick_when_surfaceless_trick_present() -> None:
    tricks = [
        Trick(day=date(2026, 1, 1), name="kickflip"),
        Trick(day=date(2026, 1, 2), name="kickflip", surface="A-frame"),
    ]
    assert list(new_tricks(tricks)) == tricks

def test_new_tricks_considers_name() -> None:
    tricks = [
        Trick(day=date(2026, 1, 1), name="kickflip"),
        Trick(day=date(2026, 1, 2), name="heelflip"),
        Trick(day=date(2026, 1, 3), name="ollie"),
    ]
    assert list(new_tricks(tricks)) == tricks
