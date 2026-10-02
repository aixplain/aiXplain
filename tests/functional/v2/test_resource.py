"""Functional tests for the generic Resource get/search/pagination contract.

Exercised through ``aix.Model`` because it is the cheapest resource to search
and fetch, but the assertions are about the shared mixins every resource
inherits: ``get()`` round-trips an id, ``search()`` returns a :class:`Page` with
real pagination metadata, and an unknown id raises.
"""

import pytest

from aixplain.v2.exceptions import APIError
from aixplain.v2.resource import Page


@pytest.fixture(scope="module")
def a_model(client):
    page = client.Model.search(page_size=1)
    assert page.results, "expected at least one model to exercise the generic resource path"
    return page.results[0]


def test_search_returns_a_page_with_pagination_metadata(client):
    page = client.Model.search(page_size=2)

    assert isinstance(page, Page)
    assert isinstance(page.results, list)
    assert len(page.results) <= 2
    assert page.page_number >= 0
    assert page.page_total >= 1
    assert page.total >= len(page.results)
    assert page.skipped >= 0


def test_page_supports_iteration_and_keyed_access(client):
    page = client.Model.search(page_size=1)

    assert list(page) == page.results
    assert page["total"] == page.total


def test_get_round_trips_the_id(a_model):
    fetched = a_model.__class__.get(a_model.id)

    assert fetched.id == a_model.id
    assert fetched.name == a_model.name


def test_get_unknown_id_raises(client):
    with pytest.raises(APIError):
        client.Model.get("does-not-exist-0000000000000000")


def test_second_page_does_not_repeat_the_first(client):
    first = client.Model.search(page_size=1, page_number=0)
    second = client.Model.search(page_size=1, page_number=1)

    if first.total < 2:
        pytest.skip("fewer than two models available")

    assert first.results[0].id != second.results[0].id
