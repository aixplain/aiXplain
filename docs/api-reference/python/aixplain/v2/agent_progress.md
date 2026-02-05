---
sidebar_label: agent_progress
title: aixplain.v2.agent_progress
---

Agent progress tracking and display module.

This module provides real-time progress tracking and formatted display
for agent execution, supporting multiple display formats and verbosity levels.

The tracker supports two display modes:
- Terminal mode: Uses a background thread for smooth 20 FPS spinner animation
- Notebook mode: Updates synchronously on each poll to avoid race conditions
  that can cause out-of-order output in Jupyter/Colab environments

Both modes use carriage return (\r) for in-place line updates.

### ProgressFormat Objects

```python
class ProgressFormat(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L56)

Display format for agent progress.

#### STATUS

Single updating line

#### LOGS

Event timeline with details

#### NONE

No progress display

### AgentProgressTracker Objects

```python
class AgentProgressTracker()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L64)

Tracks and displays agent execution progress.

This class handles real-time progress display during agent execution,
supporting multiple display formats and verbosity levels.

Display Modes:
- Terminal: Background thread updates spinner at 20 FPS for smooth animation
- Notebook: Synchronous updates on each poll (no background thread) to avoid
race conditions that cause out-of-order output in Jupyter/Colab

**Attributes**:

- `poll_func` - Callable that polls for agent status
- `poll_interval` - Time between polls in seconds
- `max_polls` - Maximum number of polls (None for unlimited)
- `format` - Display format (status, logs, none)
- `verbosity` - Detail level (1=minimal, 2=thoughts, 3=full I/O)
- `truncate` - Whether to truncate long text

#### DISPLAY\_REFRESH\_RATE

50ms = 20 FPS

#### \_\_init\_\_

```python
def __init__(poll_func: Callable[[str], Any],
             poll_interval: float = 0.05,
             max_polls: Optional[int] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L87)

Initialize the progress tracker.

**Arguments**:

- `poll_func` - Function that takes a URL and returns poll response
- `poll_interval` - Time in seconds between polls (default: 0.05)
- `max_polls` - Maximum number of polls before stopping (default: None)

#### start

```python
def start(format: ProgressFormat = ProgressFormat.STATUS,
          verbosity: int = 1,
          truncate: bool = True) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L626)

Start progress tracking (call from before_run hook).

**Arguments**:

- `format` - Display format (status, logs, none)
- `verbosity` - Detail level (1=minimal, 2=thoughts, 3=full I/O)
- `truncate` - Whether to truncate long text

#### update

```python
def update(response: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L764)

Update progress with poll response (call from on_poll hook).

**Arguments**:

- `response` - Poll response from agent execution

#### finish

```python
def finish(response: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L792)

Finish progress tracking and print completion (call from after_run hook).

**Arguments**:

- `response` - Final response from agent execution

#### stream\_progress

```python
def stream_progress(url: str,
                    format: ProgressFormat = ProgressFormat.STATUS,
                    verbosity: int = 1,
                    truncate: bool = True) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L814)

Stream agent progress until completion (standalone polling mode).

This method implements its own polling loop and is used for standalone
progress streaming. For integration with existing polling (via on_poll hook),
use the start/update/finish methods instead.

**Arguments**:

- `url` - Polling URL to check for updates
- `format` - Display format (status, logs, none)
- `verbosity` - Detail level (1=minimal, 2=thoughts, 3=full I/O)
- `truncate` - Whether to truncate long text
  

**Returns**:

  Final response from the agent

