---
sidebar_label: _backoff
title: aixplain.v2._backoff
---

Jittered backoff helpers for v2 poll loops.

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

#### jitter

```python
def jitter(wait_time: float, spread: float = JITTER_SPREAD) -> float
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/_backoff.py#L31)

Scale *wait_time* by ``uniform(1 - spread, 1 + spread)``.

**Arguments**:

- `wait_time` - Nominal interval in seconds. Non-positive values return 0.0.
- `spread` - Fractional spread, clamped to ``[0.0, 1.0]``. ``0.0`` disables
  jitter and returns *wait_time* unchanged.
  

**Returns**:

  The jittered interval in seconds, never negative.

#### next\_wait

```python
def next_wait(wait_time: float,
              factor: float = BACKOFF_FACTOR,
              cap: float = BACKOFF_CAP) -> float
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/_backoff.py#L50)

Grow *wait_time* geometrically, capped at *cap*.

**Arguments**:

- `wait_time` - Current interval in seconds.
- `factor` - Growth factor per step.
- `cap` - Upper bound on the returned interval.
  

**Returns**:

  The next nominal interval in seconds.

#### sleep\_with\_jitter

```python
def sleep_with_jitter(wait_time: float,
                      spread: float = JITTER_SPREAD,
                      max_sleep: Optional[float] = None) -> float
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/_backoff.py#L66)

Sleep ``jitter(wait_time)`` seconds, clamped to *max_sleep*.

**Arguments**:

- `wait_time` - Nominal interval in seconds.
- `spread` - Fractional jitter spread; see :func:`jitter`.
- `max_sleep` - The caller&#x27;s remaining budget, if any. Jitter must be able to
  shorten a sleep but never to push a loop past its own deadline, so
  the delay is clamped to this value.
  

**Returns**:

  The number of seconds actually slept.

