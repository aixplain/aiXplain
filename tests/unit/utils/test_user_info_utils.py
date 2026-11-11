"""Geolocation opt-out for run metadata (BUG-948).

``AIXPLAIN_NO_TELEMETRY`` / ``AIXPLAIN_DISABLE_GEOLOCATION`` must skip the
ipinfo.io lookup entirely. Network-free: ``_fetch_ipinfo`` and ``requests.get``
are patched in every test.
"""

import pathlib
from unittest import mock

import pytest

from aixplain.utils import user_info_utils

GEO_FIELDS = ("region", "language", "ipAddress", "latitude", "longitude", "timezone")
REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def _clear_flags(monkeypatch):
    monkeypatch.delenv(user_info_utils.NO_TELEMETRY_ENV_VAR, raising=False)
    monkeypatch.delenv(user_info_utils.DISABLE_GEOLOCATION_ENV_VAR, raising=False)


@pytest.mark.parametrize("var", ["AIXPLAIN_NO_TELEMETRY", "AIXPLAIN_DISABLE_GEOLOCATION"])
@pytest.mark.parametrize("value", ["1", "true", "YES", "on"])
def test_opt_out_skips_lookup(monkeypatch, var, value):
    monkeypatch.setenv(var, value)
    with (
        mock.patch.object(user_info_utils, "_fetch_ipinfo", side_effect=AssertionError("lookup made")) as fetch,
        mock.patch.object(user_info_utils.requests, "get", side_effect=AssertionError("request made")) as get,
    ):
        meta = user_info_utils.build_run_metadata()
    fetch.assert_not_called()
    get.assert_not_called()
    assert meta["userAgent"] == "sdk"
    assert all(meta[field] is None for field in GEO_FIELDS)


@pytest.mark.parametrize("value", [None, "", "0", "false"])
def test_lookup_used_when_not_opted_out(monkeypatch, value):
    if value is not None:
        monkeypatch.setenv("AIXPLAIN_NO_TELEMETRY", value)
    payload = {"ip": "203.0.113.7", "country": "US", "loc": "1.5,2.5", "timezone": "UTC"}
    with mock.patch.object(user_info_utils, "_fetch_ipinfo", return_value=payload) as fetch:
        meta = user_info_utils.build_run_metadata()
    fetch.assert_called_once()
    assert meta["ipAddress"] == "203.0.113.7"
    assert meta["latitude"] == 1.5


def test_opt_out_mid_process_drops_cached_result(monkeypatch):
    payload = {"ip": "203.0.113.7"}
    with mock.patch.object(user_info_utils, "_fetch_ipinfo", return_value=payload):
        assert user_info_utils.build_run_metadata()["ipAddress"] == "203.0.113.7"
        monkeypatch.setenv("AIXPLAIN_NO_TELEMETRY", "1")
        assert user_info_utils.build_run_metadata()["ipAddress"] is None


@pytest.mark.parametrize("doc", ["README.md", "docs/README.md", "docs/run-metadata.md"])
def test_opt_out_is_documented(doc):
    assert "AIXPLAIN_NO_TELEMETRY" in (REPO_ROOT / doc).read_text(encoding="utf-8")
