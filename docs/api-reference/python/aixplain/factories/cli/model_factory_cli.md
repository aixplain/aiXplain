---
sidebar_label: model_factory_cli
title: aixplain.factories.cli.model_factory_cli
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

Author: Michael Lam
Date: September 18th 2023
Description:
    Model Factory CLI

#### list\_host\_machines

```python
@click.command("hosts")
@click.option("--api-key",
              default=None,
              help="TEAM_API_KEY if not already set in environment")
def list_host_machines(api_key: Optional[Text] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/cli/model_factory_cli.py#L32)

List available host machines for model deployment.

This CLI command wraps the ModelFactory.list_host_machines function and outputs
the results in YAML format.

**Arguments**:

- `api_key` _Text, optional_ - Team API key for authentication. Defaults to None,
  using the configured environment variable.
  

**Returns**:

- `None` - Prints the host machines list in YAML format to stdout.

#### list\_functions

```python
@click.command("functions")
@click.option("--verbose",
              is_flag=True,
              help="List all function details, False by default.")
@click.option("--api-key",
              default=None,
              help="TEAM_API_KEY if not already set in environment.")
def list_functions(verbose: bool, api_key: Optional[Text] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/cli/model_factory_cli.py#L53)

List available functions for model deployment.

This CLI command wraps the ModelFactory.list_functions function and outputs
the results in YAML format. Functions represent the different types of
operations that models can perform.

**Arguments**:

- `verbose` _bool_ - If True, includes detailed information about each function.
  If False, provides a simplified list.
- `api_key` _Text, optional_ - Team API key for authentication. Defaults to None,
  using the configured environment variable.
  

**Returns**:

- `None` - Prints the functions list in YAML format to stdout.

#### list\_gpus

```python
@click.command("gpus")
@click.option("--api-key",
              default=None,
              help="TEAM_API_KEY if not already set in environment.")
def list_gpus(api_key: Optional[Text] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/cli/model_factory_cli.py#L76)

List available GPUs for model deployment.

This CLI command wraps the ModelFactory.list_gpus function and outputs
the results in YAML format. Shows available GPU resources that can be
used for model hosting.

**Arguments**:

- `api_key` _Text, optional_ - Team API key for authentication. Defaults to None,
  using the configured environment variable.
  

**Returns**:

- `None` - Prints the GPU list in YAML format to stdout.

#### create\_asset\_repo

```python
@click.command("image-repo")
@click.option("--name", help="Model name.")
@click.option("--description", help="Description of model.")
@click.option("--function", help="Function name obtained from LIST_FUNCTIONS.")
@click.option(
    "--source-language",
    default="en",
    help=
    "Model source language in 2-character 639-1 code or 3-character 639-3 code."
)
@click.option("--input-modality", help="Input type (text, video, image, etc.)")
@click.option("--output-modality",
              help="Output type (text, video, image, etc.)")
@click.option("--documentation-url",
              default="",
              help="Link to model documentation.")
@click.option("--api-key",
              default=None,
              help="TEAM_API_KEY if not already set in environment.")
def create_asset_repo(name: Text,
                      description: Text,
                      function: Text,
                      source_language: Text,
                      input_modality: Text,
                      output_modality: Text,
                      documentation_url: Optional[Text] = "",
                      api_key: Optional[Text] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/cli/model_factory_cli.py#L106)

Create a new asset repository for a model.

This CLI command wraps the ModelFactory.create_asset_repo function and outputs
the results in YAML format. Creates a new repository for storing model assets
and configurations.

**Arguments**:

- `name` _Text_ - Name of the model.
- `description` _Text_ - Description of the model&#x27;s purpose and functionality.
- `function` _Text_ - Model function name obtained via list_functions.
- `source_language` _Text_ - Language code in ISO 639-1 (2-char) or 639-3 (3-char) format.
- `input_modality` _Text_ - Type of input the model accepts (e.g., text, video, image).
- `output_modality` _Text_ - Type of output the model produces (e.g., text, video, image).
- `documentation_url` _Text, optional_ - URL to model documentation. Defaults to &quot;&quot;.
- `api_key` _Text, optional_ - Team API key for authentication. Defaults to None,
  using the configured environment variable.
  

**Returns**:

- `None` - Prints the created repository details in YAML format to stdout.

#### asset\_repo\_login

```python
@click.command("image-repo-login")
@click.option("--api-key",
              default=None,
              help="TEAM_API_KEY if not already set in environment.")
def asset_repo_login(api_key: Optional[Text] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/cli/model_factory_cli.py#L145)

Get login credentials for the asset repository.

This CLI command wraps the ModelFactory.asset_repo_login function and outputs
the results in YAML format. Provides authentication details needed to access
the model asset repository.

**Arguments**:

- `api_key` _Text, optional_ - Team API key for authentication. Defaults to None,
  using the configured environment variable.
  

**Returns**:

- `None` - Prints the login credentials in YAML format to stdout.

#### onboard\_model

```python
@click.command("model")
@click.option("--model-id", help="Model ID from CREATE_IMAGE_REPO.")
@click.option("--image-tag",
              help="The tag of the image that you would like hosted.")
@click.option("--image-hash",
              help="The hash of the image you would like onboarded.")
@click.option("--host-machine",
              default="",
              help="The machine on which to host the model.")
@click.option("--api-key",
              default=None,
              help="TEAM_API_KEY if not already set in environment.")
def onboard_model(model_id: Text,
                  image_tag: Text,
                  image_hash: Text,
                  host_machine: Optional[Text] = "",
                  api_key: Optional[Text] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/cli/model_factory_cli.py#L170)

Onboard a model image for deployment.

This CLI command wraps the ModelFactory.onboard_model function and outputs
the results in YAML format. Prepares a model image for deployment by registering
it with the platform.

**Arguments**:

- `model_id` _Text_ - Model ID obtained from create_asset_repo.
- `image_tag` _Text_ - Tag of the Docker image to be onboarded.
- `image_hash` _Text_ - Hash of the Docker image for verification.
- `host_machine` _Text, optional_ - ID of the machine to host the model. Defaults to &quot;&quot;.
- `api_key` _Text, optional_ - Team API key for authentication. Defaults to None,
  using the configured environment variable.
  

**Returns**:

- `None` - Prints the onboarding results in YAML format to stdout.

#### deploy\_huggingface\_model

```python
@click.command("hf-model")
@click.option("--name", help="User-defined name for Hugging Face model.")
@click.option(
    "--hf-repo-id",
    help="Repository ID from Hugging Face in {supplier}/{model name} form.")
@click.option("--revision", default="", help="Commit hash of repository.")
@click.option("--hf-token",
              default=None,
              help="Hugging Face token used to authenticate to this model.")
@click.option("--api-key",
              default=None,
              help="TEAM_API_KEY if not already set in environment.")
def deploy_huggingface_model(name: Text,
                             hf_repo_id: Text,
                             hf_token: Optional[Text] = None,
                             revision: Optional[Text] = None,
                             api_key: Optional[Text] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/cli/model_factory_cli.py#L201)

Deploy a model from Hugging Face Hub.

This CLI command wraps the ModelFactory.deploy_huggingface_model function and outputs
the results in YAML format. Deploys a model directly from Hugging Face&#x27;s model hub.

**Arguments**:

- `name` _Text_ - User-defined name for the Hugging Face model.
- `hf_repo_id` _Text_ - Repository ID from Hugging Face in &#x27;org/model-name&#x27; format.
- `hf_token` _Text, optional_ - Hugging Face token for private models. Defaults to None.
- `revision` _Text, optional_ - Specific model revision/commit hash. Defaults to None.
- `api_key` _Text, optional_ - Team API key for authentication. Defaults to None,
  using the configured environment variable.
  

**Returns**:

- `None` - Prints the deployment results in YAML format to stdout.

#### get\_huggingface\_model\_status

```python
@click.command("hf-model-status")
@click.option("--model-id", help="Model ID from DEPLOY_HUGGINGFACE_MODEL.")
@click.option("--api-key",
              default=None,
              help="TEAM_API_KEY if not already set in environment.")
def get_huggingface_model_status(model_id: Text,
                                 api_key: Optional[Text] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/cli/model_factory_cli.py#L232)

Check the deployment status of a Hugging Face model.

This CLI command wraps the ModelFactory.get_huggingface_model_status function and
outputs the results in YAML format. Retrieves the current status of a Hugging Face
model deployment.

**Arguments**:

- `model_id` _Text_ - Model ID obtained from deploy_huggingface_model.
- `api_key` _Text, optional_ - Team API key for authentication. Defaults to None,
  using the configured environment variable.
  

**Returns**:

- `None` - Prints the model status in YAML format to stdout.

