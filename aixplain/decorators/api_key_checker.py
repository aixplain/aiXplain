from aixplain.utils import config


def check_api_key(method):
    """Decorator to verify that an API key is set before executing the method.

    This decorator checks if either TEAM_API_KEY or AIXPLAIN_API_KEY is set in the
    configuration. If neither key is set, it raises an exception.

    Args:
        method (callable): The method to be decorated.

    Returns:
        callable: The wrapped method that includes API key verification.

    Raises:
        Exception: If neither TEAM_API_KEY nor AIXPLAIN_API_KEY is set.

    Example:
        @check_api_key
        def my_api_method():
            # Method implementation
            pass
    """
    def wrapper(*args, **kwargs):
        if config.TEAM_API_KEY == "" and config.AIXPLAIN_API_KEY == "":
            raise Exception(
                "A 'TEAM_API_KEY' is required to run an asset. For help, please refer to the documentation (https://github.com/aixplain/aixplain#api-key-setup)"
            )
        return method(*args, **kwargs)

    return wrapper
