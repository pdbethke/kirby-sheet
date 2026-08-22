"""What a character sheet says, as data.

The spine of every output backend. JSON serialises it, text and HTML render
it, and the .hde backend fills a template from it. It holds no logic, does no
I/O, and imports nothing from kirby-cost — a backend depending on this must
not thereby depend on the engine.

Everything here is frozen. A backend must not be able to edit the sheet while
rendering it: Hero Designer's own exporter mutates objects as it renders, and
reproducing that was the single hardest thing about reaching display parity in
kirby-cost. This design does not inherit it.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Identity:
    """The fields at the top of the sheet."""
    name: str = ""
    alternate_identities: str = ""
    player_name: str = ""
    campaign_name: str = ""
    genre: str = ""
    gm: str = ""
    hair_color: str = ""
    eye_color: str = ""


@dataclass(frozen=True)
class CharacteristicRow:
    """One row of the characteristics block."""
    xmlid: str
    name: str
    value: int
    base: int
    cost: int
    active_cost: int
    total: str          # already a display string in kirby-cost
    roll: str           # already a display string in kirby-cost
    notes: str


@dataclass(frozen=True)
class Entry:
    """One purchased thing: a power, skill, perk, talent, complication.

    Two costs, deliberately. `cost` is what the character pays once its
    framework has had its say — a slot in a Variable Power Pool costs zero,
    because the pool already bought the capacity. `cost_before_framework` is
    what the thing costs on its own, which is the number a reader expects to
    see printed beside it. Collapsing them into one field would force every
    backend to guess which it had.
    """
    id: str
    name: str
    alias: str
    xmlid: str
    display: str        # kirby-cost's column2_output, already exact
    cost: int
    cost_before_framework: int
    active_cost: int
    end: int


@dataclass(frozen=True)
class Section:
    """A named run of entries — powers, skills, perks, and so on."""
    name: str
    entries: tuple[Entry, ...] = ()

    def __post_init__(self) -> None:
        # A tuple ANNOTATION is not enforced at runtime, so `frozen=True`
        # alone leaves a caller free to pass a list and mutate it afterwards
        # -- "frozen in name only", which is the thing this module's docstring
        # warns against. Coercing here makes the guarantee real rather than
        # advisory. object.__setattr__ because the instance is frozen.
        object.__setattr__(self, "entries", tuple(self.entries))


@dataclass(frozen=True)
class Totals:
    """The numbers at the foot of the sheet."""
    total_points: float = 0.0
    available_points: float = 0.0
    base_points: float = 0.0
    complication_points: float = 0.0
    experience: float = 0.0


@dataclass(frozen=True)
class Sheet:
    """One character, as a sheet says it."""
    identity: Identity = field(default_factory=Identity)
    characteristics: tuple[CharacteristicRow, ...] = ()
    sections: tuple[Section, ...] = ()
    totals: Totals = field(default_factory=Totals)

    def __post_init__(self) -> None:
        # A tuple ANNOTATION is not enforced at runtime, so `frozen=True`
        # alone leaves a caller free to pass a list and mutate it afterwards
        # -- "frozen in name only", which is the thing this module's docstring
        # warns against. Coercing here makes the guarantee real rather than
        # advisory. object.__setattr__ because the instance is frozen.
        object.__setattr__(self, "characteristics", tuple(self.characteristics))
        object.__setattr__(self, "sections", tuple(self.sections))
