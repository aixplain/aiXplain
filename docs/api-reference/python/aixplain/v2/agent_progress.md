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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L87)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L95)

Tracks and displays agent execution progress.

This class handles real-time progress display during agent execution,
supporting multiple display formats and verbosity levels.

Display Modes:
- Terminal: Background thread updates spinner at 20 FPS for smooth animation
- Notebook: Synchronous updates on each poll (no background thread) to avoid
race conditions that cause out-of-order output in Jupyter/Colab

**Attributes**:

- `poll_func` - Callable that polls for agent status
- `poll_interval` - Starting time between polls in seconds (backed off by
  ``stream_progress``)
- `max_polls` - Maximum number of polls (None for unlimited)
- `format` - Display format (status, logs, none)
- `verbosity` - Detail level (1=minimal, 2=thoughts, 3=full I/O)
- `truncate` - Whether to truncate long text

#### DISPLAY\_REFRESH\_RATE

50ms = 20 FPS

#### \_\_init\_\_

```python
def __init__(poll_func: Callable[[str], Any],
             poll_interval: float = DEFAULT_POLL_INTERVAL,
             max_polls: Optional[int] = None,
             force_display: Optional[bool] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L138)

Initialize the progress tracker.

**Arguments**:

- `poll_func` - Function that takes a URL and returns poll response
- `poll_interval` - Starting time in seconds between polls in
  :meth:`stream_progress`, which backs it off from there
- `(default` - 0.5). Unused by the start/update/finish flow, where
  the caller&#x27;s own poll loop owns the interval.
- `max_polls` - Maximum number of polls before stopping (default: None)
- `force_display` - Override the terminal auto-detection for the
  animated repaint thread. ``None`` (default) animates only when
  stdout is a TTY or we are in a notebook; ``True`` always
  animates, ``False`` never does. The caller-thread output --
  the ``logs`` step timeline and the completion summary -- is
  written regardless, so a piped or captured run still gets a
  full, newline-terminated record.

#### stop

```python
def stop() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L219)

Stop the display thread and wait for it to exit.

Idempotent, safe from any thread, and safe on a tracker that never
started a thread. Deliberately renders nothing: stopping the thread and
printing a completion summary used to be the same call (``finish()``),
so skipping the summary on an errored run skipped the stop too and
leaked a thread that printed 20 times a second forever (BUG-943).

#### start

```python
def start(format: ProgressFormat = ProgressFormat.STATUS,
          verbosity: int = 1,
          truncate: bool = True,
          force_display: Optional[bool] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L783)

Start progress tracking (call from before_run hook).

**Arguments**:

- `format` - Display format (status, logs, none)
- `verbosity` - Detail level (1=minimal, 2=thoughts, 3=full I/O)
- `truncate` - Whether to truncate long text
- `force_display` - Override the terminal auto-detection for the
  animated repaint thread on this run. ``None`` keeps whatever
  was passed to ``__init__``.

#### update

```python
def update(response: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L965)

Update progress with poll response (call from on_poll hook).

**Arguments**:

- `response` - Poll response from agent execution

#### finish

```python
def finish(response: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L993)

Finish progress tracking and print completion (call from after_run hook).

**Arguments**:

- `response` - Final response from agent execution

#### stream\_progress

```python
def stream_progress(url: str,
                    format: ProgressFormat = ProgressFormat.STATUS,
                    verbosity: int = 1,
                    truncate: bool = True,
                    timeout: Optional[float] = DEFAULT_STREAM_TIMEOUT) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/agent_progress.py#L1012)

Stream agent progress until completion (standalone polling mode).

This method implements its own polling loop and is used for standalone
progress streaming. For integration with existing polling (via on_poll hook),
use the start/update/finish methods instead.

The poll interval starts at ``self.poll_interval`` and is backed off by
10% per poll (capped at 60s) with jitter, so a fleet of clients started
together does not stay phase-locked (BUG-942).

**Arguments**:

- `url` - Polling URL to check for updates
- `format` - Display format (status, logs, none)
- `verbosity` - Detail level (1=minimal, 2=thoughts, 3=full I/O)
- `truncate` - Whether to truncate long text
- `timeout` - Wall-clock budget in seconds (default: 300). On expiry
  ``TimeoutError`` is raised, matching ``sync_poll``: a run that
  is still IN_PROGRESS is not a result, and returning one made the
  two polling surfaces disagree about what a timeout means. Pass
  ``None`` for the previous unbounded behaviour.
  

**Returns**:

  Final response from the agent, or the last polled response if
  ``max_polls`` was reached first.
  

**Raises**:

- ``5 - If *timeout* elapses before the run reaches a terminal
  status.

