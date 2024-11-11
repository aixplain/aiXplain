import re
from typing import List


def find_prompt_params(prompt: str) -> List[str]:
    """
    This method will find the prompt parameters in the prompt string.

    :param prompt: the prompt string
    :return: list of prompt parameters
    """
    param_regex = re.compile(r"\{\{([^\}]+)\}\}")
    return param_regex.findall(prompt)
