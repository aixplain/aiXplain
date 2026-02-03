---
sidebar_label: utils
title: aixplain.modules.model.utils
---

#### build\_payload

```python
def build_payload(data: Union[Text, Dict],
                  parameters: Optional[Dict] = None,
                  stream: Optional[bool] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utils.py#L81)

Build a JSON payload for API requests.

This function constructs a JSON payload by combining input data with optional
parameters and streaming configuration. It handles various input formats and
ensures proper JSON serialization.

**Arguments**:

- `data` _Union[Text, Dict]_ - The primary data to include in the payload.
  Can be a string (which may be JSON) or a dictionary.
- `parameters` _Optional[Dict], optional_ - Additional parameters to include
  in the payload. Defaults to None.
- `stream` _Optional[bool], optional_ - Whether to enable streaming for this
  request. If provided, adds streaming configuration to parameters.
  Defaults to None.
  

**Returns**:

- `str` - A JSON string containing the complete payload with all parameters
  and data properly formatted.
  

**Notes**:

  - If data is a string that can be parsed as JSON, it will be.
  - If data is a number (after JSON parsing), it will be converted to string.
  - The function ensures the result is a valid JSON string.

#### call\_run\_endpoint

```python
def call_run_endpoint(url: Text, api_key: Text, payload: Dict) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utils.py#L134)

Call a model execution endpoint and handle the response.

This function makes a POST request to a model execution endpoint, handles
various response scenarios, and provides appropriate error handling.

**Arguments**:

- `url` _Text_ - The endpoint URL to call.
- `api_key` _Text_ - API key for authentication.
- `payload` _Dict_ - The request payload to send.
  

**Returns**:

- `Dict` - A response dictionary containing:
  - status (str): &quot;IN_PROGRESS&quot;, &quot;SUCCESS&quot;, or &quot;FAILED&quot;
  - completed (bool): Whether the request is complete
  - url (str, optional): Polling URL for async requests
  - data (Any, optional): Response data if available
  - error_message (str, optional): Error message if failed
  

**Notes**:

  - For async operations, returns a polling URL in the &#x27;url&#x27; field
  - For failures, includes an error message and sets status to &quot;FAILED&quot;
  - Handles both API errors and request exceptions

#### parse\_code

```python
def parse_code(code: Union[Text, Callable]) -> Tuple[Text, List, Text, Text]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utils.py#L198)

Parse and process code for utility model creation.

This function takes code input in various forms (callable, file path, URL, or
string) and processes it for use in a utility model. It extracts metadata,
validates the code structure, and prepares it for execution.

**Arguments**:

- `code` _Union[Text, Callable]_ - The code to parse. Can be:
  - A callable function
  - A file path (string)
  - A URL (string)
  - Raw code (string)
  

**Returns**:

  Tuple[Text, List, Text, Text]: A tuple containing:
  - code (Text): The processed code, uploaded to storage
  - inputs (List[UtilityModelInput]): List of extracted input parameters
  - description (Text): Function description from docstring
  - name (Text): Function name
  

**Raises**:

- `Exception` - If the code doesn&#x27;t have a main function
- `AssertionError` - If input types are not properly specified
- `Exception` - If an input type is not supported (must be int, float, bool, or str)
  

**Notes**:

  - The function requires a &#x27;main&#x27; function in the code
  - Input parameters must have type annotations
  - Supported input types are: int, float, bool, str
  - The code is uploaded to temporary storage for later use

#### parse\_code\_decorated

```python
def parse_code_decorated(
        code: Union[Text, Callable]) -> Tuple[Text, List, Text, Text]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utils.py#L309)

Parse and process code that may be decorated with @utility_tool.

This function handles code that may be decorated with the @utility_tool
decorator, extracting metadata from either the decorator or the code itself.
It supports various input formats and provides robust parameter extraction.

**Arguments**:

- `code` _Union[Text, Callable]_ - The code to parse. Can be:
  - A decorated callable function
  - A non-decorated callable function
  - A file path (string)
  - A URL (string)
  - Raw code (string)
  

**Returns**:

  Tuple[Text, List, Text, Text]: A tuple containing:
  - code (Text): The processed code, uploaded to storage
  - inputs (List[UtilityModelInput]): List of extracted input parameters
  - description (Text): Function description from decorator or docstring
  - name (Text): Function name from decorator or code
  

**Raises**:

- `TypeError` - If code is a class or class instance
- `AssertionError` - If input types are not properly specified
- `Exception` - In various cases:
  - If code doesn&#x27;t have a function definition
  - If code has invalid @utility_tool decorator
  - If input type is not supported
  - If code parsing fails
  

**Notes**:

  - Handles both decorated and non-decorated code
  - For decorated code, extracts metadata from decorator
  - For non-decorated code, falls back to code parsing
  - Renames the function to &#x27;main&#x27; for backend compatibility
  - Supports TEXT, BOOLEAN, and NUMBER input types
  - Uploads processed code to temporary storage

#### is\_supported\_image\_type

```python
def is_supported_image_type(value: str) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/utils.py#L523)

Check if a file path or URL points to a supported image format.

This function checks if the provided string ends with a supported image
file extension. The check is case-insensitive.

**Arguments**:

- `value` _str_ - The file path or URL to check.
  

**Returns**:

- `bool` - True if the file has a supported image extension, False otherwise.
  

**Notes**:

  Supported image formats are:
  - JPEG (.jpg, .jpeg)
  - PNG (.png)
  - GIF (.gif)
  - BMP (.bmp)
  - WebP (.webp)

