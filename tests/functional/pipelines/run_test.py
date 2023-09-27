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
from aixplain.factories import PipelineFactory


def test_run_single_str():
    pipeline_id = "64da138fa27cffd5e0c3c30d"
    pipeline = PipelineFactory.get(pipeline_id)

    response = pipeline.run(data="Translate this thing")
    assert response["status"] == "SUCCESS"


def test_run_with_url():
    pipeline_id = "64da138fa27cffd5e0c3c30d"
    pipeline = PipelineFactory.get(pipeline_id)

    response = pipeline.run(
        data="https://aixplain-platform-assets.s3.amazonaws.com/data/dev/64c81163f8bdcac7443c2dad/data/f8.txt"
    )
    assert response["status"] == "SUCCESS"


def test_run_with_dataset():
    data_asset_id = "6504a0ddf0fee977097114cd"
    data_id = "6504a0ddf0fee977097114ce"
    pipeline_id = "64da138fa27cffd5e0c3c30d"
    pipeline = PipelineFactory.get(pipeline_id)

    response = pipeline.run(data=data_id, data_asset=data_asset_id)
    assert response["status"] == "SUCCESS"


def test_run_multipipe_with_strings():
    pipeline_id = "64da16ce13d879bec2323a7f"
    pipeline = PipelineFactory.get(pipeline_id)

    response = pipeline.run(data={"Input": "Translate this thing.", "Reference": "Traduza esta coisa."})
    assert response["status"] == "SUCCESS"


def test_run_multipipe_with_datasets():
    pipeline_id = "64da16ce13d879bec2323a7f"
    pipeline = PipelineFactory.get(pipeline_id)

    response = pipeline.run(
        data={"Input": "6504a0ddf0fee977097114ce", "Reference": "6504a0ddf0fee977097114cf"},
        data_asset={"Input": "6504a0ddf0fee977097114cd", "Reference": "6504a0ddf0fee977097114cd"},
    )
    assert response["status"] == "SUCCESS"
