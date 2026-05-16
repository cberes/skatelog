# from __future__ import annotations

from datetime import date
from enum import auto, StrEnum
from sqlmodel import Field, SQLModel
from typing import Self


class Discipline(StrEnum):
    A_FRAME = auto()
    BANK = auto()
    BOWL = auto()
    BOX = auto()
    FLAT = auto()
    HIP = auto()
    MANUAL = auto()
    RAIL = auto()
    SLAPPY = auto()
    TRANSITION = auto()

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
    hip: bool = False
    manual: bool = False
    rail: bool = False
    slappy: bool = False
    transition: bool = False

    where: str | None = None
    shoe: str | None = None
    board: str | None = None
    notes: str | None = None

    @property
    def disciplines(self) -> set[Discipline]:
        flags: dict[Discipline, bool] = {
            Discipline.A_FRAME: self.flat,
            Discipline.BANK: self.bank,
            Discipline.BOWL: self.bowl,
            Discipline.BOX: self.box,
            Discipline.FLAT: self.flat,
            Discipline.HIP: self.hip,
            Discipline.MANUAL: self.manual,
            Discipline.RAIL: self.rail,
            Discipline.SLAPPY: self.slappy,
            Discipline.TRANSITION: self.transition,
        }
        return {s for s, on in flags.items() if on}

    @property
    def skated(self) -> bool:
        return bool(self.disciplines) or any([self.where, self.shoe, self.board])
