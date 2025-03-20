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
import os
from aixplain.utils.cache_utils import CACHE_FOLDER
from aixplain.modules.pipeline import Pipeline
import json
import pytest
from aixplain.factories import PipelineFactory
from aixplain.modules import Pipeline
from uuid import uuid4
from aixplain import aixplain_v2 as v2

@pytest.mark.parametrize("PipelineFactory", [PipelineFactory, v2.Pipeline])
def test_create_pipeline_from_json(PipelineFactory):
    pipeline_json = "tests/functional/pipelines/data/pipeline.json"
    pipeline_name = str(uuid4())
    pipeline = PipelineFactory.create(name=pipeline_name, pipeline=pipeline_json)

    assert isinstance(pipeline, Pipeline)
    assert pipeline.id != ""
    pipeline.delete()


@pytest.mark.parametrize("PipelineFactory", [PipelineFactory, v2.Pipeline])
def test_create_pipeline_from_string(PipelineFactory):
    pipeline_json = "tests/functional/pipelines/data/pipeline.json"
    with open(pipeline_json) as f:
        pipeline_dict = json.load(f)

    pipeline_name = str(uuid4())
    pipeline = PipelineFactory.create(name=pipeline_name, pipeline=pipeline_dict)

    assert isinstance(pipeline, Pipeline)
    assert pipeline.id != ""
    assert pipeline.status.value == "draft"

    pipeline.deploy()
    pipeline = PipelineFactory.get(pipeline.id)
    assert pipeline.status.value == "onboarded"
    pipeline.delete()


@pytest.mark.parametrize("PipelineFactory", [PipelineFactory, v2.Pipeline])
def test_update_pipeline(PipelineFactory):
    pipeline_json = "tests/functional/pipelines/data/pipeline.json"
    with open(pipeline_json) as f:
        pipeline_dict = json.load(f)

    pipeline_name = str(uuid4())
    pipeline = PipelineFactory.create(name=pipeline_name, pipeline=pipeline_dict)

    pipeline.update(pipeline=pipeline_json, save_as_asset=True, name="NEW NAME")
    assert pipeline.name == "NEW NAME"
    assert isinstance(pipeline, Pipeline)
    assert pipeline.id != ""
    pipeline.delete()


@pytest.mark.parametrize("PipelineFactory", [PipelineFactory, v2.Pipeline])
def test_create_pipeline_wrong_path(PipelineFactory):
    pipeline_name = str(uuid4())

    with pytest.raises(Exception):
        PipelineFactory.create(name=pipeline_name, pipeline="/")



@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_pipeline_cache_creation(PipelineFactory):
    cache_file = os.path.join(CACHE_FOLDER, "pipelines.json")
    if os.path.exists(cache_file):
        os.remove(cache_file)

    pipeline_json = "tests/functional/pipelines/data/pipeline.json"
    pipeline_name = str(uuid4())
    pipeline = PipelineFactory.create(name=pipeline_name, pipeline=pipeline_json)

    assert os.path.exists(cache_file), "Pipeline cache file was not created!"

    with open(cache_file, "r") as f:
        cache_data = json.load(f)

    assert "data" in cache_data, "Cache format invalid, missing 'data'."

    pipeline.delete()
    if os.path.exists(cache_file):
        os.remove(cache_file)