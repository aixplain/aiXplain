---
sidebar_label: model
title: aixplain.modules.model
---

#### \_\_author\_\_

Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Duraikrishna Selvaraju, Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: September 1st 2022
Description:
    Model Class

### Model Objects

```python
class Model(Asset)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L41)

A ready-to-use AI model that can be executed synchronously or asynchronously.

This class represents a deployable AI model in the aiXplain platform. It provides
functionality for model execution, parameter management, and status tracking.
Models can be run with both synchronous and asynchronous APIs, and some models
support streaming responses.

**Attributes**:

- `id` _Text_ - ID of the model.
- `name` _Text_ - Name of the model.
- `description` _Text_ - Detailed description of the model&#x27;s functionality.
- `api_key` _Text_ - Authentication key for API access.
- `url` _Text_ - Endpoint URL for model execution.
- `supplier` _Union[Dict, Text, Supplier, int]_ - Provider/creator of the model.
- `version` _Text_ - Version identifier of the model.
- `function` _Function_ - The AI function this model performs.
- `backend_url` _str_ - Base URL for the backend API.
- `cost` _Dict_ - Pricing information for model usage.
- `name`0 _ModelParameters_ - Parameters accepted by the model.
- `name`1 _Dict_ - Description of model outputs.
- `name`2 _ModelParameters_ - Configuration parameters for model behavior.
- `name`3 _bool_ - Whether the model supports streaming responses.
- `name`4 _FunctionType_ - Category of function (AI, UTILITY, etc.).
- `name`5 _bool_ - Whether the user has an active subscription.
- `name`6 _datetime_ - When the model was created.
- `name`7 _AssetStatus_ - Current status of the model.
- `name`8 _dict_ - Additional model metadata.

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text = "",
             description: Text = "",
             api_key: Text = config.TEAM_API_KEY,
             supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
             version: Optional[Text] = None,
             function: Optional[Function] = None,
             is_subscribed: bool = False,
             cost: Optional[Dict] = None,
             created_at: Optional[datetime] = None,
             input_params: Optional[Dict] = None,
             output_params: Optional[Dict] = None,
             model_params: Optional[Dict] = None,
             supports_streaming: bool = False,
             status: Optional[AssetStatus] = AssetStatus.ONBOARDED,
             function_type: Optional[FunctionType] = FunctionType.AI,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L71)

Initialize a new Model instance.

**Arguments**:

- `id` _Text_ - ID of the Model.
- `name` _Text, optional_ - Name of the Model. Defaults to &quot;&quot;.
- `description` _Text, optional_ - Description of the Model. Defaults to &quot;&quot;.
- `api_key` _Text, optional_ - Authentication key for API access.
  Defaults to config.TEAM_API_KEY.
- `supplier` _Union[Dict, Text, Supplier, int], optional_ - Provider/creator
  of the model. Defaults to &quot;aiXplain&quot;.
- `version` _Text, optional_ - Version identifier of the model. Defaults to None.
- `function` _Function, optional_ - The AI function this model performs.
  Defaults to None.
- `is_subscribed` _bool, optional_ - Whether the user has an active
  subscription. Defaults to False.
- `cost` _Dict, optional_ - Pricing information for model usage.
  Defaults to None.
- `created_at` _Optional[datetime], optional_ - When the model was created.
  Defaults to None.
- `name`0 _Dict, optional_ - Parameters accepted by the model.
  Defaults to None.
- `name`1 _Dict, optional_ - Description of model outputs.
  Defaults to None.
- `name`2 _Dict, optional_ - Configuration parameters for model
  behavior. Defaults to None.
- `name`3 _bool, optional_ - Whether the model supports streaming
  responses. Defaults to False.
- `name`4 _AssetStatus, optional_ - Current status of the model.
  Defaults to AssetStatus.ONBOARDED.
- `name`5 _FunctionType, optional_ - Category of function.
  Defaults to FunctionType.AI.
- `name`6 - Additional model metadata.

#### to\_dict

```python
def to_dict() -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L144)

Convert the model instance to a dictionary representation.

**Returns**:

- `Dict` - A dictionary containing the model&#x27;s configuration with keys:
  - id: Unique identifier
  - name: Model name
  - description: Model description
  - supplier: Model provider
  - additional_info: Extra metadata (excluding None/empty values)
  - input_params: Input parameter configuration
  - output_params: Output parameter configuration
  - model_params: Model behavior parameters
  - function: AI function type
  - status: Current model status

#### get\_parameters

```python
def get_parameters() -> Optional[ModelParameters]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L174)

Get the model&#x27;s configuration parameters.

**Returns**:

- `Optional[ModelParameters]` - The model&#x27;s parameter configuration if set,
  None otherwise.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L185)

Return a string representation of the model.

**Returns**:

- `str` - A string in the format &quot;Model: &lt;name&gt; by &lt;supplier&gt; (id=&lt;id&gt;)&quot;.

#### sync\_poll

```python
def sync_poll(poll_url: Text,
              name: Text = "model_process",
              wait_time: float = 0.5,
              timeout: float = 300) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L196)

Poll the platform until an asynchronous operation completes or times out.

This method repeatedly checks the status of an asynchronous operation,
implementing exponential backoff for the polling interval.

**Arguments**:

- `poll_url` _Text_ - URL to poll for operation status.
- `name` _Text, optional_ - Identifier for the operation for logging.
  Defaults to &quot;model_process&quot;.
- `wait_time` _float, optional_ - Initial wait time in seconds between polls.
  Will increase exponentially up to 60 seconds. Defaults to 0.5.
- `timeout` _float, optional_ - Maximum total time to poll in seconds.
  Defaults to 300.
  

**Returns**:

- `ModelResponse` - The final response from the operation. If polling times
  out or fails, returns a failed response with appropriate error message.
  

**Notes**:

  The minimum wait time between polls is 0.2 seconds. The wait time
  increases by 10% after each poll up to a maximum of 60 seconds.

#### poll

```python
def poll(poll_url: Text, name: Text = "model_process") -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L262)

Make a single poll request to check operation status.

**Arguments**:

- `poll_url` _Text_ - URL to poll for operation status.
- `name` _Text, optional_ - Identifier for the operation for logging.
  Defaults to &quot;model_process&quot;.
  

**Returns**:

- `ModelResponse` - The current status of the operation. Contains completion
  status, any results or errors, and usage statistics.
  

**Notes**:

  This is a low-level method used by sync_poll. Most users should use
  sync_poll instead for complete operation handling.

#### run\_stream

```python
def run_stream(data: Union[Text, Dict],
               parameters: Optional[Dict] = None) -> ModelResponseStreamer
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L312)

Execute the model with streaming response.

**Arguments**:

- `data` _Union[Text, Dict]_ - The input data for the model.
- `parameters` _Optional[Dict], optional_ - Additional parameters for model
  execution. Defaults to None.
  

**Returns**:

- `ModelResponseStreamer` - A streamer object that yields response chunks.
  

**Raises**:

- `AssertionError` - If the model doesn&#x27;t support streaming.

#### run

```python
def run(data: Union[Text, Dict],
        name: Text = "model_process",
        timeout: float = 300,
        parameters: Optional[Dict] = None,
        wait_time: float = 0.5,
        stream: bool = False) -> Union[ModelResponse, ModelResponseStreamer]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L338)

Execute the model and wait for results.

This method handles both synchronous and streaming execution modes. For
asynchronous operations, it polls until completion or timeout.

**Arguments**:

- `data` _Union[Text, Dict]_ - The input data for the model.
- `name` _Text, optional_ - Identifier for the operation for logging.
  Defaults to &quot;model_process&quot;.
- `timeout` _float, optional_ - Maximum time to wait for completion in seconds.
  Defaults to 300.
- `parameters` _Dict, optional_ - Additional parameters for model execution.
  Defaults to None.
- `wait_time` _float, optional_ - Initial wait time between polls in seconds.
  Defaults to 0.5.
- `stream` _bool, optional_ - Whether to use streaming mode. Requires model
  support. Defaults to False.
  

**Returns**:

  Union[ModelResponse, ModelResponseStreamer]: The model&#x27;s response. For
  streaming mode, returns a streamer object. For regular mode,
  returns a response object with results or error information.
  

**Notes**:

  If the model execution becomes asynchronous, this method will poll
  for completion using sync_poll with the specified timeout and wait_time.

#### run\_async

```python
def run_async(data: Union[Text, Dict],
              name: Text = "model_process",
              parameters: Optional[Dict] = None) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L408)

Start asynchronous model execution.

This method initiates model execution but doesn&#x27;t wait for completion.
Use sync_poll to check the operation status later.

**Arguments**:

- `data` _Union[Text, Dict]_ - The input data for the model.
- `name` _Text, optional_ - Identifier for the operation for logging.
  Defaults to &quot;model_process&quot;.
- `parameters` _Dict, optional_ - Additional parameters for model execution.
  Defaults to None.
  

**Returns**:

- `ModelResponse` - Initial response containing:
  - status: Current operation status
  - url: URL for polling operation status
  - error_message: Any immediate errors
  - other response metadata

#### check\_finetune\_status

```python
def check_finetune_status(after_epoch: Optional[int] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L447)

Check the status of the FineTune model.

**Arguments**:

- `after_epoch` _Optional[int], optional_ - status after a given epoch. Defaults to None.
  

**Raises**:

- `Exception` - If the &#x27;TEAM_API_KEY&#x27; is not provided.
  

**Returns**:

- `FinetuneStatus` - The status of the FineTune model.

#### delete

```python
def delete() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L514)

Delete this model from the aiXplain platform.

This method attempts to delete the model from the platform. It will fail
if the user doesn&#x27;t have appropriate permissions.

**Raises**:

- `Exception` - If deletion fails or if the user doesn&#x27;t have permission.

#### add\_additional\_info\_for\_benchmark

```python
def add_additional_info_for_benchmark(display_name: str,
                                      configuration: Dict) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L538)

Add benchmark-specific information to the model.

This method updates the model&#x27;s additional_info with benchmark-related
metadata.

**Arguments**:

- `display_name` _str_ - Name for display in benchmarks.
- `configuration` _Dict_ - Model configuration settings for benchmarking.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict) -> "Model"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/__init__.py#L552)

Create a Model instance from a dictionary representation.

**Arguments**:

- `data` _Dict_ - Dictionary containing model configuration with keys:
  - id: Model identifier
  - name: Model name
  - description: Model description
  - api_key: API key for authentication
  - supplier: Model provider information
  - version: Model version
  - function: AI function type
  - is_subscribed: Subscription status
  - cost: Pricing information
  - created_at: Creation timestamp (ISO format)
  - input_params: Input parameter configuration
  - output_params: Output parameter configuration
  - model_params: Model behavior parameters
  - additional_info: Extra metadata
  

**Returns**:

- `Model` - A new Model instance populated with the dictionary data.

