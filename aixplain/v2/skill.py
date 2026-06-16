"""Skill resource module.

A ``Skill`` is a curated bundle of files and folders (a knowledge bundle) that
can be attached to an :class:`~aixplain.v2.agent.Agent` to give it reference
material. It is a *managed* asset — it is created, searched, updated, and
deleted like every other asset, but it is **not runnable** (no ``.run()``).

Lifecycle mirrors the rest of the SDK::

    skill = aix.Skill(name="Support Playbook", privacy=aix.Privacy.PRIVATE)
    skill.save()                                   # create

    skill.children.append(aix.Skill.File(name="faq.pdf", path="./faq.pdf"))
    skill.save(save_subcomponents=True)            # reconcile the file tree

    aix.Skill.get("support-playbook")              # retrieve (path or id)
    aix.Skill.search("playbook", tags=["support"]) # search
    skill.download(to="./playbook.zip")            # download the bundle
    skill.delete()
"""

import os
from typing import Any, List, Optional, Union
from dataclasses import dataclass, field
from typing_extensions import NotRequired, Unpack
from dataclasses_json import dataclass_json, config

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


# Node kinds, as stored in the backend ``fileType`` discriminator. This is
# distinct from ``enums.FileType`` (CSV/PDF/...), which describes *content*.
FILE = "file"
FOLDER = "folder"


def _exclude(_: Any) -> bool:
    """Marker to drop a field from the serialized payload."""
    return True


@dataclass_json
@dataclass(repr=False)
class SkillNode:
    """A single file or folder inside a :class:`Skill`.

    Construct via the :meth:`Skill.File` / :meth:`Skill.Folder` helpers rather
    than instantiating this directly — they set the node ``kind`` for you.

    Attributes set by the developer:
        name: Display name of the node.
        description: Optional description.
        url: Remote URL of a file's content (mutually exclusive with ``path``).
        path: Local file path; uploaded automatically on save.
        parent: The :class:`SkillNode` folder this node lives under (``None``
            for top-level nodes).

    Read-only attributes populated by the backend:
        id, ext, size, status, created_at.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    kind: str = field(default=FILE, metadata=config(field_name="fileType"))

    # developer inputs that are sent on the dedicated node endpoints, not the
    # main skill payload — excluded from the serialized skill body.
    url: Optional[str] = field(default=None, metadata=config(exclude=_exclude))
    path: Optional[str] = field(default=None, metadata=config(exclude=_exclude))
    parent: Optional["SkillNode"] = field(default=None, repr=False, compare=False, metadata=config(exclude=_exclude))

    # backend-populated, read-only
    id: Optional[str] = None
    ext: Optional[str] = None
    size: Optional[int] = None
    status: Optional[str] = None
    created_at: Optional[str] = field(default=None, metadata=config(field_name="createdAt"))

    @property
    def is_folder(self) -> bool:
        """Whether this node is a folder."""
        return self.kind == FOLDER

    def __repr__(self) -> str:
        """Concise representation showing kind, name, and status."""
        return f"SkillNode(kind={self.kind}, name={self.name!r}, status={self.status!r})"


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
    """A curated bundle of files and folders. Not runnable.

    Skills are attached to agents via ``aix.Agent(skills=[skill_or_id, ...])``,
    the same way tools and sub-agents are.

    .. note::
        File-tree management via ``save(save_subcomponents=True)`` is **BETA** —
        syntax may change as the backend node API evolves.
    """

    RESOURCE_PATH = "sdk/skill"

    tags: List[str] = field(default_factory=list)
    privacy: Privacy = Privacy.PRIVATE
    whitelist: List[str] = field(default_factory=list)

    # The file tree. Managed via dedicated node endpoints, so it is excluded
    # from the main create/update payload and reconciled on save instead.
    children: List[SkillNode] = field(default_factory=list, metadata=config(field_name="children", exclude=_exclude))

    # backend-populated, read-only metadata
    team: Optional[int] = None
    user: Optional[int] = None
    status: Optional[str] = None
    asset_type: Optional[str] = field(default=None, metadata=config(field_name="assetType"))
    file_type: Optional[str] = field(default=None, metadata=config(field_name="fileType"))
    created_at: Optional[str] = field(default=None, metadata=config(field_name="createdAt"))
    updated_at: Optional[str] = field(default=None, metadata=config(field_name="updatedAt"))

    # ------------------------------------------------------------------ #
    # Node constructors (mirror Agent.Task / Agent.OutputFormat pattern)
    # ------------------------------------------------------------------ #
    @staticmethod
    def File(
        name: str,
        url: Optional[str] = None,
        path: Optional[str] = None,
        description: Optional[str] = None,
        parent: Optional[SkillNode] = None,
    ) -> SkillNode:
        """Create a file node. Provide either ``url`` (remote) or ``path`` (local)."""
        return SkillNode(name=name, url=url, path=path, description=description, parent=parent, kind=FILE)

    @staticmethod
    def Folder(
        name: str,
        description: Optional[str] = None,
        parent: Optional[SkillNode] = None,
    ) -> SkillNode:
        """Create a folder node."""
        return SkillNode(name=name, description=description, parent=parent, kind=FOLDER)

    def as_tool(self) -> dict:
        """Serialize this skill as a tool object for agent attachment.

        Skills follow the same on-the-wire design as tools: they are attached to
        an agent as objects (not bare ids), with ``type="skill"``.

        Returns:
            dict: ``{id, name, description, supplier, type, version, asset_id}``.
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

    def __post_init__(self) -> None:
        """Normalize children and snapshot the synced node ids."""
        self.children = [SkillNode.from_dict(c) if isinstance(c, dict) else c for c in (self.children or [])]
        self._snapshot_nodes()

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
        """Save the skill, optionally reconciling its file tree.

        Args:
            *args: Positional arguments passed to the base save method.
            save_subcomponents: If True, create/update/delete the file and
                folder nodes to match ``self.children`` (default: False).
            **kwargs: Attributes to set before saving (passed to base save).
        """
        save_subcomponents = kwargs.pop("save_subcomponents", False)
        super().save(*args, **kwargs)
        if save_subcomponents:
            self._sync_children()
        return self

    def refresh(self) -> "Skill":
        """Reload the skill (and its file tree) from the backend."""
        fresh = type(self).get(self.id)
        self.children = fresh.children
        self.status = fresh.status
        self.updated_at = fresh.updated_at
        self._snapshot_nodes()
        return self

    def get_node(self, path_or_id: str) -> SkillNode:
        """Find a node by its id or by a slash-delimited name path.

        Examples:
            skill.get_node("docs/faq.pdf")
            skill.get_node("60f...nodeId")
        """
        for node in self.children:
            if node.id == path_or_id:
                return node
        target = path_or_id.strip("/").split("/")[-1]
        for node in self.children:
            if node.name == target:
                return node
        raise ValueError(f"No node matching {path_or_id!r} in skill {self.name!r}")

    def download(self, to: str) -> str:
        """Download the skill bundle to a local path. Returns the written path."""
        self._ensure_valid_state()
        url = f"{self.RESOURCE_PATH}/{self.encoded_id}/download"
        response = self.context.client.request_raw("get", url)
        with open(to, "wb") as handle:
            handle.write(response.content)
        return to

    # ------------------------------------------------------------------ #
    # File-tree reconciliation (BETA)
    # ------------------------------------------------------------------ #
    def _snapshot_nodes(self) -> None:
        """Record the set of persisted node ids for deletion diffing."""
        self._synced_node_ids = {n.id for n in (self.children or []) if getattr(n, "id", None)}

    def _sync_children(self) -> None:
        """Create, update, and delete nodes to match ``self.children``."""
        self._ensure_valid_state()
        base = f"{self.RESOURCE_PATH}/{self.encoded_id}"

        # 1. Deletions: ids previously synced but no longer present.
        current_ids = {n.id for n in self.children if n.id}
        for node_id in self._synced_node_ids - current_ids:
            self.context.client.request_raw("delete", f"{base}/node/{node_id}")

        # 2. Creations: resolve in passes so parents exist before children.
        remaining = [n for n in self.children if n.id is None]
        progressed = True
        while remaining and progressed:
            progressed = False
            for node in list(remaining):
                if node.parent is not None and node.parent.id is None:
                    continue  # parent not created yet
                parent_id = node.parent.id if node.parent else None
                self._create_node(base, node, parent_id)
                remaining.remove(node)
                progressed = True
        if remaining:
            unresolved = ", ".join(n.name or "<unnamed>" for n in remaining)
            raise ValueError(f"Could not resolve folder hierarchy for node(s): {unresolved}")

        # 3. Updates: an existing file whose url was reassigned by the developer.
        for node in self.children:
            if node.id and node.kind == FILE and node.url:
                self.context.client.request("put", f"{base}/file/{node.id}", json={"url": node.url})

        self.refresh()

    def _create_node(self, base: str, node: SkillNode, parent_id: Optional[str]) -> None:
        """Create a single file or folder node and hydrate it from the response."""
        if node.kind == FILE and node.path and not node.url:
            node.url = self._upload(node.path)

        payload = {"name": node.name, "description": node.description, "parentId": parent_id}
        if node.kind == FOLDER:
            result = self.context.client.request("post", f"{base}/folder", json=payload)
        else:
            payload["url"] = node.url
            result = self.context.client.request("post", f"{base}/file", json=payload)

        updated = SkillNode.from_dict(result)
        node.id = updated.id
        node.ext = updated.ext
        node.size = updated.size
        node.status = updated.status
        node.created_at = updated.created_at

    def _upload(self, file_path: str) -> str:
        """Upload a local file to S3 and return its download URL."""
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        uploader = FileUploader(
            api_key=self.context.client.team_api_key,
            backend_url=self.context.backend_url,
        )
        return uploader.upload(file_path, is_temp=True, return_download_link=True)
