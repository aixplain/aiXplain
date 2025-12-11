from enum import Enum


class EvolveType(str, Enum):
    """Enumeration of evolution types for team agents.

    This enum defines the available evolution strategies that can be applied
    to team agents during the evolution process. Each type represents a
    different approach to improving agent performance.

    Attributes:
        TEAM_TUNING (str): Evolution strategy focused on tuning team-level
            configurations and interactions between agents.
        INSTRUCTION_TUNING (str): Evolution strategy focused on refining
            individual agent instructions and prompts.

    """
    TEAM_TUNING = "team_tuning"
    INSTRUCTION_TUNING = "instruction_tuning"
