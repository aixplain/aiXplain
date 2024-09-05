__author__ = "thiagocastroferreira"


from aixplain.enums import Function
from aixplain.factories import ModelFactory
from aixplain.modules import LLM
from datetime import datetime, timedelta, timezone


def pytest_generate_tests(metafunc):
    if "llm_model" in metafunc.fixturenames:
        four_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=4)
        models = ModelFactory.list(function=Function.TEXT_GENERATION)["results"]
        recent_models = [model.name for model in models if model.created_at is not None and model.created_at >= four_weeks_ago]
        if not recent_models:
            recent_models = ["Groq Llama 3 70B", "Chat GPT 3.5", "GPT-4o", "GPT 4 (32k)"]

        metafunc.parametrize("llm_model", recent_models)


def test_llm_run(llm_model):
    """Testing LLMs with history context"""
    model = ModelFactory.list(query=llm_model, function=Function.TEXT_GENERATION)["results"][0]

    assert isinstance(model, LLM)

    response = model.run(
        data="What is my name?",
        history=[{"role": "user", "content": "Hello! My name is Thiago."}, {"role": "assistant", "content": "Hello!"}],
    )
    assert response["status"] == "SUCCESS"
    assert "thiago" in response["data"].lower()
