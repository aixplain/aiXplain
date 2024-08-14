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
    @classmethod
    def upload(
        cls, local_path: Text, tags: Optional[List[Text]] = None, license: Optional[License] = None, is_temp: bool = True
    ) -> Text:
        """
        Uploads a file to an S3 bucket.

        Args:
            local_path (Text): The local path of the file to upload.
            tags (List[Text], optional): tags of the file
            license (License, optional): the license for the file
            is_temp (bool): specify if the file that will be upload is a temporary file

        Returns:
            Text: The S3 path where the file was uploaded.

        Raises:
            FileNotFoundError: If the local file is not found.
            Exception: If the file size exceeds the maximum allowed size.
        """
        if os.path.exists(local_path) is False:
            raise FileNotFoundError(f'File Upload Error: local file "{local_path}" not found.')
        # mime type format: {type}/{extension}
        mime_type = filetype.guess_mime(local_path)
        if mime_type is None:
            content_type = "text/csv"
        else:
            content_type = mime_type

        type_to_max_size = {"audio": MB_50, "application": MB_25, "video": MB_300, "image": MB_25, "other": MB_50}
        if mime_type is None or mime_type.split("/")[0] not in type_to_max_size:
            ftype = "other"
        else:
            ftype = mime_type.split("/")[0]
        if os.path.getsize(local_path) > type_to_max_size[ftype]:
            raise Exception(
                f'File Upload Error: local file "{local_path}" of type "{mime_type}" exceeds {type_to_max_size[ftype] / MB_1} MB.'
            )

        if is_temp is False:
            s3_path = upload_data(file_name=local_path, tags=tags, license=license, is_temp=is_temp, content_type=content_type)
        else:
            s3_path = upload_data(file_name=local_path)
        return s3_path

    @classmethod
    def check_storage_type(cls, input_link: Any) -> StorageType:
        """Check whether a path is a URL (s3 link or HTTP link), a file or a textual content

        Args:
            input_link (Any): path to be checked

        Returns:
            StorageType: URL, TEXT or FILE
        """
        if os.path.exists(input_link) is True:
            return StorageType.FILE
        elif (
            input_link.startswith("s3://")
            or input_link.startswith("http://")
            or input_link.startswith("https://")
            or validators.url(input_link)
        ):
            return StorageType.URL
        else:
            return StorageType.TEXT

    @classmethod
    def to_link(cls, data: Union[Text, Dict], **kwargs) -> Union[Text, Dict]:
        """If user input data is a local file, upload to aiXplain platform

        Args:
            data (Union[Text, Dict]): input data

        Returns:
            Union[Text, Dict]: input links/texts
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
        """
        Uploads a file to an S3 bucket.

        Args:
            local_path (Text): The local path of the file to upload.
            tags (List[Text], optional): tags of the file
            license (License, optional): the license for the file
            is_temp (bool): specify if the file that will be upload is a temporary file

        Returns:
            Text: The S3 path where the file was uploaded.

        Raises:
            FileNotFoundError: If the local file is not found.
            Exception: If the file size exceeds the maximum allowed size.
        """
        assert (
            license is not None if is_temp is False else True
        ),  "File Asset Creation Error: To upload a non-temporary file, you need to specify the `license`."
        return cls.upload(local_path=local_path, tags=tags, license=license, is_temp=is_temp)
