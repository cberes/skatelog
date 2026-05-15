from __future__ import annotations

from datetime import date
from enum import StrEnum
from sqlmodel import Field, SQLModel


class Discipline(StrEnum):
    A_FRAME = "a-frame"
    BANK = "bank"
    BOWL = "bowl"
    BOX = "box"
    FLAT = "flat"
    HIP = "hip"
    MANUAL = "manual"
    RAIL = "rail"
    SLAPPY = "slappy"
    TRANSITION = "transition"


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
