from typing import Optional, Text
from aixplain.factories.model_factory import ModelFactory
from aixplain.modules.model.llm_model import LLM


def get_llm_instance(
    llm_id: Text,
    api_key: Optional[Text] = None,
) -> LLM:
    """Get an LLM instance with specific configuration.

    Args:
        llm_id (Text): ID of the LLM model to use
        api_key (Optional[Text], optional): API key to use. Defaults to None.

    Returns:
        LLM: Configured LLM instance
    """
    try:
        llm = ModelFactory.get(llm_id, api_key=api_key)
        return llm
    except Exception:
        raise Exception(f"Large Language Model with ID '{llm_id}' not found.")
