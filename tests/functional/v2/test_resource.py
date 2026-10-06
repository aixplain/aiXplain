"""Functional tests for the generic Resource get/search/pagination contract.

Exercised through ``aix.Model`` because it is the cheapest resource to search
and fetch, but the assertions are about the shared mixins every resource
inherits: ``get()`` round-trips an id, ``search()`` returns a :class:`Page` with
real pagination metadata, and an unknown id raises.
"""

import pytest

from aixplain.v2 import SortBy, SortOrder
from aixplain.v2.exceptions import APIError
from aixplain.v2.resource import Page

#: Page size for the paging test: small, but more than one record per page.
_PAGE_SIZE = 3


@pytest.fixture(scope="module")
def a_model(client):
    page = client.Model.search(page_size=1)
    assert page.results, "expected at least one model to exercise the generic resource path"
    return page.results[0]


def test_search_returns_a_page_with_pagination_metadata(client):
    page = client.Model.search(page_size=2)

    assert isinstance(page, Page)
    assert len(page.results) == 2, "the model catalogue should fill a two-item page"
    assert page.page_total >= 1
    assert page.total >= 2


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
    """Consecutive pages of a sorted search share no record, starting from page 0.

    Sorted by creation time so the order is stable across requests: without a sort
    the SDK sends ``sort: [{}]`` and the backend's order is not guaranteed between
    two calls. Pages 1 and 2 are distinct pages whether the backend counts
    ``pageNumber`` from 0 or from 1, so they are checked first. Pages 0 and 1 are
    checked too, because the SDK documents ``page_number`` as 0-based: a backend
    that counts from 1 and clamps 0 up to 1 would serve the same page twice. In the
    first live CI run pages 0 and 1 of an unsorted search returned the same model;
    under a stable sort that can no longer be put down to ordering.
    """
    search = dict(page_size=_PAGE_SIZE, sort_by=SortBy.CREATED_AT, sort_order=SortOrder.ASC)
    zeroth = client.Model.search(page_number=0, **search)
    first = client.Model.search(page_number=1, **search)
    second = client.Model.search(page_number=2, **search)

    assert first.total >= 3 * _PAGE_SIZE, f"need at least three pages of models, got total={first.total}"
    assert len(first.results) == _PAGE_SIZE and len(second.results) == _PAGE_SIZE, (first.results, second.results)
    overlap = {model.id for model in first.results} & {model.id for model in second.results}
    assert not overlap, f"pages 1 and 2 share {sorted(overlap)}"

    assert len(zeroth.results) == _PAGE_SIZE, zeroth.results
    aliased = {model.id for model in zeroth.results} & {model.id for model in first.results}
    assert not aliased, (
        f"pages 0 and 1 share {sorted(aliased)}: page_number is documented as 0-based, but the backend "
        "appears to count from 1 and serve page 1 for page 0"
    )
