from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from enum import auto, StrEnum
import re
from sqlmodel import Field, SQLModel
from typing import Self

# TODO: ideally I'd want this to be more flexible, but IDK how to handle that without listing every possible abbreviation
_STANCE_REGEX = "regular|switch|fakie|nollie|reg|regs|sw|fakey|nol"

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


@dataclass
class Trick:
    name: str
    stance: Stance = Stance.REGULAR
    surface: str | None = None
    count: int = 1

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

    # TODO: this is stupid: a regex is probably overkill, and singular words can end with s
    def _singularize(self, s: str) -> str:
        return re.sub("s$", "", s)

    def _clean_surface(self, s: str) -> str:
        step1 = re.sub(r"^\s*(on|in)\s+", "", s)
        return re.sub(r"^\s*(a|the)\s+", "", step1)

    def _parse_trick_comment(self, comment: str) -> Iterator[tuple[int, Stance]]:
        pattern = re.compile(r"(?:^|,)\s*(\d+)\s+(" f"{_STANCE_REGEX}" r")\s*(?=$|,)", re.IGNORECASE)
        matches = pattern.finditer(comment.strip("() "))
        for match in matches:
            groups = match.groups()
            yield (int(groups[0]), Stance(groups[1]))

    @property
    def tricks(self) -> Iterator[Trick]:
        if not self.skated or self.notes is None or self.notes.isspace():
            return
        pattern = re.compile((
                r"(?:^|,)\s*"
                r"(?P<count>\d*)\s*"
                r"(?P<stance>(?:" f"{_STANCE_REGEX}" r")(?=\s+))?\s*"
                r"(?P<name>[^,()]+?)\s*"
                r"(?P<surface>(?:\s+in\s+|\s+on\s+)[^,()]+)?\s*"
                r"(?P<comment>\([^()]+\))?\s*" # TODO: hmm I want to allow commas and nested parentheses, but I don't want this capturing too much
                r"(?=$|,)"
        ), re.IGNORECASE)
        matches = pattern.finditer(self.notes)
        for match in matches:
            groups = {k: v for k, v in match.groupdict().items() if v}
            kwargs = {}
            name = self._singularize(match.group("name"))
            parsed = 0
            if "count" in groups:
                kwargs["count"] = int(groups["count"])
            if "stance" in groups:
                kwargs["stance"] = Stance(groups["stance"])
            if "surface" in groups:
                kwargs["surface"] = self._clean_surface(groups["surface"])
            if "comment" in groups:
                for count, stance in self._parse_trick_comment(groups["comment"]):
                    kwargs["count"] = count
                    kwargs["stance"] = stance
                    yield Trick(name, **kwargs)
                    parsed += 1
            if parsed == 0:
                yield Trick(name, **kwargs)
