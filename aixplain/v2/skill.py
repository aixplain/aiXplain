"""Skill resource module.

A ``Skill`` is a Claude-style skill — a ``SKILL.md`` (YAML frontmatter + markdown
instructions), optionally alongside ``scripts/`` and ``resources/`` — registered as
an aiXplain asset and attachable to agents. It is authored from a local path, either
a folder containing ``SKILL.md`` or a single ``.md`` file; the file tree is uploaded
and managed internally.

The frontmatter ``description`` is the routing signal an agent sees; the body and
resources are loaded just-in-time at runtime (progressive disclosure). Skills are
attached to agents the same way tools are::

    skill = aix.Skill(file_path="./skills/pdf-filler")  # folder
    skill = aix.Skill(file_path="calculator.md")        # single file
    skill.save()                                   # upload bundle + register asset

    agent = aix.Agent(name="analyst", skills=[skill])
    agent.save()

    aix.Skill.get("my-workspace/pdf-filler")       # retrieve (path or id)
    aix.Skill.search("pdf form")                   # search
    skill.download()                               # download the bundle to ./{name}.zip
    skill.download(file_path="./pdf-filler.zip")   # ...or an explicit path
"""

import os
from typing import Any, Dict, List, Optional, Tuple
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
    _filter_values,
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
    """A Claude-style skill registered as an aiXplain asset.

    Authored from a local path via ``aix.Skill(file_path=...)`` — either a folder
    containing ``SKILL.md`` or a single ``.md`` file; the bundle's file tree is
    uploaded internally on ``save()``. Attach to agents with
    ``aix.Agent(skills=[skill_or_id])``.
    """

    RESOURCE_PATH = "sdk/skill"

    tags: List[str] = field(default_factory=list)
    privacy: Privacy = Privacy.PRIVATE
    whitelist: List[str] = field(default_factory=list)

    # Authoring input: a local Claude-style skill folder or a single ``.md`` file.
    # Parsed on construction; never sent to the backend.
    file_path: Optional[str] = field(default=None, repr=False, metadata=config(exclude=_exclude))

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
        """Load skill metadata from the local path when authoring a new skill."""
        self._local_path = None
        self._local_is_file = False
        if self.file_path:
            self._load_from_path(self.file_path)

    def _load_from_path(self, path: str) -> None:
        """Parse the skill markdown and stage the source for upload on save.

        Accepts either a Claude-style skill folder (containing ``SKILL.md``) or a
        single ``.md`` file that serves as the skill's ``SKILL.md``.
        """
        path = os.path.abspath(path)
        if os.path.isdir(path):
            skill_md = os.path.join(path, "SKILL.md")
            if not os.path.isfile(skill_md):
                raise ValueError(f"A skill folder must contain a SKILL.md file: {path}")
            fallback_name = os.path.basename(path)
            self._local_is_file = False
        elif os.path.isfile(path):
            skill_md = path
            fallback_name = os.path.splitext(os.path.basename(path))[0]
            self._local_is_file = True
        else:
            raise ValueError(f"Skill path not found: {path}")
        with open(skill_md, "r", encoding="utf-8") as handle:
            name, description, requires, body = _parse_skill_md(handle.read())
        # Precedence: explicit name= > SKILL.md frontmatter > folder/file name.
        self.name = self.name or name or fallback_name
        if not self.name:
            raise ValueError("Could not determine a skill name (pass name= or set it in SKILL.md).")
        self.description = self.description or description or ""
        self.required_tools = requires
        self.instructions = body
        self._local_path = path

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
            filters["suppliers"] = _filter_values(params["suppliers"])
        if params.get("saved") is not None:
            filters["saved"] = params["saved"]
        return filters

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def save(self, *args: Any, **kwargs: Any) -> "Skill":
        """Save the skill, uploading the bundle when authored from a local path.

        Re-parses ``file_path`` from disk on every call, so re-saving an already
        saved ``Skill`` after editing its ``SKILL.md`` (or reassigning
        ``file_path`` to updated content) re-uploads the bundle instead of
        silently skipping it.

        Args:
            *args: Positional arguments passed to the base save method.
            **kwargs: Attributes to set before saving (passed to base save).
        """
        if self.file_path:
            self._load_from_path(self.file_path)
        super().save(*args, **kwargs)
        if getattr(self, "_local_path", None):
            if self._local_is_file:
                self._upload_file_as_skill(self._local_path)
            else:
                self._upload_folder(self._local_path)
            self._local_path = None
        return self

    def refresh(self) -> "Skill":
        """Reload the skill's metadata from the backend."""
        fresh = type(self).get(self.id)
        self.status = fresh.status
        self.updated_at = fresh.updated_at
        return self

    def download(self, file_path: Optional[str] = None) -> str:
        """Download the skill bundle to a local path. Returns the written path.

        Args:
            file_path: Where to write the bundle. Defaults to ``./{name}.zip``.
        """
        self._ensure_valid_state()
        file_path = file_path or f"./{self.name}.zip"
        url = f"{self.RESOURCE_PATH}/{self.encoded_id}/download"
        response = self.context.client.request_raw("get", url)
        with open(file_path, "wb") as handle:
            handle.write(response.content)
        return file_path

    def list_files(self) -> List[str]:
        """List the relative paths of every file and folder in this skill's bundle.

        Use this to find the ``name`` to pass to :meth:`update` when you want
        to swap out an existing file (or add a new one) with local content —
        e.g. ``"SKILL.md"``, ``"scripts/helper.py"``, ``"resources"``.
        """
        return sorted(self._tree_index().keys())

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
    # Internal: upload the local source as the skill's file tree
    # ------------------------------------------------------------------ #
    def _tree_index(self) -> Dict[str, str]:
        """Map each node already in the skill's backend file tree to its id.

        Keyed by the node's ``path`` (forward-slash relative path from the
        skill root, e.g. ``"SKILL.md"`` or ``"scripts/run.py"``), so a re-save
        can tell an existing node from a genuinely new one and update it in
        place instead of colliding on name.
        """
        base = f"{self.RESOURCE_PATH}/{self.encoded_id}"
        tree = self.context.client.request("get", f"{base}/tree") or []
        return {node["path"]: node["id"] for node in tree if node.get("path")}

    def _ensure_folder(self, rel_path: str, existing: Dict[str, str]) -> Optional[str]:
        """Ensure every segment of ``rel_path`` exists as a folder node.

        Creates any missing segment (reusing ``existing`` where a segment is
        already present, and recording newly created ones into it) and
        returns the leaf folder's id, or ``None`` for the skill root.
        """
        if not rel_path:
            return None
        base = f"{self.RESOURCE_PATH}/{self.encoded_id}"
        parent_id: Optional[str] = None
        built = ""
        for segment in rel_path.split("/"):
            built = f"{built}/{segment}" if built else segment
            node_id = existing.get(built)
            if node_id is None:
                result = self.context.client.request(
                    "post",
                    f"{base}/folder",
                    json={"name": segment, "description": "", "parentId": parent_id},
                )
                node_id = result.get("id")
                existing[built] = node_id
            parent_id = node_id
        return parent_id

    def _put_or_post_file(
        self, local_path: str, rel_path: str, parent_id: Optional[str], existing: Dict[str, str]
    ) -> str:
        """Upload ``local_path`` and create/update the file node at ``rel_path``.

        A node already at ``rel_path`` (per ``existing``) is updated in place
        (``PUT``); otherwise a new one is created (``POST``).
        """
        base = f"{self.RESOURCE_PATH}/{self.encoded_id}"
        url = self._upload(local_path)
        payload = {"name": os.path.basename(rel_path), "url": url, "description": "", "parentId": parent_id}
        existing_id = existing.get(rel_path)
        if existing_id:
            self.context.client.request("put", f"{base}/file/{existing_id}", json=payload)
            return existing_id
        result = self.context.client.request("post", f"{base}/file", json=payload)
        new_id = result.get("id")
        existing[rel_path] = new_id
        return new_id

    def _upload_file_as_skill(self, path: str) -> None:
        """Upload a single ``.md`` file as the skill's ``SKILL.md`` at the root.

        Updates the existing ``SKILL.md`` node in place when one is already
        registered for this skill; otherwise creates it.
        """
        self._ensure_valid_state()
        self._put_or_post_file(path, "SKILL.md", None, self._tree_index())

    def _upload_folder(self, root: str) -> None:
        """Walk the local folder and create/update the backend file/folder tree.

        Folder structure is preserved: each subdirectory becomes a folder node and
        each file is uploaded and registered under its parent. A node already
        present in the backend tree (matched by relative path) is reused (folders)
        or updated in place (files) rather than re-created. Node management is
        entirely internal — it is not part of the developer-facing surface.
        """
        self._ensure_valid_state()
        existing = self._tree_index()

        for dirpath, _dirnames, filenames in os.walk(root):
            rel = os.path.relpath(dirpath, root)
            rel = "" if rel == "." else rel.replace(os.sep, "/")
            parent_id = self._ensure_folder(rel, existing) if rel else None
            for filename in sorted(filenames):
                rel_path = f"{rel}/{filename}" if rel else filename
                self._put_or_post_file(os.path.join(dirpath, filename), rel_path, parent_id, existing)

    def update(self, path: str, name: Optional[str] = None) -> "Skill":
        """Update (or add) a single file or folder within this skill's bundle.

        Unlike :meth:`save` (which re-authors the *whole* bundle from
        ``file_path``), ``update`` pushes just one changed file or subfolder —
        useful when you only have the new content on hand, not the original
        authoring folder. A node already at ``name`` is updated in place; a
        new one is created (intermediate folders are created as needed).

        Args:
            path: Local file or folder to upload from.
            name: Where this content lives within the skill — a bare filename
                (``"SKILL.md"``) or a relative path (``"scripts/helper.py"``).
                Defaults to ``os.path.basename(path)``.

        Returns:
            This ``Skill``.

        Example:
            >>> skill.update("./SKILL.md")                       # replace SKILL.md
            >>> skill.update("./helper.py", "scripts/helper.py")  # add/update a script
            >>> skill.update("./resources", "resources")         # sync a whole subfolder
        """
        self._ensure_valid_state()
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise ValueError(f"Path not found: {path}")
        name = (name or os.path.basename(path)).strip("/")
        existing = self._tree_index()

        if os.path.isdir(path):
            for dirpath, _dirnames, filenames in os.walk(path):
                rel = os.path.relpath(dirpath, path)
                rel = "" if rel == "." else rel.replace(os.sep, "/")
                mounted_dir = f"{name}/{rel}" if rel else name
                parent_id = self._ensure_folder(mounted_dir, existing)
                for filename in sorted(filenames):
                    rel_path = f"{mounted_dir}/{filename}"
                    self._put_or_post_file(os.path.join(dirpath, filename), rel_path, parent_id, existing)
        else:
            parent = os.path.dirname(name)
            parent_id = self._ensure_folder(parent, existing) if parent else None
            self._put_or_post_file(path, name, parent_id, existing)

        if name == "SKILL.md" and not os.path.isdir(path):
            with open(path, "r", encoding="utf-8") as handle:
                _, description, requires, body = _parse_skill_md(handle.read())
            self.description = description or self.description
            self.required_tools = requires
            self.instructions = body

        return self

    def _upload(self, file_path: str) -> str:
        """Upload a local file to S3 and return its download URL."""
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        uploader = FileUploader(
            api_key=self.context.client.team_api_key,
            backend_url=self.context.backend_url,
        )
        return uploader.upload(file_path, is_temp=True, return_download_link=True)
