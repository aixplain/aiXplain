"""Search request bodies against what platform-backend reads (ENG-3782, layer 1).

BUG-1092 and #1146: the SDK sent sort and filter keys the backend accepted and
ignored, and the unit tests pinned those keys against a mock. Here the SDK's
real request body is checked against ``platform_request_readers``, the keys
each paginate service actually reads.
"""

import pytest

from aixplain.v2.enums import OwnershipType, SortBy, SortOrder
from tests.contract import platform_request_readers as readers
from tests.support.platform_replay import PlatformStub, StubResponse

EMPTY_PAGE = StubResponse(body={"results": [], "pageTotal": 0, "total": 0, "filteredFrom": 0, "pagesCount": 0})


def _body(platform: PlatformStub, resource: str) -> dict:
    [request] = platform.sent("POST", "/v2/%s/paginate" % resource)
    return request.json()


@pytest.fixture
def pages(platform: PlatformStub) -> PlatformStub:
    for resource in ("agents", "models", "tools"):
        platform.route("POST", "backend", "/v2/%s/paginate" % resource, EMPTY_PAGE)
    return platform


def test_model_page_is_parsed_into_models(aix, platform: PlatformStub) -> None:
    platform.serve("backend/models-paginate")

    page = aix.Model.search(query="gpt")

    assert [m.id for m in page.results] == ["6646261c6eb563165658bbb1"]
    assert page.total == 1


@pytest.mark.parametrize("sort_by", list(SortBy), ids=[s.name for s in SortBy])
def test_model_sort_reaches_the_backend(aix, pages: PlatformStub, sort_by: SortBy) -> None:
    aix.Model.search(query="gpt", sort_by=sort_by, sort_order=SortOrder.DESC)

    body = _body(pages, "models")
    assert readers.sort_problems(body) == []
    assert body["sort"][0]["dir"] == -1


def test_tool_sort_reaches_the_backend(aix, pages: PlatformStub) -> None:
    aix.Tool.search(query="search", sort_by=SortBy.NAME, sort_order=SortOrder.ASC)

    body = _body(pages, "tools")
    assert readers.sort_problems(body) == [] and body["sort"] == [{"field": "name", "dir": 1}]
    assert readers.unread_keys(body, readers.TOOL_PAGINATE) == ["sortBy", "sortOrder"]  # harmless legacy keys


@pytest.mark.xfail(
    strict=True,
    reason=(
        "ENG-3782 finding (BUG-1092 class): Agent.search sends only sortBy/sortOrder, which "
        "AgentService.paginateV2 never reads (it reads `sort: [{field, dir}]`), so agent search results "
        "are never sorted. #1146 fixed this for Model/Tool only."
    ),
)
def test_agent_sort_reaches_the_backend(aix, pages: PlatformStub) -> None:
    aix.Agent.search(query="geo", sort_by=SortBy.CREATED_AT, sort_order=SortOrder.DESC)

    assert readers.sort_problems(_body(pages, "agents")) == []


@pytest.mark.xfail(
    strict=True,
    reason=(
        "ENG-3782 finding (BUG-1092 class): the `ownership` filter is sent to v2/models/paginate and "
        "v2/agents/paginate, and neither service reads it (agents read `owned`), so "
        "search(ownership=PRIVATE) returns every visible asset."
    ),
)
@pytest.mark.parametrize("resource", ["Agent", "Model"])
def test_ownership_filter_reaches_the_backend(aix, pages: PlatformStub, resource: str) -> None:
    getattr(aix, resource).search(query="x", ownership=OwnershipType.PRIVATE)

    body = _body(pages, resource.lower() + "s")
    reads = readers.AGENT_PAGINATE if resource == "Agent" else readers.MODEL_PAGINATE
    assert "ownership" not in readers.unread_keys(body, reads)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "ENG-3782 finding (BUG-1092 class): Model.search sends sourceLanguages/targetLanguages, which "
        "ModelService.paginateModels never reads (ModelPaginationInput has no language filter), so the "
        "filter is accepted and ignored."
    ),
)
def test_language_filters_reach_the_backend(aix, pages: PlatformStub) -> None:
    aix.Model.search(query="translate", source_languages=["en"], target_languages=["fr"])

    assert readers.unread_keys(_body(pages, "models"), readers.MODEL_PAGINATE) == []
