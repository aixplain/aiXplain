"""Skill resource module.

A ``Skill`` is a Claude-style folder bundle — a ``SKILL.md`` (YAML frontmatter +
markdown instructions) plus optional ``scripts/`` and ``resources/`` — registered
as an aiXplain asset and attachable to agents. It is authored from a local folder;
the file tree is uploaded and managed internally.

The frontmatter ``description`` is the routing signal an agent sees; the body and
resources are loaded just-in-time at runtime (progressive disclosure). Skills are
attached to agents the same way tools are::

    skill = aix.Skill(folder="./skills/pdf-filler")
    skill.save()                                   # upload bundle + register asset

    agent = aix.Agent(name="analyst", skills=[skill])
    agent.save()

    aix.Skill.get("my-workspace/pdf-filler")       # retrieve (path or id)
    aix.Skill.search("pdf form")                   # search
    skill.download(to="./pdf-filler.zip")          # download the bundle
"""

import os
from typing import Any, List, Optional, Tuple
from dataclasses import dataclass, field
from typing_extensions import NotRequired, Unpack
from dataclasses_json import dataclass_json, config

import yaml

from .resource import (
    BaseResource,
    BaseGetParams,
    BaseSearchParams,
    BaseDeleteParams,
    SearchResourceMixin,
    GetResourceMixin,
    DeleteResourceMixin,
    Page,
)
from .enums import Privacy
from .mixins import ToolableMixin
from .upload_utils import FileUploader


def _exclude(_: Any) -> bool:
    """Marker to drop a field from the serialized payload."""
    return True


def _parse_skill_md(text: str) -> Tuple[Optional[str], Optional[str], List[str], str]:
    """Parse a ``SKILL.md`` into (name, description, required_tools, body).

    Frontmatter is an optional ``---``-delimited YAML block at the top of the
    file carrying ``name``, ``description``, and ``requires`` (tool paths).
    """
    name = description = None
    requires: List[str] = []
    body = text
    if text.lstrip().startswith("---"):
        stripped = text.lstrip()
        end = stripped.find("\n---", 3)
        if end != -1:
            front = stripped[3:end].strip()
            body = stripped[end + 4 :].lstrip("\n")
            meta = yaml.safe_load(front) or {}
            name = meta.get("name")
            description = meta.get("description")
            requires = meta.get("requires") or meta.get("required_tools") or []
            if isinstance(requires, str):
                requires = [requires]
    return name, description, list(requires), body


class SkillSearchParams(BaseSearchParams):
    """Search parameters for skills.

    Attributes:
        tags: Filter by tags.
        suppliers: Filter by suppliers.
        saved: Only return skills the caller has saved.
    """

    tags: NotRequired[List[str]]
    suppliers: NotRequired[List[str]]
    saved: NotRequired[bool]


@dataclass_json
@dataclass(repr=False)
class Skill(
    BaseResource,
    SearchResourceMixin[SkillSearchParams, "Skill"],
    GetResourceMixin[BaseGetParams, "Skill"],
    DeleteResourceMixin[BaseDeleteParams, "Skill"],
    ToolableMixin,
):
    """A Claude-style folder bundle registered as an aiXplain asset.

    Authored from a local folder via ``aix.Skill(folder=...)``; the bundle's file
    tree is uploaded internally on ``save()``. Attach to agents with
    ``aix.Agent(skills=[skill_or_id])``.
    """

    RESOURCE_PATH = "sdk/skill"

    tags: List[str] = field(default_factory=list)
    privacy: Privacy = Privacy.PRIVATE
    whitelist: List[str] = field(default_factory=list)

    # Authoring input: a local Claude-style skill folder. Parsed on construction;
    # never sent to the backend.
    folder: Optional[str] = field(default=None, repr=False, metadata=config(exclude=_exclude))

    # Parsed from SKILL.md frontmatter/body when authored from a folder. Read-only
    # to a developer and excluded from the create/update payload.
    required_tools: List[str] = field(default_factory=list, metadata=config(exclude=_exclude))
    instructions: Optional[str] = field(default=None, repr=False, metadata=config(exclude=_exclude))

    # backend-populated, read-only metadata
    team: Optional[int] = None
    user: Optional[int] = None
    status: Optional[str] = None
    asset_type: Optional[str] = field(default=None, metadata=config(field_name="assetType"))
    file_type: Optional[str] = field(default=None, metadata=config(field_name="fileType"))
    created_at: Optional[str] = field(default=None, metadata=config(field_name="createdAt"))
    updated_at: Optional[str] = field(default=None, metadata=config(field_name="updatedAt"))

    def __post_init__(self) -> None:
        """Load skill metadata from the local folder when authoring a new skill."""
        self._local_folder = None
        if self.folder and not self.id:
            self._load_from_folder(self.folder)

    def _load_from_folder(self, folder: str) -> None:
        """Parse ``SKILL.md`` and stage the folder for upload on save."""
        folder = os.path.abspath(folder)
        skill_md = os.path.join(folder, "SKILL.md")
        if not os.path.isfile(skill_md):
            raise ValueError(f"A skill folder must contain a SKILL.md file: {folder}")
        with open(skill_md, "r", encoding="utf-8") as handle:
            name, description, requires, body = _parse_skill_md(handle.read())
        self.name = self.name or name
        if not self.name:
            raise ValueError("SKILL.md frontmatter must include a 'name' (or pass name=).")
        self.description = self.description or description or ""
        self.required_tools = requires
        self.instructions = body
        self._local_folder = folder

    # ------------------------------------------------------------------ #
    # Retrieval / search
    # ------------------------------------------------------------------ #
    @classmethod
    def get(cls: type["Skill"], id: str, **kwargs: Unpack[BaseGetParams]) -> "Skill":
        """Get a skill by path or id."""
        return super().get(id, **kwargs)

    @classmethod
    def search(
        cls: type["Skill"],
        query: Optional[str] = None,
        **kwargs: Unpack[SkillSearchParams],
    ) -> Page["Skill"]:
        """Search skills with an optional free-text query and filters."""
        if query is not None:
            kwargs["query"] = query
        return super().search(**kwargs)

    @classmethod
    def _populate_filters(cls, params: dict) -> dict:
        """Add skill-specific filters on top of the standard pagination ones."""
        filters = super()._populate_filters(params)
        if params.get("tags") is not None:
            filters["tags"] = params["tags"]
        if params.get("suppliers") is not None:
            filters["suppliers"] = params["suppliers"]
        if params.get("saved") is not None:
            filters["saved"] = params["saved"]
        return filters

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def save(self, *args: Any, **kwargs: Any) -> "Skill":
        """Save the skill, uploading the bundle when authored from a folder.

        Args:
            *args: Positional arguments passed to the base save method.
            **kwargs: Attributes to set before saving (passed to base save).
        """
        super().save(*args, **kwargs)
        if getattr(self, "_local_folder", None):
            self._upload_folder(self._local_folder)
            self._local_folder = None
        return self

    def refresh(self) -> "Skill":
        """Reload the skill's metadata from the backend."""
        fresh = type(self).get(self.id)
        self.status = fresh.status
        self.updated_at = fresh.updated_at
        return self

    def download(self, to: str) -> str:
        """Download the skill bundle to a local path. Returns the written path."""
        self._ensure_valid_state()
        url = f"{self.RESOURCE_PATH}/{self.encoded_id}/download"
        response = self.context.client.request_raw("get", url)
        with open(to, "wb") as handle:
            handle.write(response.content)
        return to

    def as_tool(self) -> dict:
        """Serialize this skill as a tool object for agent attachment.

        Skills follow the same wire design as tools: attached as objects (not bare
        ids), with ``type="skill"``.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "supplier": "aixplain",
            "type": "skill",
            "version": None,
            "asset_id": self.id,
        }

    # ------------------------------------------------------------------ #
    # Internal: upload the local folder as the skill's file tree
    # ------------------------------------------------------------------ #
    def _upload_folder(self, root: str) -> None:
        """Walk the local folder and create the backend file/folder tree.

        Folder structure is preserved: each subdirectory becomes a folder node and
        each file is uploaded and registered under its parent. Node management is
        entirely internal — it is not part of the developer-facing surface.
        """
        self._ensure_valid_state()
        base = f"{self.RESOURCE_PATH}/{self.encoded_id}"
        folder_ids = {"": None}  # relative dir -> backend folder id (root -> None)

        for dirpath, _dirnames, filenames in os.walk(root):
            rel = os.path.relpath(dirpath, root)
            rel = "" if rel == "." else rel

            if rel:  # create a folder node for this subdirectory
                parent_id = folder_ids.get(os.path.dirname(rel))
                result = self.context.client.request(
                    "post",
                    f"{base}/folder",
                    json={"name": os.path.basename(rel), "description": "", "parentId": parent_id},
                )
                folder_ids[rel] = result.get("id")

            parent_id = folder_ids.get(rel)
            for filename in sorted(filenames):
                url = self._upload(os.path.join(dirpath, filename))
                self.context.client.request(
                    "post",
                    f"{base}/file",
                    json={"name": filename, "url": url, "description": "", "parentId": parent_id},
                )

    def _upload(self, file_path: str) -> str:
        """Upload a local file to S3 and return its download URL."""
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        uploader = FileUploader(
            api_key=self.context.client.team_api_key,
            backend_url=self.context.backend_url,
        )
        return uploader.upload(file_path, is_temp=True, return_download_link=True)
