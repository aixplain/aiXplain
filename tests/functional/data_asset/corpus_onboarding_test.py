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
from aixplain.enums import Language, License, OnboardStatus
from aixplain.factories.corpus_factory import CorpusFactory
from uuid import uuid4


@pytest.mark.parametrize("CorpusFactory", [CorpusFactory])
def test_corpus_onboard_get_delete(CorpusFactory):
    upload_file = "tests/functional/data_asset/input/audio-en_url.csv"
    schema = [
        {
            "name": "audio",
            "dtype": "audio",
            "storage_type": "url",
            "start_column": "audio_start_time",
            "end_column": "audio_end_time",
            "languages": [Language.ENGLISH_UNITED_STATES],
        },
        {
            "name": "text",
            "dtype": "text",
            "storage_type": "text",
            "languages": [Language.ENGLISH_UNITED_STATES],
        },
    ]

    response = CorpusFactory.create(
        name=str(uuid4()),
        description="This corpus contain 20 English audios with their corresponding transcriptions.",
        license=License.MIT,
        content_path=upload_file,
        schema=schema,
    )
    asset_id = response["asset_id"]
    onboard_status = OnboardStatus(response["status"])
    while onboard_status == OnboardStatus.ONBOARDING:
        corpus = CorpusFactory.get(asset_id)
        onboard_status = corpus.onboard_status
        time.sleep(1)
    # assert the asset was onboarded
    assert onboard_status == OnboardStatus.ONBOARDED
    # assert the asset was deleted
    corpus.delete()
    with pytest.raises(Exception):
        corpus = CorpusFactory.get(asset_id)


@pytest.mark.parametrize("CorpusFactory", [CorpusFactory])
def test_corpus_listing(CorpusFactory):
    response = CorpusFactory.list()
    assert "results" in response


@pytest.mark.parametrize("CorpusFactory", [CorpusFactory])
def test_corpus_get_error(CorpusFactory):
    with pytest.raises(Exception):
        response = CorpusFactory.get("131312")
