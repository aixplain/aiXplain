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
from aixplain.utils.file_utils import upload_data
from typing import Text


class FileFactory:
    @classmethod
    def upload(cls, local_path: Text) -> Text:
        if os.path.exists(local_path) is False:
            raise Exception(f'File Upload Error: local file "{local_path}" not found.')
        if os.path.getsize(local_path) > 10485760:
            raise Exception(f'File Upload Error: local file "{local_path}" exceeds 10 MB.')
        s3_path = upload_data(file_name=local_path)
        return s3_path
