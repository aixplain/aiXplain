"""Unit tests for the v2 exception hierarchy.

This module tests the exception classes and error factory functions that
provide consistent error handling across the SDK.
"""

import pytest

from aixplain.v2.exceptions import (
    AixplainV2Error,
    ResourceError,
    APIError,
    ValidationError,
    TimeoutError,
    FileUploadError,
    create_operation_failed_error,
)


class TestAixplainV2Error:
    """Tests for the base exception class."""

    def test_string_message(self):
        """String message should be stored and accessible."""
        error = AixplainV2Error("Something went wrong")

        assert error.message == "Something went wrong"
        assert str(error) == "Something went wrong"

    def test_list_message_joined(self):
        """List messages should be joined with newlines."""
        error = AixplainV2Error(["Error 1", "Error 2", "Error 3"])

        assert error.message == "Error 1\nError 2\nError 3"
        assert "Error 1" in str(error)
        assert "Error 2" in str(error)
        assert "Error 3" in str(error)

    def test_empty_list_message(self):
        """Empty list message should result in empty string."""
        error = AixplainV2Error([])

        assert error.message == ""

    def test_single_item_list_message(self):
        """Single item list should not have extra newlines."""
        error = AixplainV2Error(["Only one error"])

        assert error.message == "Only one error"

    def test_details_stored(self):
        """Details dict should be accessible."""
        details = {"code": "ERR001", "field": "name"}
        error = AixplainV2Error("Error with details", details=details)

        assert error.details == details
        assert error.details["code"] == "ERR001"
        assert error.details["field"] == "name"

    def test_details_default_empty_dict(self):
        """Details should default to empty dict when not provided."""
        error = AixplainV2Error("No details")

        assert error.details == {}

    def test_details_none_becomes_empty_dict(self):
        """None details should become empty dict."""
        error = AixplainV2Error("None details", details=None)

        assert error.details == {}

    def test_exception_inheritance(self):
        """AixplainV2Error should inherit from Exception."""
        error = AixplainV2Error("Test")

        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self):
        """Error should be raiseable and catchable."""
        with pytest.raises(AixplainV2Error) as exc_info:
            raise AixplainV2Error("Raised error")

        assert "Raised error" in str(exc_info.value)


class TestResourceError:
    """Tests for resource operation errors."""

    def test_inherits_from_base(self):
        """ResourceError should inherit from AixplainV2Error."""
        error = ResourceError("Resource operation failed")

        assert isinstance(error, AixplainV2Error)
        assert isinstance(error, Exception)

    def test_message_stored(self):
        """Message should be stored correctly."""
        error = ResourceError("Failed to save resource")

        assert error.message == "Failed to save resource"

    def test_details_stored(self):
        """Details should be stored correctly."""
        error = ResourceError("Failed", details={"resource_id": "123"})

        assert error.details["resource_id"] == "123"

    def test_can_catch_as_base_error(self):
        """ResourceError should be catchable as AixplainV2Error."""
        with pytest.raises(AixplainV2Error):
            raise ResourceError("Resource error")


class TestAPIError:
    """Tests for API call errors."""

    def test_inherits_from_base(self):
        """APIError should inherit from AixplainV2Error."""
        error = APIError("API call failed")

        assert isinstance(error, AixplainV2Error)

    def test_status_code_stored(self):
        """HTTP status code should be accessible."""
        error = APIError("Not found", status_code=404)

        assert error.status_code == 404

    def test_status_code_default_zero(self):
        """Status code should default to 0."""
        error = APIError("Error without status")

        assert error.status_code == 0

    def test_response_data_stored(self):
        """Response data dict should be accessible."""
        response_data = {"errors": [{"field": "name"}], "code": "VALIDATION_ERROR"}
        error = APIError("Validation failed", status_code=422, response_data=response_data)

        assert error.response_data == response_data
        assert error.response_data["code"] == "VALIDATION_ERROR"

    def test_response_data_default_empty_dict(self):
        """Response data should default to empty dict."""
        error = APIError("Error")

        assert error.response_data == {}

    def test_response_data_none_becomes_empty_dict(self):
        """None response data should become empty dict."""
        error = APIError("Error", response_data=None)

        assert error.response_data == {}

    def test_error_field_from_message(self):
        """Error field should default to message if not provided."""
        error = APIError("Something went wrong")

        assert error.error == "Something went wrong"

    def test_error_field_explicit(self):
        """Explicit error field should be stored."""
        error = APIError("Human readable message", error="INTERNAL_ERROR")

        assert error.error == "INTERNAL_ERROR"

    def test_error_field_with_list_message(self):
        """Error field should use str(message) when message is a list."""
        error = APIError(["Error 1", "Error 2"])

        # When message is a list and no explicit error is provided,
        # error becomes str(message) per implementation
        assert error.error == "['Error 1', 'Error 2']"

    def test_details_include_all_fields(self):
        """Details should include status_code, response_data, and error."""
        error = APIError(
            "Failed",
            status_code=500,
            response_data={"key": "value"},
            error="SERVER_ERROR",
        )

        assert error.details["status_code"] == 500
        assert error.details["response_data"] == {"key": "value"}
        assert error.details["error"] == "SERVER_ERROR"

    def test_full_error_construction(self):
        """Test complete APIError construction."""
        error = APIError(
            "Resource not found",
            status_code=404,
            response_data={"resourceId": "123", "resourceType": "agent"},
            error="NOT_FOUND",
        )

        assert "Resource not found" in str(error)
        assert error.status_code == 404
        assert error.response_data["resourceId"] == "123"
        assert error.error == "NOT_FOUND"


class TestValidationError:
    """Tests for validation errors."""

    def test_inherits_from_base(self):
        """ValidationError should inherit from AixplainV2Error."""
        error = ValidationError("Validation failed")

        assert isinstance(error, AixplainV2Error)

    def test_message_stored(self):
        """Message should be stored correctly."""
        error = ValidationError("Name is required")

        assert error.message == "Name is required"

    def test_can_catch_as_base_error(self):
        """ValidationError should be catchable as AixplainV2Error."""
        with pytest.raises(AixplainV2Error):
            raise ValidationError("Invalid input")


class TestTimeoutError:
    """Tests for timeout errors."""

    def test_inherits_from_base(self):
        """TimeoutError should inherit from AixplainV2Error."""
        error = TimeoutError("Operation timed out")

        assert isinstance(error, AixplainV2Error)

    def test_message_stored(self):
        """Message should be stored correctly."""
        error = TimeoutError("Operation timed out after 300 seconds")

        assert error.message == "Operation timed out after 300 seconds"

    def test_does_not_shadow_builtin(self):
        """Should not interfere with built-in TimeoutError in different context."""
        from aixplain.v2.exceptions import TimeoutError as V2TimeoutError

        error = V2TimeoutError("V2 timeout")
        assert isinstance(error, AixplainV2Error)


class TestFileUploadError:
    """Tests for file upload errors."""

    def test_inherits_from_base(self):
        """FileUploadError should inherit from AixplainV2Error."""
        error = FileUploadError("Upload failed")

        assert isinstance(error, AixplainV2Error)

    def test_message_stored(self):
        """Message should be stored correctly."""
        error = FileUploadError("File too large")

        assert error.message == "File too large"

    def test_details_stored(self):
        """Details should be stored correctly."""
        error = FileUploadError(
            "Upload failed",
            details={"file_name": "test.pdf", "size": 100000000},
        )

        assert error.details["file_name"] == "test.pdf"
        assert error.details["size"] == 100000000


class TestCreateOperationFailedError:
    """Tests for the error factory function."""

    def test_extracts_supplier_error(self):
        """Should extract 'supplierError' field (camelCase)."""
        response = {
            "status": "FAILED",
            "supplierError": "Rate limit exceeded",
        }

        error = create_operation_failed_error(response)

        assert isinstance(error, APIError)
        assert "Rate limit exceeded" in str(error)

    def test_extracts_supplier_error_snake_case(self):
        """Should extract 'supplier_error' field (snake_case)."""
        response = {
            "status": "FAILED",
            "supplier_error": "Model unavailable",
        }

        error = create_operation_failed_error(response)

        assert "Model unavailable" in str(error)

    def test_extracts_error_message(self):
        """Should extract 'error_message' field."""
        response = {
            "status": "FAILED",
            "error_message": "Invalid input format",
        }

        error = create_operation_failed_error(response)

        assert "Invalid input format" in str(error)

    def test_extracts_error(self):
        """Should extract 'error' field."""
        response = {
            "status": "FAILED",
            "error": "Connection refused",
        }

        error = create_operation_failed_error(response)

        assert "Connection refused" in str(error)

    def test_fallback_message(self):
        """Should use 'Operation failed' as fallback when no error field."""
        response = {
            "status": "FAILED",
        }

        error = create_operation_failed_error(response)

        assert "Operation failed" in str(error)

    def test_priority_supplier_error_first(self):
        """supplierError should take priority over other fields."""
        response = {
            "status": "FAILED",
            "supplierError": "Supplier error message",
            "error_message": "Error message",
            "error": "Error",
        }

        error = create_operation_failed_error(response)

        assert "Supplier error message" in str(error)

    def test_priority_supplier_error_snake_case_second(self):
        """supplier_error should take priority over error_message."""
        response = {
            "status": "FAILED",
            "supplier_error": "Supplier error snake",
            "error_message": "Error message",
            "error": "Error",
        }

        error = create_operation_failed_error(response)

        assert "Supplier error snake" in str(error)

    def test_priority_error_message_third(self):
        """error_message should take priority over error."""
        response = {
            "status": "FAILED",
            "error_message": "Error message field",
            "error": "Error field",
        }

        error = create_operation_failed_error(response)

        assert "Error message field" in str(error)

    def test_status_code_extracted(self):
        """Should extract statusCode from response."""
        response = {
            "status": "FAILED",
            "error": "Server error",
            "statusCode": 500,
        }

        error = create_operation_failed_error(response)

        assert error.status_code == 500

    def test_status_code_default_zero(self):
        """Status code should default to 0 if not in response."""
        response = {
            "status": "FAILED",
            "error": "Error",
        }

        error = create_operation_failed_error(response)

        assert error.status_code == 0

    def test_response_data_stored(self):
        """Full response should be stored in response_data."""
        response = {
            "status": "FAILED",
            "error": "Error",
            "extra_field": "extra_value",
            "details": {"key": "value"},
        }

        error = create_operation_failed_error(response)

        assert error.response_data == response
        assert error.response_data["extra_field"] == "extra_value"

    def test_error_field_set(self):
        """Error field should be set to extracted error message."""
        response = {
            "status": "FAILED",
            "supplierError": "Specific error",
        }

        error = create_operation_failed_error(response)

        assert error.error == "Specific error"

    def test_message_format(self):
        """Message should be formatted as 'Operation failed: <error>'."""
        response = {
            "status": "FAILED",
            "error": "Something went wrong",
        }

        error = create_operation_failed_error(response)

        assert "Operation failed: Something went wrong" in str(error)

    def test_empty_response(self):
        """Should handle empty response dict."""
        response = {}

        error = create_operation_failed_error(response)

        assert "Operation failed" in str(error)
        assert error.status_code == 0


class TestExceptionHierarchy:
    """Tests for the overall exception hierarchy."""

    def test_all_errors_inherit_from_base(self):
        """All custom errors should inherit from AixplainV2Error."""
        errors = [
            ResourceError("test"),
            APIError("test"),
            ValidationError("test"),
            TimeoutError("test"),
            FileUploadError("test"),
        ]

        for error in errors:
            assert isinstance(error, AixplainV2Error)

    def test_catch_all_with_base_error(self):
        """All errors should be catchable with AixplainV2Error."""
        error_classes = [
            ResourceError,
            APIError,
            ValidationError,
            TimeoutError,
            FileUploadError,
        ]

        for error_class in error_classes:
            try:
                raise error_class("Test error")
            except AixplainV2Error as e:
                assert "Test error" in str(e)
            except Exception:
                pytest.fail(f"{error_class.__name__} was not caught as AixplainV2Error")

    def test_specific_catch_before_base(self):
        """Specific error types should be catchable before base."""
        try:
            raise APIError("API specific", status_code=401)
        except APIError as e:
            assert e.status_code == 401
        except AixplainV2Error:
            pytest.fail("APIError should be caught before AixplainV2Error")
