"""Unified File asset resource for files and directories.

Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

import logging
import mimetypes
import os
import tempfile
import warnings
import zipfile
from dataclasses import MISSING, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from typing_extensions import NotRequired
from urllib.parse import quote, unquote, urlparse

import requests
from dataclasses_json import config, dataclass_json

from aixplain.utils.url_safety import safe_get, validate_upload_url

from .enums import FileType, Privacy, SortBy
from .exceptions import APIError, FileUploadError, ResourceError, ValidationError
from .resource import (
    BaseDeleteParams,
    BaseResource,
    BaseSearchParams,
    DeleteResourceMixin,
    DeleteResult,
    Page,
    SearchResourceMixin,
    _filter_value,
    _filter_values,
    _is_excluded_from_serialization,
    _sort_direction,
)

logger = logging.getLogger(__name__)


class FileSearchParams(BaseSearchParams):
    """Search parameters for File assets.

    Attributes:
        file_type: Filter by structural type (``file`` or ``folder``).
        parent_type: Filter by the parent asset's type.
        parent_id: Filter by parent folder id.
        ownership, sort_by, sort_order: Inherited from :class:`BaseSearchParams`
            like every other resource. ``sort_by`` accepts ``SortBy.NAME`` /
            ``SortBy.CREATED_AT`` / ``SortBy.UPDATED_AT`` or a raw backend field
            name; defaults to newest-created first.
    """

    file_type: NotRequired[Union[FileType, str]]
    parent_type: NotRequired[str]
    parent_id: NotRequired[str]


@dataclass_json
@dataclass(repr=False, init=False)
class File(
    BaseResource,
    SearchResourceMixin[FileSearchParams, "File"],
    DeleteResourceMixin[BaseDeleteParams, "File"],
):
    """A persisted aiXplain file or folder.

    Args:
        source: A local file, local directory, or HTTP(S) URL.
        name: Optional name overriding the name inferred from ``source``.
        kwargs: Backend metadata used when hydrating an existing File.
    """

    RESOURCE_PATH = "sdk/file-asset"

    source: Optional[str] = field(default=None, metadata=config(exclude=lambda _: True))
    file_type: FileType = field(default=FileType.FILE, metadata=config(field_name="fileType"))
    # Internal only, not a constructor parameter: whether this File has been
    # saved yet. The upload flow (``sdk/file/upload/temp-url`` claimed by
    # ``POST sdk/file-asset``) has no permanent-vs-temporary switch to honor a
    # caller's request either way, so there is nothing for a public ``is_temp``
    # parameter to actually control; ``save()`` is what flips this to ``False``.
    is_temp: bool = field(default=True, metadata=config(field_name="isTemp"))
    children: List["File"] = field(default_factory=list)
    extension: Optional[str] = field(default=None, metadata=config(field_name="ext"))
    size: Optional[int] = None
    parent_id: Optional[str] = field(default=None, metadata=config(field_name="parentId"))
    tags: List[str] = field(default_factory=list)
    privacy: Privacy = Privacy.PRIVATE
    whitelist: List[Any] = field(default_factory=list)
    status: Optional[str] = None
    created_at: Optional[str] = field(default=None, metadata=config(field_name="createdAt"))
    updated_at: Optional[str] = field(default=None, metadata=config(field_name="updatedAt"))
    # SDK-internal: the top-level asset id this node lives under (``get()``'s
    # ``/children/recursive`` and a saved directory's tree set this on every
    # child). ``None`` for a standalone root file/folder, where the node's own
    # id already is the root. Never sent to or read from the wire.
    _root_id: Optional[str] = field(default=None, repr=False, metadata=config(exclude=lambda _: True))

    def __init__(
        self,
        source: Optional[Union[str, os.PathLike[str]]] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a File without performing network writes."""
        if "is_temp" in kwargs:
            raise TypeError(
                "File() no longer accepts 'is_temp': the upload flow has no way to honor a "
                "caller's temp-vs-permanent choice either way, so it was never a real switch. "
                "A new File starts as unsaved and save() is what persists it."
            )
        if name is not None and not name.strip():
            raise ValidationError("File name cannot be empty")
        BaseResource.__init__(
            self,
            id=kwargs.pop("id", None),
            name=name,
            description=kwargs.pop("description", None),
            path=kwargs.pop("path", None),
        )
        ignored = {"context", "RESOURCE_PATH", "_saved_state", "id", "name", "description", "path"}
        for item in fields(type(self)):
            if item.name in ignored:
                continue
            if item.default_factory is not MISSING:
                setattr(self, item.name, item.default_factory())
            elif item.default is not MISSING:
                setattr(self, item.name, item.default)

        self.source = os.fspath(source) if source is not None else None
        aliases = {
            "fileType": "file_type",
            "ext": "extension",
            "parentId": "parent_id",
            "createdAt": "created_at",
            "updatedAt": "updated_at",
        }
        for key, value in kwargs.items():
            setattr(self, aliases.get(key, key), value)
        self.file_type = self._coerce_file_type(getattr(self, "file_type", FileType.FILE))
        self.privacy = self._coerce_privacy(getattr(self, "privacy", Privacy.PRIVATE))
        self.children = [
            self._from_data(child) if isinstance(child, dict) else child for child in (self.children or [])
        ]
        if self.source is not None:
            self._validate_and_infer_source(name)
        elif not self.name and not self.id:
            hint = (
                " ('path' identifies an already-saved asset; pass the local path or URL as 'source' instead)"
                if self.path
                else ""
            )
            raise ValidationError(f"File requires a source, name, or backend ID{hint}")

    @staticmethod
    def _coerce_file_type(value: Any) -> FileType:
        """Normalize a backend structural file type."""
        if isinstance(value, FileType):
            return value
        return FileType(str(value or "file").lower())

    @staticmethod
    def _coerce_privacy(value: Any) -> Privacy:
        """Normalize a backend privacy value."""
        return value if isinstance(value, Privacy) else Privacy(value or Privacy.PRIVATE.value)

    def _validate_and_infer_source(self, explicit_name: Optional[str]) -> None:
        parsed = urlparse(self.source or "")
        if parsed.scheme:
            if parsed.scheme not in {"http", "https"}:
                raise ValidationError(f"Unsupported File URL scheme: {parsed.scheme}")
            inferred = unquote(Path(parsed.path.rstrip("/")).name)
            if not explicit_name and not inferred:
                raise ValidationError("Could not infer a File name from the URL")
            self.name = explicit_name or inferred
            self.file_type = FileType.FILE
            return
        local_path = Path(self.source or "").expanduser()
        if not local_path.exists():
            raise ValidationError(f"File source does not exist: {self.source}")
        self.source = str(local_path)
        self.name = explicit_name or local_path.name
        if not self.name:
            raise ValidationError("File name cannot be empty")
        self.file_type = FileType.FOLDER if local_path.is_dir() else FileType.FILE
        if local_path.is_file():
            self.extension = local_path.suffix or None
            self.size = local_path.stat().st_size

    @property
    def is_dir(self) -> bool:
        """Whether this File represents a directory."""
        return self.file_type == FileType.FOLDER

    @classmethod
    def _from_data(cls, data: Dict[str, Any]) -> "File":
        """Hydrate a File from a backend response."""
        data = dict(data)
        asset_info = data.pop("assetInfo", None) or {}
        if not data.get("path"):
            data["path"] = asset_info.get("instanceId") or asset_info.get("assetPath")
        data.setdefault("fileType", "file")
        obj = cls(**data)
        obj.context = cls.context
        obj.is_temp = False
        obj._update_saved_state()
        return obj

    def _apply_data(self, data: Dict[str, Any]) -> None:
        fresh = type(self)._from_data(data)
        for item in fields(type(self)):
            if not _is_excluded_from_serialization(item):
                setattr(self, item.name, getattr(fresh, item.name))
        self.context = type(self).context

    def _check_upload_allowance(self, local_path: str) -> None:
        """Ask the backend whether this upload fits the team's quota before sending its bytes."""
        size = os.path.getsize(local_path)
        allowance = self.context.client.get(f"{self.RESOURCE_PATH}/upload-allowance", params={"size": size})
        if not allowance.get("allowed", True):
            raise FileUploadError(
                f"Upload of {Path(local_path).name} ({size} bytes) is not allowed: "
                f"{allowance.get('reason', 'quota exceeded')}. "
                f"Remaining size: {allowance.get('remainingSize')}, remaining files: {allowance.get('remainingFiles')}."
            )

    def _upload_local_file(self, local_path: str) -> str:
        self._check_upload_allowance(local_path)
        content_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
        # ``sdk/file/upload/temp-url`` is the only presigned-upload endpoint the
        # file-asset flow uses: the object it returns becomes permanent once
        # ``POST sdk/file-asset`` claims it below, regardless of ``is_temp``.
        # ``is_temp`` itself is local state only ("has this File been saved
        # yet") — the backend's create/paginate responses take no such field
        # (unlike ``sdk/file/upload-url``, a *different*, legacy endpoint that
        # both lacks a ``downloadUrl`` and creates its own File record as a
        # side effect, so it cannot be swapped in here).
        response = self.context.client.post(
            "sdk/file/upload/temp-url",
            json={"contentType": content_type, "originalName": Path(local_path).name},
        )
        upload_url = response.get("uploadUrl")
        reference = response.get("downloadUrl") or response.get("url") or response.get("key")
        if not upload_url or not reference:
            raise FileUploadError("Temporary upload response did not include uploadUrl and a file reference")
        # ``uploadUrl`` is chosen by the response, so the host is checked before
        # the file bytes leave the machine (BUG-939).
        validate_upload_url(upload_url)
        with open(local_path, "rb") as handle:
            # A presigned S3 PUT never legitimately redirects, and following one
            # would re-send the file bytes to a host that never passed
            # ``validate_upload_url`` (BUG-939).
            upload_response = requests.put(
                upload_url,
                data=handle,
                headers={"Content-Type": content_type},
                timeout=self.context.client.timeout,
                allow_redirects=False,
            )
        if not upload_response.ok:
            raise FileUploadError(f"Upload failed with HTTP {upload_response.status_code}")
        return reference

    def _save_file(self, local_path: str) -> None:
        reference = self._upload_local_file(local_path)
        data = self.context.client.post(
            self.RESOURCE_PATH,
            json={
                "name": self.name,
                "fileType": "file",
                "url": reference,
                "description": self.description or "",
                "tags": self.tags,
                "privacy": self.privacy.value,
                "whitelist": self.whitelist,
            },
        )
        self._apply_data(data)

    def _create_child_folder(self, root_id: str, path: Path, parent_id: Optional[str]) -> Dict[str, Any]:
        body: Dict[str, Any] = {"name": path.name, "description": ""}
        if parent_id:
            body["parentId"] = parent_id
        data = self.context.client.post(f"{self.RESOURCE_PATH}/{quote(root_id, safe='')}/folder", json=body)
        if not data.get("id"):
            raise ResourceError(f"Backend did not return an ID for folder {path}")
        return data

    def _rollback_directory_upload(self, root: Path, root_id: str) -> str:
        """Best-effort delete of a partially-uploaded folder, for the failure message.

        Uses ``request_raw``, not ``request``: the delete endpoint returns an
        empty body, and ``request`` always calls ``.json()`` on the response —
        which would make a *successful* rollback land in the ``except`` below
        and misreport itself as failed.
        """
        try:
            self.context.client.request_raw("delete", f"{self.RESOURCE_PATH}/{quote(root_id, safe='')}")
        except Exception:
            logger.warning("Failed to roll back partially uploaded folder %s (id=%s)", root, root_id, exc_info=True)
            return "The partially uploaded folder could not be automatically removed; delete it manually."
        return "The partially uploaded folder was removed."

    def _save_directory(self, root: Path) -> None:
        root_data = self.context.client.post(
            self.RESOURCE_PATH,
            json={
                "name": self.name,
                "fileType": "folder",
                "description": self.description or "",
                "tags": self.tags,
                "privacy": self.privacy.value,
                "whitelist": self.whitelist,
            },
        )
        root_id = root_data.get("id")
        if not root_id:
            raise ResourceError("Backend did not return an ID for the root folder")
        # Track each directory's local Path -> its own backend id (still being
        # built), so newly created children attach to the right parent without
        # depending on the backend echoing ``parentId`` back on create. Raw
        # records are kept (not hydrated into File objects) until every upload
        # in the walk has actually succeeded — see the comment on
        # ``raw_records`` below for why.
        parents: Dict[Path, Optional[str]] = {root: None}
        raw_records: Dict[Path, Dict[str, Any]] = {}
        # Path -> child Paths, keyed the same way ``parents`` is (``None`` slot
        # unused; top-level children live under ``root`` itself).
        raw_children: Dict[Path, List[Path]] = {root: []}
        try:
            for current, directory_names, file_names in os.walk(root):
                directory_names.sort()
                file_names.sort()
                current_path = Path(current)
                parent_id = parents[current_path]
                for directory_name in directory_names:
                    directory = current_path / directory_name
                    folder_data = self._create_child_folder(root_id, directory, parent_id)
                    parents[directory] = folder_data["id"]
                    raw_records[directory] = folder_data
                    raw_children[current_path].append(directory)
                    raw_children[directory] = []
                for file_name in file_names:
                    local_file = current_path / file_name
                    reference = self._upload_local_file(str(local_file))
                    body: Dict[str, Any] = {
                        "name": file_name,
                        "url": reference,
                        "description": "",
                        "tags": [],
                    }
                    if parent_id:
                        body["parentId"] = parent_id
                    file_data = self.context.client.post(
                        f"{self.RESOURCE_PATH}/{quote(root_id, safe='')}/file", json=body
                    )
                    raw_records[local_file] = file_data
                    raw_children[current_path].append(local_file)
        except Exception as exc:
            rollback_note = self._rollback_directory_upload(root, root_id)
            raise ResourceError(
                f"Directory upload for {root} stopped after a partial upload: {exc}. {rollback_note}"
            ) from exc

        # Hydrate the tree only now that every upload has succeeded. Doing this
        # inside the ``try`` above would make a purely local parsing error (an
        # ``fileType``/``privacy`` value the SDK doesn't recognize yet) look
        # exactly like an upload failure and roll back an otherwise fully
        # uploaded folder.
        def _hydrate(path: Path) -> "File":
            node = self._from_data(raw_records[path])
            node._root_id = root_id
            node.children = [_hydrate(child) for child in raw_children.get(path, [])]
            return node

        self._apply_data(root_data)
        self.children = [_hydrate(path) for path in raw_children[root]]

    def save(self, **_: Any) -> "File":
        """Upload the source and persist it as a backend File asset.

        Raises:
            ResourceError: If the file has been deleted.
        """
        # File.save() never reaches BaseResource.save(), so it needs its own
        # deleted-state guard (BUG-1093).
        if self.id or self.is_deleted:
            self._ensure_saveable()

        if self.context is None:
            self.context = type(self).context
        if not self.source:
            raise ValidationError("A local path or URL source is required to save a new File")
        parsed = urlparse(self.source)
        temporary_path: Optional[str] = None
        try:
            if parsed.scheme in {"http", "https"}:
                suffix = Path(parsed.path).suffix
                # ``source`` is caller-supplied and its body is uploaded to the
                # platform, so it is the same SSRF sink as the remote-code fetch
                # in ``code_utils`` and is gated the same way (BUG-939).
                # ``safe_get`` re-validates every redirect target: a public host
                # that 302s to ``http://169.254.169.254/`` would otherwise defeat
                # a one-shot check on ``self.source``.
                with safe_get(self.source, stream=True, timeout=self.context.client.timeout) as response:
                    response.raise_for_status()
                    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
                        temporary_path = handle.name
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                handle.write(chunk)
                self._save_file(temporary_path)
            elif Path(self.source).is_dir():
                self._save_directory(Path(self.source))
            else:
                self._save_file(self.source)
        finally:
            if temporary_path:
                Path(temporary_path).unlink(missing_ok=True)
        self.is_temp = False
        self._update_saved_state()
        return self

    def get_signed_url(self, expires_in: Optional[int] = None) -> str:
        """Return a short-lived signed URL for this file's bytes.

        The backend's file-asset responses (create/get/paginate) never carry a
        stable ``url`` — it must be requested on demand through the same
        signed-URL endpoint the platform UI uses to render media inline. The
        endpoint is ``{rootAssetId}/file/{fileId}/url``: a standalone root file
        addresses itself both ways, but a child (from ``folder.children``)
        must address its parent folder's asset id, tracked in ``_root_id``.

        Args:
            expires_in: Signed URL lifetime in seconds (backend default: 1
                hour; capped at 7 days).

        Raises:
            ValidationError: If the File is unsaved or is a folder (a folder
                has no single downloadable object — use :meth:`download`).
        """
        if not self.id:
            raise ValidationError("File must be saved before a signed url can be requested")
        if self.is_dir:
            raise ValidationError("Folders have no single signed url; use .download() instead")
        kwargs: Dict[str, Any] = {"params": {"expiresIn": expires_in}} if expires_in is not None else {}
        encoded_root = quote(self._root_id or self.id, safe="")
        encoded_id = quote(self.id, safe="")
        response = self.context.client.get(f"{self.RESOURCE_PATH}/{encoded_root}/file/{encoded_id}/url", **kwargs)
        return response["url"]

    def build_delete_url(self, **kwargs: Any) -> str:
        """Refuse to delete a non-root child node; there is no documented endpoint for one.

        Only the root asset (a standalone File, or a folder as a whole) has a
        confirmed delete endpoint (``DELETE {RESOURCE_PATH}/{id}``). A node
        from ``folder.children`` carries a ``_root_id`` different from its own
        ``id`` — deleting the *folder* removes it along with the rest of the
        tree; there is no separate per-child delete to fall back on here.
        """
        if self._root_id and self._root_id != self.id:
            raise ValidationError(
                f"File '{self.name}' (id={self.id}) is a child under folder {self._root_id}; "
                "delete the parent folder instead of an individual child node."
            )
        return super().build_delete_url(**kwargs)

    @classmethod
    def get(cls, identifier: str, recursive: bool = True) -> "File":
        """Retrieve a File by ID, encoded asset path, or instance ID."""
        if not identifier:
            raise ValidationError("File identifier cannot be empty")
        data = cls.context.client.get(f"{cls.RESOURCE_PATH}/{quote(str(identifier), safe='')}")
        obj = cls._from_data(data)
        if recursive and obj.is_dir and obj.id:
            try:
                nodes = cls.context.client.get(f"{cls.RESOURCE_PATH}/{quote(obj.id, safe='')}/children/recursive")
            except APIError as exc:
                if exc.status_code not in {403, 404, 405}:
                    raise
                logger.warning(
                    "Recursive children are unavailable for File %s (HTTP %s); using immediate children",
                    obj.id,
                    exc.status_code,
                )
            else:
                node_list = nodes.get("results", nodes) if isinstance(nodes, dict) else nodes
                obj.children = cls._build_tree(obj.id, node_list or [])
                obj._update_saved_state()
        return obj

    @classmethod
    def _build_tree(cls, root_id: str, nodes: List[Dict[str, Any]]) -> List["File"]:
        built = {}
        for node in nodes:
            item = cls._from_data(node)
            # Every node in a recursive-children response lives under this
            # folder's own asset id (BUG: get_signed_url()/delete() used to
            # address a child by its own id twice, which the backend only
            # accepts for a root file).
            item._root_id = root_id
            built[str(node.get("id"))] = item
        roots: List[File] = []
        for node in nodes:
            item = built[str(node.get("id"))]
            parent_id = str(node.get("parentId") or "")
            if parent_id in built:
                built[parent_id].children.append(item)
            elif parent_id == root_id or not parent_id:
                roots.append(item)
        return roots

    # Wire keys File.search() understands, beyond the base pagination/query/
    # ownership/sort ones. Anything else is rejected rather than silently
    # dropped, so a typo'd filter fails loudly instead of matching everything.
    _SEARCH_FILTER_KEYS = {"file_type": "fileType", "parent_type": "parentType", "parent_id": "parentId"}
    _SEARCH_KNOWN_KEYS = frozenset(
        {
            "query",
            "page_number",
            "page_size",
            "sort_by",
            "sort_order",
            "ownership",
            "resource_path",
            "api_key",
            "paginate_items_key",
            "strict",
        }
        | set(_SEARCH_FILTER_KEYS)
    )

    # SortBy's UPPER_SNAKE values -> the backend's camelCase field names for
    # the file-asset paginate endpoint's ``sort: [{field, dir}]`` shape.
    _SORT_FIELD_BY_KEY = {
        SortBy.NAME: "name",
        SortBy.CREATED_AT: "createdAt",
        SortBy.UPDATED_AT: "updatedAt",
    }

    @classmethod
    def _populate_filters(cls, params: dict) -> dict:
        """Build the ``paginate`` request body for File assets.

        Like every other resource, ``sort_by``/``sort_order``/``ownership``
        (inherited from :class:`~aixplain.v2.resource.BaseSearchParams`) are
        accepted here — mapped onto this endpoint's own
        ``sort: [{field, dir}]`` wire shape rather than the raw shape being
        exposed directly. Defaults to newest-created-first.

        Raises:
            ValidationError: If ``params`` carries a filter this resource does
                not recognize (a typo'd kwarg would otherwise be dropped and
                silently match everything).
        """
        unknown = set(params) - cls._SEARCH_KNOWN_KEYS
        if unknown:
            raise ValidationError(f"File.search() received unsupported filter(s): {sorted(unknown)}")
        sort_by = params.get("sort_by")
        sort_field = cls._SORT_FIELD_BY_KEY.get(sort_by, _filter_value(sort_by)) if sort_by is not None else "createdAt"
        sort_order = params.get("sort_order")
        sort_dir = _sort_direction(sort_order) if sort_order is not None else -1
        body: Dict[str, Any] = {
            "q": params.get("query"),
            "pageNumber": params.get("page_number", cls.PAGINATE_DEFAULT_PAGE_NUMBER),
            "pageSize": params.get("page_size", cls.PAGINATE_DEFAULT_PAGE_SIZE),
            "sort": [{"field": sort_field, "dir": sort_dir}],
        }
        ownership = params.get("ownership")
        if ownership is not None:
            body["ownership"] = (
                _filter_values(ownership) if isinstance(ownership, (list, tuple, set)) else _filter_value(ownership)
            )
        for key, wire_key in cls._SEARCH_FILTER_KEYS.items():
            if params.get(key) is not None:
                value = params[key]
                body[wire_key] = value.value if hasattr(value, "value") else value
        return {key: value for key, value in body.items() if value is not None}

    @classmethod
    def _deserialize_items(cls, items: List[dict], context: Any) -> Tuple[List["File"], List[str]]:
        """Hydrate paginated records through :meth:`_from_data`, reporting failures."""
        resources: List["File"] = []
        errors: List[str] = []
        for index, item in enumerate(items):
            try:
                obj = cls._from_data(item)
            except Exception as e:
                logger.warning("Skipping item during %s deserialization: %s", cls.__name__, e)
                errors.append(f"item[{index}]: {e}")
                continue
            obj.context = context
            resources.append(obj)
        return resources, errors

    def download(self, destination: Optional[Union[str, os.PathLike[str]]] = None) -> str:
        """Stream this File to disk, safely extracting folders from one ZIP request.

        Args:
            destination: Where to write the file (or extract the folder). Defaults
                to ``self.name`` in the current directory.
        """
        if not self.id:
            raise ValidationError("File must be saved before it can be downloaded")
        # Sanitize before ever using the backend name as a bare filename: a
        # name containing separators or ".." must not let a caller-omitted
        # destination write outside the intended directory.
        safe_name = Path(self.name).name if self.name else "download"
        target = Path(destination if destination is not None else safe_name).expanduser()
        response = self.context.client.request_stream("GET", f"{self.RESOURCE_PATH}/{quote(self.id, safe='')}/download")
        if self.is_dir:
            target.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as archive:
                archive_path = Path(archive.name)
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        archive.write(chunk)
            try:
                with zipfile.ZipFile(archive_path) as bundle:
                    target_root = target.resolve()
                    for member in bundle.infolist():
                        member_path = (target / member.filename).resolve()
                        if os.path.commonpath([target_root, member_path]) != str(target_root):
                            raise ResourceError(f"Unsafe ZIP entry: {member.filename}")
                    bundle.extractall(target)
            except zipfile.BadZipFile as exc:
                raise ResourceError("Downloaded folder archive is not a valid ZIP file") from exc
            finally:
                archive_path.unlink(missing_ok=True)
            return str(target)
        if target.exists() and target.is_dir():
            target = target / safe_name
        elif str(destination).endswith(os.sep):
            target = target / safe_name
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.part")
        try:
            with open(temporary, "wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        return str(target)


__all__ = ["File", "Resource"]


def __getattr__(name: str) -> Any:
    """PEP 562: warn on the deprecated ``Resource`` alias, matching ``Aixplain().Resource``.

    ``Resource`` is deliberately not a plain module attribute: importing this
    module — including transitively, through ``aixplain.v2`` — must never warn
    by itself. Only an actual access to the deprecated name does.
    """
    if name == "Resource":
        warnings.warn(
            "`aixplain.v2.file.Resource` is deprecated; use `File` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return File
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
