from enum import Enum


class EvolveType(str, Enum):
    TEAM_TUNING = "team_tuning"
    INSTRUCTION_TUNING = "instruction_tuning"
