"""API key validation decorator for aiXplain SDK."""

from aixplain.utils.config import check_api_keys_available


def check_api_key(method):
    """Decorator to verify that an API key is set before executing the method.

    This decorator uses the centralized API key validation logic from config.py
    to ensure consistent behavior across the entire SDK.

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
        # Use centralized validation - single source of truth
        check_api_keys_available()
        return method(*args, **kwargs)

    return wrapper
