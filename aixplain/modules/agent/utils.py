from typing import Dict, Text, Union
import re


def process_variables(
    query: Union[Text, Dict], data: Union[Dict, Text], parameters: Dict, agent_description: Union[Text, None]
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
        if isinstance(data, dict):
            assert (
                variable in data or variable in parameters
            ), f"Variable '{variable}' not found in data or parameters. This variable is required by the agent according to its description ('{agent_description}')."
            input_data[variable] = data.pop(variable) if variable in data else parameters.pop(variable)
        else:
            assert (
                variable in parameters
            ), f"Variable '{variable}' not found in parameters. This variable is required by the agent according to its description ('{agent_description}')."
            input_data[variable] = parameters.pop(variable)

    return input_data
