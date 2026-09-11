"""Unit tests for the v1 ``artifacts`` field on the agent run response.

v1 mirrors the v2 ``Artifact`` model field-for-field so user code that still
imports ``aixplain.modules.agent`` gets the same typed deliverables. The same
records arrive with two key casings (snake_case from the poll path, camelCase
from the webhook body), so both must decode into the same object. These tests
cover the dual-casing decode, the back-compat cases (absent / ``null`` / junk /
non-list), unknown ``category`` passthrough, the ``AgentResponse.artifacts``
passthrough property, and v1/v2 field parity.
"""

import dataclasses

from aixplain.enums import ResponseStatus
from aixplain.modules.agent.agent_response import AgentResponse
from aixplain.modules.agent.agent_response_data import AgentResponseData, Artifact
from aixplain.v2.agent import Artifact as V2Artifact

# Captured from a live prod run: a Seedream image returned by a tool.
SNAKE_IMAGE_ARTIFACT = {
    "id": "6c968445-161c-48b3-acfc-6a1ddcaa6d25",
    "name": "021786092513318a25d9fd8bbdfc574a90b55d3ae211a62db7f63_0.jpeg",
    "title": None,
    "mime_type": "image/jpeg",
    "category": "image",
    "source": "tool_output",
    "tool_name": "actions_run",
    "url": "https://ark-content-generation-v2-ap-southeast-1.tos-ap-southeast-1.volces.com/seedream-4-0/x.jpeg?X-Tos-Expires=86400",
    "url_expires_at": "2026-08-08T08:48:42Z",
    "content": None,
    "sha256": None,
    "byte_size": None,
    "mentioned_in_answer": False,
    "created_at": "2026-08-07T08:48:43.640756Z",
}

# Captured from a live prod run: a CSV the agent wrote into its workspace.
SNAKE_WORKSPACE_ARTIFACT = {
    "id": "4a955263-bcd1-4503-8eb4-778e8bc01111",
    "name": "outputs/report.csv",
    "mime_type": "text/csv",
    "category": "data",
    "source": "workspace",
    "tool_name": None,
    "url": None,
    "url_expires_at": None,
    "content": "quarter,revenue\nQ1,120000\nQ2,135000\nQ3,151000\nQ4,168000",
    "sha256": "19b413378251d828b0c0347ebcfb50343f3aff8ebd54ee5d0fe439f974dfecb3",
    "byte_size": 55,
    "mentioned_in_answer": True,
    "created_at": "2026-08-07T08:45:08.054556Z",
}

_CAMEL_KEYS = {
    "mime_type": "mimeType",
    "tool_name": "toolName",
    "url_expires_at": "urlExpiresAt",
    "byte_size": "byteSize",
    "mentioned_in_answer": "mentionedInAnswer",
    "created_at": "createdAt",
}


def _camelize(payload):
    """Convert a snake_case artifact payload to the camelCase webhook shape."""
    return {_CAMEL_KEYS.get(key, key): value for key, value in payload.items()}


CAMEL_IMAGE_ARTIFACT = _camelize(SNAKE_IMAGE_ARTIFACT)
CAMEL_WORKSPACE_ARTIFACT = _camelize(SNAKE_WORKSPACE_ARTIFACT)


def _artifacts(payload):
    """Decode an ``artifacts`` payload through ``AgentResponseData.from_dict``."""
    return AgentResponseData.from_dict({"artifacts": payload}).artifacts


def test_snake_case_payload_populates_every_field():
    """The poll path (snake_case) lands on all 14 attributes."""
    (artifact,) = _artifacts([SNAKE_IMAGE_ARTIFACT])

    assert artifact.id == "6c968445-161c-48b3-acfc-6a1ddcaa6d25"
    assert artifact.name == "021786092513318a25d9fd8bbdfc574a90b55d3ae211a62db7f63_0.jpeg"
    assert artifact.title is None
    assert artifact.mime_type == "image/jpeg"
    assert artifact.category == "image"
    assert artifact.source == "tool_output"
    assert artifact.tool_name == "actions_run"
    assert artifact.url == SNAKE_IMAGE_ARTIFACT["url"]
    assert artifact.url_expires_at == "2026-08-08T08:48:42Z"
    assert artifact.content is None
    assert artifact.sha256 is None
    assert artifact.byte_size is None
    assert artifact.mentioned_in_answer is False
    assert artifact.created_at == "2026-08-07T08:48:43.640756Z"


def test_camel_case_payload_decodes_identically():
    """The webhook path (camelCase) yields an object equal to the snake_case one."""
    assert _artifacts([CAMEL_IMAGE_ARTIFACT]) == _artifacts([SNAKE_IMAGE_ARTIFACT])
    assert _artifacts([CAMEL_WORKSPACE_ARTIFACT]) == _artifacts([SNAKE_WORKSPACE_ARTIFACT])


def test_workspace_artifact_carries_inline_content():
    """Workspace artifacts have inline text and a digest, and no URL."""
    (artifact,) = _artifacts([SNAKE_WORKSPACE_ARTIFACT])

    assert artifact.source == "workspace"
    assert artifact.url is None
    assert artifact.content.startswith("quarter,revenue")
    assert artifact.sha256 == SNAKE_WORKSPACE_ARTIFACT["sha256"]
    assert artifact.byte_size == 55
    assert artifact.mentioned_in_answer is True


def test_missing_key_yields_empty_list():
    """Pre-#342 payloads have no ``artifacts`` key at all."""
    assert AgentResponseData.from_dict({"output": "hi"}).artifacts == []
    assert AgentResponseData().artifacts == []


def test_null_artifacts_yields_empty_list():
    """An explicit ``"artifacts": null`` decodes to ``[]`` rather than ``None``."""
    assert _artifacts(None) == []


def test_non_list_artifacts_yields_empty_list():
    """A scalar where a list was expected must not raise."""
    assert _artifacts("nope") == []
    assert _artifacts({"id": "x"}) == []


def test_junk_entries_are_dropped_and_valid_ones_kept():
    """Undecodable list entries are skipped rather than failing the response."""
    artifacts = _artifacts(["oops", 3, None, SNAKE_IMAGE_ARTIFACT])

    assert [a.id for a in artifacts] == ["6c968445-161c-48b3-acfc-6a1ddcaa6d25"]


def test_unknown_category_and_source_pass_through():
    """The engine may add media categories before the SDK knows about them."""
    (artifact,) = _artifacts([{"category": "hologram", "source": "teleporter"}])

    assert artifact.category == "hologram"
    assert artifact.source == "teleporter"


def test_unknown_extra_key_is_ignored():
    """Additive engine fields must not break deserialization."""
    (artifact,) = _artifacts([dict(SNAKE_IMAGE_ARTIFACT, thumbnailUrl="https://thumb")])

    assert artifact.id == SNAKE_IMAGE_ARTIFACT["id"]


def test_partial_payload_falls_back_to_defaults():
    """A truncated payload degrades to defaults instead of raising."""
    (artifact,) = _artifacts([{"name": "out.txt"}])

    assert artifact.name == "out.txt"
    assert artifact.id == ""
    assert artifact.category == "other"
    assert artifact.mentioned_in_answer is False


def test_constructor_accepts_artifact_instances():
    """``AgentResponseData(artifacts=[Artifact(...)])`` keeps the typed entries."""
    artifact = Artifact.from_dict(SNAKE_IMAGE_ARTIFACT)

    assert AgentResponseData(artifacts=[artifact]).artifacts == [artifact]


def test_artifact_supports_dict_style_access():
    """v1 response objects are routinely read dict-style."""
    (artifact,) = _artifacts([SNAKE_WORKSPACE_ARTIFACT])

    assert artifact["category"] == "data"
    assert artifact.get("mime_type") == "text/csv"
    assert artifact.get("nonexistent", "fallback") == "fallback"


def test_to_dict_emits_camel_case_and_round_trips():
    """Serialization matches the camelCase wire shape and is lossless."""
    (artifact,) = _artifacts([SNAKE_IMAGE_ARTIFACT])
    payload = artifact.to_dict()

    assert payload == CAMEL_IMAGE_ARTIFACT
    assert Artifact.from_dict(payload) == artifact


def test_response_data_to_dict_includes_artifacts():
    """``AgentResponseData.to_dict()`` carries the serialized artifacts."""
    data = AgentResponseData.from_dict({"artifacts": [SNAKE_WORKSPACE_ARTIFACT]})

    # The live workspace payload omits ``title``; serialization fills the default.
    assert data.to_dict()["artifacts"] == [dict(CAMEL_WORKSPACE_ARTIFACT, title=None)]
    assert AgentResponseData().to_dict()["artifacts"] == []


def test_agent_response_artifacts_passthrough():
    """``response.artifacts`` mirrors ``response.data.artifacts``."""
    response = AgentResponse(
        status=ResponseStatus.SUCCESS,
        data=AgentResponseData(artifacts=[SNAKE_IMAGE_ARTIFACT]),
    )

    assert response.artifacts is response.data.artifacts
    assert response.artifacts[0].category == "image"


def test_agent_response_artifacts_empty_without_artifact_bearing_data():
    """Responses with no data — or non-agent data — still yield a list."""
    assert AgentResponse(status=ResponseStatus.FAILED).artifacts == []

    response = AgentResponse(status=ResponseStatus.SUCCESS)
    response.data = object()  # e.g. an EvolverResponseData, which has no artifacts
    assert response.artifacts == []


def test_agent_response_dict_assignment_decodes_artifacts():
    """``response["data"] = {...}`` routes through ``AgentResponseData.from_dict``."""
    response = AgentResponse(status=ResponseStatus.SUCCESS)
    response["data"] = {"output": "done", "artifacts": [CAMEL_IMAGE_ARTIFACT]}

    assert response.artifacts[0].url == SNAKE_IMAGE_ARTIFACT["url"]


def test_agent_response_artifacts_from_raw_dict_data():
    """``data`` is a bare dict on some paths (``Agent.evolve``), not AgentResponseData."""
    response = AgentResponse(status=ResponseStatus.SUCCESS, data={"artifacts": [CAMEL_IMAGE_ARTIFACT]})

    assert [a.category for a in response.artifacts] == ["image"]


def test_agent_response_artifacts_dict_style_access():
    """v1 response objects are routinely read dict-style, including via ``get``."""
    response = AgentResponse(
        status=ResponseStatus.SUCCESS,
        data=AgentResponseData(artifacts=[SNAKE_IMAGE_ARTIFACT]),
    )

    assert response["artifacts"] == response.artifacts
    assert "artifacts" in response
    # Never None — the same guarantee the attribute makes.
    assert AgentResponse(status=ResponseStatus.FAILED).get("artifacts") == []


def test_v1_and_v2_constructors_coerce_raw_dicts_alike():
    """Hand-built response data types its artifacts the same way in v1 and v2."""
    from aixplain.v2.agent import AgentResponseData as V2AgentResponseData

    v1_artifacts = AgentResponseData(artifacts=[CAMEL_IMAGE_ARTIFACT]).artifacts
    v2_artifacts = V2AgentResponseData(artifacts=[CAMEL_IMAGE_ARTIFACT]).artifacts

    assert [dataclasses.asdict(a) for a in v1_artifacts] == [dataclasses.asdict(a) for a in v2_artifacts]


def test_v1_and_v2_artifact_fields_are_identical():
    """The duplicated v1/v2 definitions must not drift apart."""
    v1_fields = {f.name for f in dataclasses.fields(Artifact)}
    v2_fields = {f.name for f in dataclasses.fields(V2Artifact)}

    assert v1_fields == v2_fields


def test_v1_and_v2_decode_the_same_payload_the_same_way():
    """Parity holds at the value level, for both casings."""
    for payload in (SNAKE_IMAGE_ARTIFACT, CAMEL_IMAGE_ARTIFACT, SNAKE_WORKSPACE_ARTIFACT):
        v1_artifact = Artifact.from_dict(payload)
        v2_artifact = V2Artifact.from_dict(payload)

        assert dataclasses.asdict(v1_artifact) == dataclasses.asdict(v2_artifact)
        assert v1_artifact.to_dict() == v2_artifact.to_dict()
