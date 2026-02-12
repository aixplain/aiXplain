r"""Agent progress tracking and display module.

This module provides real-time progress tracking and formatted display
for agent execution, supporting multiple display formats and verbosity levels.

The tracker supports two display modes:
- Terminal mode: Uses a background thread for smooth 20 FPS spinner animation
- Notebook mode: Updates synchronously on each poll to avoid race conditions
  that can cause out-of-order output in Jupyter/Colab environments

Both modes use carriage return (\r) for in-place line updates.
"""

import json
import sys
import time
import threading
from enum import Enum
from typing import Any, Dict, List, Optional, Callable


# Internal flag to use legacy time format (MM:SS.cc always)
# Set to True to revert to the old behavior where centiseconds are always shown
_USE_LEGACY_TIME_FORMAT = False


def _is_notebook_environment() -> bool:
    """Detect if running in a Jupyter/IPython notebook environment.

    Checks for IPython kernel (Jupyter) or Google Colab environment.
    This is used to determine whether to use background threading for
    spinner animation (which can cause race conditions in notebooks).

    Returns:
        True if running in a notebook environment, False otherwise.
    """
    try:
        from IPython import get_ipython

        ipython = get_ipython()
        if ipython is None:
            return False
        # ZMQInteractiveShell indicates Jupyter notebook kernel
        # TerminalInteractiveShell indicates IPython terminal (not notebook)
        shell_class = ipython.__class__.__name__
        if "ZMQ" in shell_class or "Kernel" in shell_class:
            return True
        # Check for Google Colab
        if "google.colab" in sys.modules:
            return True
        return False
    except (ImportError, AttributeError):
        return False


class ProgressFormat(str, Enum):
    """Display format for agent progress."""

    STATUS = "status"  # Single updating line
    LOGS = "logs"  # Event timeline with details
    NONE = "none"  # No progress display


class AgentProgressTracker:
    """Tracks and displays agent execution progress.

    This class handles real-time progress display during agent execution,
    supporting multiple display formats and verbosity levels.

    Display Modes:
        - Terminal: Background thread updates spinner at 20 FPS for smooth animation
        - Notebook: Synchronous updates on each poll (no background thread) to avoid
          race conditions that cause out-of-order output in Jupyter/Colab

    Attributes:
        poll_func: Callable that polls for agent status
        poll_interval: Time between polls in seconds
        max_polls: Maximum number of polls (None for unlimited)
        format: Display format (status, logs, none)
        verbosity: Detail level (1=minimal, 2=thoughts, 3=full I/O)
        truncate: Whether to truncate long text
    """

    SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    DISPLAY_REFRESH_RATE = 0.05  # 50ms = 20 FPS

    def __init__(
        self,
        poll_func: Callable[[str], Any],
        poll_interval: float = 0.05,
        max_polls: Optional[int] = None,
    ):
        """Initialize the progress tracker.

        Args:
            poll_func: Function that takes a URL and returns poll response
            poll_interval: Time in seconds between polls (default: 0.05)
            max_polls: Maximum number of polls before stopping (default: None)
        """
        self.poll = poll_func
        self.poll_interval = poll_interval
        self.max_polls = max_polls

        # Detect notebook environment once at init time
        self._is_notebook = _is_notebook_environment()

        # Tracking state
        self._seen_steps: Dict[str, Dict] = {}
        self._first_seen: Dict[str, float] = {}
        self._poll_count = 0
        self._total_start_time: Optional[float] = None
        self._total_credits = 0.0
        self._total_api_calls = 0

        # Display state
        self._printed_events: Dict[str, Dict] = {}
        self._printed_thoughts: Dict[int, str] = {}
        self._status_lines_count = 0
        self._spinner_frames: Dict[str, int] = {}  # Per-step frame counter for sequential animation

        # Threading for smooth animation
        self._display_thread: Optional[threading.Thread] = None
        self._stop_display = threading.Event()
        self._display_lock = threading.Lock()
        self._current_display_data: Optional[Dict] = None

        # Display options (set during stream_progress)
        self._format = ProgressFormat.STATUS
        self._verbosity = 1
        self._truncate = True

    def _now(self) -> float:
        """Get current timestamp."""
        return time.time()

    def _get_spinner(self) -> str:
        """Get spinner frame based on elapsed time for smooth animation."""
        elapsed = self._now() - (self._total_start_time or self._now())
        frame_duration = 0.05  # 50ms per frame
        frame_index = int(elapsed / frame_duration) % len(self.SPINNER_FRAMES)
        return self.SPINNER_FRAMES[frame_index]

    def _get_spinner_for_step(self, step_id: str) -> str:
        """Get spinner frame for a specific step with sequential animation.

        This ensures frames advance in order on each call, regardless of timing.
        Used in notebook mode where irregular poll intervals would cause
        time-based spinners to skip frames.
        """
        if step_id not in self._spinner_frames:
            self._spinner_frames[step_id] = 0
        frame_index = self._spinner_frames[step_id]
        self._spinner_frames[step_id] = (frame_index + 1) % len(self.SPINNER_FRAMES)
        return self.SPINNER_FRAMES[frame_index]

    def _parse_steps(self, response: Any) -> List[Dict]:
        """Extract and normalize steps from poll response.

        Args:
            response: Poll response object

        Returns:
            List of normalized step dictionaries
        """
        raw = {}
        if hasattr(response, "to_dict"):
            try:
                raw = response.to_dict()
            except Exception:
                pass
        if not raw and hasattr(response, "_raw_data"):
            raw = response._raw_data or {}

        # Try multiple known locations for steps
        steps = None
        try:
            steps = raw.get("_raw_data", {}).get("data", {}).get("steps")
        except Exception:
            pass

        if steps is None:
            try:
                steps = raw.get("data", {}).get("steps")
            except Exception:
                pass

        if steps is None and hasattr(response, "steps"):
            steps = response.steps

        if not steps:
            return []

        # Normalize steps with unique IDs
        normalized = []
        for i, s in enumerate(steps):
            step = dict(s) if isinstance(s, dict) else s
            sid = step.get("id") or step.get("step_id") or f"idx-{i}"
            step["_progress_id"] = sid
            normalized.append(step)
        return normalized

    def _format_elapsed(self, seconds: Optional[float]) -> str:
        """Format elapsed time as MM:SS.cc."""
        if seconds is None:
            return "--:--.--"
        m = int(seconds // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{m:02d}:{s:02d}.{cs:02d}"

    def _format_elapsed_ticks(self, seconds: Optional[float], is_complete: bool = False) -> str:
        """Format elapsed time with tick precision.

        Args:
            seconds: Elapsed time in seconds
            is_complete: If True, show centiseconds precision; otherwise placeholder

        Returns:
            Formatted time string (e.g., "00:05.--" while running, "00:05.23" when complete)
        """
        if seconds is None:
            return "--:--.--"
        m = int(seconds // 60)
        s = int(seconds % 60)
        if is_complete:
            # Centiseconds precision when complete
            cs = int((seconds % 1) * 100)
            return f"{m:02d}:{s:02d}.{cs:02d}"
        else:
            # Placeholder for centiseconds while running (prevents flicker)
            return f"{m:02d}:{s:02d}.--"

    def _format_multiline(self, text: str, width: int = 70) -> str:
        """Format text with word wrapping and pipe continuation."""
        if not text:
            return ""

        text = str(text).strip()
        lines = []
        paragraphs = text.split("\n")

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if self._truncate:
                words = para.split()
                current_line = ""
                for word in words:
                    if not current_line:
                        current_line = word
                    elif len(current_line) + len(word) + 1 <= width:
                        current_line += " " + word
                    else:
                        lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
            else:
                lines.append(para)

        if not lines:
            return text

        result = "│ " + lines[0]
        for line in lines[1:]:
            result += "\n    │ " + line
        return result

    def _format_json(self, data: Any, indent: int = 2) -> str:
        """Format JSON/dict with pipe indentation."""
        try:
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    return self._format_multiline(data)

            json_str = json.dumps(data, indent=indent)
            lines = json_str.split("\n")

            result = "│ " + lines[0]
            for line in lines[1:]:
                result += "\n    │ " + line
            return result
        except Exception:
            return self._format_multiline(str(data))

    def _format_mentalist_plan(self, output_data: Any) -> Optional[str]:
        """Format Mentalist task plan as a readable numbered list."""
        try:
            if isinstance(output_data, str):
                try:
                    tasks = json.loads(output_data)
                except json.JSONDecodeError:
                    # Cannot parse as JSON, return None to fall back to default formatting
                    return None
            else:
                tasks = output_data

            if not isinstance(tasks, list):
                return None

            formatted_tasks = []
            for task_str in tasks:
                if isinstance(task_str, str):
                    task = json.loads(task_str)
                else:
                    task = task_str

                step_id = task.get("step_id", "?")
                name = task.get("name", "").strip()
                description = task.get("description", "").strip()
                agent = task.get("agent", "")
                expected = task.get("expectedOutput", "").strip()
                deps = task.get("dependencies", [])

                task_lines = []
                if name and description:
                    task_lines.append(f"│ {step_id}. ➤ {name}: {description}")
                elif name:
                    task_lines.append(f"│ {step_id}. ➤ {name}")
                else:
                    task_lines.append(f"│ {step_id}. ➤ {description}")

                task_lines.append(f"│      ⧈ {agent}")

                if expected:
                    task_lines.append(f"│      Expected: {expected}")

                if deps:
                    dep_names = []
                    for dep in deps:
                        if isinstance(dep, dict):
                            dep_name = dep.get("name", "")
                            if dep_name:
                                dep_names.append(dep_name)
                    if dep_names:
                        task_lines.append(f"│      ⤷ depends on: {', '.join(dep_names)}")

                formatted_tasks.append("\n    ".join(task_lines))

            result = "\n    │\n    ".join(formatted_tasks)
            return result

        except Exception:
            return None

    def _get_label(self, step: Dict, field_type: str, step_idx: int) -> str:
        """Determine semantic label based on step context."""
        unit = step.get("unit") or {}
        unit_type = unit.get("type", "").lower() if isinstance(unit, dict) else ""

        agent_field = step.get("agent") or step.get("agent_name") or ""
        if isinstance(agent_field, dict):
            agent_name = agent_field.get("name", "").lower()
        else:
            agent_name = str(agent_field).lower()

        output = step.get("output", "")

        if field_type == "input":
            if step_idx == 0:
                return "Query"
            elif unit_type == "tool":
                return "Input"
            else:
                return "Context"

        elif field_type == "output":
            if "response generator" in agent_name:
                return "Output"
            elif unit_type == "tool":
                return "Result ✓"
            else:
                output_str = str(output).lower()
                if "final answer" in output_str or "final_answer" in output_str:
                    return "Final Action"
                else:
                    return "Plan"

        return "Data"

    def _format_step_line(
        self,
        step: Dict,
        step_idx: int,
        icon: str,
        step_elapsed: Optional[float] = None,
        show_timing: bool = True,
        is_complete: bool = False,
    ) -> str:
        """Format the main step line with proper symbols and structure.

        Args:
            step: Step data dictionary
            step_idx: Step index (0-based)
            icon: Icon to display (spinner or completion icon)
            step_elapsed: Elapsed time for this step
            show_timing: Whether to show timing information
            is_complete: Whether step is complete (affects time_ticks precision)
        """
        agent_field = step.get("agent") or step.get("agent_name") or "Unknown"
        if isinstance(agent_field, dict):
            agent_name = agent_field.get("name") or agent_field.get("id") or str(agent_field)
            is_system_agent = agent_field.get("is_system_agent", False)
        else:
            agent_name = str(agent_field)
            is_system_agent = False

        unit = step.get("unit") or {}
        if isinstance(unit, dict):
            unit_name = unit.get("name") or unit.get("id") or step.get("action") or "Unknown"
            unit_type = unit.get("type", "").lower()
        else:
            unit_name = step.get("action") or str(unit)
            unit_type = ""

        if unit_type == "tool":
            agent_action_part = f"{agent_name} ⚒ {unit_name}"
        else:
            if is_system_agent:
                agent_action_part = f"{agent_name} (⚙) ⧈ {unit_name}"
            else:
                agent_action_part = f"{agent_name} ⧈ {unit_name}"

        step_line = f"{icon} Step {step_idx + 1:2d}"

        if show_timing and step_elapsed is not None:
            if _USE_LEGACY_TIME_FORMAT:
                time_str = self._format_elapsed(step_elapsed)
            else:
                time_str = self._format_elapsed_ticks(step_elapsed, is_complete)
            step_line += f" · ⏱ {time_str}"
            api_calls = step.get("api_calls") or 0
            step_line += f" · API {api_calls:2d}"
            step_credits = step.get("used_credits") or step.get("usedCredits") or 0
            step_line += f" · ${step_credits:.6f}"

        step_line += f" · {agent_action_part}"
        return step_line

    def _display_refresh_loop(self) -> None:
        """Background thread that refreshes display for smooth spinner animation."""
        while not self._stop_display.is_set():
            with self._display_lock:
                if self._current_display_data is None:
                    time.sleep(self.DISPLAY_REFRESH_RATE)
                    continue
                data = self._current_display_data.copy()

            steps = data.get("steps", [])
            if not steps:
                time.sleep(self.DISPLAY_REFRESH_RATE)
                continue

            if self._format == ProgressFormat.STATUS:
                self._refresh_status_display(steps)
            elif self._format == ProgressFormat.LOGS:
                self._refresh_logs_display(steps)

            time.sleep(self.DISPLAY_REFRESH_RATE)

    def _refresh_status_display(self, steps: List[Dict]) -> None:
        """Refresh status mode display (single updating line)."""
        active = steps[-1]
        step_num = len(steps) - 1
        step_elapsed = self._now() - self._first_seen.get(active.get("_progress_id"), self._now())

        has_output = active.get("output")
        is_complete = bool(has_output)
        icon = "✓" if is_complete else self._get_spinner()

        status_line = self._format_step_line(
            active,
            step_num,
            icon,
            step_elapsed,
            show_timing=True,
            is_complete=is_complete,
        )

        if self._verbosity >= 2:
            task = active.get("task")
            if task:
                status_line += f" · ➤ {task}"
            action = active.get("action")
            if action and action != "None":
                status_line += f" · ⚡ {action}"

        if self._verbosity >= 3:
            error = active.get("error") or active.get("error_message")
            if error:
                error_str = str(error).replace("\n", " ").strip()
                if len(error_str) > 50:
                    error_str = error_str[:47] + "..."
                status_line += f" · → Error: {error_str}"
            elif active.get("output"):
                output = active.get("output")
                output_str = str(output).replace("\n", " ").strip()
                if len(output_str) > 50:
                    output_str = output_str[:47] + "..."
                status_line += f" · → {output_str}"

        current_len = len(status_line)
        if self._status_lines_count > 0 and current_len < self._status_lines_count:
            status_line += " " * (self._status_lines_count - current_len)

        print(f"\r{status_line}", end="", flush=True)
        self._status_lines_count = current_len

    def _refresh_logs_display(self, steps: List[Dict]) -> None:
        """Refresh logs mode display (update running step spinners)."""
        for idx, step in enumerate(steps):
            sid = step.get("_progress_id")
            has_output = step.get("output")

            if not has_output and sid in self._printed_events:
                step_elapsed = self._now() - self._first_seen.get(sid, self._now())
                icon = self._get_spinner()
                status_line = self._format_step_line(step, idx, icon, step_elapsed, show_timing=True, is_complete=False)
                print(f"\r{status_line}", end="", flush=True)
                self._printed_events[sid]["status_line"] = status_line

    def _print_step_details(self, step: Dict, idx: int) -> None:
        """Print step details for logs mode (verbosity 2+)."""
        if self._verbosity >= 2:
            task = step.get("task")
            if task:
                print(f"  ➤ {task}")

            action = step.get("action")
            if action and action != "None":
                print(f"  ⚡ {action}")

            thought = step.get("thought") or step.get("reason") or ""
            if thought:
                duplicate_step = None
                for prev_idx, prev_thought in self._printed_thoughts.items():
                    if prev_thought == thought:
                        duplicate_step = prev_idx
                        break

                if duplicate_step is not None:
                    print(f"  ∷ [see Step {duplicate_step + 1}]")
                else:
                    thought_formatted = self._format_multiline(thought, width=70)
                    thought_text = thought_formatted[2:] if thought_formatted.startswith("│ ") else thought_formatted
                    print(f"  ∷ {thought_text}")
                    self._printed_thoughts[idx] = thought

        if self._verbosity >= 3:
            if step.get("input"):
                input_label = self._get_label(step, "input", idx)
                input_data = step.get("input")
                print(f"  ← {input_label}")
                if isinstance(input_data, dict) or (isinstance(input_data, str) and input_data.strip().startswith("{")):
                    print(f"    {self._format_json(input_data)}")
                else:
                    print(f"    {self._format_multiline(str(input_data))}")

            error = step.get("error") or step.get("error_message")
            if error:
                print(f"  → Error ✗")
                print(f"    {self._format_multiline(str(error))}")
            elif step.get("output"):
                output_label = self._get_label(step, "output", idx)
                output_data = step.get("output")
                print(f"  → {output_label}")

                agent_field = step.get("agent") or step.get("agent_name") or ""
                if isinstance(agent_field, dict):
                    agent_name = agent_field.get("name", "").lower()
                else:
                    agent_name = str(agent_field).lower()

                formatted_plan = None
                if "mentalist" in agent_name and output_label == "Plan":
                    formatted_plan = self._format_mentalist_plan(output_data)

                if formatted_plan:
                    print(f"    {formatted_plan}")
                elif isinstance(output_data, dict) or (
                    isinstance(output_data, str) and output_data.strip().startswith("{")
                ):
                    print(f"    {self._format_json(output_data)}")
                else:
                    print(f"    {self._format_multiline(str(output_data))}")

    def _print_completion_message(self, status: str, steps: List[Dict]) -> None:
        """Print final completion message with stats."""
        total_steps = len(steps) if steps else 0
        total_elapsed = (self._now() - self._total_start_time) if self._total_start_time else 0

        prefix = "\n" if self._format == ProgressFormat.STATUS else ""

        if status == "SUCCESS":
            print(
                f"{prefix}✓ Completed {total_steps} steps · "
                f"⏱ {self._format_elapsed(total_elapsed)} · "
                f"API {self._total_api_calls} · "
                f"${self._total_credits:.6f}"
            )
        elif status in {"FAILED", "ABORTED", "CANCELLED", "ERROR"}:
            print(
                f"{prefix}✗ Agent failed with status: {status} · "
                f"{total_steps} steps · "
                f"⏱ {self._format_elapsed(total_elapsed)} · "
                f"API {self._total_api_calls} · "
                f"${self._total_credits:.6f}"
            )
        else:
            print(
                f"{prefix}⏸ Stopped: reached max polling limit ({self.max_polls}) · "
                f"{total_steps} steps · "
                f"⏱ {self._format_elapsed(total_elapsed)} · "
                f"API {self._total_api_calls} · "
                f"${self._total_credits:.6f}"
            )

    # =========================================================================
    # Hook-based API for integration with resource.sync_poll via on_poll hook
    # =========================================================================

    def start(
        self,
        format: ProgressFormat = ProgressFormat.STATUS,
        verbosity: int = 1,
        truncate: bool = True,
    ) -> None:
        """Start progress tracking (call from before_run hook).

        Args:
            format: Display format (status, logs, none)
            verbosity: Detail level (1=minimal, 2=thoughts, 3=full I/O)
            truncate: Whether to truncate long text
        """
        # Reset tracking state
        self._seen_steps = {}
        self._first_seen = {}
        self._poll_count = 0
        self._total_start_time = self._now()
        self._total_credits = 0.0
        self._total_api_calls = 0
        self._printed_events = {}
        self._printed_thoughts = {}
        self._status_lines_count = 0
        self._spinner_frames = {}

        # Store display options
        self._format = format if isinstance(format, ProgressFormat) else ProgressFormat(format)
        self._verbosity = verbosity
        self._truncate = truncate

        # Reset threading state
        self._stop_display.clear()
        self._current_display_data = None

        # Start display refresh thread for smooth spinner animation
        # Skip threading in notebook environments - it causes display issues
        if self._format != ProgressFormat.NONE and not self._is_notebook:
            self._display_thread = threading.Thread(target=self._display_refresh_loop, daemon=True)
            self._display_thread.start()

    def _update_metrics(self, steps: List[Dict]) -> None:
        """Update tracking metrics from steps data."""
        self._total_credits = 0.0
        self._total_api_calls = 0
        for idx, s in enumerate(steps):
            sid = s.get("_progress_id")
            if sid not in self._first_seen:
                self._first_seen[sid] = self._now()
            self._seen_steps[sid] = s

            credits = s.get("used_credits") or s.get("usedCredits") or 0
            if credits:
                self._total_credits += float(credits)

            api_calls = s.get("api_calls") or 0
            if api_calls:
                self._total_api_calls += int(api_calls)

    def _display_logs_format(self, steps: List[Dict]) -> None:
        """Handle display for LOGS format (event timeline)."""
        for idx, step in enumerate(steps):
            sid = step.get("_progress_id")
            prev = self._printed_events.get(sid, {})
            has_output = step.get("output")
            prev_has_output = prev.get("has_output", False)

            # First time seeing this step - show spinner
            if sid not in self._printed_events:
                step_elapsed = self._now() - self._first_seen.get(sid, self._now())
                icon = self._get_spinner()
                status_line = self._format_step_line(step, idx, icon, step_elapsed, show_timing=True, is_complete=False)
                print(f"\r{status_line}", end="", flush=True)
                self._printed_events[sid] = {
                    "has_output": False,
                    "status_line": status_line,
                }

            # In notebook mode, update spinner synchronously (no background thread)
            # Use sequential spinner to prevent frame skipping from irregular poll intervals
            elif not has_output and self._is_notebook:
                step_elapsed = self._now() - self._first_seen.get(sid, self._now())
                icon = self._get_spinner_for_step(sid)
                status_line = self._format_step_line(step, idx, icon, step_elapsed, show_timing=True, is_complete=False)
                print(f"\r{status_line}", end="", flush=True)

            # Step completed - show completion icon
            if has_output and not prev_has_output:
                step_elapsed = self._now() - self._first_seen.get(sid, self._now())
                has_error = step.get("error") or step.get("error_message")
                completion_icon = "✗" if has_error else "✓"
                completion_line = self._format_step_line(
                    step,
                    idx,
                    completion_icon,
                    step_elapsed,
                    show_timing=True,
                    is_complete=True,
                )
                print(f"\r{completion_line}")
                self._print_step_details(step, idx)
                self._printed_events[sid]["has_output"] = True

    def _display_status_format_notebook(self, steps: List[Dict]) -> None:
        """Handle display for STATUS format in notebook mode (synchronous updates)."""
        if not steps:
            return

        active = steps[-1]
        sid = active.get("_progress_id")
        step_num = len(steps) - 1
        has_output = active.get("output")
        is_complete = bool(has_output)
        step_elapsed = self._now() - self._first_seen.get(sid, self._now())

        # Use sequential spinner to prevent frame skipping from irregular poll intervals
        icon = "✓" if is_complete else self._get_spinner_for_step(sid)
        status_line = self._format_step_line(
            active,
            step_num,
            icon,
            step_elapsed,
            show_timing=True,
            is_complete=is_complete,
        )

        # Pad to overwrite previous longer lines
        current_len = len(status_line)
        if self._status_lines_count > 0 and current_len < self._status_lines_count:
            status_line += " " * (self._status_lines_count - current_len)

        print(f"\r{status_line}", end="", flush=True)
        self._status_lines_count = current_len

        if sid not in self._printed_events:
            self._printed_events[sid] = {"has_output": False}
        if has_output:
            self._printed_events[sid]["has_output"] = True

    def update(self, response: Any) -> None:
        """Update progress with poll response (call from on_poll hook).

        Args:
            response: Poll response from agent execution
        """
        if self._format == ProgressFormat.NONE:
            return

        self._poll_count += 1
        steps = self._parse_steps(response)

        if not steps:
            return

        # Update metrics
        self._update_metrics(steps)

        # Update shared display data for background thread (terminal mode)
        with self._display_lock:
            self._current_display_data = {"steps": steps}

        # Handle display based on format
        if self._format == ProgressFormat.LOGS:
            self._display_logs_format(steps)
        elif self._format == ProgressFormat.STATUS and self._is_notebook:
            self._display_status_format_notebook(steps)

    def finish(self, response: Any) -> None:
        """Finish progress tracking and print completion (call from after_run hook).

        Args:
            response: Final response from agent execution
        """
        # Stop display thread
        self._stop_display.set()
        if self._display_thread and self._display_thread.is_alive():
            self._display_thread.join(timeout=1.0)

        if self._format == ProgressFormat.NONE:
            return

        # Get final status and steps
        status = getattr(response, "status", None)
        status_up = (str(status) if status else "").upper()
        steps = self._parse_steps(response)

        # Print completion message
        self._print_completion_message(status_up, steps)

    def stream_progress(
        self,
        url: str,
        format: ProgressFormat = ProgressFormat.STATUS,
        verbosity: int = 1,
        truncate: bool = True,
    ) -> Any:
        """Stream agent progress until completion (standalone polling mode).

        This method implements its own polling loop and is used for standalone
        progress streaming. For integration with existing polling (via on_poll hook),
        use the start/update/finish methods instead.

        Args:
            url: Polling URL to check for updates
            format: Display format (status, logs, none)
            verbosity: Detail level (1=minimal, 2=thoughts, 3=full I/O)
            truncate: Whether to truncate long text

        Returns:
            Final response from the agent
        """
        terminal_success = "SUCCESS"
        terminal_failures = {"FAILED", "ABORTED", "CANCELLED", "ERROR"}

        # Initialize state using start()
        self.start(format=format, verbosity=verbosity, truncate=truncate)
        # Override _total_start_time to None - will be set on first steps
        self._total_start_time = None

        try:
            while True:
                resp = self.poll(url)
                status = getattr(resp, "status", None)
                status_up = (str(status) if status else "").upper()

                steps = self._parse_steps(resp)

                if steps and self._total_start_time is None:
                    self._total_start_time = self._now()

                # Update metrics and display using shared logic
                if steps:
                    self._poll_count += 1
                    self._update_metrics(steps)

                    # Update shared display data for background thread (terminal mode)
                    with self._display_lock:
                        self._current_display_data = {"steps": steps}

                    # Handle display based on format
                    if self._format == ProgressFormat.LOGS:
                        self._display_logs_format(steps)
                    elif self._format == ProgressFormat.STATUS and self._is_notebook:
                        self._display_status_format_notebook(steps)

                # Check termination conditions
                if status_up == terminal_success:
                    if self._format != ProgressFormat.NONE:
                        self._print_completion_message(status_up, steps)
                    return resp

                if status_up in terminal_failures:
                    if self._format != ProgressFormat.NONE:
                        self._print_completion_message(status_up, steps)
                    return resp

                if self.max_polls is not None and self._poll_count >= self.max_polls:
                    if self._format != ProgressFormat.NONE:
                        self._print_completion_message("MAX_POLLS", steps)
                    return resp

                time.sleep(self.poll_interval)

        finally:
            self._stop_display.set()
            if self._display_thread and self._display_thread.is_alive():
                self._display_thread.join(timeout=1.0)
