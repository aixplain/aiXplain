__author__ = "thiagocastroferreira"

import pytest

from aixplain.enums import Function
from aixplain.factories import ModelFactory
from aixplain.modules import LLM


@pytest.mark.parametrize("llm_model", ["Groq Llama 3 70B", "Chat GPT 3.5", "GPT-4o", "GPT 4 (32k)"])
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
