__author__ = "thiagocastroferreira"

import pytest
import requests

from aixplain.enums import Function, EmbeddingModel
from aixplain.factories import ModelFactory
from aixplain.modules import LLM
from datetime import datetime, timedelta, timezone
from pathlib import Path
from aixplain.factories.index_factory.utils import (
    AirParams,
    VectaraParams,
    ZeroEntropyParams,
)
import time
import os
import json

CACHE_FOLDER = ".cache"


def pytest_generate_tests(metafunc):
    if "llm_model" in metafunc.fixturenames:
        four_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=4)
        models = ModelFactory.list(function=Function.TEXT_GENERATION)["results"]

        predefined_models = []
        for predefined_model in ["GPT-4.1 Mini", "GPT-4o"]:
            predefined_models.extend(
                [
                    m
                    for m in ModelFactory.list(query=predefined_model, function=Function.TEXT_GENERATION)["results"]
                    if m.name == predefined_model and "aiXplain-testing" not in str(m.supplier)
                ]
            )
        recent_models = [
            model
            for model in models
            if model.created_at and model.created_at >= four_weeks_ago and "aiXplain-testing" not in str(model.supplier)
        ]
        combined_models = recent_models + predefined_models
        model_ids = [model.id for model in combined_models]
        metafunc.parametrize("llm_model", combined_models, ids=model_ids)


def test_llm_run(llm_model):
    """Testing LLMs with history context"""

    assert isinstance(llm_model, LLM)
    response = llm_model.run(
        data="What is my name?",
        history=[
            {"role": "user", "content": "Hello! My name is Thiago."},
            {"role": "assistant", "content": "Hello!"},
        ],
    )

    assert response["status"] == "SUCCESS"


def test_llm_run_stream():
    """Testing LLMs with streaming"""
    from aixplain.modules.model.response import ModelResponse, ResponseStatus
    from aixplain.modules.model.model_response_streamer import ModelResponseStreamer

    llm_model = ModelFactory.get("669a63646eb56306647e1091")

    assert isinstance(llm_model, LLM)
    response = llm_model.run(
        data="This is a test prompt where I expect you to respond with the following phrase: 'This is a test response.'",
        stream=True,
    )
    assert isinstance(response, ModelResponseStreamer)
    for chunk in response:
        assert isinstance(chunk, ModelResponse)
        assert chunk.data in "This is a test response."
    assert response.status == ResponseStatus.SUCCESS


def test_run_async():
    """Testing Model Async"""
    model = ModelFactory.get("60ddef828d38c51c5885d491")

    response = model.run_async("Test")
    poll_url = response["url"]
    response = model.sync_poll(poll_url)

    assert response["status"] == "SUCCESS"
    assert "teste" in response["data"].lower()


def run_index_model(index_model, retries):
    from aixplain.modules.model.record import Record

    for _ in range(retries):
        try:
            index_model.upsert(
                [
                    Record(
                        value="Berlin is the capital of Germany.",
                        value_type="text",
                        uri="",
                        id="1",
                        attributes={},
                    )
                ]
            )
            break
        except Exception:
            time.sleep(180)

    time.sleep(2)
    response = index_model.search("Berlin")
    assert str(response.status) == "SUCCESS"
    assert "germany" in response.data.lower()
    assert index_model.count() == 1

    index_model.delete()


@pytest.mark.parametrize(
    "embedding_model,supplier_params",
    [
        pytest.param(None, VectaraParams, id="VECTARA"),
        pytest.param(None, ZeroEntropyParams, id="ZERO_ENTROPY"),
        pytest.param(EmbeddingModel.OPENAI_ADA002, AirParams, id="AIR - OpenAI Ada 002"),
        pytest.param(
            EmbeddingModel.MULTILINGUAL_E5_LARGE,
            AirParams,
            id="AIR - Multilingual E5 Large",
        ),
        pytest.param("67efd4f92a0a850afa045af7", AirParams, id="AIR - BGE M3"),
    ],
)
def test_index_model(embedding_model, supplier_params):
    from uuid import uuid4
    from aixplain.factories import IndexFactory

    params = supplier_params(name=str(uuid4()), description=str(uuid4()))
    if embedding_model is not None:
        print(f"Embedding Model : {embedding_model}")
        params = supplier_params(name=str(uuid4()), description=str(uuid4()), embedding_model=embedding_model)

    index_model = IndexFactory.create(params=params)
    if embedding_model in [EmbeddingModel.MULTILINGUAL_E5_LARGE, EmbeddingModel.BGE_M3]:
        retries = 3
    else:
        retries = 1
    run_index_model(index_model, retries)


@pytest.mark.parametrize(
    "embedding_model,supplier_params",
    [
        pytest.param(EmbeddingModel.OPENAI_ADA002, AirParams, id="OpenAI Ada 002"),
        pytest.param(
            EmbeddingModel.JINA_CLIP_V2_MULTIMODAL,
            AirParams,
            id="Jina Clip v2 Multimodal",
        ),
        pytest.param(EmbeddingModel.MULTILINGUAL_E5_LARGE, AirParams, id="Multilingual E5 Large"),
        pytest.param("67efd4f92a0a850afa045af7", AirParams, id="BGE M3"),
    ],
)
def test_index_model_with_filter(embedding_model, supplier_params):
    from uuid import uuid4
    from aixplain.modules.model.record import Record
    from aixplain.factories import IndexFactory
    from aixplain.modules.model.index_model import IndexFilter, IndexFilterOperator

    params = supplier_params(name=str(uuid4()), description=str(uuid4()))
    if embedding_model is not None:
        params = supplier_params(name=str(uuid4()), description=str(uuid4()), embedding_model=embedding_model)

    index_model = IndexFactory.create(params=params)
    if embedding_model in [EmbeddingModel.MULTILINGUAL_E5_LARGE, EmbeddingModel.BGE_M3]:
        retries = 3
    else:
        retries = 1
    for _ in range(retries):
        try:
            index_model.upsert(
                [
                    Record(
                        value="Hello, aiXplain!",
                        value_type="text",
                        uri="",
                        id="1",
                        attributes={"category": "hello"},
                    )
                ]
            )
            break
        except Exception:
            time.sleep(180)
    for _ in range(retries):
        try:
            index_model.upsert(
                [
                    Record(
                        value="The world is great",
                        value_type="text",
                        uri="",
                        id="2",
                        attributes={"category": "world"},
                    )
                ]
            )
            break
        except Exception:
            time.sleep(180)

    time.sleep(2)
    assert index_model.count() == 2
    response = index_model.search(
        "",
        filters=[IndexFilter(field="category", value="world", operator=IndexFilterOperator.EQUALS)],
    )
    assert str(response.status) == "SUCCESS"
    assert "world" in response.data.lower()
    assert len(response.details) == 1
    index_model.delete()


def test_llm_run_with_file():
    """Testing LLM with local file input containing emoji"""

    # Create test file path
    test_file_path = Path(__file__).parent / "data" / "test_input.txt"

    # Get a text generation model
    llm_model = ModelFactory.get("674a17f6098e7d5b18453da7")  # Llama 3.1 Nemotron 70B Instruct

    assert isinstance(llm_model, LLM)

    # Run model with file path
    response = llm_model.run(data=str(test_file_path))

    # Verify response
    assert response["status"] == "SUCCESS"
    assert "🤖" in response["data"], "Robot emoji should be present in the response"


def test_aixplain_model_cache_creation():
    """Ensure AssetCache is triggered and cache is created."""

    cache_file = os.path.join(CACHE_FOLDER, "model.json")

    # Clean up cache before the test
    if os.path.exists(cache_file):
        os.remove(cache_file)

    # Instantiate the Model (replace this with a real model ID from your env)
    model_id = "6239efa4822d7a13b8e20454"  # Translate from Punjabi to Portuguese (Brazil)
    _ = ModelFactory.get(model_id)

    # Assert the cache file was created
    assert os.path.exists(cache_file), "Expected cache file was not created."

    with open(cache_file, "r", encoding="utf-8") as f:
        cache_data = json.load(f)

    assert "data" in cache_data, "Cache file structure invalid - missing 'data' key."
    # Cache structure is: {"expiry": ..., "data": {"model_id": {...}}}
    # So we check if the model_id exists as a key in cache_data["data"]
    assert model_id in cache_data["data"], "Instantiated model not found in cache."


def test_index_model_air_with_image():
    from aixplain.factories import IndexFactory
    from aixplain.modules.model.record import Record
    from uuid import uuid4
    from aixplain.factories.index_factory.utils import AirParams

    params = AirParams(
        name=f"Image Index {uuid4()}",
        description="Index for images",
        embedding_model=EmbeddingModel.JINA_CLIP_V2_MULTIMODAL,
    )

    index_model = IndexFactory.create(params=params)

    records = []
    # Building image
    records.append(
        Record(
            uri="https://aixplain-platform-assets.s3.us-east-1.amazonaws.com/samples/building.png",
            value_type="image",
            attributes={},
            id="1",
        )
    )

    # beach image
    image_url = "https://aixplain-platform-assets.s3.us-east-1.amazonaws.com/samples/hurricane.jpeg"
    response = requests.get(image_url)
    if response.status_code == 200:
        with open("hurricane.jpeg", "wb") as f:
            f.write(response.content)

    records.append(Record(uri="hurricane.jpeg", value_type="image", attributes={}, id="2"))

    # people image
    image_url = "https://aixplain-platform-assets.s3.us-east-1.amazonaws.com/samples/faces.jpeg"
    records.append(Record(uri=image_url, value_type="image", attributes={}, id="3"))

    records.append(Record(value="Hello, world!", value_type="text", uri="", attributes={}, id="4"))

    index_model.upsert(records)

    time.sleep(2)
    response = index_model.search("beach")
    assert str(response.status) == "SUCCESS"
    second_record = response.details[1]["metadata"]["uri"]
    assert "hurricane" in second_record.lower()

    time.sleep(2)
    response = index_model.search("people")
    assert str(response.status) == "SUCCESS"
    first_record = response.details[0]["data"]
    assert "hello" in first_record.lower()
    third_record = response.details[2]["metadata"]["uri"]
    assert "faces" in third_record.lower()

    assert index_model.count() == 4

    response = index_model.get_record("2")
    assert str(response.status) == "SUCCESS"
    second_record = response.details[0]["metadata"]["uri"]
    assert "hurricane" in second_record.lower()

    index_model.delete()


@pytest.mark.parametrize(
    "embedding_model,supplier_params",
    [
        pytest.param(EmbeddingModel.OPENAI_ADA002, AirParams, id="OpenAI Ada 002"),
        pytest.param(
            EmbeddingModel.JINA_CLIP_V2_MULTIMODAL,
            AirParams,
            id="Jina Clip v2 Multimodal",
        ),
        pytest.param(EmbeddingModel.MULTILINGUAL_E5_LARGE, AirParams, id="Multilingual E5 Large"),
        pytest.param(EmbeddingModel.BGE_M3, AirParams, id="BGE M3"),
    ],
)
def test_index_model_air_with_splitter(embedding_model, supplier_params):
    from aixplain.factories import IndexFactory
    from aixplain.modules.model.record import Record
    from uuid import uuid4
    from aixplain.modules.model.index_model import Splitter
    from aixplain.enums.splitting_options import SplittingOptions

    params = supplier_params(
        name=f"Splitter Index {uuid4()}",
        description="Index for splitter",
        embedding_model=embedding_model,
    )
    index_model = IndexFactory.create(params=params)
    index_model.upsert(
        [
            Record(
                value="Berlin is the capital of Germany.",
                value_type="text",
                uri="",
                id="1",
                attributes={},
            )
        ],
        splitter=Splitter(split=True, split_by=SplittingOptions.WORD, split_length=1, split_overlap=0),
    )
    response = index_model.count()
    assert response == 6
    time.sleep(2)
    response = index_model.search("berlin")
    assert str(response.status) == "SUCCESS"
    assert "berlin" in response.data.lower()
    index_model.delete()


def test_index_model_with_txt_file():
    """Testing Index Model with local txt file input"""
    from aixplain.factories import IndexFactory
    from uuid import uuid4
    from aixplain.factories.index_factory.utils import AirParams
    from pathlib import Path

    # Create test file path
    test_file_path = Path(__file__).parent / "data" / "test_input.txt"

    # Create index with OpenAI Ada 002 for text processing
    params = AirParams(
        name=f"File Index {uuid4()}",
        description="Index for file processing",
        embedding_model=EmbeddingModel.OPENAI_ADA002,
    )
    index_model = IndexFactory.create(params=params)

    try:
        # Upsert the file
        response = index_model.upsert(str(test_file_path))
        assert str(response.status) == "SUCCESS"

        # Verify the content was indexed
        response = index_model.search("demo")
        assert str(response.status) == "SUCCESS"
        assert "🤖" in response.data, "Robot emoji should be present in the response"

        # Verify count
        assert index_model.count() > 0

    finally:
        # Cleanup
        index_model.delete()


def test_index_model_with_pdf_file():
    """Testing Index Model with PDF file input"""
    from aixplain.factories import IndexFactory
    from uuid import uuid4
    from aixplain.factories.index_factory.utils import AirParams
    from pathlib import Path

    # Create test file path
    test_file_path = Path(__file__).parent / "data" / "test_file_parser_input.pdf"

    # Create index with OpenAI Ada 002 for text processing
    params = AirParams(
        name=f"PDF Index {uuid4()}",
        description="Index for PDF processing",
        embedding_model=EmbeddingModel.OPENAI_ADA002,
    )
    index_model = IndexFactory.create(params=params)

    try:
        # Upsert the PDF file
        response = index_model.upsert(str(test_file_path))
        assert str(response.status) == "SUCCESS"

        # Verify the content was indexed
        response = index_model.search("document")
        assert str(response.status) == "SUCCESS"
        assert len(response.data) > 0

        # Verify count
        assert index_model.count() > 0

    finally:
        # Cleanup
        index_model.delete()


def test_index_model_with_invalid_file():
    """Testing Index Model with invalid file input"""
    from aixplain.factories import IndexFactory
    from uuid import uuid4
    from aixplain.factories.index_factory.utils import AirParams
    from pathlib import Path

    # Create non-existent file path
    test_file_path = Path(__file__).parent / "data" / "nonexistent.pdf"

    # Create index with OpenAI Ada 002 for text processing
    params = AirParams(
        name=f"Invalid File Index {uuid4()}",
        description="Index for invalid file testing",
        embedding_model=EmbeddingModel.OPENAI_ADA002,
    )
    index_model = IndexFactory.create(params=params)

    try:
        # Attempt to upsert non-existent file
        with pytest.raises(Exception) as e:
            index_model.upsert(str(test_file_path))
        assert "does not exist" in str(e.value)

    finally:
        # Cleanup
        index_model.delete()


def _test_records():
    from aixplain.modules.model.record import Record
    from aixplain.enums import DataType

    return [
        Record(
            value="Artificial intelligence is transforming industries worldwide, from healthcare to finance.",
            value_type=DataType.TEXT,
            id="doc1",
            uri="",
            attributes={"category": "technology", "date": 1751464788},
        ),
        Record(
            value="The Mona Lisa, painted by Leonardo da Vinci, is one of the most famous artworks in history.",
            value_type=DataType.TEXT,
            id="doc2",
            uri="",
            attributes={"category": "art", "date": 1751464790},
        ),
        Record(
            value="Machine learning algorithms are being used to predict patient outcomes in hospitals.",
            value_type=DataType.TEXT,
            id="doc3",
            uri="",
            attributes={"category": "technology", "date": 1751464795},
        ),
        Record(
            value="The Earth orbits the Sun once every 365.25 days, creating the calendar year.",
            value_type=DataType.TEXT,
            id="doc4",
            uri="",
            attributes={"category": "science", "date": 1751464798},
        ),
        Record(
            value="Quantum computing promises to solve complex problems that are currently intractable for classical computers.",
            value_type=DataType.TEXT,
            id="doc5",
            uri="",
            attributes={"category": "technology", "date": 1751464801},
        ),
    ]


@pytest.fixture(scope="function")
def setup_index_with_test_records():
    from aixplain.factories import IndexFactory
    from aixplain.enums import EmbeddingModel
    from aixplain.factories.index_factory.utils import AirParams
    from uuid import uuid4

    params = AirParams(
        name=f"Test Index {uuid4()}",
        description="Test index for filter/date tests",
        embedding_model=EmbeddingModel.OPENAI_ADA002,
    )
    index_model = IndexFactory.create(params=params)
    records = _test_records()

    index_model.upsert(records)

    yield index_model
    index_model.delete()


def test_retrieve_records_with_filter(setup_index_with_test_records):
    from aixplain.modules.model.index_model import IndexFilter, IndexFilterOperator

    index_model = setup_index_with_test_records
    filter_ = IndexFilter(field="category", value="technology", operator=IndexFilterOperator.EQUALS)
    response = index_model.retrieve_records_with_filter(filter_)
    assert response.status == "SUCCESS"
    assert len(response.details) == 3
    for item in response.details:
        assert item["metadata"]["category"] == "technology"


def test_delete_records_by_date(setup_index_with_test_records):
    from aixplain.modules.model.index_model import IndexFilter, IndexFilterOperator

    index_model = setup_index_with_test_records
    response = index_model.delete_records_by_date(1751464796)
    assert response.status == "SUCCESS"
    assert response.data == "2"  # 2 records should remain
    filter_all = IndexFilter(field="date", value=0, operator=IndexFilterOperator.GREATER_THAN)
    response = index_model.retrieve_records_with_filter(filter_all)
    assert response.status == "SUCCESS"
    assert len(response.details) == 2
