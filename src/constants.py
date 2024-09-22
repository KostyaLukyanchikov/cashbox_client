from enum import StrEnum, auto
from typing import Final


class ColorTheme(StrEnum):
    LIGHT = auto()
    DARK = auto()
    SYSTEM = auto()


class LogLineColor:
    GREY: Final[str] = "#7a7a7a"
    ORANGE: Final[str] = "#ffa500"
    RED: Final[str] = "#ff6347"
