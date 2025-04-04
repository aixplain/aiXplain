# Error Handling in aiXplain SDK

This guide explains the error handling system in the aiXplain SDK and provides information on how to use it effectively.

## Overview

The aiXplain error handling system is designed to:

1. Provide structured, consistent error messages across the SDK, Backend, and Agentification services
2. Separate internal error details from user-facing messages
3. Allow for centralized error message management
4. Support retry mechanisms for recoverable errors
5. Track usage credits and runtime metrics during error scenarios

## Error Hierarchy

The system uses a hierarchy of exception classes:

```
AixplainBaseException
├── AuthenticationError
├── ValidationError
├── ResourceError
├── BillingError
├── SupplierError
├── NetworkError
├── ServiceError
├── InternalError
└── AgentError
    ├── AgentExecutionError
    ├── AgentTimeoutError
    └── AgentIterationLimitError
```

All error classes provide default user-friendly messages while allowing custom messages to be specified when needed.

## Using the Error System

### Raising Errors

When you need to raise an error, use the appropriate exception class from the hierarchy:

```python
from aixplain.exceptions import ValidationError

# Basic usage
raise ValidationError(
    message="Invalid input parameter: max_tokens must be an integer",
)

# With additional details
raise ValidationError(
    message="Invalid input parameter: max_tokens must be an integer",
    details={"parameter": "max_tokens", "provided_value": "ten", "expected_type": "int"}
)

# Using the default user message
raise ValidationError(
    message="Invalid input parameter: max_tokens must be an integer"
)

# For agent execution errors
from aixplain.exceptions import AgentExecutionError

# With custom user message
raise AgentExecutionError(
    message="Failed to execute agent due to model error",
)

# Using the default user message
raise AgentExecutionError(
    message="Failed to execute agent due to model error"
)
```

### Using the Raise Error Utility

For consistent error creation, use the `raise_error` utility:

```python
from aixplain.exceptions.error_handler import raise_error

# Raise an error using an error code from the registry
# The exception class will be automatically determined from the error code prefix
raise_error("validation.token_limit_exceeded", limit=10000, provided=15000)

# Explicitly specify the exception class
from aixplain.exceptions import ValidationError
raise_error("validation.token_limit_exceeded", ValidationError, limit=10000, provided=15000)
```

### Checking for Existing Error Messages

Before creating a new error message, check if one already exists in the registry:

```python
from aixplain.exceptions.registry import ErrorRegistry

# Search for error codes containing 'token'
matching_errors = ErrorRegistry.search_errors("token")
print(matching_errors)  # ['validation.token_limit_exceeded', 'billing.insufficient_tokens', ...]

# Look up a specific error message
error_message = ErrorRegistry.get_error_message("validation.token_limit_exceeded")
print(error_message)  # {'message': 'Token limit exceeded...',}
```

### Using Predefined Error Messages

Use the `create_exception` method from `ErrorRegistry` to create exceptions with predefined messages:

```python
from aixplain.exceptions import ValidationError
from aixplain.exceptions.registry import ErrorRegistry

# Create an exception using a predefined error message
exception = ErrorRegistry.create_exception(
    "validation.token_limit_exceeded", 
    ValidationError, 
    limit=10000, 
    provided=15000
)

# Raise the exception
raise exception
```

### Registering New Error Messages

If you need to add a new error message to the registry:

```python
from aixplain.exceptions.registry import ErrorRegistry

# Register a new error message
ErrorRegistry.register_error(
    "agent.custom_error_code",
    "Detailed technical message for developers",
    "User-friendly message explaining what went wrong"
)
```

## Handling Errors

### Basic Error Handling

```python
from aixplain.exceptions import AixplainBaseException, ValidationError

try:
    # Code that might raise an exception
    agent.run(query="What is the capital of France?", max_tokens="invalid")
except ValidationError as e:
    # Handle validation errors specifically
    print(f"Validation error: {e.message}")
except AixplainBaseException as e:
    # Handle any aiXplain exception
    print(f"Error: {e.message}")
    
    # For debugging
    print(f"Technical details: {e.message}")
    print(f"Category: {e.category.value}")
    print(f"Details: {e.details}")
```

### Using the Response Object

When calling agent methods, you can check the response object for errors:

```python
response = agent.run(query="What is the capital of France?")

if response.status == ResponseStatus.FAILED:
    # Handle error
    print(f"Error: {response.error_message}")
    
    # For debugging
    print(f"Technical details: {response.error}")
else:
    # Process successful response
    print(response.data.output)
```

## Error Categories and When to Use Them

| Category | Use When | Example |
|---|---|---|
| `AUTHENTICATION` | Issues with API keys or permissions | Invalid API key |
| `VALIDATION` | Input validation problems | Required parameter missing |
| `RESOURCE` | Resource availability issues | Model not found |
| `BILLING` | Credit or payment issues | Insufficient credits |
| `SUPPLIER` | Issues with external providers | Provider service unavailable |
| `NETWORK` | Network connectivity problems | Connection timeout |
| `SERVICE` | Internal service availability | Service undergoing maintenance |
| `INTERNAL` | Internal system errors | Database error |
| `AGENT` | Agent-specific problems | Agent iteration limit reached |

## Best Practices

1. **Be specific**: Use the most specific exception class applicable
2. **Separate concerns**: Keep technical details in `message`
3. **Provide context**: Include relevant details in the `details` dict
4. **Check the registry**: Before creating new error messages, check if one already exists
5. **Log appropriately**: Log technical details for debugging but present only user-friendly messages to end users
6. **Handle errors gracefully**: Catch and handle specific exceptions to provide better user experience

## Common Error Patterns

### Non-recoverable Errors

When an error can't be recovered from and should immediately stop processing:

```python
from aixplain.exceptions import ValidationError

if not isinstance(max_tokens, int):
    raise ValidationError(
        message=f"max_tokens must be an integer, got {type(max_tokens).__name__}",
    )
```

### Agent Execution Errors

For agent-specific execution issues:

```python
from aixplain.exceptions import AgentExecutionError

# Error with technical details for logs but default user message
try:
    result = agent.run_async(query="What is the meaning of life?")
except Exception as e:
    raise AgentExecutionError(
        message=f"Agent execution failed with error: {str(e)}"
        # Uses default user message: "There was an issue starting the agent. Please try again later."
    )

# Error with custom user message for specific scenarios
if agent.llm_id is None:
    raise AgentExecutionError(
        message="Agent execution failed: No LLM configured",
    )
```

### Implementing Simple Retry Logic

When you need to implement your own retry logic for potentially recoverable errors:

```python
import time
from aixplain.exceptions import SupplierError, NetworkError

def call_with_retry(func, max_retries=3, initial_delay=1, backoff_factor=2):
    """Call a function with exponential backoff retry logic."""
    retries = 0
    delay = initial_delay
    
    while True:
        try:
            return func()
        except (SupplierError, NetworkError) as e:
            retries += 1
            if retries > max_retries:
                # We've used all our retries, raise the last error
                raise
            
            # Log the error
            print(f"Error occurred: {e}. Retrying in {delay}s ({retries}/{max_retries})")
            
            # Wait before retrying with exponential backoff
            time.sleep(delay)
            delay *= backoff_factor
```

## Debugging Error Handling Issues

When debugging error handling issues:

1. Enable DEBUG level logging to see more details
2. Check the full error chain with `traceback.format_exc()`
3. Examine the `details` field of exceptions for additional context

```python
import logging
import traceback

logging.basicConfig(level=logging.DEBUG)

# Your code that might raise exceptions
try:
    # Your code here
    pass
except Exception as e:
    print(f"Error: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    
    # If it's an aiXplain exception, check for additional details
    if hasattr(e, 'details'):
        print(f"Error details: {e.details}")
```

## Error Handling for API Calls

When making API calls or using SDK functions, you should implement appropriate error handling:

```python
from aixplain.exceptions import AuthenticationError, ValidationError, ServiceError

try:
    response = api_client.call_function(params)
    # Process response
except AuthenticationError as e:
    print(f"Authentication error: {e.message}")
    # Prompt user to re-authenticate or update credentials
except ValidationError as e:
    print(f"Invalid input: {e.message}")
    # Correct the invalid parameters
except ServiceError as e:
    print(f"Service error: {e.message}")
    # Consider retrying after a delay
except Exception as e:
    print(f"Unexpected error: {str(e)}")
    # Handle any other unexpected errors
```

## Understanding Error Types

### Non-Recoverable Errors

These errors require manual intervention and are not suitable for automatic retries:

- Validation errors (invalid input parameters)
- Authentication errors (unauthorized API key)
- Billing-related errors (insufficient credits, payment issues)

### Potentially Recoverable Errors

These errors may be resolved by retrying the operation:

- Network errors (temporary connection issues)
- Service errors (temporary service unavailability)
- Supplier errors (temporary issues with providers)
- Rate limiting errors (too many requests) 