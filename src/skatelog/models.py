from collections.abc import Iterator
from datetime import date
from enum import auto, StrEnum
import re
from sqlmodel import Field, Relationship, SQLModel
from typing import Self

# TODO: ideally I'd want this to be more flexible, but IDK how to handle that without listing every possible abbreviation
_STANCE_REGEX = "regular|switch|fakie|nollie|reg|regs|sw|fakey|nol"

_TRICK_PATTERN = re.compile((
        r"(?:^|,)\s*"
        r"(?P<count>\d*)\s*"
        r"(?P<stance>(?:" f"{_STANCE_REGEX}" r")(?=\s+))?\s*"
        r"(?P<name>[^,()]+?)\s*"
        r"(?P<comment>\([^()]+\))?\s*" # TODO: hmm I want to allow commas and nested parentheses, but I don't want this capturing too much
        r"(?P<surface>(?:\s+(?:at|in|on|over)\s+)[^,()]+)?\s*"
        r"(?=$|,)"
), re.IGNORECASE)

_TRICK_COMMENT_PATTERN = re.compile(r"(?:^|,)\s*(\d+)\s+(" f"{_STANCE_REGEX}" r")\s*(?=$|,)", re.IGNORECASE)

_ON_THE_PATTERN = re.compile(r"^\s*(at|in|on|over)\s+((a|the)\s+)?", re.IGNORECASE)

class Stance(StrEnum):
    REGULAR = auto()
    SWITCH = auto()
    FAKIE = auto()
    NOLLIE = auto()

    @classmethod
    def _missing_(cls, value: object) -> Self | None:
        if not isinstance(value, str):
            return None
        value = value.lower()
        for member in cls:
            if member.value[0:1] == value[0:1]:
                return member
        return None

class Trick(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    day: date = Field(foreign_key="session.day")
    name: str = Field(index=True)
    stance: Stance = Field(default=Stance.REGULAR, index=True)
    surface: str | None = None
    count: int = 1
    session: Session = Relationship(back_populates="tricks")

    def _special_cases(self) -> None:
        """Handles special cases for Trick instances."""
        match self.name.lower():
            case "flip":
                self.name = "kickflip"
            case "nollie":
                self.stance = Stance.NOLLIE

    @classmethod
    def _singularize(cls, s: str) -> str:
        return s[:-1] if s[-1].lower() == "s" else s

    @classmethod
    def _clean_surface(cls, s: str) -> str:
        return _ON_THE_PATTERN.sub("", s)

    @classmethod
    def _parse_trick_comment(cls, comment: str) -> Iterator[tuple[int, Stance]]:
        matches = _TRICK_COMMENT_PATTERN.finditer(comment.strip("() "))
        for match in matches:
            groups = match.groups()
            yield (int(groups[0]), Stance(groups[1]))

    @classmethod
    def parse(cls, day: date, value: str) -> Iterator[Trick]:
        matches = _TRICK_PATTERN.finditer(value)
        for match in matches:
            groups = {k: v for k, v in match.groupdict().items() if v}
            kwargs = {}
            name = cls._singularize(match.group("name"))
            parsed = 0
            if "count" in groups:
                kwargs["count"] = int(groups["count"])
            if "stance" in groups:
                kwargs["stance"] = Stance(groups["stance"])
            if "surface" in groups:
                kwargs["surface"] = cls._clean_surface(groups["surface"])
            if "comment" in groups:
                for count, stance in cls._parse_trick_comment(groups["comment"]):
                    kwargs["count"] = count
                    kwargs["stance"] = stance
                    t = Trick(day=day, name=name, **kwargs)
                    t._special_cases()
                    yield t
                    parsed += 1
            if parsed == 0:
                t = Trick(day=day, name=name, **kwargs)
                t._special_cases()
                yield t


class Discipline(StrEnum):
    A_FRAME = auto()
    BANK = auto()
    BOWL = auto()
    BOX = auto()
    FLAT = auto()
    FREE = auto()
    HIP = auto()
    MANUAL = auto()
    RAIL = auto()
    SLAPPY = auto()
    TRANSITION = auto()
    VERT = auto()

    @classmethod
    def _missing_(cls, value: object) -> Self | None:
        if not isinstance(value, str):
            return None
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        return None


class Session(SQLModel, table=True):
    day: date = Field(primary_key=True)

    a_frame: bool = False
    bank: bool = False
    bowl: bool = False
    box: bool = False
    flat: bool = False
    free: bool = False
    hip: bool = False
    manual: bool = False
    rail: bool = False
    slappy: bool = False
    transition: bool = False
    vert: bool = False

    where: str | None = None
    shoe: str | None = None
    board: str | None = None
    notes: str | None = None
    tricks: list[Trick] = Relationship(back_populates="session", cascade_delete=True)

    @property
    def disciplines(self) -> set[Discipline]:
        flags: dict[Discipline, bool] = {
            Discipline.A_FRAME: self.a_frame,
            Discipline.BANK: self.bank,
            Discipline.BOWL: self.bowl,
            Discipline.BOX: self.box,
            Discipline.FLAT: self.flat,
            Discipline.FREE: self.free,
            Discipline.HIP: self.hip,
            Discipline.MANUAL: self.manual,
            Discipline.RAIL: self.rail,
            Discipline.SLAPPY: self.slappy,
            Discipline.TRANSITION: self.transition,
            Discipline.VERT: self.vert,
        }
        return {s for s, on in flags.items() if on}

    @property
    def skated(self) -> bool:
        return bool(self.disciplines) or any([self.where, self.shoe, self.board])

    @property
    def is_good(self) -> bool:
        return self.skated or bool(self.notes)

    @property
    def trick_count(self) -> int:
        return sum(t.count for t in self.tricks) if self.tricks else 0

    def parse_tricks(self) -> None:
        if not self.skated or self.notes is None or self.notes.isspace():
            return
        self.tricks.extend(Trick.parse(self.day, self.notes))
