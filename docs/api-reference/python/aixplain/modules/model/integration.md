---
sidebar_label: integration
title: aixplain.modules.model.integration
---

### AuthenticationSchema Objects

```python
class AuthenticationSchema(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/integration.py#L11)

Enumeration of supported authentication schemes for integrations.

This enum defines the various authentication methods that can be used
when connecting to external services through integrations.

**Attributes**:

- `BEARER_TOKEN` _str_ - Bearer token authentication scheme.
- `OAUTH1` _str_ - OAuth 1.0 authentication scheme.
- `OAUTH2` _str_ - OAuth 2.0 authentication scheme.
- `API_KEY` _str_ - API key authentication scheme.
- `BASIC` _str_ - Basic authentication scheme (username/password).
- `NO_AUTH` _str_ - No authentication required.

### BaseAuthenticationParams Objects

```python
class BaseAuthenticationParams(BaseModel)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/integration.py#L34)

Base model for authentication parameters used in integrations.

This class defines the common parameters that are used across different
authentication schemes when connecting to external services.

**Attributes**:

- `name` _Optional[Text]_ - Optional name for the connection. Defaults to None.
- `connector_id` _Optional[Text]_ - Optional ID of the connector. Defaults to None.

#### build\_connector\_params

```python
def build_connector_params(**kwargs) -> BaseAuthenticationParams
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/integration.py#L49)

Build authentication parameters for a connector from keyword arguments.

This function creates a BaseAuthenticationParams instance from the provided
keyword arguments, extracting the name and connector_id if present.

**Arguments**:

- `**kwargs` - Arbitrary keyword arguments. Supported keys:
  - name (Optional[Text]): Name for the connection
  - connector_id (Optional[Text]): ID of the connector
  

**Returns**:

- `BaseAuthenticationParams` - An instance containing the extracted parameters.
  

**Example**:

  &gt;&gt;&gt; params = build_connector_params(name=&quot;My Connection&quot;, connector_id=&quot;123&quot;)
  &gt;&gt;&gt; print(params.name)
  &#x27;My Connection&#x27;

### Integration Objects

```python
class Integration(Model)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/integration.py#L73)

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text,
             description: Text = "",
             api_key: Optional[Text] = None,
             supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
             version: Optional[Text] = None,
             function: Optional[Function] = None,
             is_subscribed: bool = False,
             cost: Optional[Dict] = None,
             function_type: Optional[FunctionType] = FunctionType.INTEGRATION,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/integration.py#L74)

Initialize a new Integration instance.

**Arguments**:

- `id` _Text_ - ID of the Integration.
- `name` _Text_ - Name of the Integration.
- `description` _Text, optional_ - Description of the Integration. Defaults to &quot;&quot;.
- `api_key` _Text, optional_ - API key for the Integration. Defaults to None.
- `supplier` _Union[Dict, Text, Supplier, int], optional_ - Supplier of the Integration. Defaults to &quot;aiXplain&quot;.
- `version` _Text, optional_ - Version of the Integration. Defaults to &quot;1.0&quot;.
- `function` _Function, optional_ - Function of the Integration. Defaults to None.
- `is_subscribed` _bool, optional_ - Whether the user is subscribed. Defaults to False.
- `cost` _Dict, optional_ - Cost of the Integration. Defaults to None.
- `function_type` _FunctionType, optional_ - Type of the function. Must be FunctionType.INTEGRATION.
  Defaults to FunctionType.INTEGRATION.
- `name`0 - Any additional Integration info to be saved.
  

**Raises**:

- `name`1 - If function_type is not FunctionType.INTEGRATION.

#### connect

```python
def connect(authentication_schema: AuthenticationSchema,
            args: Optional[BaseAuthenticationParams] = None,
            data: Optional[Dict] = None,
            **kwargs) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/integration.py#L127)

Connect to the integration using the specified authentication scheme.

This method establishes a connection to the integration service using the provided
authentication method and credentials. The required parameters vary depending on
the authentication scheme being used.

**Arguments**:

- `authentication_schema` _AuthenticationSchema_ - The authentication scheme to use
  (e.g., BEARER_TOKEN, OAUTH1, OAUTH2, API_KEY, BASIC, NO_AUTH).
- `args` _Optional[BaseAuthenticationParams], optional_ - Common connection parameters.
  If not provided, will be built from kwargs. Defaults to None.
- `data` _Optional[Dict], optional_ - Authentication-specific parameters required by
  the chosen authentication scheme. Defaults to None.
- `**kwargs` - Additional keyword arguments used to build BaseAuthenticationParams
  if args is not provided. Supported keys:
  - name (str): Name for the connection
  - connector_id (str): ID of the connector
  

**Returns**:

- `ModelResponse` - A response object containing:
  - data (Dict): Contains connection details including:
  - id (str): Connection ID (can be used with ModelFactory.get(id))
  - redirectURL (str, optional): URL to complete OAuth authentication
  (only for OAuth1/OAuth2)
  

**Raises**:

- `ValueError` - If the authentication schema is not supported by this integration
  or if required parameters are missing from the data dictionary.
  

**Examples**:

  Using Bearer Token authentication:
  &gt;&gt;&gt; integration.connect(
  ...     AuthenticationSchema.BEARER_TOKEN,
  ...     data=\{&quot;token&quot;: &quot;1234567890&quot;},
  ...     name=&quot;My Connection&quot;
  ... )
  
  Using OAuth2 authentication:
  &gt;&gt;&gt; response = integration.connect(
  ...     AuthenticationSchema.OAUTH2,
  ...     name=&quot;My Connection&quot;
  ... )
  &gt;&gt;&gt; # For OAuth2, you&#x27;ll need to visit the redirectURL to complete auth
  &gt;&gt;&gt; print(response.data.get(&quot;redirectURL&quot;))
  
  Using API Key authentication:
  &gt;&gt;&gt; integration.connect(
  ...     AuthenticationSchema.API_KEY,
  ...     data=\{&quot;api_key&quot;: &quot;your-api-key&quot;},
  ...     name=&quot;My Connection&quot;
  ... )

#### \_\_repr\_\_

```python
def __repr__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/integration.py#L242)

Return a string representation of the Integration instance.

**Returns**:

- `str` - A string in the format &quot;Integration: &lt;name&gt; by &lt;supplier&gt; (id=&lt;id&gt;)&quot;.
  If supplier is a dictionary, uses supplier[&#x27;name&#x27;], otherwise uses supplier directly.

