---
sidebar_label: model_factory
title: aixplain.v1.factories.model_factory
---

Model Factory Class.

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
    Model Factory Class

### ModelFactory Objects

```python
class ModelFactory(ModelGetterMixin, ModelListMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/model_factory/__init__.py#L43)

Factory class for creating, managing, and exploring models.

This class provides functionality for creating various types of models,
managing model repositories, and interacting with the aiXplain platform&#x27;s
model-related features.

**Attributes**:

- `backend_url` _str_ - Base URL for the aiXplain backend API.

#### PYTHON\_SANDBOX\_ID

Python sandbox integration ID

#### create\_utility\_model

```python
@classmethod
def create_utility_model(cls,
                         name: Optional[Text] = None,
                         code: Union[Text, Callable] = None,
                         inputs: List[UtilityModelInput] = [],
                         description: Optional[Text] = None,
                         output_examples: Text = "",
                         api_key: Optional[Text] = None,
                         **kwargs) -> UtilityModel
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/model_factory/__init__.py#L58)

Create a new utility model for custom functionality.

.. deprecated::
This method is deprecated. Please use :meth:`create_script_connection_tool` instead.

This method creates a utility model that can execute custom code or functions
with specified inputs and outputs.

**Arguments**:

- `name` _Optional[Text]_ - Name of the utility model.
- `code` _Union[Text, Callable]_ - Python code as string or callable function
  implementing the model&#x27;s functionality.
- `inputs` _List[UtilityModelInput], optional_ - List of input specifications.
  Defaults to empty list.
- `description` _Optional[Text], optional_ - Description of what the model does.
  Defaults to None.
- `output_examples` _Text, optional_ - Examples of expected outputs.
  Defaults to empty string.
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
- `**kwargs` - Additional keyword arguments.
  

**Returns**:

- `UtilityModel` - Created and registered utility model instance.
  

**Raises**:

- `Exception` - If model creation fails or validation fails.

#### create\_script\_connection\_tool

```python
@classmethod
def create_script_connection_tool(cls,
                                  name: Optional[Text] = None,
                                  code: Union[Text, Callable] = None,
                                  description: Optional[Text] = None,
                                  api_key: Optional[Text] = None,
                                  **kwargs) -> ConnectionTool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/model_factory/__init__.py#L136)

Create a new script connection tool for custom functionality.

This method creates a connection tool that can execute custom code or functions
with specified inputs and outputs. It uses the Python sandbox integration
via ToolFactory.create as the underlying implementation.

**Arguments**:

- `name` _Optional[Text]_ - Name of the connection tool.
- `code` _Union[Text, Callable]_ - Python code as string or callable function
  implementing the connection tool&#x27;s functionality.
- `description` _Optional[Text], optional_ - Description of what the connection tool does.
  Defaults to None.
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
- `**kwargs` - Additional keyword arguments.
  

**Returns**:

- `ConnectionTool` - Created and registered connection tool instance.
  

**Raises**:

- `Exception` - If model creation fails or validation fails.

#### list\_host\_machines

```python
@classmethod
def list_host_machines(cls,
                       api_key: Optional[Text] = None,
                       **kwargs) -> List[Dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/model_factory/__init__.py#L215)

Lists available hosting machines for model.

**Arguments**:

- `api_key` _Text, optional_ - Team API key. Defaults to None.
- `**kwargs` - Additional keyword arguments.
  

**Returns**:

- `List[Dict]` - List of dictionaries containing information about
  each hosting machine.

#### list\_gpus

```python
@classmethod
def list_gpus(cls,
              api_key: Optional[Text] = None,
              **kwargs) -> List[List[Text]]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/model_factory/__init__.py#L237)

List GPU names on which you can host your language model.

**Arguments**:

- `api_key` _Text, optional_ - Team API key. Defaults to None.
- `**kwargs` - Additional keyword arguments.
  

**Returns**:

- `List[List[Text]]` - List of all available GPUs and their prices.

#### list\_functions

```python
@classmethod
def list_functions(cls,
                   verbose: Optional[bool] = False,
                   api_key: Optional[Text] = None,
                   **kwargs) -> List[Dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/model_factory/__init__.py#L258)

Lists supported model functions on platform.

**Arguments**:

- `verbose` _Boolean, optional_ - Set to True if a detailed response
  is desired; is otherwise False by default.
- `api_key` _Text, optional_ - Team API key. Defaults to None.
- `**kwargs` - Additional keyword arguments.
  

**Returns**:

- `List[Dict]` - List of dictionaries containing information about
  each supported function.

#### create\_asset\_repo

```python
@classmethod
def create_asset_repo(cls,
                      name: Text,
                      description: Text,
                      function: Text,
                      source_language: Text,
                      input_modality: Text,
                      output_modality: Text,
                      documentation_url: Optional[Text] = "",
                      api_key: Optional[Text] = None,
                      **kwargs) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/model_factory/__init__.py#L292)

Create a new model repository in the platform.

This method creates and registers a new model repository, setting up the
necessary infrastructure for model deployment.

**Arguments**:

- `name` _Text_ - Name of the model.
- `description` _Text_ - Description of the model&#x27;s functionality.
- `function` _Text_ - Function name from list_functions() defining model&#x27;s task.
- `source_language` _Text_ - Language code in ISO 639-1 (2-char) or 639-3 (3-char) format.
- `input_modality` _Text_ - Type of input the model accepts (e.g., text, audio).
- `output_modality` _Text_ - Type of output the model produces (e.g., text, audio).
- `documentation_url` _Optional[Text], optional_ - URL to model documentation.
  Defaults to empty string.
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
- `**kwargs` - Additional keyword arguments.
  

**Returns**:

- `Dict` - Repository creation response containing model ID and other details.
  

**Raises**:

- `description`0 - If function name is invalid.
- `description`1 - If response status code is not 201.

#### asset\_repo\_login

```python
@classmethod
def asset_repo_login(cls, api_key: Optional[Text] = None, **kwargs) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/model_factory/__init__.py#L363)

Return login credentials for the image repository.

Returns credentials for the image repository that corresponds
with the given API_KEY.

**Arguments**:

- `api_key` _Text, optional_ - Team API key. Defaults to None.
- `**kwargs` - Additional keyword arguments.
  

**Returns**:

- `Dict` - Backend response

#### onboard\_model

```python
@classmethod
def onboard_model(cls,
                  model_id: Text,
                  image_tag: Text,
                  image_hash: Text,
                  host_machine: Optional[Text] = "",
                  api_key: Optional[Text] = None,
                  **kwargs) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/model_factory/__init__.py#L388)

Onboard a model after its image has been pushed to ECR.

**Arguments**:

- `model_id` _Text_ - Model ID obtained from CREATE_ASSET_REPO.
- `image_tag` _Text_ - Image tag to be onboarded.
- `image_hash` _Text_ - Image digest.
- `host_machine` _Text, optional_ - Machine on which to host model.
- `api_key` _Text, optional_ - Team API key. Defaults to None.
- `**kwargs` - Additional keyword arguments.
  

**Returns**:

- `Dict` - Backend response

#### create\_rlm

```python
@classmethod
def create_rlm(cls,
               orchestrator_model_id: Text,
               worker_model_id: Text,
               name: Text = "RLM",
               description:
               Text = "Recursive Language Model for long-context analysis.",
               max_iterations: int = 10,
               api_key: Optional[Text] = None) -> RLM
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/model_factory/__init__.py#L425)

Create an RLM (Recursive Language Model) instance for long-context analysis.

RLM overcomes LLM context window limits by giving a powerful orchestrator
model a Python REPL environment pre-loaded with the user&#x27;s context. The
orchestrator writes code to chunk and explore the data, delegating
per-chunk analysis to a lighter worker model via ``llm_query()`` calls.

**Arguments**:

- `orchestrator_model_id` _Text_ - aiXplain model ID of the root LLM that
  plans and writes REPL code. Use a powerful, reasoning-capable model.
- `worker_model_id` _Text_ - aiXplain model ID of the sub-LLM called inside
  the REPL for per-chunk analysis. A fast, cost-efficient model is
  recommended as it may be invoked many times per run.
- `name` _Text, optional_ - Display name for the RLM instance.
  Defaults to ``&quot;RLM&quot;``.
- `description` _Text, optional_ - Description of this RLM instance.
  Defaults to a generic string.
- `max_iterations` _int, optional_ - Maximum orchestrator loop iterations
  before a forced final answer is requested. Defaults to 10.
- `api_key` _Optional[Text], optional_ - API key for model lookups.
  Defaults to ``config.TEAM_API_KEY``.
  

**Returns**:

- ``2 - A configured RLM instance ready to call ``run()``.
  

**Raises**:

- ``5 - If either model ID cannot be fetched from the platform.
  
  Example::
  
  from aixplain.factories import ModelFactory
  
  rlm = ModelFactory.create_rlm(
  orchestrator_model_id=&quot;&lt;powerful-model-id&gt;&quot;,
  worker_model_id=&quot;&lt;fast-cheap-model-id&gt;&quot;,
  max_iterations=10,
  )
  response = rlm.run(data=\{
- ``6 - very_long_document,
- ``7 - &quot;What are the key findings?&quot;,
  })
  print(response.data)
  print(f&quot;Done in \{response[&#x27;iterations_used&#x27;]} iterations.&quot;)

#### deploy\_huggingface\_model

```python
@classmethod
def deploy_huggingface_model(cls,
                             name: Text,
                             hf_repo_id: Text,
                             revision: Optional[Text] = "",
                             hf_token: Optional[Text] = "",
                             api_key: Optional[Text] = None,
                             **kwargs) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/model_factory/__init__.py#L502)

Deploy a model from Hugging Face Hub to the aiXplain platform.

This method handles the deployment of a Hugging Face model, including
authentication and configuration setup.

**Arguments**:

- `name` _Text_ - Display name for the deployed model.
- `hf_repo_id` _Text_ - Hugging Face repository ID in &#x27;author/model-name&#x27; format.
- `revision` _Optional[Text], optional_ - Specific model revision/commit hash.
  Defaults to empty string (latest version).
- `hf_token` _Optional[Text], optional_ - Hugging Face access token for private models.
  Defaults to empty string.
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
- `**kwargs` - Additional keyword arguments.
  

**Returns**:

- `Dict` - Deployment response containing model ID and status information.

#### get\_huggingface\_model\_status

```python
@classmethod
def get_huggingface_model_status(cls,
                                 model_id: Text,
                                 api_key: Optional[Text] = None,
                                 **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/factories/model_factory/__init__.py#L560)

Check the deployment status of a Hugging Face model.

This method retrieves the current status and details of a deployed
Hugging Face model.

**Arguments**:

- `model_id` _Text_ - Model ID returned by deploy_huggingface_model.
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
- `**kwargs` - Additional keyword arguments.
  

**Returns**:

- `Dict` - Status response containing:
  - status: Current deployment status
  - name: Model name
  - id: Model ID
  - pricing: Pricing information

