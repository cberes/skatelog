from datetime import date
import pytest
from skatelog.models import Session, Stance, Trick

DAY = date(2026, 1, 1)

@pytest.mark.parametrize("notes,expected_tricks", [
    ("", []),
    (" \t\n", []),
    ("noseslide", [Trick(day=DAY, name="noseslide")]),
    ("blunt nose grab", [Trick(day=DAY, name="blunt nose grab")]),
    ("ollie", [Trick(day=DAY, name="ollie")]),
    ("fakie ollie", [Trick(day=DAY, name="ollie", stance=Stance.FAKIE)]),
    ("nollie", [Trick(day=DAY, name="nollie", stance=Stance.NOLLIE)]),
    ("2 nollies", [Trick(day=DAY, name="nollie", stance=Stance.NOLLIE, count=2)]),
    ("nol bigspin", [Trick(day=DAY, name="bigspin", stance=Stance.NOLLIE)]),
    ("sw boardslide", [Trick(day=DAY, name="boardslide", stance=Stance.SWITCH)]),
    ("fakey boardslide", [Trick(day=DAY, name="boardslide", stance=Stance.FAKIE)]),
    ("switch flip", [Trick(day=DAY, name="kickflip", stance=Stance.SWITCH)]),
    ("3 blunt nose grabs", [Trick(day=DAY, name="blunt nose grab", count=3)]),
    ("3 switch blunt nose grabs", [Trick(day=DAY, name="blunt nose grab", stance=Stance.SWITCH, count=3)]),
    ("3 switch blunt nose grabs in the bowl", [Trick(day=DAY, name="blunt nose grab", stance=Stance.SWITCH, surface="bowl", count=3)]),
    ("3 switch blunt nose grabs on 4' QP", [Trick(day=DAY, name="blunt nose grab", stance=Stance.SWITCH, surface="4' QP", count=3)]),
    ("nollie bigspin, 2 fakie boardslide", [Trick(day=DAY, name="bigspin", stance=Stance.NOLLIE), Trick(day=DAY, name="boardslide", stance=Stance.FAKIE, count=2)]),
    ("switch blunt nose grab (3 regular, 4 switch)", [Trick(day=DAY, name="blunt nose grab", count=3), Trick(day=DAY, name="blunt nose grab", stance=Stance.SWITCH, count=4)]),
    ("switch blunt nose grab (3 regular, 4 switch), nollie bigspin", [Trick(day=DAY, name="bigspin", stance=Stance.NOLLIE), Trick(day=DAY, name="blunt nose grab", count=3), Trick(day=DAY, name="blunt nose grab", stance=Stance.SWITCH, count=4)]),
])
def test_trick_parsing(notes: str, expected_tricks: list[Trick]) -> None:
    session = Session(day=DAY, where="Skatepark", notes=notes)
    session.parse_tricks()
    tricks = sorted(list(session.tricks), key=lambda it: it.count)
    print(tricks)
    assert tricks == expected_tricks

def test_trick_parsing_empty_when_notes_none() -> None:
    session = Session(day=DAY, where="Skatepark")
    session.parse_tricks()
    assert list(session.tricks) == []

def test_trick_parsing_empty_when_not_skated() -> None:
    session = Session(day=DAY, notes="kickflip")
    session.parse_tricks()
    assert list(session.tricks) == []
