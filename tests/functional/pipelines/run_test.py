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
import os
from aixplain.factories import DatasetFactory, PipelineFactory


def test_list_pipelines():
    search_result = PipelineFactory.list()

    assert "results" in search_result
    assert "page_total" in search_result
    assert "page_number" in search_result
    assert "total" in search_result
    assert len(search_result["results"]) > 0


def test_get_pipeline():
    reference_pipeline = PipelineFactory.list()["results"][0]

    hypothesis_pipeline = PipelineFactory.get(reference_pipeline.id)
    assert hypothesis_pipeline.id == reference_pipeline.id


@pytest.mark.parametrize("batchmode", [True, False])
def test_run_single_str(batchmode: bool):
    pipeline = PipelineFactory.list(query="SingleNodePipeline")["results"][0]

    response = pipeline.run(data="Translate this thing", **{"batchmode": batchmode})
    assert response["status"] == "SUCCESS"


@pytest.mark.parametrize("batchmode", [True, False])
def test_run_single_local_file(batchmode: bool):
    pipeline = PipelineFactory.list(query="SingleNodePipeline")["results"][0]

    fname = "translate_this.txt"
    with open(fname, "w") as f:
        f.write("Translate this thing")

    response = pipeline.run(data=fname, **{"batchmode": batchmode})
    os.remove(fname)
    assert response["status"] == "SUCCESS"


@pytest.mark.parametrize("batchmode", [True, False])
def test_run_with_url(batchmode: bool):
    pipeline = PipelineFactory.list(query="SingleNodePipeline")["results"][0]

    response = pipeline.run(
        data="https://aixplain-platform-assets.s3.amazonaws.com/data/dev/64c81163f8bdcac7443c2dad/data/f8.txt",
        **{"batchmode": batchmode}
    )
    assert response["status"] == "SUCCESS"


@pytest.mark.parametrize("batchmode", [True, False])
def test_run_with_dataset(batchmode: bool):
    dataset = DatasetFactory.list(query="for_functional_tests")["results"][0]
    data_asset_id = dataset.id
    data_id = dataset.source_data["en"].id
    pipeline = PipelineFactory.list(query="SingleNodePipeline")["results"][0]

    response = pipeline.run(data=data_id, data_asset=data_asset_id, **{"batchmode": batchmode})
    assert response["status"] == "SUCCESS"


@pytest.mark.parametrize("batchmode", [True, False])
def test_run_multipipe_with_strings(batchmode: bool):
    pipeline = PipelineFactory.list(query="MultiInputPipeline")["results"][0]

    response = pipeline.run(
        data={"Input": "Translate this thing.", "Reference": "Traduza esta coisa."}, **{"batchmode": batchmode}
    )
    assert response["status"] == "SUCCESS"


@pytest.mark.parametrize("batchmode", [True, False])
def test_run_multipipe_with_datasets(batchmode: bool):
    pipeline = PipelineFactory.list(query="MultiInputPipeline")["results"][0]

    dataset = DatasetFactory.list(query="for_functional_tests")["results"][0]
    data_asset_id = dataset.id

    input_id = dataset.source_data["en"].id
    reference_id = dataset.target_data["pt"][0].id

    response = pipeline.run(
        data={"Input": input_id, "Reference": reference_id},
        data_asset={"Input": data_asset_id, "Reference": data_asset_id},
        **{"batchmode": batchmode}
    )
    assert response["status"] == "SUCCESS"
