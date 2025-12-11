---
sidebar_label: evolve_type
title: aixplain.enums.evolve_type
---

### EvolveType Objects

```python
class EvolveType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/evolve_type.py#L4)

Enumeration of evolution types for team agents.

This enum defines the available evolution strategies that can be applied
to team agents during the evolution process. Each type represents a
different approach to improving agent performance.

**Attributes**:

- `TEAM_TUNING` _str_ - Evolution strategy focused on tuning team-level
  configurations and interactions between agents.
- `INSTRUCTION_TUNING` _str_ - Evolution strategy focused on refining
  individual agent instructions and prompts.

