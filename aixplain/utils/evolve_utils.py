"""Utility functions for agent and team agent evolution."""

from typing import Union, Dict, Any, Optional, Text
from aixplain.modules.model.llm_model import LLM
from aixplain.enums.supplier import Supplier
from aixplain.enums.function import Function


def create_llm_dict(llm: Optional[Union[Text, LLM]]) -> Optional[Dict[str, Any]]:
    """Create a dictionary representation of an LLM for evolution parameters.

    Args:
        llm: Either an LLM ID string or an LLM object instance.

    Returns:
        Dictionary with LLM information if llm is provided, None otherwise.
    """
    if llm is None:
        return None

    if isinstance(llm, LLM):
        # Serialize supplier enum to string
        supplier = llm.supplier
        if isinstance(supplier, Supplier):
            supplier = supplier.value["code"]

        # Serialize function enum to string
        function = llm.function
        if isinstance(function, Function):
            function = function.value

        return {
            "id": llm.id,
            "name": llm.name,
            "description": llm.description,
            "supplier": supplier,
            "version": llm.version,
            "function": function,
            "parameters": (llm.get_parameters().to_list() if llm.get_parameters() else None),
            "temperature": getattr(llm, "temperature", None),
        }
    else:
        return {"id": llm}
