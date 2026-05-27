from datetime import date
import pytest
from skatelog.models import Session, Stance, Trick

@pytest.mark.parametrize("notes,expected_tricks", [
    ("", []),
    (" \t\n", []),
    ("noseslide", [Trick("noseslide")]),
    ("blunt nose grab", [Trick("blunt nose grab")]),
    ("nol bigspin", [Trick("bigspin", stance=Stance.NOLLIE)]),
    ("sw boardslide", [Trick("boardslide", stance=Stance.SWITCH)]),
    ("fakey boardslide", [Trick("boardslide", stance=Stance.FAKIE)]),
    ("3 blunt nose grabs", [Trick("blunt nose grab", count=3)]),
    ("3 switch blunt nose grabs", [Trick("blunt nose grab", stance=Stance.SWITCH, count=3)]),
    ("3 switch blunt nose grabs in the bowl", [Trick("blunt nose grab", stance=Stance.SWITCH, surface="bowl", count=3)]),
    ("3 switch blunt nose grabs on 4' QP", [Trick("blunt nose grab", stance=Stance.SWITCH, surface="4' QP", count=3)]),
    ("nollie bigspin, 2 fakie boardslide", [Trick("bigspin", stance=Stance.NOLLIE), Trick("boardslide", stance=Stance.FAKIE, count=2)]),
    ("switch blunt nose grab (3 regular, 4 switch)", [Trick("blunt nose grab", count=3), Trick("blunt nose grab", stance=Stance.SWITCH, count=4)]),
    ("switch blunt nose grab (3 regular, 4 switch), nollie bigspin", [Trick("bigspin", stance=Stance.NOLLIE), Trick("blunt nose grab", count=3), Trick("blunt nose grab", stance=Stance.SWITCH, count=4)]),
])
def test_trick_parsing(notes: str, expected_tricks: list[Trick]) -> None:
    session = Session(day=date(2026, 1, 1), where="Skatepark", notes=notes)
    tricks = sorted(list(session.tricks), key=lambda it: it.count)
    print(tricks)
    assert tricks == expected_tricks

def test_trick_parsing_empty_when_notes_none() -> None:
    session = Session(day=date(2026, 1, 1), where="Skatepark")
    assert list(session.tricks) == []

def test_trick_parsing_empty_when_not_skated() -> None:
    session = Session(day=date(2026, 1, 1), notes="kickflip")
    assert list(session.tricks) == []
