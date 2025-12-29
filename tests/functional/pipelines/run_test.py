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
from aixplain.enums.response_status import ResponseStatus


@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_list_pipelines(PipelineFactory):
    search_result = PipelineFactory.list()

    assert "results" in search_result
    assert "page_total" in search_result
    assert "page_number" in search_result
    assert "total" in search_result
    assert len(search_result["results"]) > 0


@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_get_pipeline(PipelineFactory):
    reference_pipeline = PipelineFactory.list()["results"][0]

    hypothesis_pipeline = PipelineFactory.get(reference_pipeline.id)
    assert hypothesis_pipeline.id == reference_pipeline.id


@pytest.mark.parametrize(
    "batchmode,version",
    [
        (True, "2.0"),
        (True, "3.0"),
        (False, "2.0"),
        (False, "3.0"),
    ],
)
def test_run_single_str(batchmode: bool, version: str):
    pipeline = PipelineFactory.list(query="SingleNodePipeline")["results"][0]

    response = pipeline.run(data="Translate this thing", batch_mode=batchmode, **{"version": version})
    assert response["status"] == ResponseStatus.SUCCESS


@pytest.mark.parametrize(
    "batchmode,version",
    [
        (True, "2.0"),
        (True, "3.0"),
        (False, "2.0"),
        (False, "3.0"),
    ],
)
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_single_local_file(batchmode: bool, version: str, PipelineFactory):
    pipeline = PipelineFactory.list(query="SingleNodePipeline")["results"][0]

    fname = "translate_this.txt"
    with open(fname, "w") as f:
        f.write("Translate this thing")

    response = pipeline.run(data=fname, batch_mode=batchmode, **{"version": version})
    os.remove(fname)
    assert response["status"] == ResponseStatus.SUCCESS


@pytest.mark.parametrize(
    "batchmode,version",
    [
        (True, "2.0"),
        (True, "3.0"),
        (False, "2.0"),
        (False, "3.0"),
    ],
)
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_with_url(batchmode: bool, version: str, PipelineFactory):
    pipeline = PipelineFactory.list(query="SingleNodePipeline")["results"][0]

    response = pipeline.run(
        data="https://aixplain-platform-assets.s3.amazonaws.com/data/dev/64c81163f8bdcac7443c2dad/data/f8.txt",
        batch_mode=batchmode,
        **{"version": version},
    )
    assert response["status"] == ResponseStatus.SUCCESS


@pytest.mark.parametrize(
    "batchmode,version",
    [
        (True, "2.0"),
        (True, "3.0"),
        (False, "2.0"),
        (False, "3.0"),
    ],
)
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_with_dataset(batchmode: bool, version: str, PipelineFactory):
    dataset = DatasetFactory.list(query="for_functional_tests")["results"][0]
    data_asset_id = dataset.id
    data_id = dataset.source_data["en"].id
    pipeline = PipelineFactory.list(query="SingleNodePipeline")["results"][0]

    response = pipeline.run(
        data=data_id,
        data_asset=data_asset_id,
        batch_mode=batchmode,
        **{"version": version},
    )
    assert response["status"] == ResponseStatus.SUCCESS


@pytest.mark.parametrize(
    "batchmode,version",
    [
        (True, "2.0"),
        (True, "3.0"),
        (False, "2.0"),
        (False, "3.0"),
    ],
)
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_multipipe_with_strings(batchmode: bool, version: str, PipelineFactory):
    pipeline = PipelineFactory.list(query="MultiInputPipeline")["results"][0]

    response = pipeline.run(
        data={"Input": "Translate this thing.", "Reference": "Traduza esta coisa."},
        batch_mode=batchmode,
        **{"version": version},
    )
    assert response["status"] == ResponseStatus.SUCCESS


@pytest.mark.parametrize(
    "batchmode,version",
    [
        (True, "2.0"),
        (True, "3.0"),
        (False, "2.0"),
        (False, "3.0"),
    ],
)
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_multipipe_with_datasets(batchmode: bool, version: str, PipelineFactory):
    pipeline = PipelineFactory.list(query="MultiInputPipeline")["results"][0]

    dataset = DatasetFactory.list(query="for_functional_tests")["results"][0]
    data_asset_id = dataset.id

    input_id = dataset.source_data["en"].id
    reference_id = dataset.target_data["pt"][0].id

    response = pipeline.run(
        data={"Input": input_id, "Reference": reference_id},
        data_asset={"Input": data_asset_id, "Reference": data_asset_id},
        batch_mode=batchmode,
        **{"version": version},
    )
    assert response["status"] == ResponseStatus.SUCCESS


@pytest.mark.parametrize("version", ["2.0", "3.0"])
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_segment_reconstruct(version: str, PipelineFactory):
    pipeline = PipelineFactory.list(query="Segmentation/Reconstruction Functional Test - DO NOT DELETE")["results"][0]
    response = pipeline.run(
        "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
        **{"version": version},
    )

    assert response["status"] == ResponseStatus.SUCCESS


@pytest.mark.parametrize("version", ["2.0", "3.0"])
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_translation_metric(version: str, PipelineFactory):
    dataset = DatasetFactory.list(query="for_functional_tests")["results"][0]
    data_asset_id = dataset.id

    reference_id = dataset.target_data["pt"][0].id

    pipeline = PipelineFactory.list(query="Translation Metric Functional Test - DO NOT DELETE")["results"][0]
    response = pipeline.run(
        data={"TextInput": reference_id, "ReferenceInput": reference_id},
        data_asset={"TextInput": data_asset_id, "ReferenceInput": data_asset_id},
        **{"version": version},
    )

    assert response["status"] == ResponseStatus.SUCCESS


@pytest.mark.skip
@pytest.mark.parametrize("version", ["2.0", "3.0"])
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_metric(version: str, PipelineFactory):
    pipeline = PipelineFactory.list(query="ASR Metric Functional Test - DO NOT DELETE")["results"][0]
    response = pipeline.run(
        {
            "AudioInput": "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
            "ReferenceInput": "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.txt",
        },
        **{"version": version},
    )

    assert response["status"] == ResponseStatus.SUCCESS


@pytest.mark.parametrize(
    "input_data,output_data,version",
    [
        (
            "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
            "AudioOutput",
            "2.0",
        ),
        (
            "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.txt",
            "TextOutput",
            "2.0",
        ),
        (
            "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
            "AudioOutput",
            "3.0",
        ),
        (
            "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.txt",
            "TextOutput",
            "3.0",
        ),
    ],
)
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_router(input_data: str, output_data: str, version: str, PipelineFactory):
    pipeline = PipelineFactory.list(query="Router Test - DO NOT DELETE")["results"][0]
    response = pipeline.run(input_data, **{"version": version})

    assert response["status"] == ResponseStatus.SUCCESS


@pytest.mark.parametrize(
    "input_data,output_data,version",
    [
        ("I love it.", "PositiveOutput", "2.0"),
        ("I hate it.", "NegativeOutput", "2.0"),
        ("I love it.", "PositiveOutput", "3.0"),
        ("I hate it.", "NegativeOutput", "3.0"),
    ],
)
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_decision(input_data: str, output_data: str, version: str, PipelineFactory):
    pipeline = PipelineFactory.list(query="Decision Test - DO NOT DELETE")["results"][0]
    response = pipeline.run(input_data, **{"version": version})

    assert response["status"] == ResponseStatus.SUCCESS
    assert response["data"][0]["label"] == output_data


@pytest.mark.parametrize("version", ["3.0"])
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_script(version: str, PipelineFactory):
    pipeline = PipelineFactory.list(query="Script Functional Test - DO NOT DELETE")["results"][0]
    response = pipeline.run(
        "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
        **{"version": version},
    )

    assert response["status"] == ResponseStatus.SUCCESS
    data = response["data"][0]["segments"][0]["response"]
    assert data.startswith("SCRIPT MODIFIED:")


@pytest.mark.parametrize("version", ["2.0", "3.0"])
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_text_reconstruction(version: str, PipelineFactory):
    pipeline = PipelineFactory.list(query="Text Reconstruction - DO NOT DELETE")["results"][0]
    response = pipeline.run("Segment A\nSegment B\nSegment C", **{"version": version})

    assert response["status"] == ResponseStatus.SUCCESS
    labels = [d["label"] for d in response["data"]]
    assert "Audio (Direct)" in labels
    assert "Audio (Text Reconstruction)" in labels
    assert "Audio (Audio Reconstruction)" in labels
    assert "Text Reconstruction" in labels

    for d in response["data"]:
        assert len(d["segments"]) > 0
        assert d["segments"][0]["success"] is True


@pytest.mark.parametrize("version", ["3.0"])
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_diarization(version: str, PipelineFactory):
    pipeline = PipelineFactory.list(query="Diarization ASR Functional Test - DO NOT DELETE")["results"][0]
    response = pipeline.run(
        "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
        **{"version": version},
    )

    assert response["status"] == ResponseStatus.SUCCESS
    for d in response["data"]:
        assert len(d["segments"]) > 0
        assert d["segments"][0]["success"] is True


@pytest.mark.parametrize("version", ["3.0"])
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_failure(version: str, PipelineFactory):
    pipeline = PipelineFactory.list(query="Script Functional Test - DO NOT DELETE")["results"][0]
    response = pipeline.run(
        "INCORRECT DATA",
        **{"version": version},
    )

    assert response["status"] == ResponseStatus.FAILED


@pytest.mark.parametrize("version", ["2.0", "3.0"])
@pytest.mark.parametrize("PipelineFactory", [PipelineFactory])
def test_run_async_simple(version: str, PipelineFactory):
    """Test simple async pipeline execution with polling"""
    pipeline = PipelineFactory.list(query="SingleNodePipeline")["results"][0]

    # Start async execution
    response = pipeline.run_async(data="Translate this simple text", **{"version": version})

    poll_url = response["url"]
    import time

    max_attempts = 55
    attempt = 0

    while attempt < max_attempts:
        poll_response = pipeline.poll(poll_url)
        if hasattr(poll_response, "completed") and poll_response.completed:
            break
        elif isinstance(poll_response, dict) and poll_response.get("completed", False):
            break
        time.sleep(1)
        attempt += 1

    assert poll_response.status == ResponseStatus.SUCCESS
