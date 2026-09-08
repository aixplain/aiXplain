"""Guards against reporting partial results and failures as complete successes.

BUG-1094. Three v2 paths used to present an incomplete operation to the caller
as a complete one:

* ``search()`` / ``list()`` logged a warning and dropped any record it could
  not deserialize, while ``Page.total`` still came straight from the backend
  envelope -- so ``len(page.results) != page.total`` was a normal state and a
  bulk ``for x in page`` silently skipped rows. Dropping the record stays the
  default -- one unmodelled backend enum value must not break discovery on
  ``Model.search`` / ``Inspector.search`` / ``APIKey.list`` / ``Trigger.list``
  -- but the count is now corrected to match what was actually returned, the
  skip is logged, and ``strict=True`` raises for callers that want the
  ``get()``-like contract.
* ``_build_page`` computed three sensible fallbacks and then overwrote each one
  with a raising ``json_data[key]`` lookup, so an envelope missing ``results``,
  ``total`` or ``pageTotal`` turned every search into ``KeyError: 'total'``.
  The counts still fall back; a body carrying no readable item list at all is
  now reported instead, because an empty page there is indistinguishable from
  a search that genuinely matched nothing.
* ``poll()`` did ``response.get("data") or {}``, so a classifier that
  legitimately answers ``0`` -- or a model whose correct answer is ``""`` --
  came back as ``{}``, and ``result.data.strip()`` then raised
  ``AttributeError``. The synchronous path passes those values through
  unchanged, so the *same model* returned ``""`` when run sync and ``{}`` when
  polled.

The tests are effect-based: they assert on ``page.total`` / ``page.skipped``
and on the value *and type* of ``result.data``, because that is where each
defect was observable.
"""

import logging
from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from dataclasses_json import dataclass_json

from aixplain.v2.exceptions import ResourceError
from aixplain.v2.inspector import Inspector
from aixplain.v2.model import Model
from aixplain.v2.resource import (
    BaseResource,
    BaseRunParams,
    Page,
    Result,
    RunnableResourceMixin,
    SearchResourceMixin,
)

# A record the deserializer cannot handle at all: ``from_dict`` needs a mapping.
BAD_RECORD = "not_a_dict"


def _model_envelope(*items, **overrides):
    """Build a models/paginate envelope around *items*."""
    envelope = {"results": list(items), "total": len(items), "pageTotal": 1}
    envelope.update(overrides)
    return envelope


def _bind(monkeypatch, cls, response):
    """Bind *cls* to a mock context whose client returns *response*."""
    context = Mock(client=Mock(), backend_url="https://platform-api.aixplain.com", api_key="test_key")
    context.client.request.return_value = response
    context.client.get.return_value = response
    monkeypatch.setattr(cls, "context", context, raising=False)
    return context


# =============================================================================
# Finding 1 -- unparseable records must not be dropped behind an inflated total
# =============================================================================


class TestStrictListing:
    """``search()`` must not return a ``total`` that counts records it dropped."""

    def test_unparseable_record_is_skipped_by_default(self, monkeypatch, caplog):
        """Lenient is the default: one bad row must not cost the whole listing."""
        _bind(
            monkeypatch,
            Model,
            _model_envelope({"id": "m1", "name": "Good"}, BAD_RECORD, {"id": "m2", "name": "Also good"}),
        )

        with caplog.at_level(logging.WARNING, logger="aixplain.v2.resource"):
            page = Model.search()

        assert [r.id for r in page.results] == ["m1", "m2"]
        # The count never lies: the dropped row is not counted.
        assert page.total == 2
        assert page.skipped == 1
        # The degradation has to be visible rather than silent.
        messages = [record.getMessage() for record in caplog.records]
        assert any("skipped 1 of 3 record(s)" in message for message in messages)
        # And the message must tell the caller how to get the raising contract.
        assert any("strict=True" in message for message in messages)

    def test_strict_true_raises(self, monkeypatch):
        """``strict=True`` opts into the ``get()``-like contract."""
        _bind(
            monkeypatch,
            Model,
            _model_envelope({"id": "m1", "name": "Good"}, BAD_RECORD, {"id": "m2", "name": "Also good"}),
        )

        with pytest.raises(ResourceError) as exc_info:
            Model.search(strict=True)

        message = str(exc_info.value)
        assert "Failed to deserialize 1 of 3 Model record(s)" in message
        assert "strict=False" in message

    def test_strict_false_corrects_total(self, monkeypatch):
        """``strict=False`` skips the record *and* stops over-reporting."""
        _bind(
            monkeypatch,
            Model,
            _model_envelope({"id": "m1", "name": "Good"}, BAD_RECORD, {"id": "m2", "name": "Also good"}),
        )

        page = Model.search(strict=False)

        assert len(page.results) == 2
        # The backend said 3; a total that counts the dropped row is the bug.
        assert page.total == 2
        assert page.skipped == 1

    def test_strict_false_subtracts_only_this_pages_drops(self, monkeypatch):
        """A multi-page ``total`` stays meaningful: subtract, don't collapse."""
        _bind(
            monkeypatch,
            Model,
            _model_envelope(
                {"id": "m1", "name": "Good"},
                BAD_RECORD,
                total=97,
                pageTotal=5,
            ),
        )

        page = Model.search(strict=False)

        assert len(page.results) == 1
        assert page.total == 96
        assert page.skipped == 1

    def test_strict_false_never_reports_fewer_than_returned(self, monkeypatch):
        """A nonsense backend ``total`` cannot push it below ``len(results)``."""
        _bind(
            monkeypatch,
            Model,
            _model_envelope({"id": "m1", "name": "Good"}, BAD_RECORD, total=1),
        )

        page = Model.search(strict=False)

        assert page.total == 1
        assert page.total >= len(page.results)

    def test_strict_does_not_reach_the_wire(self, monkeypatch):
        """``strict`` is a client-side concern; it must not become a filter."""
        context = _bind(monkeypatch, Model, _model_envelope({"id": "m1", "name": "Good"}))

        Model.search(strict=False)

        body = context.client.request.call_args.kwargs["json"]
        assert "strict" not in body

    def test_all_valid_page_keeps_backend_total(self, monkeypatch):
        """Regression guard: the happy path is untouched."""
        _bind(
            monkeypatch,
            Model,
            _model_envelope({"id": "m1", "name": "Good"}, {"id": "m2", "name": "Also good"}, total=42, pageTotal=3),
        )

        page = Model.search()

        assert len(page.results) == 2
        assert page.total == 42
        assert page.page_total == 3
        assert page.skipped == 0

    def test_paginate_strict_class_attribute_opts_in(self, monkeypatch):
        """A resource whose rows must all parse can opt into raising."""
        _bind(monkeypatch, Model, _model_envelope({"id": "m1", "name": "Good"}, BAD_RECORD))
        monkeypatch.setattr(Model, "PAGINATE_STRICT", True, raising=False)

        with pytest.raises(ResourceError):
            Model.search()

    def test_per_call_strict_overrides_class_attribute(self, monkeypatch):
        """``strict=False`` wins over ``PAGINATE_STRICT = True``."""
        _bind(monkeypatch, Model, _model_envelope({"id": "m1", "name": "Good"}, BAD_RECORD))
        monkeypatch.setattr(Model, "PAGINATE_STRICT", True, raising=False)

        page = Model.search(strict=False)

        assert len(page.results) == 1
        assert page.total == 1
        assert page.skipped == 1

    def test_build_resources_wrapper_still_returns_a_list(self, monkeypatch):
        """The public-ish ``_build_resources`` signature is unchanged."""
        context = _bind(monkeypatch, Model, _model_envelope())

        resources = Model._build_resources([{"id": "m1", "name": "Good"}, BAD_RECORD], context)

        assert [r.id for r in resources] == ["m1"]

    def test_inspector_override_reports_errors(self, monkeypatch):
        """``Inspector`` migrated its override to the new hook."""
        _bind(monkeypatch, Inspector, _model_envelope(BAD_RECORD))

        with pytest.raises(ResourceError, match="Inspector record"):
            Inspector.search(strict=True)

    def test_unmodelled_enum_value_does_not_break_discovery(self, monkeypatch):
        """The motivating case: a new backend enum value must not kill search.

        ``strict=True`` used to be the default, so a single record carrying a
        value this client does not model yet took the whole listing with it.
        """
        _bind(
            monkeypatch,
            Model,
            _model_envelope(
                {"id": "m1", "name": "Good"},
                {"id": "m2", "name": "Brand new", "status": "a_status_this_sdk_has_never_heard_of"},
                total=2,
            ),
        )

        page = Model.search()

        assert [r.id for r in page.results] == ["m1"]
        assert page.skipped == 1
        assert page.total == len(page.results) == 1

    def test_inspector_lenient_mode_corrects_total(self, monkeypatch):
        """``Inspector`` honours ``strict=False`` through the same hook."""
        _bind(monkeypatch, Inspector, _model_envelope(BAD_RECORD, total=7))

        page = Inspector.search(strict=False)

        assert page.results == []
        assert page.total == 6
        assert page.skipped == 1

    def test_constructor_fallback_failure_is_reported_not_raised(self):
        """The no-``from_dict`` branch reports failures like the main one does.

        It used to build ``cls(**item)`` unguarded, so a record the constructor
        rejects escaped as a raw ``TypeError`` -- even from a call that asked to
        be lenient.
        """

        class Stub:
            """A resource-shaped class without ``from_dict``."""

            def __init__(self, id=None):
                self.id = id

            def _update_saved_state(self):
                pass

        deserialize = SearchResourceMixin.__dict__["_deserialize_items"].__func__
        resources, errors = deserialize(Stub, [{"id": "s1"}, {"unexpected": "field"}], Mock())

        assert [r.id for r in resources] == ["s1"]
        assert len(errors) == 1
        assert errors[0].startswith("item[1]:")

    def test_page_defaults_skipped_to_zero(self):
        """``Page`` gains ``skipped`` additively, so old constructions still work."""
        page = Page(results=[], page_number=0, page_total=1, total=0)

        assert page.skipped == 0


# =============================================================================
# Finding 2 -- a missing envelope key uses the computed default, not KeyError
# =============================================================================


class TestBuildPageDefaults:
    """``_build_page`` falls back for the counts, but not for the records.

    A missing ``total`` / ``pageTotal`` is a cosmetic gap with an honest
    default. A missing (or unreadable) item list is not: it means the client
    could not read the response at all, and returning it as an empty page hides
    a renamed envelope or a 200 error body behind "no results".
    """

    def test_missing_total_and_page_total_fall_back_to_item_count(self, monkeypatch):
        """No ``total`` / ``pageTotal`` used to raise ``KeyError: 'total'``."""
        _bind(monkeypatch, Model, {"results": [{"id": "m1", "name": "Good"}, {"id": "m2", "name": "Also"}]})

        page = Model.search()

        assert len(page.results) == 2
        assert page.total == 2
        assert page.page_total == 2

    def test_missing_items_key_is_reported(self, monkeypatch):
        """A renamed envelope must not masquerade as "no results"."""
        _bind(monkeypatch, Model, {"total": 5, "pageTotal": 1})

        with pytest.raises(ResourceError) as exc_info:
            Model.search()

        message = str(exc_info.value)
        assert "'results'" in message
        # The keys that *were* returned are what identifies the real envelope.
        assert "total" in message

    def test_error_body_served_with_status_200_is_reported(self, monkeypatch):
        """The symptom: an error body is not an empty search result."""
        _bind(monkeypatch, Model, {"error": "Forbidden resource", "statusCode": 403})

        with pytest.raises(ResourceError, match="missing the 'results' key"):
            Model.search()

    def test_empty_items_list_is_a_genuinely_empty_page(self, monkeypatch):
        """A search that matched nothing still returns an empty page."""
        _bind(monkeypatch, Model, {"results": [], "total": 0, "pageTotal": 0})

        page = Model.search()

        assert page.results == []
        assert page.total == 0
        assert page.skipped == 0

    def test_null_items_key_yields_an_empty_page(self, monkeypatch):
        """``{"results": null}`` is an empty page, not a crash."""
        _bind(monkeypatch, Model, {"results": None, "total": 0, "pageTotal": 0})

        assert Model.search().results == []

    def test_non_list_items_are_reported(self, monkeypatch):
        """A non-list ``results`` cannot be iterated into garbage resources."""
        _bind(monkeypatch, Model, {"results": {"id": "m1"}, "total": 1, "pageTotal": 1})

        with pytest.raises(ResourceError, match="not a list of records"):
            Model.search()

    def test_scalar_response_body_is_reported(self, monkeypatch):
        """A body that is neither an envelope nor an array is unusable."""
        _bind(monkeypatch, Model, "Service Unavailable")

        with pytest.raises(ResourceError, match="not a list of records"):
            Model.search()

    @pytest.mark.parametrize("bad_total", ["12", None, True, 3.5])
    def test_non_int_total_falls_back_to_item_count(self, monkeypatch, bad_total):
        """A malformed ``total`` degrades to the honest count."""
        _bind(monkeypatch, Model, {"results": [{"id": "m1", "name": "Good"}], "total": bad_total})

        page = Model.search()

        assert page.total == 1
        assert type(page.total) is int

    def test_empty_envelope_is_reported(self, monkeypatch):
        """The degenerate ``{}`` body carries no item list to read."""
        _bind(monkeypatch, Model, {})

        with pytest.raises(ResourceError, match="missing the 'results' key"):
            Model.search()

    def test_bare_array_response_is_unaffected(self, monkeypatch):
        """``PAGINATE_ITEMS_KEY = None`` resources keep reading the top-level list."""
        monkeypatch.setattr(Model, "PAGINATE_ITEMS_KEY", None, raising=False)
        _bind(monkeypatch, Model, [{"id": "m1", "name": "Good"}, {"id": "m2", "name": "Also"}])

        page = Model.search()

        assert [r.id for r in page.results] == ["m1", "m2"]
        assert page.total == 2
        assert page.page_total == 2

    def test_bare_array_is_read_even_when_a_key_is_configured(self, monkeypatch):
        """``APIKey.list`` answers with an array while inheriting the key."""
        _bind(monkeypatch, Model, [{"id": "m1", "name": "Good"}])

        page = Model.search()

        assert [r.id for r in page.results] == ["m1"]
        assert page.total == 1

    def test_object_body_for_a_bare_array_resource_is_reported(self, monkeypatch):
        """``PAGINATE_ITEMS_KEY = None`` plus an object body is unreadable."""
        monkeypatch.setattr(Model, "PAGINATE_ITEMS_KEY", None, raising=False)
        _bind(monkeypatch, Model, {"results": [{"id": "m1", "name": "Good"}]})

        with pytest.raises(ResourceError, match="expects a bare array"):
            Model.search()


# =============================================================================
# Finding 5 -- a polled falsy result must not be coerced to {}
# =============================================================================


def _create_runnable_resource():
    """Create a minimal resource with run/poll capabilities."""

    @dataclass_json
    @dataclass
    class RunnableResource(BaseResource, RunnableResourceMixin[BaseRunParams, Result]):
        RESOURCE_PATH = "runnable"
        RUN_ACTION_PATH = "run"

    resource = RunnableResource(id="123", name="runnable")
    resource.context = Mock()
    return resource


FALSY_PAYLOADS = ["", 0, False, [], 0.0]
FALSY_IDS = ["empty-string", "zero", "false", "empty-list", "zero-float"]


class TestPolledFalsyData:
    """``poll()`` must preserve a falsy-but-present ``data`` payload."""

    @pytest.mark.parametrize("payload", FALSY_PAYLOADS, ids=FALSY_IDS)
    def test_falsy_data_is_preserved(self, payload):
        """``0`` / ``""`` / ``False`` / ``[]`` used to arrive as ``{}``."""
        resource = _create_runnable_resource()
        resource.context.client.get = Mock(return_value={"status": "SUCCESS", "completed": True, "data": payload})

        result = resource.poll("https://poll.url")

        assert result.data == payload
        assert type(result.data) is type(payload)

    def test_empty_string_result_supports_string_methods(self):
        """The reported symptom: ``result.data.strip()`` raised AttributeError."""
        resource = _create_runnable_resource()
        resource.context.client.get = Mock(return_value={"status": "SUCCESS", "completed": True, "data": ""})

        result = resource.poll("https://poll.url")

        assert result.data.strip() == ""

    def test_absent_data_still_yields_empty_dict(self):
        """Genuinely absent data keeps its historical shape."""
        resource = _create_runnable_resource()
        resource.context.client.get = Mock(return_value={"status": "SUCCESS", "completed": True})

        assert resource.poll("https://poll.url").data == {}

    def test_null_data_still_yields_empty_dict(self):
        """An explicit ``null`` is treated as absent, as before."""
        resource = _create_runnable_resource()
        resource.context.client.get = Mock(return_value={"status": "SUCCESS", "completed": True, "data": None})

        assert resource.poll("https://poll.url").data == {}

    @pytest.mark.parametrize("payload", FALSY_PAYLOADS + [{"k": "v"}, "text"], ids=FALSY_IDS + ["dict", "text"])
    def test_sync_and_polled_paths_agree(self, payload):
        """The same model must not return ``""`` when sync and ``{}`` when polled."""
        response = {"status": "SUCCESS", "completed": True, "data": payload}

        sync_resource = _create_runnable_resource()
        sync_result = sync_resource.handle_run_response(dict(response))

        polled_resource = _create_runnable_resource()
        polled_resource.context.client.get = Mock(return_value=dict(response))
        polled_result = polled_resource.poll("https://poll.url")

        assert polled_result.data == sync_result.data
        assert type(polled_result.data) is type(sync_result.data)

    @pytest.mark.parametrize("payload", ["", 0, False, []], ids=["empty-string", "zero", "false", "empty-list"])
    def test_fallback_branch_preserves_falsy_data(self, payload, monkeypatch):
        """The deserialization-fallback branch had the same ``or {}`` bug."""
        resource = _create_runnable_resource()
        resource.context.client.get = Mock(return_value={"status": "SUCCESS", "completed": True, "data": payload})

        original_from_dict = Result.from_dict
        calls = {"n": 0}

        def flaky_from_dict(data, *args, **kwargs):
            """Fail the first (full-payload) parse, succeed on the fallback."""
            calls["n"] += 1
            if calls["n"] == 1:
                raise ValueError("simulated deserialization failure")
            return original_from_dict(data, *args, **kwargs)

        monkeypatch.setattr(Result, "from_dict", flaky_from_dict)

        result = resource.poll("https://poll.url")

        assert calls["n"] == 2
        assert result.data == payload
        assert type(result.data) is type(payload)
