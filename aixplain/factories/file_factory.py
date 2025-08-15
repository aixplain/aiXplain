__author__ = "shreyassharma"

"""
Copyright 2023 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: aiXplain team
Date: March 20th 2023
Description:
    File Factory Class
"""

import os
import validators
import filetype
from aixplain.enums.storage_type import StorageType
from aixplain.enums.license import License
from aixplain.utils.file_utils import upload_data
from typing import Any, Dict, Text, Union, Optional, List


MB_1 = 1048576
MB_25 = 26214400
MB_50 = 52428800
MB_300 = 314572800


class FileFactory:
    """Factory class for managing file uploads and storage in the aiXplain platform.

    This class provides functionality for uploading files to S3 storage,
    checking storage types, and managing file links. It supports various file
    types with different size limits and handles both temporary and permanent
    storage.
    """

    @classmethod
    def upload(
        cls,
        local_path: Text,
        tags: Optional[List[Text]] = None,
        license: Optional[License] = None,
        is_temp: bool = True,
        return_download_link: bool = False,
        api_key: Optional[Text] = None,
    ) -> Text:
        """Upload a file to the aiXplain S3 storage.

        This method uploads a file to S3 storage with size limits based on file type:
            - Audio: 50MB
            - Application: 25MB
            - Video: 300MB
            - Image: 25MB
            - Database: 300MB
            - Other: 50MB

        Args:
            local_path (Text): Path to the file to upload.
            tags (Optional[List[Text]], optional): Tags to associate with the file.
                Defaults to None.
            license (Optional[License], optional): License type for the file.
                Required for non-temporary files. Defaults to None.
            is_temp (bool, optional): Whether this is a temporary upload.
                Defaults to True.
            return_download_link (bool, optional): Whether to return a download
                link instead of S3 path. Only valid for temporary files.
                Defaults to False.

        Returns:
            Text: Either:
                - S3 path where the file was uploaded (if return_download_link=False)
                - Download URL for the file (if return_download_link=True)

        Raises:
            FileNotFoundError: If the local file doesn't exist.
            Exception: If:
                - File size exceeds the type-specific limit
                - Requesting download link for non-temporary file
            AssertionError: If requesting download link for non-temporary file.
        """
        if is_temp is False:
            assert (
                return_download_link is False
            ), "File Upload Error: It is not allowed to return the download link for non-temporary files."
        if os.path.exists(local_path) is False:
            raise FileNotFoundError(f'File Upload Error: local file "{local_path}" not found.')
        # mime type format: {type}/{extension}
        mime_type = filetype.guess_mime(local_path)
        if mime_type is None:
            content_type = "text/csv"
        else:
            content_type = mime_type

        type_to_max_size = {
            "audio": MB_50,
            "application": MB_25,
            "video": MB_300,
            "image": MB_25,
            "other": MB_50,
            "database": MB_300,
        }
        if local_path.endswith(".db"):
            ftype = "database"
        elif mime_type is None or mime_type.split("/")[0] not in type_to_max_size:
            ftype = "other"
        else:
            ftype = mime_type.split("/")[0]
        if os.path.getsize(local_path) > type_to_max_size[ftype]:
            raise Exception(
                f'File Upload Error: local file "{local_path}" of type "{mime_type}" exceeds {type_to_max_size[ftype] / MB_1} MB.'
            )

        if is_temp is False:
            s3_path = upload_data(
                file_name=local_path,
                tags=tags,
                license=license,
                is_temp=is_temp,
                content_type=content_type,
                return_download_link=return_download_link,
            )
        else:
            s3_path = upload_data(file_name=local_path, return_download_link=return_download_link, api_key=api_key)
        return s3_path

    @classmethod
    def check_storage_type(cls, input_link: Any) -> StorageType:
        """Determine the storage type of a given input.

        This method checks whether the input is a local file path, a URL
        (including S3 and HTTP/HTTPS links), or raw text content.

        Args:
            input_link (Any): Input to check. Can be a file path, URL, or text.

        Returns:
            StorageType: Storage type enum value:
                - StorageType.FILE: Local file path
                - StorageType.URL: S3 or HTTP/HTTPS URL
                - StorageType.TEXT: Raw text content
        """
        if os.path.exists(input_link) is True and os.path.isfile(input_link) is True:
            return StorageType.FILE
        elif (
            input_link.startswith("s3://")  # noqa
            or input_link.startswith("http://")  # noqa
            or input_link.startswith("https://")  # noqa
            or validators.url(input_link)  # noqa
        ):
            return StorageType.URL
        else:
            return StorageType.TEXT

    @classmethod
    def to_link(cls, data: Union[Text, Dict], **kwargs) -> Union[Text, Dict]:
        """Convert local file paths to aiXplain platform links.

        This method checks if the input contains local file paths and uploads
        them to the platform, replacing the paths with the resulting URLs.
        Other types of input (URLs, text) are left unchanged.

        Args:
            data (Union[Text, Dict]): Input data to process. Can be:
                - Text: Single file path, URL, or text content
                - Dict: Dictionary with string values that may be file paths
            **kwargs: Additional arguments passed to upload() method.

        Returns:
            Union[Text, Dict]: Processed input where any local file paths have
            been replaced with platform URLs. Structure matches input type.
        """
        if isinstance(data, dict):
            for key in data:
                if isinstance(data[key], str):
                    if cls.check_storage_type(data[key]) == StorageType.FILE:
                        data[key] = cls.upload(local_path=data[key], **kwargs)
        elif isinstance(data, str):
            if cls.check_storage_type(data) == StorageType.FILE:
                data = cls.upload(local_path=data, **kwargs)
        return data

    @classmethod
    def create(
        cls, local_path: Text, tags: Optional[List[Text]] = None, license: Optional[License] = None, is_temp: bool = False
    ) -> Text:
        """Create a permanent or temporary file asset in the platform.

        This method is similar to upload() but with a focus on creating file
        assets. For permanent assets (is_temp=False), a license is required.

        Args:
            local_path (Text): Path to the file to upload.
            tags (Optional[List[Text]], optional): Tags to associate with the file.
                Defaults to None.
            license (Optional[License], optional): License type for the file.
                Required for non-temporary files. Defaults to None.
            is_temp (bool, optional): Whether this is a temporary upload.
                Defaults to False.

        Returns:
            Text: Either:
                - S3 path for permanent files (is_temp=False)
                - Download URL for temporary files (is_temp=True)

        Raises:
            FileNotFoundError: If the local file doesn't exist.
            Exception: If file size exceeds the type-specific limit.
            AssertionError: If license is not provided for non-temporary files.
        """
        assert (
            license is not None if is_temp is False else True
        ), "File Asset Creation Error: To upload a non-temporary file, you need to specify the `license`."
        return cls.upload(local_path=local_path, tags=tags, license=license, is_temp=is_temp, return_download_link=is_temp)
