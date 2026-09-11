"""Unit tests for the v2 ``artifacts`` field on the agent run response.

The agent engine emits a session ``artifacts`` array describing the user-facing
deliverables a run produced (generated media URLs, files written into the agent
workspace). The same records reach the SDK with two different key casings — the
poll / ``checkRequest`` path emits snake_case, the webhook body is camelCased by
the engine — so both must deserialize into the same object. These tests cover:
- snake_case and camelCase payloads decode to equal ``Artifact`` objects.
- Absent, ``null``, non-list, and junk-element payloads yield ``[]`` without
  raising and without emitting a ``RuntimeWarning``.
- Unknown ``category`` / ``source`` values and unknown extra keys pass through.
- ``to_dict()`` emits camelCase and round-trips losslessly.
- ``AgentRunResult.artifacts`` mirrors ``result.data.artifacts``, and is ``[]``
  when ``data`` is a plain string or missing entirely.
"""

import warnings

from aixplain.v2.agent import AgentResponseData, AgentRunResult, Artifact

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
    """Decode an ``artifacts`` payload through ``AgentResponseData``."""
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


def test_null_artifacts_yields_empty_list_without_warning():
    """An explicit ``"artifacts": null`` decodes to ``[]`` and warns about nothing."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        data = AgentResponseData.from_dict({"artifacts": None})

    assert data.artifacts == []
    assert [str(w.message) for w in caught] == []


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


def test_artifacts_instances_pass_through_the_decoder():
    """Already-typed entries survive a second decode pass unchanged."""
    (artifact,) = _artifacts([SNAKE_IMAGE_ARTIFACT])

    assert _artifacts([artifact]) == [artifact]


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


def test_direct_construction_types_raw_dicts():
    """``AgentResponseData(artifacts=[{...}])`` bypasses the field decoder.

    Hand-built response data must still yield typed artifacts, matching v1.
    """
    data = AgentResponseData(artifacts=[SNAKE_IMAGE_ARTIFACT, CAMEL_WORKSPACE_ARTIFACT])

    assert all(isinstance(a, Artifact) for a in data.artifacts)
    assert [a.category for a in data.artifacts] == ["image", "data"]


def test_direct_construction_normalizes_none_and_junk():
    """The always-a-list guarantee holds for the constructor, not just decode."""
    assert AgentResponseData(artifacts=None).artifacts == []
    assert AgentResponseData(artifacts="nope").artifacts == []
    assert AgentResponseData(artifacts=["oops", 3]).artifacts == []


def test_run_result_decodes_nested_artifacts():
    """``AgentRunResult.from_dict`` types artifacts nested under ``data``."""
    result = AgentRunResult.from_dict(
        {"status": "completed", "completed": True, "data": {"artifacts": [CAMEL_IMAGE_ARTIFACT]}}
    )

    assert isinstance(result.data, AgentResponseData)
    assert isinstance(result.data.artifacts[0], Artifact)
    assert result.data.artifacts[0].category == "image"


def test_run_result_artifacts_property_mirrors_data():
    """``result.artifacts`` is the same list as ``result.data.artifacts``."""
    result = AgentRunResult.from_dict(
        {"status": "completed", "completed": True, "data": {"artifacts": [SNAKE_IMAGE_ARTIFACT]}}
    )

    assert result.artifacts is result.data.artifacts


def test_run_result_artifacts_property_decodes_raw_dict_data():
    """``data`` is a bare dict on hand-built results, not just decoded ones."""
    result = AgentRunResult(status="completed", completed=True, data={"artifacts": [CAMEL_IMAGE_ARTIFACT]})

    assert [a.category for a in result.artifacts] == ["image"]


def test_run_result_artifacts_property_is_empty_without_structured_data():
    """``data`` is a bare string on some paths, and may be missing entirely."""
    text_result = AgentRunResult.from_dict({"status": "completed", "completed": True, "data": "plain text"})
    empty_result = AgentRunResult(status="completed", completed=True)

    assert text_result.artifacts == []
    assert empty_result.artifacts == []
