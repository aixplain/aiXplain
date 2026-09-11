"""Tests for the API key handling in ``aixplain.utils.config``.

The split these tests lock in (ENG-3431):

* **Normalisation is eager.** ``AIXPLAIN_API_KEY`` is copied into
  ``TEAM_API_KEY`` at import time, because ~40 v1 call sites bind
  ``config.TEAM_API_KEY`` as a default argument value.
* **Validation is lazy.** Importing the module with no key set must *not*
  raise, otherwise the unit suite cannot even be collected without a
  credential. The "you need a key" error is raised at the point of use by
  ``check_api_keys_available()``.
"""

import importlib

import pytest

from aixplain.utils import config


@pytest.fixture
def reload_config(monkeypatch):
    """Reload ``aixplain.utils.config`` under a controlled environment.

    Returns a callable taking the desired values of the two key env vars
    (``None`` meaning "unset") and returning the freshly reloaded module.
    The module is reloaded once more on teardown so that the process-wide
    state seen by the rest of the suite is restored.
    """
    original_team = config.TEAM_API_KEY
    original_aixplain = config.AIXPLAIN_API_KEY

    def _reload(team_api_key=None, aixplain_api_key=None):
        for name, value in (
            ("TEAM_API_KEY", team_api_key),
            ("AIXPLAIN_API_KEY", aixplain_api_key),
        ):
            if value is None:
                monkeypatch.delenv(name, raising=False)
            else:
                monkeypatch.setenv(name, value)
        return importlib.reload(config)

    yield _reload

    # Restore the module to the environment the rest of the session expects.
    monkeypatch.setenv("TEAM_API_KEY", original_team)
    monkeypatch.setenv("AIXPLAIN_API_KEY", original_aixplain)
    importlib.reload(config)


def test_import_without_any_key_succeeds(reload_config):
    """Importing the config module with no credential must not raise."""
    reloaded = reload_config(team_api_key=None, aixplain_api_key=None)

    assert reloaded.TEAM_API_KEY == ""
    assert reloaded.AIXPLAIN_API_KEY == ""


def test_aixplain_key_normalized_to_team_key(reload_config):
    """AIXPLAIN_API_KEY-only users still get a populated TEAM_API_KEY."""
    reloaded = reload_config(team_api_key=None, aixplain_api_key="aixplain-key")

    assert reloaded.TEAM_API_KEY == "aixplain-key"


def test_team_key_is_left_alone(reload_config):
    """TEAM_API_KEY-only is the common case and must pass through untouched."""
    reloaded = reload_config(team_api_key="team-key", aixplain_api_key=None)

    assert reloaded.TEAM_API_KEY == "team-key"


def test_conflicting_keys_raise_on_import(reload_config):
    """Two different keys are a misconfiguration; fail loudly and early."""
    with pytest.raises(Exception, match="Conflicting API keys"):
        reload_config(team_api_key="team-key", aixplain_api_key="other-key")


def test_matching_keys_do_not_raise(reload_config):
    """Setting both vars to the same value is redundant but legal."""
    reloaded = reload_config(team_api_key="same-key", aixplain_api_key="same-key")

    assert reloaded.TEAM_API_KEY == "same-key"


def test_check_api_keys_available_raises_when_unset(reload_config):
    """The lazy path is where a missing credential is reported."""
    reloaded = reload_config(team_api_key=None, aixplain_api_key=None)

    with pytest.raises(Exception, match="An API key is required"):
        reloaded.check_api_keys_available()


def test_check_api_keys_available_passes_when_set(reload_config):
    """No exception, and the key that made it pass is the normalised one."""
    reloaded = reload_config(team_api_key="team-key", aixplain_api_key=None)

    reloaded.check_api_keys_available()  # must not raise

    assert reloaded.TEAM_API_KEY == "team-key"


def test_validate_api_keys_still_raises_when_unset(reload_config):
    """The eager wrapper is kept for backwards compatibility."""
    reloaded = reload_config(team_api_key=None, aixplain_api_key=None)

    with pytest.raises(Exception, match="An API key is required"):
        reloaded.validate_api_keys()


def test_validate_api_keys_normalizes_then_passes(reload_config, monkeypatch):
    """validate_api_keys() normalises before checking, as it always did."""
    reloaded = reload_config(team_api_key=None, aixplain_api_key=None)
    # Simulate a key arriving after import time, the way a caller that sets
    # os.environ late would; validate_api_keys() re-reads module state only,
    # so poke the module attribute directly.
    monkeypatch.setattr(reloaded, "AIXPLAIN_API_KEY", "late-key")

    reloaded.validate_api_keys()

    assert reloaded.TEAM_API_KEY == "late-key"
