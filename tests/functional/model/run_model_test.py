__author__ = "thiagocastroferreira"


from aixplain.enums import Function
from aixplain.factories import ModelFactory
from aixplain.modules import LLM
from datetime import datetime, timedelta, timezone


def pytest_generate_tests(metafunc):
    if "llm_model" in metafunc.fixturenames:
        four_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=4)
        models = ModelFactory.list(function=Function.TEXT_GENERATION)["results"]

        predefined_models = []
        for predefined_model in ["Groq Llama 3 70B", "Chat GPT 3.5", "GPT-4o"]:
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


def test_run_async():
    """Testing Model Async"""
    model = ModelFactory.get("60ddef828d38c51c5885d491")

    response = model.run_async("Test")
    poll_url = response["url"]
    response = model.sync_poll(poll_url)

    assert response["status"] == "SUCCESS"
    assert "teste" in response["data"].lower()


def test_index_model():
    from uuid import uuid4
    from aixplain.modules.model.record import Record
    from aixplain.factories import IndexFactory

    for index in IndexFactory.list()["results"]:
        index.delete()

    index_model = IndexFactory.create(name=str(uuid4()), description=str(uuid4()))
    index_model.upsert([Record(value="Hello, world!", value_type="text", uri="", id="1", attributes={})])
    response = index_model.search("Hello")
    assert str(response.status) == "SUCCESS"
    assert "world" in response.data.lower()
    assert index_model.count() == 1
    index_model.upsert([Record(value="Hello, aiXplain!", value_type="text", uri="", id="1", attributes={})])
    response = index_model.search("aiXplain")
    assert str(response.status) == "SUCCESS"
    assert "aixplain" in response.data.lower()
    assert index_model.count() == 1
    index_model.delete()
