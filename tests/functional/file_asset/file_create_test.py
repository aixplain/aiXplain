__author__ = "mohammedalyafeai"

"""
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

import pytest
from aixplain.enums import License
from aixplain.factories import FileFactory


@pytest.mark.parametrize(
    "FileFactory, is_temp, expected_link",
    [
        (FileFactory, True, "http"),
        (FileFactory, False, "s3"),
    ],
)
def test_file_create(FileFactory, is_temp, expected_link):
    upload_file = "tests/functional/file_asset/input/test.csv"
    s3_link = FileFactory.create(local_path=upload_file, tags=["test1", "test2"], license=License.MIT, is_temp=is_temp)
    assert s3_link.startswith(expected_link)
