"""Unit tests for the v2 batch lookups ``Tool.get_many`` and ``Skill.get_many``."""

import logging
from unittest.mock import Mock, patch

import pytest

from aixplain import Aixplain, APIError, Skill, SkillBatch, Tool, ToolBatch


def _oid(n: int) -> str:
    return f"{n:024x}"


def _tool_row(id: str, path: str = None) -> dict:
    row = {"id": id, "name": f"tool-{id[-4:]}", "status": "onboarded"}
    if path:
        row["assetInfo"] = {"assetPath": path}
    return row


def _skill_row(id: str) -> dict:
    return {
        "id": id,
        "name": f"skill-{id[-4:]}",
        "assetInfo": {"instanceId": f"team/skill-{id[-4:]}"},
        "updatedAt": "2026-10-08T10:00:00.000Z",
    }


def _echo_tools(path, params, **kwargs):
    return {"results": [_tool_row(i) for i in params["ids"].split(",")], "missing": []}


def _echo_skills(path, json, **kwargs):
    return {"results": [_skill_row(i) for i in json["ids"]], "notFound": [], "forbidden": []}


@pytest.fixture
def aix() -> Aixplain:
    """Return an isolated client."""
    return Aixplain(api_key="test-key", backend_url="https://example.test")


class TestToolGetMany:
    """Tool.get_many wraps GET v2/tools?ids=..."""

    def test_no_ids_makes_no_request(self, aix):
        aix.client.get = Mock()

        batch = aix.Tool.get_many([])

        assert batch == ToolBatch()
        aix.client.get.assert_not_called()

    def test_single_chunk(self, aix):
        a, b = _oid(1), _oid(2)
        aix.client.get = Mock(return_value={"results": [_tool_row(a), _tool_row(b)], "missing": []})

        batch = aix.Tool.get_many([a, b])

        aix.client.get.assert_called_once_with("v2/tools", params={"ids": f"{a},{b}"})
        assert list(batch.tools) == [a, b]
        assert isinstance(batch.tools[a], Tool)
        assert batch.tools[b].id == b
        assert batch.tools[a].context is aix
        assert list(batch.rows) == [a, b]
        assert batch.missing == []

    def test_bare_string_is_one_id(self, aix):
        a = _oid(1)
        aix.client.get = Mock(return_value={"results": [_tool_row(a)], "missing": []})

        batch = aix.Tool.get_many(a)

        aix.client.get.assert_called_once_with("v2/tools", params={"ids": a})
        assert list(batch.tools) == [a]

    def test_blank_ids_go_to_missing_without_reaching_backend(self, aix):
        a = _oid(1)
        aix.client.get = Mock(return_value={"results": [_tool_row(a)], "missing": []})

        batch = aix.Tool.get_many(["", a, "  "])

        aix.client.get.assert_called_once_with("v2/tools", params={"ids": a})
        assert list(batch.tools) == [a]
        assert batch.missing == ["", "  "]

    def test_mutating_tool_leaves_raw_row_untouched(self, aix):
        a = _oid(1)
        row = {**_tool_row(a), "config": {"nested": {"k": "v"}}}
        aix.client.get = Mock(return_value={"results": [row], "missing": []})

        batch = aix.Tool.get_many([a])
        batch.tools[a].config["nested"]["k"] = "changed"

        assert batch.rows[a]["config"] == {"nested": {"k": "v"}}

    def test_250_ids_are_split_into_three_requests(self, aix):
        ids = [_oid(i) for i in range(250)]
        aix.client.get = Mock(side_effect=_echo_tools)

        batch = aix.Tool.get_many(ids)

        chunks = [c.kwargs["params"]["ids"].split(",") for c in aix.client.get.call_args_list]
        assert [len(c) for c in chunks] == [100, 100, 50]
        assert sum(chunks, []) == ids
        assert list(batch.tools) == ids

    def test_dedupe_keeps_order(self, aix):
        a, b = _oid(1), _oid(2)
        aix.client.get = Mock(side_effect=_echo_tools)

        batch = aix.Tool.get_many([b, a, b])

        assert aix.client.get.call_args.kwargs["params"] == {"ids": f"{b},{a}"}
        assert list(batch.tools) == [b, a]

    def test_missing_is_passed_through(self, aix):
        a, b, c = _oid(1), _oid(2), _oid(3)
        aix.client.get = Mock(return_value={"results": [_tool_row(a), _tool_row(c)], "missing": [b]})

        batch = aix.Tool.get_many([a, b, c])

        assert batch.missing == [b]
        assert list(batch.tools) == [a, c]
        assert batch.tools[c].id == c

    def test_raw_rows_are_not_flattened(self, aix):
        a = _oid(1)
        row = _tool_row(a, path="aixplain/slack")
        aix.client.get = Mock(return_value={"results": [row], "missing": []})

        batch = aix.Tool.get_many([a])

        assert batch.rows[a] is row
        assert "path" not in row
        assert batch.tools[a].path == "aixplain/slack"

    def test_asset_path_key_maps_to_its_tool(self, aix):
        a = _oid(1)
        aix.client.get = Mock(
            return_value={"results": [_tool_row(_oid(9), path="aixplain/slack"), _tool_row(a)], "missing": []}
        )

        batch = aix.Tool.get_many(["aixplain/slack", a])

        assert batch.tools["aixplain/slack"].id == _oid(9)
        assert batch.rows["aixplain/slack"]["id"] == _oid(9)
        assert batch.tools[a].id == a

    def test_id_mismatch_falls_back_to_row_id(self, aix, caplog):
        a, b = _oid(1), _oid(2)
        aix.client.get = Mock(return_value={"results": [_tool_row(b), _tool_row(a)], "missing": []})

        with caplog.at_level(logging.WARNING):
            batch = aix.Tool.get_many([a, b])

        assert "do not line up" in caplog.text
        assert batch.tools[a].id == a
        assert batch.tools[b].id == b

    def test_length_mismatch_falls_back_to_row_id(self, aix, caplog):
        a, b = _oid(1), _oid(2)
        aix.client.get = Mock(return_value={"results": [_tool_row(b)], "missing": []})

        with caplog.at_level(logging.WARNING):
            batch = aix.Tool.get_many(["aixplain/slack", a])

        assert "do not line up" in caplog.text
        assert list(batch.tools) == [b]

    def test_row_failing_from_dict_goes_to_missing(self, aix, caplog):
        a, b = _oid(1), _oid(2)
        aix.client.get = Mock(return_value={"results": [_tool_row(a), _tool_row(b)], "missing": []})
        original = Tool.from_dict.__func__

        def flaky_from_dict(cls, obj, *args, **kwargs):
            if obj["id"] == a:
                raise ValueError("bad row")
            return original(cls, obj, *args, **kwargs)

        with patch.object(Tool, "from_dict", classmethod(flaky_from_dict)), caplog.at_level(logging.WARNING):
            batch = aix.Tool.get_many([a, b])

        assert batch.missing == [a]
        assert a not in batch.tools and a not in batch.rows
        assert list(batch.tools) == [b]
        assert f"Skipping tool '{a}'" in caplog.text

    def test_timeout_is_forwarded(self, aix):
        aix.client.get = Mock(side_effect=_echo_tools)

        aix.Tool.get_many([_oid(1)], timeout=5)

        assert aix.client.get.call_args.kwargs["timeout"] == 5

    def test_no_timeout_leaves_client_default(self, aix):
        aix.client.get = Mock(side_effect=_echo_tools)

        aix.Tool.get_many([_oid(1)])

        assert "timeout" not in aix.client.get.call_args.kwargs

    def test_http_error_propagates(self, aix):
        error = APIError("Not Found", status_code=404)
        aix.client.get = Mock(side_effect=error)

        with pytest.raises(APIError) as exc_info:
            aix.Tool.get_many([_oid(1)])

        assert exc_info.value is error


class TestSkillGetMany:
    """Skill.get_many wraps POST sdk/skill/batch."""

    def test_no_ids_makes_no_request(self, aix):
        aix.client.post = Mock()

        batch = aix.Skill.get_many([])

        assert batch == SkillBatch()
        aix.client.post.assert_not_called()

    def test_posts_ids_to_batch_route(self, aix):
        a, b = _oid(1), _oid(2)
        aix.client.get = Mock()
        aix.client.post = Mock(side_effect=_echo_skills)

        batch = aix.Skill.get_many([a, b])

        aix.client.post.assert_called_once_with("sdk/skill/batch", json={"ids": [a, b]})
        aix.client.get.assert_not_called()
        assert isinstance(batch.skills[a], Skill)
        assert batch.skills[a].updated_at == "2026-10-08T10:00:00.000Z"
        assert batch.skills[b].context is aix

    def test_250_ids_are_split_into_three_requests(self, aix):
        ids = [_oid(i) for i in range(250)]
        aix.client.post = Mock(side_effect=_echo_skills)

        batch = aix.Skill.get_many(ids)

        chunks = [c.kwargs["json"]["ids"] for c in aix.client.post.call_args_list]
        assert [len(c) for c in chunks] == [100, 100, 50]
        assert list(batch.skills) == ids

    def test_dedupe_keeps_order(self, aix):
        a, b = _oid(1), _oid(2)
        aix.client.post = Mock(side_effect=_echo_skills)

        batch = aix.Skill.get_many([b, a, a])

        assert aix.client.post.call_args.kwargs["json"] == {"ids": [b, a]}
        assert list(batch.skills) == [b, a]

    def test_blank_ids_go_to_not_found_without_reaching_backend(self, aix):
        a = _oid(1)
        aix.client.post = Mock(side_effect=_echo_skills)

        batch = aix.Skill.get_many([a, " "])

        assert aix.client.post.call_args.kwargs["json"] == {"ids": [a]}
        assert batch.not_found == [" "]

    def test_mutating_skill_leaves_raw_row_untouched(self, aix):
        a = _oid(1)
        aix.client.post = Mock(side_effect=_echo_skills)

        batch = aix.Skill.get_many([a])
        batch.skills[a].name = "changed"

        assert batch.rows[a]["name"] == f"skill-{a[-4:]}"
        assert batch.rows[a]["assetInfo"] == {"instanceId": f"team/skill-{a[-4:]}"}

    def test_not_found_and_forbidden_are_passed_through(self, aix):
        a, b, c, d = _oid(1), _oid(2), _oid(3), _oid(4)
        aix.client.post = Mock(
            return_value={"results": [_skill_row(a), _skill_row(d)], "notFound": [b], "forbidden": [c]}
        )

        batch = aix.Skill.get_many([a, b, c, d])

        assert batch.not_found == [b]
        assert batch.forbidden == [c]
        assert list(batch.skills) == [a, d]
        assert batch.skills[d].id == d

    def test_raw_rows_are_not_flattened(self, aix):
        a = _oid(1)
        row = _skill_row(a)
        aix.client.post = Mock(return_value={"results": [row], "notFound": [], "forbidden": []})

        batch = aix.Skill.get_many([a])

        assert batch.rows[a] is row
        assert "path" not in row
        assert batch.skills[a].path == row["assetInfo"]["instanceId"]

    def test_path_key_maps_to_its_skill(self, aix):
        aix.client.post = Mock(return_value={"results": [_skill_row(_oid(7))], "notFound": [], "forbidden": []})

        batch = aix.Skill.get_many(["team/pdf-filler"])

        assert batch.skills["team/pdf-filler"].id == _oid(7)

    def test_row_failing_from_dict_goes_to_not_found(self, aix, caplog):
        a, b = _oid(1), _oid(2)
        aix.client.post = Mock(side_effect=_echo_skills)
        original = Skill.from_dict.__func__

        def flaky_from_dict(cls, obj, *args, **kwargs):
            if obj["id"] == b:
                raise ValueError("bad row")
            return original(cls, obj, *args, **kwargs)

        with patch.object(Skill, "from_dict", classmethod(flaky_from_dict)), caplog.at_level(logging.WARNING):
            batch = aix.Skill.get_many([a, b])

        assert batch.not_found == [b]
        assert list(batch.skills) == [a] and list(batch.rows) == [a]
        assert f"Skipping skill '{b}'" in caplog.text

    def test_timeout_is_forwarded(self, aix):
        aix.client.post = Mock(side_effect=_echo_skills)

        aix.Skill.get_many([_oid(1)], timeout=(3, 30))

        assert aix.client.post.call_args.kwargs["timeout"] == (3, 30)

    def test_http_error_propagates(self, aix):
        error = APIError("Method Not Allowed", status_code=405)
        aix.client.post = Mock(side_effect=error)

        with pytest.raises(APIError) as exc_info:
            aix.Skill.get_many([_oid(1)])

        assert exc_info.value is error
