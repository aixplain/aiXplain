---
sidebar_label: types
title: aixplain.exceptions.types
---

Exception types and error handling for the aiXplain SDK.

### ErrorSeverity Objects

```python
class ErrorSeverity(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L7)

Enumeration of error severity levels in the aiXplain system.

This enum defines the different levels of severity that can be assigned to
errors, ranging from informational messages to critical system errors.

**Attributes**:

- `INFO` _str_ - Informational message, not an actual error.
- `WARNING` _str_ - Warning that doesn&#x27;t prevent operation completion.
- `ERROR` _str_ - Error condition that prevents operation completion.
- `CRITICAL` _str_ - Severe error that might affect system stability.

#### INFO

Informational, not an error

#### WARNING

Warning, operation can continue

#### ERROR

Error, operation cannot continue

#### CRITICAL

System stability might be compromised

### ErrorCategory Objects

```python
class ErrorCategory(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L26)

Enumeration of error categories in the aiXplain system.

This enum defines the different domains or areas where errors can occur,
helping to classify and organize error handling.

**Attributes**:

- `AUTHENTICATION` _str_ - Authentication and authorization errors.
- `VALIDATION` _str_ - Input validation errors.
- `RESOURCE` _str_ - Resource availability and access errors.
- `BILLING` _str_ - Billing and payment-related errors.
- `SUPPLIER` _str_ - External supplier and third-party service errors.
- `NETWORK` _str_ - Network connectivity errors.
- `SERVICE` _str_ - Service availability errors.
- `INTERNAL` _str_ - Internal system errors.
- `AGENT` _str_ - Agent-specific errors.
- `UNKNOWN` _str_ - Uncategorized or unclassified errors.

#### AUTHENTICATION

API keys, permissions

#### VALIDATION

Input validation

#### RESOURCE

Resource availability

#### BILLING

Credits, payment

#### SUPPLIER

External supplier issues

#### NETWORK

Network connectivity

#### SERVICE

Service availability

#### INTERNAL

Internal system errors

#### AGENT

Agent-specific errors

#### UNKNOWN

Uncategorized errors

### ErrorCode Objects

```python
class ErrorCode(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L57)

Standard error codes for aiXplain exceptions.

The format is AX-&lt;CATEGORY&gt;-&lt;ID&gt;, where &lt;CATEGORY&gt; is a short identifier
derived from the ErrorCategory (e.g., AUTH, VAL, RES) and &lt;ID&gt; is a
unique sequential number within that category, starting from 1000.

How to Add a New Error Code:
1.  Identify the appropriate `ErrorCategory` for the new error.
2.  Determine the next available sequential ID within that category.
    For example, if `AX-AUTH-1000` exists, the next authentication-specific
    error could be `AX-AUTH-1001`.
3.  Define the new enum member using the format `AX-<CATEGORY_ABBR>-<ID>`.
    Use a concise abbreviation for the category (e.g., AUTH, VAL, RES, BIL,
    SUP, NET, SVC, INT).
4.  Assign the string value (e.g., `"AX-AUTH-1001"`).
5.  Add a clear docstring explaining the specific condition that triggers
    this error code.
6.  (Optional but recommended) Consider creating a more specific exception
    class inheriting from the corresponding category exception (e.g.,
    `class InvalidApiKeyError(AuthenticationError): ...`) and assign the
    new error code to it.

#### AX\_AUTH\_ERROR

General authentication error. Use for issues like invalid API keys, insufficient permissions, or failed login attempts.

#### AX\_VAL\_ERROR

General validation error. Use when user-provided input fails validation checks (e.g., incorrect data type, missing required fields, invalid format.

#### AX\_RES\_ERROR

General resource error. Use for issues related to accessing or managing resources, such as a requested model being unavailable or quota limits exceeded.

#### AX\_BIL\_ERROR

General billing error. Use for problems related to billing, payments, or credits (e.g., insufficient funds, expired subscription.

#### AX\_SUP\_ERROR

General supplier error. Use when an error originates from an external supplier or third-party service integrated with aiXplain.

#### AX\_NET\_ERROR

General network error. Use for issues related to network connectivity, such as timeouts, DNS resolution failures, or unreachable services.

#### AX\_SVC\_ERROR

General service error. Use when a specific aiXplain service or endpoint is unavailable or malfunctioning (e.g., service downtime, internal component failure.

#### AX\_INT\_ERROR

General internal error. Use for unexpected server-side errors that are not covered by other categories. This often indicates a bug or an issue within the aiXplain platform itself.

#### \_\_str\_\_

```python
def __str__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L90)

Return the string representation of the error code.

**Returns**:

- `str` - The error code value as a string.

### AixplainBaseException Objects

```python
class AixplainBaseException(Exception)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L99)

Base exception class for all aiXplain exceptions.

This class serves as the foundation for all custom exceptions in the aiXplain
system. It provides structured error information including categorization,
severity, and additional context.

**Attributes**:

- `message` _str_ - Error message.
- `category` _ErrorCategory_ - Category of the error.
- `severity` _ErrorSeverity_ - Severity level of the error.
- `status_code` _Optional[int]_ - HTTP status code if applicable.
- `details` _Dict[str, Any]_ - Additional error context and details.
- `retry_recommended` _bool_ - Whether retrying the operation might succeed.
- `error_code` _Optional[ErrorCode]_ - Standardized error code.

#### \_\_init\_\_

```python
def __init__(message: str,
             category: ErrorCategory = ErrorCategory.UNKNOWN,
             severity: ErrorSeverity = ErrorSeverity.ERROR,
             status_code: Optional[int] = None,
             details: Optional[Dict[str, Any]] = None,
             retry_recommended: bool = False,
             error_code: Optional[ErrorCode] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L116)

Initialize the base exception with structured error information.

**Arguments**:

- `message` - Error message describing the issue.
- `category` - Category of the error (default: UNKNOWN).
- `severity` - Severity level of the error (default: ERROR).
- `status_code` - HTTP status code if applicable.
- `details` - Additional error context and details.
- `retry_recommended` - Whether retrying the operation might succeed.
- `error_code` - Standardized error code for the exception.

#### \_\_str\_\_

```python
def __str__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L146)

Return a string representation of the exception.

**Returns**:

- `str` - Formatted string containing the exception class name,
  error code (if present), and error message.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L156)

Convert the exception to a dictionary for serialization.

**Returns**:

  Dict[str, Any]: Dictionary containing all exception attributes
  including message, category, severity, status code, details,
  retry recommendation, and error code.

### AuthenticationError Objects

```python
class AuthenticationError(AixplainBaseException)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L175)

Raised when authentication fails.

#### \_\_init\_\_

```python
def __init__(message: str, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L178)

Initialize authentication error.

**Arguments**:

- `message` - Error message describing the authentication issue.
- `**kwargs` - Additional keyword arguments passed to parent class.

### ValidationError Objects

```python
class ValidationError(AixplainBaseException)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L195)

Raised when input validation fails.

#### \_\_init\_\_

```python
def __init__(message: str, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L198)

Initialize validation error.

**Arguments**:

- `message` - Error message describing the validation issue.
- `**kwargs` - Additional keyword arguments passed to parent class.

### AlreadyDeployedError Objects

```python
class AlreadyDeployedError(AixplainBaseException)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L215)

Raised when attempting to deploy an asset that is already deployed.

#### \_\_init\_\_

```python
def __init__(message: str, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L218)

Initialize already deployed error.

**Arguments**:

- `message` - Error message describing the deployment state conflict.
- `**kwargs` - Additional keyword arguments passed to parent class.

### ResourceError Objects

```python
class ResourceError(AixplainBaseException)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L233)

Raised when a resource is unavailable.

#### \_\_init\_\_

```python
def __init__(message: str, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L236)

Initialize resource error.

**Arguments**:

- `message` - Error message describing the resource issue.
- `**kwargs` - Additional keyword arguments passed to parent class.

### BillingError Objects

```python
class BillingError(AixplainBaseException)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L253)

Raised when there are billing issues.

#### \_\_init\_\_

```python
def __init__(message: str, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L256)

Initialize billing error.

**Arguments**:

- `message` - Error message describing the billing issue.
- `**kwargs` - Additional keyword arguments passed to parent class.

### SupplierError Objects

```python
class SupplierError(AixplainBaseException)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L273)

Raised when there are issues with external suppliers.

#### \_\_init\_\_

```python
def __init__(message: str, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L276)

Initialize supplier error.

**Arguments**:

- `message` - Error message describing the supplier issue.
- `**kwargs` - Additional keyword arguments passed to parent class.

### NetworkError Objects

```python
class NetworkError(AixplainBaseException)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L293)

Raised when there are network connectivity issues.

#### \_\_init\_\_

```python
def __init__(message: str, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L296)

Initialize network error.

**Arguments**:

- `message` - Error message describing the network issue.
- `**kwargs` - Additional keyword arguments passed to parent class.

### ServiceError Objects

```python
class ServiceError(AixplainBaseException)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L313)

Raised when a service is unavailable.

#### \_\_init\_\_

```python
def __init__(message: str, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L316)

Initialize service error.

**Arguments**:

- `message` - Error message describing the service issue.
- `**kwargs` - Additional keyword arguments passed to parent class.

### InternalError Objects

```python
class InternalError(AixplainBaseException)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L333)

Raised when there is an internal system error.

#### \_\_init\_\_

```python
def __init__(message: str, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L336)

Initialize internal error.

**Arguments**:

- `message` - Error message describing the internal issue.
- `**kwargs` - Additional keyword arguments passed to parent class.

### AlreadyDeployedError Objects

```python
class AlreadyDeployedError(AixplainBaseException)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/types.py#L359)

Raised when an asset is already deployed.

