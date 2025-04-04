"""
Error message registry for aiXplain SDK.

This module maintains a centralized registry of error messages used throughout the aiXplain ecosystem.
It allows developers to look up existing error messages and reuse them instead of creating new ones.
"""

from typing import Dict, List, Optional, Type
from . import AixplainBaseException


class ErrorRegistry:
    """
    A centralized registry for error messages used throughout the aiXplain ecosystem.
    """

    # Initialize with predefined error messages
    _error_registry: Dict[str, Dict] = {
        # Authentication errors
        "auth.invalid_api_key": {
            "message": "Invalid API key provided",
            "user_message": "The API key you provided is invalid. Please check your credentials.",
        },
        "auth.expired_api_key": {
            "message": "The provided API key has expired",
            "user_message": "Your API key has expired. Please renew your subscription.",
        },
        # Validation errors
        "validation.missing_required_field": {
            "message": "Required field '{field}' is missing",
            "user_message": "Please provide the required field: {field}",
        },
        "validation.invalid_input_format": {
            "message": "Invalid format for '{field}': {reason}",
            "user_message": "The format for '{field}' is invalid: {reason}",
        },
        # Resource errors
        "resource.not_found": {
            "message": "Resource '{resource}' not found",
            "user_message": "The requested resource '{resource}' does not exist.",
        },
        "resource.already_exists": {
            "message": "Resource '{resource}' already exists",
            "user_message": "A resource with name '{resource}' already exists.",
        },
        # Billing errors
        "billing.insufficient_credits": {
            "message": "Insufficient credits to perform operation",
            "user_message": "You don't have enough credits to perform this operation.",
        },
        "billing.quota_exceeded": {
            "message": "Usage quota exceeded",
            "user_message": "You've exceeded your usage quota. Please upgrade your plan.",
        },
        # Supplier errors
        "supplier.unavailable": {
            "message": "Supplier '{supplier}' is currently unavailable",
            "user_message": "The service provider is currently unavailable. Please try again later.",
        },
        "supplier.rate_limited": {
            "message": "Rate limit exceeded for supplier '{supplier}'",
            "user_message": "You've reached the rate limit for this service. Please try again later.",
        },
        # Agent errors
        "agent.execution_failed": {
            "message": "Agent execution failed: {reason}",
            "user_message": "The agent was unable to complete the task: {reason}",
        },
        "agent.iteration_limit": {
            "message": "Agent stopped due to iteration limit ({limit})",
            "user_message": "The agent reached its maximum number of steps without completing the task.",
        },
        "agent.timeout": {
            "message": "Agent execution timed out after {seconds} seconds",
            "user_message": "The operation timed out. Please try again or simplify your request.",
        },
        # Network errors
        "network.connection_error": {
            "message": "Failed to connect to server: {reason}",
            "user_message": "Unable to connect to the server. Please check your internet connection.",
        },
        "network.timeout": {
            "message": "Connection timed out after {seconds} seconds",
            "user_message": "The connection timed out. Please try again later.",
        },
        # Service errors
        "service.unavailable": {
            "message": "Service '{service}' is currently unavailable",
            "user_message": "The service is currently unavailable. Please try again later.",
        },
        "service.maintenance": {
            "message": "Service '{service}' is under maintenance",
            "user_message": "The service is under maintenance. Please try again later.",
        },
        # Internal errors
        "internal.unexpected_error": {
            "message": "An unexpected error occurred: {error}",
            "user_message": "An unexpected error occurred. Our team has been notified.",
        },
        "internal.database_error": {
            "message": "Database error: {error}",
            "user_message": "An internal database error occurred. Our team has been notified.",
        },
    }

    @classmethod
    def get_error_message(cls, error_code: str, **kwargs) -> Dict:
        """
        Get an error message by its code.

        Args:
            error_code (str): The error code to look up.
            **kwargs: Format parameters for the error message.

        Returns:
            Dict: The error message dictionary with formatted message and user_message.
        """
        if error_code not in cls._error_registry:
            return {"message": f"Unknown error: {error_code}", "user_message": "An unknown error occurred."}

        error_dict = cls._error_registry[error_code].copy()

        # Format message and user_message with provided kwargs
        if kwargs:
            error_dict["message"] = error_dict["message"].format(**kwargs)
            error_dict["user_message"] = error_dict["user_message"].format(**kwargs)

        return error_dict

    @classmethod
    def register_error(cls, error_code: str, message: str, user_message: Optional[str] = None) -> None:
        """
        Register a new error message.

        Args:
            error_code (str): The error code to register.
            message (str): The error message for developers.
            user_message (Optional[str]): The user-friendly error message. If None, uses message.
        """
        if not user_message:
            user_message = message

        cls._error_registry[error_code] = {"message": message, "user_message": user_message}

    @classmethod
    def search_errors(cls, keyword: str) -> List[str]:
        """
        Search for error codes containing the given keyword.

        Args:
            keyword (str): The keyword to search for.

        Returns:
            List[str]: A list of error codes containing the keyword.
        """
        return [code for code in cls._error_registry.keys() if keyword.lower() in code.lower()]

    @classmethod
    def list_errors(cls, category: Optional[str] = None) -> List[str]:
        """
        List all error codes, optionally filtered by category.

        Args:
            category (Optional[str]): The category to filter by.

        Returns:
            List[str]: A list of error codes.
        """
        if category is None:
            return list(cls._error_registry.keys())

        return [code for code in cls._error_registry.keys() if code.startswith(f"{category}.")]

    @classmethod
    def create_exception(cls, error_code: str, exception_class: Type[AixplainBaseException], **kwargs) -> AixplainBaseException:
        """
        Create an exception instance using a registered error message.

        Args:
            error_code (str): The error code to use.
            exception_class (Type[AixplainBaseException]): The exception class to instantiate.
            **kwargs: Additional parameters for the exception constructor and message formatting.

        Returns:
            AixplainBaseException: An instance of the specified exception class.
        """
        error_dict = cls.get_error_message(error_code, **kwargs)

        # Extract any format parameters from kwargs that should not be passed to the exception
        exception_kwargs = {k: v for k, v in kwargs.items() if k not in error_dict}

        return exception_class(message=error_dict["message"], user_message=error_dict["user_message"], **exception_kwargs)
