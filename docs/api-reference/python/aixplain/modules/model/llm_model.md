---
sidebar_label: llm_model
title: aixplain.modules.model.llm_model
---

#### \_\_author\_\_

Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: June 4th 2024
Description:
    Large Language Model Class

### LLM Objects

```python
class LLM(Model)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/llm_model.py#L36)

Ready-to-use LLM model. This model can be run in both synchronous and asynchronous manner.

**Attributes**:

- `id` _Text_ - ID of the Model
- `name` _Text_ - Name of the Model
- `description` _Text, optional_ - description of the model. Defaults to &quot;&quot;.
- `api_key` _Text, optional_ - API key of the Model. Defaults to None.
- `url` _Text, optional_ - endpoint of the model. Defaults to config.MODELS_RUN_URL.
- `supplier` _Union[Dict, Text, Supplier, int], optional_ - supplier of the asset. Defaults to &quot;aiXplain&quot;.
- `version` _Text, optional_ - version of the model. Defaults to &quot;1.0&quot;.
- `function` _Text, optional_ - model AI function. Defaults to None.
- `url` _str_ - URL to run the model.
- `backend_url` _str_ - URL of the backend.
- `name`0 _Dict, optional_ - model price. Defaults to None.
- `name`1 _FunctionType, optional_ - type of the function. Defaults to FunctionType.AI.
- `name`2 - Any additional Model info to be saved

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
             temperature: float = 0.001,
             function_type: Optional[FunctionType] = FunctionType.AI,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/llm_model.py#L55)

Initialize a new LLM instance.

**Arguments**:

- `id` _Text_ - ID of the LLM model.
- `name` _Text_ - Name of the LLM model.
- `description` _Text, optional_ - Description of the model. Defaults to &quot;&quot;.
- `api_key` _Text, optional_ - API key for the model. Defaults to None.
- `supplier` _Union[Dict, Text, Supplier, int], optional_ - Supplier of the model. Defaults to &quot;aiXplain&quot;.
- `version` _Text, optional_ - Version of the model. Defaults to &quot;1.0&quot;.
- `function` _Function, optional_ - Model&#x27;s AI function. Must be Function.TEXT_GENERATION.
- `is_subscribed` _bool, optional_ - Whether the user is subscribed. Defaults to False.
- `cost` _Dict, optional_ - Cost of the model. Defaults to None.
- `temperature` _float, optional_ - Default temperature for text generation. Defaults to 0.001.
- `name`0 _FunctionType, optional_ - Type of the function. Defaults to FunctionType.AI.
- `name`1 - Any additional model info to be saved.
  

**Raises**:

- `name`2 - If function is not Function.TEXT_GENERATION.

#### run

```python
def run(data: Text,
        context: Optional[Text] = None,
        prompt: Optional[Text] = None,
        history: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 128,
        top_p: float = 1.0,
        name: Text = "model_process",
        timeout: float = 300,
        parameters: Optional[Dict] = None,
        wait_time: float = 0.5,
        stream: bool = False) -> Union[ModelResponse, ModelResponseStreamer]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/llm_model.py#L107)

Run the LLM model synchronously to generate text.

This method runs the LLM model to generate text based on the provided input.
It supports both single-turn and conversational interactions, with options
for streaming responses.

**Arguments**:

- `data` _Text_ - The input text or last user utterance for text generation.
- `context` _Optional[Text], optional_ - System message or context for the model.
  Defaults to None.
- `prompt` _Optional[Text], optional_ - Prompt template or prefix to prepend to
  the input. Defaults to None.
- `history` _Optional[List[Dict]], optional_ - Conversation history in OpenAI format
  (e.g., [\{&quot;role&quot;: &quot;assistant&quot;, &quot;content&quot;: &quot;Hello!&quot;}, ...]). Defaults to None.
- `temperature` _Optional[float], optional_ - Sampling temperature for text generation.
  Higher values make output more random. If None, uses the model&#x27;s default.
  Defaults to None.
- `max_tokens` _int, optional_ - Maximum number of tokens to generate.
  Defaults to 128.
- `top_p` _float, optional_ - Nucleus sampling parameter. Only tokens with cumulative
  probability &lt; top_p are considered. Defaults to 1.0.
- `name` _Text, optional_ - Identifier for this model run. Useful for logging.
  Defaults to &quot;model_process&quot;.
- `timeout` _float, optional_ - Maximum time in seconds to wait for completion.
  Defaults to 300.
- `parameters` _Optional[Dict], optional_ - Additional model-specific parameters.
  Defaults to None.
- `context`0 _float, optional_ - Time in seconds between polling attempts.
  Defaults to 0.5.
- `context`1 _bool, optional_ - Whether to stream the model&#x27;s output tokens.
  Defaults to False.
  

**Returns**:

  Union[ModelResponse, ModelResponseStreamer]: If stream=False, returns a ModelResponse
  containing the complete generated text and metadata. If stream=True, returns
  a ModelResponseStreamer that yields tokens as they&#x27;re generated.

#### run\_async

```python
def run_async(data: Text,
              context: Optional[Text] = None,
              prompt: Optional[Text] = None,
              history: Optional[List[Dict]] = None,
              temperature: Optional[float] = None,
              max_tokens: int = 128,
              top_p: float = 1.0,
              name: Text = "model_process",
              parameters: Optional[Dict] = None) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/llm_model.py#L205)

Run the LLM model asynchronously to generate text.

This method starts an asynchronous text generation task and returns immediately
with a response containing a polling URL. The actual result can be retrieved
later using the polling URL.

**Arguments**:

- `data` _Text_ - The input text or last user utterance for text generation.
- `context` _Optional[Text], optional_ - System message or context for the model.
  Defaults to None.
- `prompt` _Optional[Text], optional_ - Prompt template or prefix to prepend to
  the input. Defaults to None.
- `history` _Optional[List[Dict]], optional_ - Conversation history in OpenAI format
  (e.g., [\{&quot;role&quot;: &quot;assistant&quot;, &quot;content&quot;: &quot;Hello!&quot;}, ...]). Defaults to None.
- `temperature` _Optional[float], optional_ - Sampling temperature for text generation.
  Higher values make output more random. If None, uses the model&#x27;s default.
  Defaults to None.
- `max_tokens` _int, optional_ - Maximum number of tokens to generate.
  Defaults to 128.
- `top_p` _float, optional_ - Nucleus sampling parameter. Only tokens with cumulative
  probability &lt; top_p are considered. Defaults to 1.0.
- `name` _Text, optional_ - Identifier for this model run. Useful for logging.
  Defaults to &quot;model_process&quot;.
- `parameters` _Optional[Dict], optional_ - Additional model-specific parameters.
  Defaults to None.
  

**Returns**:

- `ModelResponse` - A response object containing:
  - status (ResponseStatus): Status of the request (e.g., IN_PROGRESS)
  - url (str): URL to poll for the final result
  - data (str): Empty string (result not available yet)
  - details (Dict): Additional response details
  - completed (bool): False (task not completed yet)
  - error_message (str): Error message if request failed
  Other fields may be present depending on the response.

