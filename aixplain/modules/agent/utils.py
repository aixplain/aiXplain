from typing import Dict, Text, Union
import re


def process_variables(
    query: Union[Text, Dict],
    data: Union[Dict, Text],
    parameters: Dict,
    agent_description: Union[Text, None],
) -> Text:
    """Process variables in an agent's description and input data.

    This function validates and processes variables in an agent's description and
    input data, ensuring that all required variables are present and properly
    formatted.

    Args:
        query (Union[Text, Dict]): The input data provided to the agent.
        data (Union[Dict, Text]): The data to be processed.
        parameters (Dict): The parameters available to the agent.
        agent_description (Union[Text, None]): The description of the agent.

    Returns:
        Text: The processed input data with all required variables included.

    Raises:
        AssertionError: If a required variable is not found in the data or parameters.
    """
    from aixplain.factories.file_factory import FileFactory

    if isinstance(query, dict):
        for key, value in query.items():
            assert isinstance(value, str), "When providing a dictionary, all values must be strings."
            query[key] = FileFactory.to_link(value)
        input_data = query
    else:
        input_data = {"input": FileFactory.to_link(query)}

    variables = re.findall(r"(?<!{){([^}]+)}(?!})", agent_description or "")
    for variable in variables:
        if isinstance(data, dict) and variable in data:
            input_data[variable] = data[variable]
        elif variable in parameters:
            input_data[variable] = parameters[variable]

    return input_data


def validate_history(history):
    """
    Validates that `history` is a list of dicts, each with 'role' and 'content' keys.
    Raises a ValueError if validation fails.
    """
    if not isinstance(history, list):
        raise ValueError(
            "History must be a list of message dictionaries. "
            "Example: [{'role': 'user', 'content': 'Hello'}, {'role': 'assistant', 'content': 'Hi there!'}]"
        )

    allowed_roles = {"user", "assistant"}

    for i, item in enumerate(history):
        if not isinstance(item, dict):
            raise ValueError(
                f"History item at index {i} is not a dict: {item}. "
                "Each item must be a dictionary like: {'role': 'user', 'content': 'Hello'}"
            )

        if "role" not in item or "content" not in item:
            raise ValueError(
                f"History item at index {i} is missing 'role' or 'content': {item}. "
                "Example of a valid message: {'role': 'assistant', 'content': 'Hi there!'}"
            )

        if item["role"] not in allowed_roles:
            raise ValueError(
                f"Invalid role '{item['role']}' at index {i}. Allowed roles: {allowed_roles}. "
                "Example: {'role': 'user', 'content': 'Tell me a joke'}"
            )

        if not isinstance(item["content"], str):
            raise ValueError(
                f"'content' at index {i} must be a string. Got: {type(item['content'])}. "
                "Example: {'role': 'assistant', 'content': 'Sure! Here’s one...'}"
            )

    return True
