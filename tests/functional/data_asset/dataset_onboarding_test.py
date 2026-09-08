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
import time

from uuid import uuid4
from aixplain.enums import (
    Function,
    Language,
    License,
    Privacy,
    DataSubtype,
    DataType,
    StorageType,
    OnboardStatus,
)
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
            "languages": [Language.ENGLISH_UNITED_STATES],
        }
    ]


@pytest.fixture
def meta2():
    return [
        {
            "name": "text",
            "dtype": "text",
            "storage_type": "text",
            "languages": [Language.ENGLISH_UNITED_STATES],
        }
    ]


@pytest.fixture
def split():
    return MetaData(
        name="split",
        dtype=DataType.LABEL,
        dsubtype=DataSubtype.SPLIT,
        storage_type=StorageType.TEXT,
    )


def _track_dataset(resource_tracker, DatasetFactory, asset_id):
    """Register an onboarded dataset for guaranteed cleanup (BUG-947).

    ``DatasetFactory.create`` returns a dict, not a deletable object, so the
    tracker is given a callback that resolves the id when teardown runs.

    Returns:
        The tracker entry, to pass to ``mark_cleaned`` if the test deletes the
        dataset itself.
    """
    return resource_tracker.add_callback(f"Dataset id={asset_id}", lambda: DatasetFactory.get(asset_id).delete())


@pytest.mark.parametrize("DatasetFactory", [DatasetFactory])
def test_dataset_onboard_get_delete(meta1, meta2, resource_tracker, DatasetFactory):
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
    asset_id = response["asset_id"]
    # `create` returns a dict rather than a deletable object, so the tracker gets
    # a callback. Registered before the polling loop: an assertion failure or a
    # timeout while waiting for ONBOARDED used to leak the dataset (BUG-947).
    cleanup = _track_dataset(resource_tracker, DatasetFactory, asset_id)

    onboard_status = OnboardStatus(response["status"])
    while onboard_status == OnboardStatus.ONBOARDING:
        dataset = DatasetFactory.get(asset_id)
        onboard_status = dataset.onboard_status
        time.sleep(1)
    # assert the asset was onboarded
    assert onboard_status == OnboardStatus.ONBOARDED
    # assert the asset was deleted -- the delete is the behaviour under test, so
    # deregister it rather than letting teardown delete a second time.
    dataset.delete()
    resource_tracker.mark_cleaned(cleanup)
    with pytest.raises(Exception):
        dataset = DatasetFactory.get(asset_id)


@pytest.mark.parametrize("DatasetFactory", [DatasetFactory])
def test_invalid_dataset_onboard(meta1, meta2, DatasetFactory):
    # Nothing to register: `create` is expected to raise, so there is no asset_id
    # to clean up. If the backend ever *accepted* this payload the assertion
    # would fail (correctly) and one dataset would leak, with no id available to
    # prevent it -- a documented residual risk of BUG-947, not an oversight.
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


@pytest.mark.parametrize("DatasetFactory", [DatasetFactory])
def test_dataset_listing(DatasetFactory):
    response = DatasetFactory.list()
    assert "results" in response


@pytest.mark.parametrize("DatasetFactory", [DatasetFactory])
def test_dataset_get_error(DatasetFactory):
    with pytest.raises(Exception):
        response = DatasetFactory.get("131312")


@pytest.mark.parametrize("DatasetFactory", [DatasetFactory])
def test_invalid_dataset_splitting(meta1, meta2, split, DatasetFactory):
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


@pytest.mark.parametrize("DatasetFactory", [DatasetFactory])
def test_valid_dataset_splitting(meta1, meta2, split, resource_tracker, DatasetFactory):
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

    asset_id = response["asset_id"]
    cleanup = _track_dataset(resource_tracker, DatasetFactory, asset_id)

    assert response["status"] == "onboarding"
    onboard_status = OnboardStatus(response["status"])
    while onboard_status == OnboardStatus.ONBOARDING:
        dataset = DatasetFactory.get(asset_id)
        onboard_status = dataset.onboard_status
        time.sleep(1)
    # assert the asset was onboarded
    assert onboard_status == OnboardStatus.ONBOARDED
    dataset.delete()
    resource_tracker.mark_cleaned(cleanup)
