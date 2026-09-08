"""Unit tests for the jittered backoff helpers (BUG-942 item 1).

Every poll interval in the SDK grew deterministically from a shared start, so a
batch of clients launched together stayed phase-locked for the whole run. These
tests pin the properties the fix relies on: the jitter is bounded, it is
actually random, it preserves the mean, and it can never push a budgeted loop
past its own deadline.
"""

import statistics
from unittest.mock import patch

import pytest

from aixplain.v2._backoff import (
    BACKOFF_CAP,
    BACKOFF_FACTOR,
    JITTER_SPREAD,
    jitter,
    next_wait,
    sleep_with_jitter,
)


class TestJitter:
    """Bounds and distribution of :func:`jitter`."""

    @pytest.mark.parametrize("wait_time", [0.2, 0.5, 1.0, 60.0])
    def test_stays_within_the_spread(self, wait_time):
        """1,000 real-RNG samples must all land in ``[0.8w, 1.2w]``."""
        samples = [jitter(wait_time) for _ in range(1000)]

        assert min(samples) >= wait_time * (1 - JITTER_SPREAD)
        assert max(samples) <= wait_time * (1 + JITTER_SPREAD)

    def test_is_actually_random(self):
        """A constant "jitter" would decorrelate nothing, so pin the spread."""
        samples = [jitter(1.0) for _ in range(200)]

        assert len(set(samples)) >= 100

    def test_preserves_the_mean_interval(self):
        """Symmetric multiplicative jitter must not slow a run down on average.

        This is why the helper multiplies by ``U(0.8, 1.2)`` rather than using
        AWS-style ``U(0, w)``, which would halve the mean interval and issue
        *more* requests per run.
        """
        mean = statistics.fmean(jitter(10.0) for _ in range(5000))

        assert 10.0 * 0.97 < mean < 10.0 * 1.03

    @pytest.mark.parametrize("wait_time", [0.0, -1.0])
    def test_non_positive_wait_returns_zero(self, wait_time):
        """A zero/negative interval must not become a negative sleep."""
        assert jitter(wait_time) == 0.0

    def test_zero_spread_disables_jitter(self):
        """``spread=0`` reproduces the old deterministic behaviour exactly."""
        assert jitter(3.0, spread=0.0) == 3.0

    @pytest.mark.parametrize("spread", [-5.0, 5.0])
    def test_spread_is_clamped_to_a_sane_range(self, spread):
        """An out-of-range spread must not produce a negative or absurd sleep."""
        samples = [jitter(1.0, spread=spread) for _ in range(200)]

        assert min(samples) >= 0.0
        assert max(samples) <= 2.0

    @pytest.mark.parametrize(
        "uniform_result,expected",
        [(0.8, 0.8), (1.0, 1.0), (1.2, 1.2)],
    )
    def test_uses_the_documented_uniform_range(self, uniform_result, expected):
        """The extremes come straight from ``random.uniform(0.8, 1.2)``."""
        with patch("aixplain.v2._backoff.random.uniform", return_value=uniform_result) as uniform:
            assert jitter(1.0) == pytest.approx(expected)

        uniform.assert_called_once_with(0.8, 1.2)


class TestNextWait:
    """The SDK-wide ``x1.1`` / 60s-capped backoff ladder."""

    def test_grows_by_the_backoff_factor(self):
        assert next_wait(1.0) == pytest.approx(BACKOFF_FACTOR)

    def test_is_capped(self):
        assert next_wait(59.0) == pytest.approx(BACKOFF_CAP)
        assert next_wait(BACKOFF_CAP) == BACKOFF_CAP
        assert next_wait(1000.0) == BACKOFF_CAP

    def test_ladder_converges_on_the_cap_and_never_exceeds_it(self):
        wait = 0.5
        for _ in range(500):
            wait = next_wait(wait)
            assert wait <= BACKOFF_CAP
        assert wait == BACKOFF_CAP


class TestSleepWithJitter:
    """The deadline clamp: jitter may shorten a sleep, never extend a timeout."""

    def test_sleeps_the_jittered_interval(self):
        with patch("aixplain.v2._backoff.time.sleep") as sleep:
            slept = sleep_with_jitter(2.0)

        sleep.assert_called_once()
        assert sleep.call_args.args[0] == pytest.approx(slept)
        assert 1.6 <= slept <= 2.4

    def test_never_sleeps_past_the_remaining_budget(self):
        """The whole point of ``max_sleep``: jitter cannot overrun a deadline."""
        with patch("aixplain.v2._backoff.time.sleep") as sleep:
            for _ in range(200):
                slept = sleep_with_jitter(10.0, max_sleep=0.25)
                assert slept <= 0.25

        assert all(call.args[0] <= 0.25 for call in sleep.call_args_list)

    def test_exhausted_budget_does_not_sleep_at_all(self):
        with patch("aixplain.v2._backoff.time.sleep") as sleep:
            assert sleep_with_jitter(5.0, max_sleep=0.0) == 0.0
            assert sleep_with_jitter(5.0, max_sleep=-3.0) == 0.0

        sleep.assert_not_called()

    def test_zero_interval_does_not_sleep(self):
        with patch("aixplain.v2._backoff.time.sleep") as sleep:
            assert sleep_with_jitter(0.0) == 0.0

        sleep.assert_not_called()

    def test_no_max_sleep_means_no_clamp(self):
        with patch("aixplain.v2._backoff.time.sleep"):
            assert sleep_with_jitter(4.0, max_sleep=None) >= 3.2


class TestFleetDecorrelation:
    """The acceptance criterion, as an offline proxy.

    Two clients started at the same instant must produce a *spread* sequence of
    poll timestamps rather than aligned spikes. Simulated by summing the sleeps
    each client would perform: identical sequences prove phase-lock.
    """

    @staticmethod
    def _poll_offsets(polls=25, spread=JITTER_SPREAD):
        """Cumulative sleep offsets one client would poll at."""
        offsets, elapsed, wait = [], 0.0, 0.5
        for _ in range(polls):
            elapsed += jitter(wait, spread=spread)
            offsets.append(elapsed)
            wait = next_wait(wait)
        return offsets

    def test_two_simultaneous_clients_drift_apart(self):
        a, b = self._poll_offsets(), self._poll_offsets()

        assert a != b
        # By the 25th poll the two have accumulated a visible phase difference,
        # rather than both landing in the same instant.
        assert abs(a[-1] - b[-1]) > 0.05

    def test_without_jitter_the_clients_stay_phase_locked(self):
        """Control: reproduces the pre-fix behaviour, so the test above means something."""
        a = self._poll_offsets(spread=0.0)
        b = self._poll_offsets(spread=0.0)

        assert a == b
