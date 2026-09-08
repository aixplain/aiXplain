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

import os

import pytest
from aixplain.enums import License
from aixplain.factories import FileFactory

UPLOAD_FILE = "tests/functional/file_asset/input/test.csv"

#: BUG-947: the ``is_temp=False`` leg ran on every push to `main`, against the
#: production tenant, and left the S3 object behind permanently -- there is no
#: delete path for it. ``FileFactory.create(is_temp=False)`` returns a bare
#: ``s3://`` string rather than an asset id, and the v2 ``File`` resource has no
#: ``DeleteResourceMixin``, so "delete what it uploads" is not implementable
#: today. The ticket's alternative -- ``is_temp=True`` -- is the default here,
#: and the permanent path stays available behind this flag for anyone verifying
#: it deliberately.
ALLOW_PERMANENT_ENV = "AIXPLAIN_ALLOW_PERMANENT_UPLOADS"

_TRUTHY = ("1", "true", "yes", "on")


@pytest.mark.parametrize(
    "FileFactory, is_temp, expected_link",
    [
        (FileFactory, True, "http"),
    ],
)
def test_file_create(FileFactory, is_temp, expected_link):
    s3_link = FileFactory.create(local_path=UPLOAD_FILE, tags=["test1", "test2"], license=License.MIT, is_temp=is_temp)
    assert s3_link.startswith(expected_link)


@pytest.mark.skipif(
    os.getenv(ALLOW_PERMANENT_ENV, "").lower() not in _TRUTHY,
    reason=(
        "a permanent upload cannot be deleted through the SDK, so this leaks an S3 object; "
        f"set {ALLOW_PERMANENT_ENV}=1 to run it deliberately (BUG-947)"
    ),
)
def test_file_create_permanent():
    """The is_temp=False path. Leaves a permanent S3 object behind by design."""
    link = FileFactory.create(local_path=UPLOAD_FILE, tags=["test1", "test2"], license=License.MIT, is_temp=False)
    assert link.startswith("s3")
