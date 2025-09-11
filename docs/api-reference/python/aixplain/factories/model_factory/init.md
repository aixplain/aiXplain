---
sidebar_label: model_factory
title: aixplain.factories.model_factory
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
    Model Factory Class

### ModelFactory Objects

```python
class ModelFactory(ModelGetterMixin, ModelListMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/__init__.py#L33)

Factory class for creating, managing, and exploring models.

This class provides functionality for creating various types of models,
managing model repositories, and interacting with the aiXplain platform&#x27;s
model-related features.

**Attributes**:

- `backend_url` _str_ - Base URL for the aiXplain backend API.

#### create\_utility\_model

```python
@classmethod
def create_utility_model(cls,
                         name: Optional[Text] = None,
                         code: Union[Text, Callable] = None,
                         inputs: List[UtilityModelInput] = [],
                         description: Optional[Text] = None,
                         output_examples: Text = "",
                         api_key: Optional[Text] = None) -> UtilityModel
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/__init__.py#L47)

Create a new utility model for custom functionality.

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
  

**Returns**:

- `UtilityModel` - Created and registered utility model instance.
  

**Raises**:

- `Exception` - If model creation fails or validation fails.

#### list\_host\_machines

```python
@classmethod
def list_host_machines(cls, api_key: Optional[Text] = None) -> List[Dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/__init__.py#L117)

Lists available hosting machines for model.

**Arguments**:

- `api_key` _Text, optional_ - Team API key. Defaults to None.
  

**Returns**:

- `List[Dict]` - List of dictionaries containing information about
  each hosting machine.

#### list\_gpus

```python
@classmethod
def list_gpus(cls, api_key: Optional[Text] = None) -> List[List[Text]]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/__init__.py#L143)

List GPU names on which you can host your language model.

**Arguments**:

- `api_key` _Text, optional_ - Team API key. Defaults to None.
  

**Returns**:

- `List[List[Text]]` - List of all available GPUs and their prices.

#### list\_functions

```python
@classmethod
def list_functions(cls,
                   verbose: Optional[bool] = False,
                   api_key: Optional[Text] = None) -> List[Dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/__init__.py#L168)

Lists supported model functions on platform.

**Arguments**:

- `verbose` _Boolean, optional_ - Set to True if a detailed response
  is desired; is otherwise False by default.
- `api_key` _Text, optional_ - Team API key. Defaults to None.
  

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
                      api_key: Optional[Text] = None) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/__init__.py#L208)

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
  

**Returns**:

- `Dict` - Repository creation response containing model ID and other details.
  

**Raises**:

- `Exception` - If function name is invalid.
- `description`0 - If response status code is not 201.

#### asset\_repo\_login

```python
@classmethod
def asset_repo_login(cls, api_key: Optional[Text] = None) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/__init__.py#L284)

Return login credentials for the image repository that corresponds with
the given API_KEY.

**Arguments**:

- `api_key` _Text, optional_ - Team API key. Defaults to None.
  

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
                  api_key: Optional[Text] = None) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/__init__.py#L311)

Onboard a model after its image has been pushed to ECR.

**Arguments**:

- `model_id` _Text_ - Model ID obtained from CREATE_ASSET_REPO.
- `image_tag` _Text_ - Image tag to be onboarded.
- `image_hash` _Text_ - Image digest.
- `host_machine` _Text, optional_ - Machine on which to host model.
- `api_key` _Text, optional_ - Team API key. Defaults to None.

**Returns**:

- `Dict` - Backend response

#### deploy\_huggingface\_model

```python
@classmethod
def deploy_huggingface_model(cls,
                             name: Text,
                             hf_repo_id: Text,
                             revision: Optional[Text] = "",
                             hf_token: Optional[Text] = "",
                             api_key: Optional[Text] = None) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/__init__.py#L352)

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
  

**Returns**:

- `Dict` - Deployment response containing model ID and status information.

#### get\_huggingface\_model\_status

```python
@classmethod
def get_huggingface_model_status(cls,
                                 model_id: Text,
                                 api_key: Optional[Text] = None) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/__init__.py#L413)

Check the deployment status of a Hugging Face model.

This method retrieves the current status and details of a deployed
Hugging Face model.

**Arguments**:

- `model_id` _Text_ - Model ID returned by deploy_huggingface_model.
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
  

**Returns**:

- `Dict` - Status response containing:
  - status: Current deployment status
  - name: Model name
  - id: Model ID
  - pricing: Pricing information

