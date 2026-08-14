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
import zipfile
from dataclasses import MISSING, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote, unquote, urlparse

import requests
from dataclasses_json import config, dataclass_json

from .enums import FileType, Privacy
from .exceptions import APIError, FileUploadError, ResourceError, ValidationError
from .resource import BaseResource, Page

logger = logging.getLogger(__name__)


@dataclass_json
@dataclass(repr=False, init=False)
class File(BaseResource):
    """A persisted aiXplain file or folder.

    Args:
        source: A local file, local directory, or HTTP(S) URL.
        name: Optional name overriding the name inferred from ``source``.
        is_temp: Whether the source is still transient. A successful save sets this to ``False``.
        kwargs: Backend metadata used when hydrating an existing File.
    """

    RESOURCE_PATH = "sdk/file-asset"

    source: Optional[str] = field(default=None, metadata=config(exclude=lambda _: True))
    file_type: FileType = field(default=FileType.FILE, metadata=config(field_name="fileType"))
    is_temp: bool = field(default=True, metadata=config(field_name="isTemp"))
    children: List["File"] = field(default_factory=list)
    extension: Optional[str] = field(default=None, metadata=config(field_name="ext"))
    size: Optional[int] = None
    parent_id: Optional[str] = field(default=None, metadata=config(field_name="parentId"))
    relative_path: Optional[str] = field(default=None, metadata=config(field_name="relativePath"))
    tags: List[str] = field(default_factory=list)
    privacy: Privacy = Privacy.PRIVATE
    whitelist: List[Any] = field(default_factory=list)
    status: Optional[str] = None
    created_at: Optional[str] = field(default=None, metadata=config(field_name="createdAt"))
    updated_at: Optional[str] = field(default=None, metadata=config(field_name="updatedAt"))
    s3_url: Optional[str] = field(default=None, metadata=config(field_name="s3Url"))

    def __init__(
        self,
        source: Optional[Union[str, os.PathLike[str]]] = None,
        name: Optional[str] = None,
        is_temp: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize a File without performing network writes."""
        if name is not None and not name.strip():
            raise ValidationError("File name cannot be empty")
        if source is None:
            source = kwargs.pop("file_path", None)
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
        self.is_temp = is_temp
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
            raise ValidationError("File requires a source, name, or backend ID")

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

    @property
    def url(self) -> Optional[str]:
        """Return the uploaded URL for compatibility with the early Resource API."""
        return self.s3_url

    @property
    def file_path(self) -> Optional[str]:
        """Return the original local path for compatibility with the early Resource API."""
        return self.source

    @classmethod
    def create_from_file(cls, file_path: str, is_temp: bool = True, **kwargs: Any) -> "File":
        """Create a File from a local path."""
        return cls(file_path, is_temp=is_temp, **kwargs)

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
            if item.name not in {"context", "RESOURCE_PATH"}:
                setattr(self, item.name, getattr(fresh, item.name))
        self.context = type(self).context

    def _upload_local_file(self, local_path: str) -> str:
        content_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
        response = self.context.client.post(
            "sdk/file/upload/temp-url",
            json={"contentType": content_type, "originalName": Path(local_path).name},
        )
        upload_url = response.get("uploadUrl")
        reference = response.get("downloadUrl") or response.get("url") or response.get("key")
        if not upload_url or not reference:
            raise FileUploadError("Temporary upload response did not include uploadUrl and a file reference")
        with open(local_path, "rb") as handle:
            upload_response = requests.put(
                upload_url,
                data=handle,
                headers={"Content-Type": content_type},
                timeout=self.context.client.timeout,
            )
        if not upload_response.ok:
            raise FileUploadError(f"Upload failed with HTTP {upload_response.status_code}")
        return reference

    def _save_file(self, local_path: str) -> None:
        reference = self._upload_local_file(local_path)
        data = self.context.client.post(
            self.RESOURCE_PATH,
            json={"name": self.name, "fileType": "file", "url": reference},
        )
        self._apply_data(data)

    def _create_child_folder(self, root_id: str, path: Path, parent_id: Optional[str]) -> str:
        body: Dict[str, Any] = {"name": path.name, "description": ""}
        if parent_id:
            body["parentId"] = parent_id
        data = self.context.client.post(f"{self.RESOURCE_PATH}/{quote(root_id, safe='')}/folder", json=body)
        child_id = data.get("id")
        if not child_id:
            raise ResourceError(f"Backend did not return an ID for folder {path}")
        return child_id

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
        parents: Dict[Path, Optional[str]] = {root: None}
        try:
            for current, directory_names, file_names in os.walk(root):
                directory_names.sort()
                file_names.sort()
                current_path = Path(current)
                parent_id = parents[current_path]
                for directory_name in directory_names:
                    directory = current_path / directory_name
                    parents[directory] = self._create_child_folder(root_id, directory, parent_id)
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
                    self.context.client.post(f"{self.RESOURCE_PATH}/{quote(root_id, safe='')}/file", json=body)
        except Exception as exc:
            raise ResourceError(f"Directory upload for {root} stopped after a partial upload: {exc}") from exc
        self._apply_data(root_data)

    def save(self, **_: Any) -> "File":
        """Upload the source and persist it as a backend File asset."""
        if self.context is None:
            self.context = type(self).context
        if not self.source:
            raise ValidationError("A local path or URL source is required to save a new File")
        parsed = urlparse(self.source)
        temporary_path: Optional[str] = None
        try:
            if parsed.scheme in {"http", "https"}:
                suffix = Path(parsed.path).suffix
                with requests.get(self.source, stream=True, timeout=self.context.client.timeout) as response:
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
        built = {str(node.get("id")): cls._from_data(node) for node in nodes}
        roots: List[File] = []
        for node in nodes:
            item = built[str(node.get("id"))]
            parent_id = str(node.get("parentId") or "")
            if parent_id in built:
                built[parent_id].children.append(item)
            elif parent_id == root_id or not parent_id:
                roots.append(item)
        return roots

    @classmethod
    def search(
        cls,
        query: Optional[str] = None,
        page_number: int = 0,
        page_size: int = 20,
        sort: Optional[List[Dict[str, Any]]] = None,
        **filters: Any,
    ) -> Page["File"]:
        """Search top-level File assets."""
        body = {"q": query, "pageNumber": page_number, "pageSize": page_size}
        body["sort"] = sort or [{"field": "createdAt", "dir": -1}]
        mapping = {"file_type": "fileType", "parent_type": "parentType"}
        body.update(
            {mapping.get(key, key): value.value if hasattr(value, "value") else value for key, value in filters.items()}
        )
        body = {key: value for key, value in body.items() if value is not None}
        data = cls.context.client.post(f"{cls.RESOURCE_PATH}/paginate", json=body)
        return Page(
            results=[cls._from_data(item) for item in data.get("results", [])],
            page_number=page_number,
            page_total=data.get("pageTotal", 0),
            total=data.get("total", 0),
        )

    def download(self, destination: Union[str, os.PathLike[str]]) -> str:
        """Stream this File to disk, safely extracting folders from one ZIP request."""
        if not self.id:
            raise ValidationError("File must be saved before it can be downloaded")
        target = Path(destination).expanduser()
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
            target = target / (self.name or "download")
        elif str(destination).endswith(os.sep):
            target = target / (self.name or "download")
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


Resource = File

__all__ = ["File", "Resource"]
