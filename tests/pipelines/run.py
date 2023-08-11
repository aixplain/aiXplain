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

from aixplain.factories import PipelineFactory


def test_run_single_str():
    pipeline_id = "642c57142155270012fa0d17"
    pipeline = PipelineFactory.get(pipeline_id)

    response = pipeline.run(data="Translate this thing")
    assert response["status"] == "SUCCESS"


def test_run_with_url():
    pipeline_id = "642c57142155270012fa0d17"
    pipeline = PipelineFactory.get(pipeline_id)

    response = pipeline.run(
        data="https://aixplain-platform-assets.s3.amazonaws.com/data/dev/64c81163f8bdcac7443c2dad/data/f8.txt"
    )
    assert response["status"] == "SUCCESS"


def test_run_with_dataset():
    data_asset_id = "64c81163f8bdcac7443c2dac"
    data_id = "64c81163f8bdcac7443c2dad"
    pipeline_id = "642c57142155270012fa0d17"
    pipeline = PipelineFactory.get(pipeline_id)

    response = pipeline.run(data=data_id, data_asset=data_asset_id)
    assert response["status"] == "SUCCESS"


def test_run_multipipe_with_strings():
    pipeline_id = "64cd4a79024b1d9e905c0023"
    pipeline = PipelineFactory.get(pipeline_id)

    response = pipeline.run(data={"Hypothesis": "Translate this thing.", "Reference": "Traduisez cette chose."})
    assert response["status"] == "SUCCESS"


def test_run_multipipe_with_datasets():
    pipeline_id = "64cd4a79024b1d9e905c0023"
    pipeline = PipelineFactory.get(pipeline_id)

    response = pipeline.run(
        data={"Hypothesis": "64c81163f8bdcac7443c2dad", "Reference": "64c81163f8bdcac7443c2dae"},
        data_asset={"Hypothesis": "64c81163f8bdcac7443c2dac", "Reference": "64c81163f8bdcac7443c2dac"},
    )
    assert response["status"] == "SUCCESS"
