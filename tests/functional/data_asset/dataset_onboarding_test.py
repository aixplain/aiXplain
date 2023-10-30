__author__ = "thiagocastroferreira"

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
from uuid import uuid4
from aixplain.enums import Function, Language, License, Privacy, DataSubtype, DataType, StorageType
from aixplain.factories import DatasetFactory
from aixplain.modules import MetaData


@pytest.fixture
def meta1():
    return [
        {
            "name": "audio",
            "dtype": "audio",
            "storage_type": "url",
            "start_column": "audio_start_time",
            "end_column": "audio_end_time",
            "languages": [Language.English_UNITED_STATES],
        }
    ]


@pytest.fixture
def meta2():
    return [{"name": "text", "dtype": "text", "storage_type": "text", "languages": [Language.English_UNITED_STATES]}]


@pytest.fixture
def split():
    return MetaData(
        name="split",
        dtype=DataType.LABEL,
        dsubtype=DataSubtype.SPLIT,
        storage_type=StorageType.TEXT,
    )


def test_dataset_onboard(meta1, meta2):
    upload_file = "tests/functional/data_asset/input/audio-en_url.csv"

    response = DatasetFactory.create(
        name=str(uuid4()),
        description="Test dataset",
        license=License.MIT,
        function=Function.SPEECH_RECOGNITION,
        content_path=upload_file,
        input_schema=meta1,
        output_schema=meta2,
        tags=[],
        privacy=Privacy.PRIVATE,
    )
    assert response["status"] == "onboarding"


def test_invalid_dataset_onboard(meta1, meta2):
    upload_file = "tests/functional/data_asset/input/audio-en_url.csv"

    with pytest.raises(Exception):
        response = DatasetFactory.create(
            name=str(uuid4()),
            description="Test dataset",
            license=License.MIT,
            function=Function.TRANSLATION,
            content_path=upload_file,
            input_schema=meta1,
            output_schema=meta2,
            tags=[],
            privacy=Privacy.PRIVATE,
        )


def test_dataset_listing():
    response = DatasetFactory.list()
    assert "results" in response


def test_dataset_get_error():
    with pytest.raises(Exception):
        response = DatasetFactory.get("131312")


def test_invalid_dataset_splitting(meta1, meta2, split):
    upload_file = "tests/functional/data_asset/input/audio-en_with_invalid_split_url.csv"

    split2 = MetaData(
        name="split-2",
        dtype=DataType.LABEL,
        dsubtype=DataSubtype.SPLIT,
        storage_type=StorageType.TEXT,
    )

    with pytest.raises(Exception):
        response = DatasetFactory.create(
            name=str(uuid4()),
            description="Test dataset",
            license=License.MIT,
            function=Function.SPEECH_RECOGNITION,
            content_path=upload_file,
            input_schema=meta1,
            output_schema=meta2,
            metadata_schema=[split, split2],
            tags=[],
            privacy=Privacy.PRIVATE,
        )


def test_valid_dataset_splitting(meta1, meta2, split):
    upload_file = "tests/functional/data_asset/input/audio-en_with_split_url.csv"

    response = DatasetFactory.create(
        name=str(uuid4()),
        description="Test dataset",
        license=License.MIT,
        function=Function.SPEECH_RECOGNITION,
        content_path=upload_file,
        input_schema=meta1,
        output_schema=meta2,
        metadata_schema=[split],
        tags=[],
        privacy=Privacy.PRIVATE,
    )

    assert response["status"] == "onboarding"
