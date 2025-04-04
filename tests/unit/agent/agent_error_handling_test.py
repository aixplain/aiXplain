import pytest
import requests_mock
from unittest.mock import patch, MagicMock, call

from aixplain.modules import Agent
from aixplain.enums.asset_status import AssetStatus
from aixplain.exceptions import (
    ValidationError,
    AuthenticationError,
    BillingError,
    SupplierError,
    NetworkError,
    AgentExecutionError,
)
from aixplain.enums import ResponseStatus
from aixplain.utils import config
from urllib.parse import urljoin


def create_mock_agent():
    agent = Agent(
        id="test-agent-123",
        name="Test Error Handling Agent",
        description="Agent for testing error handling",
        instructions="Handle errors properly",
        status=AssetStatus.ONBOARDED,
    )
    # Set a validate method that always returns True to skip validation
    agent.validate = lambda: True
    agent.url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}/run")
    return agent


# Tests for non-recoverable errors
@pytest.mark.parametrize(
    "error_class,error_message,status_code,http_response",
    [
        (ValidationError, "Invalid input parameters", 400, {"message": "Invalid input parameters", "code": 490}),
        (AuthenticationError, "Unauthorized API key", 401, {"message": "Unauthorized API key", "code": 401}),
        (BillingError, "Insufficient credits", 402, {"message": "Insufficient credits", "code": 470}),
        (ValidationError, "Subscription expired", 403, {"message": "Subscription expired", "code": 460}),
    ],
)
def test_non_recoverable_errors(error_class, error_message, status_code, http_response):
    """Test that non-recoverable errors break the process immediately without retries."""
    agent = create_mock_agent()

    # Mock the error handling process
    mock_error_handler = MagicMock()
    mock_error_handler.handle_error.return_value = {
        "break_process": True,
        "should_retry": False,
        "error": error_class(error_message),
    }
    agent.error_handler = mock_error_handler

    with requests_mock.Mocker() as mock:
        # Mock the HTTP response with the error
        mock.post(agent.url, status_code=status_code, json=http_response)

        # Call the agent
        response = agent.run_async(query="Test query")

        # Verify the response indicates failure
        assert response.status == ResponseStatus.FAILED
        assert error_message in response.error_message

        # Verify the error handler was called exactly once (no retries)
        assert mock_error_handler.handle_error.call_count == 1


# Tests for recoverable errors with retry
def test_supplier_error_retry_with_progressive_interval():
    """Test that supplier/quota errors trigger retries with progressive intervals."""
    agent = create_mock_agent()

    # Mock the error handling process to simulate retries
    mock_error_handler = MagicMock()
    # First call: should retry in 2 seconds
    # Second call: should retry in 4 seconds
    # Third call: should retry in 8 seconds
    # Fourth call: break the process (no more retries)
    mock_error_handler.handle_error.side_effect = [
        {"break_process": False, "should_retry": True, "retry_after": 2, "error": SupplierError("Rate limit exceeded")},
        {"break_process": False, "should_retry": True, "retry_after": 4, "error": SupplierError("Rate limit exceeded")},
        {"break_process": False, "should_retry": True, "retry_after": 8, "error": SupplierError("Rate limit exceeded")},
        {"break_process": False, "should_retry": False, "error": SupplierError("Rate limit exceeded")},
    ]
    agent.error_handler = mock_error_handler

    # Mock time.sleep to avoid actual waiting
    with patch("time.sleep") as mock_sleep, requests_mock.Mocker() as mock:
        # Mock the HTTP response with the error
        mock.post(agent.url, status_code=480, json={"message": "Rate limit exceeded", "code": 480})

        # Call the agent
        response = agent.run_async(query="Test query")

        # Verify the response indicates failure
        assert response.status == ResponseStatus.FAILED
        assert "Rate limit exceeded" in response.error_message

        # Verify error handler was called 4 times (3 retries + initial attempt)
        assert mock_error_handler.handle_error.call_count == 4

        # Verify time.sleep was called with progressive intervals
        assert mock_sleep.call_count == 3
        mock_sleep.assert_has_calls([call(2), call(4), call(8)])


# Test for unspecified errors with fixed retry interval
def test_unspecified_error_retry():
    """Test that unspecified errors trigger retries with fixed interval."""
    agent = create_mock_agent()

    # Create a generic error that doesn't fit into specific categories
    generic_error = AgentExecutionError(
        message="Unspecified error occurred",
    )

    # Mock the error handling process to simulate retries
    mock_error_handler = MagicMock()
    # Simulate 3 retry attempts with fixed 1-second intervals
    mock_error_handler.handle_error.side_effect = [
        {"break_process": False, "should_retry": True, "retry_after": 1, "error": generic_error},
        {"break_process": False, "should_retry": True, "retry_after": 1, "error": generic_error},
        {"break_process": False, "should_retry": True, "retry_after": 1, "error": generic_error},
        {"break_process": False, "should_retry": False, "error": generic_error},
    ]
    agent.error_handler = mock_error_handler

    # Mock time.sleep to avoid actual waiting
    with patch("time.sleep") as mock_sleep, requests_mock.Mocker() as mock:
        # Mock the HTTP response with the error
        mock.post(agent.url, status_code=500, json={"message": "Internal server error", "code": 500})

        # Call the agent
        response = agent.run_async(query="Test query")

        # Verify the response indicates failure
        assert response.status == ResponseStatus.FAILED
        assert "Unspecified error" in response.error_message

        # Verify error handler was called 4 times (3 retries + initial attempt)
        assert mock_error_handler.handle_error.call_count == 4

        # Verify time.sleep was called with fixed intervals
        assert mock_sleep.call_count == 3
        mock_sleep.assert_has_calls([call(1), call(1), call(1)])


# Test for successful recovery after a temporary error
def test_successful_recovery_after_error():
    """Test that the agent can recover after a temporary error."""
    agent = create_mock_agent()

    # Mock the error handling process to simulate a successful retry
    mock_error_handler = MagicMock()
    mock_error_handler.handle_error.return_value = {
        "break_process": False,
        "should_retry": True,
        "retry_after": 1,
        "error": NetworkError("Temporary network issue"),
    }
    agent.error_handler = mock_error_handler

    with patch("time.sleep") as mock_sleep, requests_mock.Mocker() as mock:
        # First request fails with network error
        # Second request succeeds
        mock.post(
            agent.url,
            [
                {"status_code": 503, "json": {"message": "Service unavailable", "code": 503}},
                {"status_code": 200, "json": {"data": "http://result.url", "status": "IN_PROGRESS"}},
            ],
        )

        # Call the agent
        response = agent.run_async(query="Test query")

        # Verify the response indicates success
        assert response.status == ResponseStatus.IN_PROGRESS
        assert response.url == "http://result.url"

        # Verify error handler was called once for the first error
        assert mock_error_handler.handle_error.call_count == 1

        # Verify time.sleep was called once with the specified interval
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(1)


# Test the actual error_handler implementation (not just mocks)
def test_error_handler_implementation():
    """Test the actual error handler implementation for correct classification of errors."""
    from aixplain.exceptions.error_handler import ErrorHandler

    error_handler = ErrorHandler(max_retries=3)

    # Test non-recoverable errors
    validation_error = ValidationError("Invalid input")
    auth_error = AuthenticationError("Invalid API key")
    billing_error = BillingError("Payment required")

    # Each of these should immediately break the process
    for error in [validation_error, auth_error, billing_error]:
        result = error_handler.handle_error(error, "test_operation")
        assert result["break_process"] is True
        assert result["should_retry"] is False

    # Test recoverable errors
    supplier_error = SupplierError("Rate limit exceeded")

    # Should recommend retry with exponential backoff
    error_handler.retry_count = 0  # Reset retry counter
    result1 = error_handler.handle_error(supplier_error, "test_operation")
    assert result1["break_process"] is False
    assert result1["should_retry"] is True
    assert result1["retry_after"] == 2  # 2^1

    result2 = error_handler.handle_error(supplier_error, "test_operation")
    assert result2["break_process"] is False
    assert result2["should_retry"] is True
    assert result2["retry_after"] == 4  # 2^2

    result3 = error_handler.handle_error(supplier_error, "test_operation")
    assert result3["break_process"] is False
    assert result3["should_retry"] is True
    assert result3["retry_after"] == 8  # 2^3

    # Fourth retry should fail
    result4 = error_handler.handle_error(supplier_error, "test_operation")
    assert result4["should_retry"] is False
