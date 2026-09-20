from dataclasses import dataclass

from app.starter_pack import DEFAULT_PACK


@dataclass(frozen=True)
class SyntheticOptions:
    mode: str = "normal"
    interval: int = 60
    steps: int = 0
    buildings: str | None = None


@dataclass(frozen=True)
class SourceOptions:
    pack: str = str(DEFAULT_PACK)
    acceleration: float = 60
    wait_for_rule: bool = False
    steps: int = 0
    buildings: str | None = None
