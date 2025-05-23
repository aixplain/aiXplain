__author__ = "thiagocastroferreira"

import pytest
import requests

from aixplain.enums import Function, EmbeddingModel
from aixplain.factories import ModelFactory
from aixplain.modules import LLM
from datetime import datetime, timedelta, timezone
from pathlib import Path
from aixplain.factories.index_factory.utils import AirParams, VectaraParams, GraphRAGParams, ZeroEntropyParams


def pytest_generate_tests(metafunc):
    if "llm_model" in metafunc.fixturenames:
        four_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=4)
        models = ModelFactory.list(function=Function.TEXT_GENERATION)["results"]

        predefined_models = []
        for predefined_model in ["Groq Llama 3 70B", "GPT-4o"]:
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
        history=[{"role": "user", "content": "Hello! My name is Thiago."}, {"role": "assistant", "content": "Hello!"}],
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


def run_index_model(index_model):
    from aixplain.modules.model.record import Record

    index_model.upsert([Record(value="Berlin is the capital of Germany.", value_type="text", uri="", id="1", attributes={})])
    response = index_model.search("Berlin")
    assert str(response.status) == "SUCCESS"
    assert "germany" in response.data.lower()
    assert index_model.count() == 1

    index_model.upsert([Record(value="Ankara is the capital of Turkey.", value_type="text", uri="", id="1", attributes={})])
    response = index_model.search("Ankara")
    assert str(response.status) == "SUCCESS"
    assert "turkey" in response.data.lower()
    assert index_model.count() == 1

    index_model.upsert([Record(value="London is the capital of England.", value_type="text", uri="", id="2", attributes={})])
    assert index_model.count() == 2

    response = index_model.get_record("1")
    assert str(response.status) == "SUCCESS"
    assert response.data == "Ankara is the capital of Turkey."
    assert index_model.count() == 2

    response = index_model.delete_record("1")
    assert str(response.status) == "SUCCESS"
    assert index_model.count() == 1

    index_model.delete()


@pytest.mark.parametrize(
    "embedding_model,supplier_params",
    [
        pytest.param(None, VectaraParams, id="VECTARA"),
        pytest.param(None, ZeroEntropyParams, id="ZERO_ENTROPY"),
        pytest.param(EmbeddingModel.OPENAI_ADA002, GraphRAGParams, id="GRAPHRAG"),
        pytest.param(EmbeddingModel.OPENAI_ADA002, AirParams, id="AIR - OpenAI Ada 002"),
        pytest.param(EmbeddingModel.SNOWFLAKE_ARCTIC_EMBED_M_LONG, AirParams, id="AIR - Snowflake Arctic Embed M Long"),
        pytest.param(EmbeddingModel.SNOWFLAKE_ARCTIC_EMBED_L_V2_0, AirParams, id="AIR - Snowflake Arctic Embed L v2.0"),
        pytest.param(EmbeddingModel.MULTILINGUAL_E5_LARGE, AirParams, id="AIR - Multilingual E5 Large"),
        pytest.param(EmbeddingModel.BGE_M3, AirParams, id="AIR - BGE M3"),
        pytest.param(EmbeddingModel.AIXPLAIN_LEGAL_EMBEDDINGS, AirParams, id="AIR - aiXplain Legal Embeddings"),
    ],
)
def test_index_model(embedding_model, supplier_params):
    from uuid import uuid4
    from aixplain.factories import IndexFactory

    params = supplier_params(name=str(uuid4()), description=str(uuid4()))
    if embedding_model is not None:
        params = supplier_params(name=str(uuid4()), description=str(uuid4()), embedding_model=embedding_model)

    index_model = IndexFactory.create(params=params)
    run_index_model(index_model)


@pytest.mark.parametrize(
    "embedding_model,supplier_params",
    [
        pytest.param(None, VectaraParams, id="VECTARA"),
        pytest.param(EmbeddingModel.OPENAI_ADA002, AirParams, id="OpenAI Ada 002"),
        pytest.param(EmbeddingModel.SNOWFLAKE_ARCTIC_EMBED_M_LONG, AirParams, id="Snowflake Arctic Embed M Long"),
        pytest.param(EmbeddingModel.SNOWFLAKE_ARCTIC_EMBED_L_V2_0, AirParams, id="Snowflake Arctic Embed L v2.0"),
        pytest.param(EmbeddingModel.JINA_CLIP_V2_MULTIMODAL, AirParams, id="Jina Clip v2 Multimodal"),
        pytest.param(EmbeddingModel.MULTILINGUAL_E5_LARGE, AirParams, id="Multilingual E5 Large"),
        pytest.param(EmbeddingModel.BGE_M3, AirParams, id="BGE M3"),
        pytest.param(EmbeddingModel.AIXPLAIN_LEGAL_EMBEDDINGS, AirParams, id="aiXplain Legal Embeddings"),
    ],
)
def test_index_model_with_filter(embedding_model, supplier_params):
    from uuid import uuid4
    from aixplain.modules.model.record import Record
    from aixplain.factories import IndexFactory
    from aixplain.modules.model.index_model import IndexFilter, IndexFilterOperator

    for index in IndexFactory.list()["results"]:
        index.delete()

    params = supplier_params(name=str(uuid4()), description=str(uuid4()))
    if embedding_model is not None:
        params = supplier_params(name=str(uuid4()), description=str(uuid4()), embedding_model=embedding_model)

    index_model = IndexFactory.create(params=params)
    index_model.upsert([Record(value="Hello, aiXplain!", value_type="text", uri="", id="1", attributes={"category": "hello"})])
    index_model.upsert(
        [Record(value="The world is great", value_type="text", uri="", id="2", attributes={"category": "world"})]
    )
    assert index_model.count() == 2
    response = index_model.search(
        "", filters=[IndexFilter(field="category", value="world", operator=IndexFilterOperator.EQUALS)]
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


def test_index_model_air_with_image():
    from aixplain.factories import IndexFactory
    from aixplain.modules.model.record import Record
    from uuid import uuid4
    from aixplain.factories.index_factory.utils import AirParams

    for index in IndexFactory.list()["results"]:
        index.delete()

    params = AirParams(
        name=f"Image Index {uuid4()}", description="Index for images", embedding_model=EmbeddingModel.JINA_CLIP_V2_MULTIMODAL
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

    response = index_model.search("beach")
    assert str(response.status) == "SUCCESS"
    second_record = response.details[1]["metadata"]["uri"]
    assert "hurricane" in second_record.lower()

    response = index_model.search("people")
    assert str(response.status) == "SUCCESS"
    first_record = response.details[0]["data"]
    assert "hello" in first_record.lower()
    second_record = response.details[1]["metadata"]["uri"]
    assert "faces" in second_record.lower()

    assert index_model.count() == 4

    response = index_model.get_record("2")
    assert str(response.status) == "SUCCESS"
    second_record = response.details[0]["metadata"]["uri"]
    assert "hurricane" in second_record.lower()

    index_model.delete()

    import os

    if os.path.exists("hurricane.jpeg"):
        os.remove("hurricane.jpeg")
