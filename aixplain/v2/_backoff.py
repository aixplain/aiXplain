"""Jittered backoff helpers for v2 poll loops.

Every poll interval in this SDK used to grow deterministically from a shared
start (``wait_time *= 1.1``, capped at 60s), so any batch of clients launched
together -- a CI matrix, a notebook fan-out, or a platform-wide recovery after
an outage -- stayed phase-locked for the whole run and hit the platform in
synchronized waves (BUG-942).  Jitter is what breaks that correlation.

The form used here is *multiplicative and symmetric*: ``wait * U(1-s, 1+s)``.
It preserves the mean poll rate, so no individual run gets slower on average,
and it scales correctly across an interval range that spans 300x (0.2s to 60s)
-- unlike additive jitter, which would be a 500% perturbation at the bottom of
that range and noise at the top.
"""

import random
import time
from typing import Optional

# +/-20% around the nominal interval. Enough spread to decorrelate a fleet
# within a couple of intervals, small enough that a caller's observed latency
# and the 60s cap keep their intended meaning.
JITTER_SPREAD = 0.2

# The SDK-wide poll backoff: grow by 10% per poll, never sleep more than a
# minute between polls.
BACKOFF_FACTOR = 1.1
BACKOFF_CAP = 60.0


def jitter(wait_time: float, spread: float = JITTER_SPREAD) -> float:
    """Scale *wait_time* by ``uniform(1 - spread, 1 + spread)``.

    Args:
        wait_time: Nominal interval in seconds. Non-positive values return 0.0.
        spread: Fractional spread, clamped to ``[0.0, 1.0]``. ``0.0`` disables
            jitter and returns *wait_time* unchanged.

    Returns:
        The jittered interval in seconds, never negative.
    """
    if wait_time <= 0:
        return 0.0
    spread = min(max(spread, 0.0), 1.0)
    if spread == 0.0:
        return float(wait_time)
    return max(0.0, wait_time * random.uniform(1.0 - spread, 1.0 + spread))


def next_wait(wait_time: float, factor: float = BACKOFF_FACTOR, cap: float = BACKOFF_CAP) -> float:
    """Grow *wait_time* geometrically, capped at *cap*.

    Args:
        wait_time: Current interval in seconds.
        factor: Growth factor per step.
        cap: Upper bound on the returned interval.

    Returns:
        The next nominal interval in seconds.
    """
    if wait_time >= cap:
        return cap
    return min(wait_time * factor, cap)


def sleep_with_jitter(
    wait_time: float,
    spread: float = JITTER_SPREAD,
    max_sleep: Optional[float] = None,
) -> float:
    """Sleep ``jitter(wait_time)`` seconds, clamped to *max_sleep*.

    Args:
        wait_time: Nominal interval in seconds.
        spread: Fractional jitter spread; see :func:`jitter`.
        max_sleep: The caller's remaining budget, if any. Jitter must be able to
            shorten a sleep but never to push a loop past its own deadline, so
            the delay is clamped to this value.

    Returns:
        The number of seconds actually slept.
    """
    delay = jitter(wait_time, spread)
    if max_sleep is not None:
        delay = min(delay, max(0.0, max_sleep))
    if delay > 0:
        time.sleep(delay)
    return delay
