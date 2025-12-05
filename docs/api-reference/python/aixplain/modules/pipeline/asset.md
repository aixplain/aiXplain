---
sidebar_label: asset
title: aixplain.modules.pipeline.asset
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
Date: November 25th 2024
Description:
    Pipeline Asset Class

### Pipeline Objects

```python
class Pipeline(Asset, DeployableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/asset.py#L39)

Representing a custom pipeline that was created on the aiXplain Platform

**Attributes**:

- `id` _Text_ - ID of the Pipeline
- `name` _Text_ - Name of the Pipeline
- `api_key` _Text_ - Team API Key to run the Pipeline.
- `url` _Text, optional_ - running URL of platform. Defaults to config.BACKEND_URL.
- `supplier` _Text, optional_ - Pipeline supplier. Defaults to &quot;aiXplain&quot;.
- `version` _Text, optional_ - version of the pipeline. Defaults to &quot;1.0&quot;.
- `status` _AssetStatus, optional_ - Pipeline status. Defaults to AssetStatus.DRAFT.
- `**additional_info` - Any additional Pipeline info to be saved

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text,
             api_key: Text,
             url: Text = config.BACKEND_URL,
             supplier: Text = "aiXplain",
             version: Text = "1.0",
             status: AssetStatus = AssetStatus.DRAFT,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/asset.py#L56)

Create a Pipeline with the necessary information

**Arguments**:

- `id` _Text_ - ID of the Pipeline
- `name` _Text_ - Name of the Pipeline
- `api_key` _Text_ - Team API Key to run the Pipeline.
- `url` _Text, optional_ - running URL of platform. Defaults to config.BACKEND_URL.
- `supplier` _Text, optional_ - Pipeline supplier. Defaults to &quot;aiXplain&quot;.
- `version` _Text, optional_ - version of the pipeline. Defaults to &quot;1.0&quot;.
- `status` _AssetStatus, optional_ - Pipeline status. Defaults to AssetStatus.DRAFT.
- `**additional_info` - Any additional Pipeline info to be saved

#### poll

```python
def poll(poll_url: Text,
         name: Text = "pipeline_process",
         response_version: Text = "v2") -> Union[Dict, PipelineResponse]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/asset.py#L143)

Poll the platform to check whether an asynchronous call is done.

**Arguments**:

- `poll_url` _Text_ - polling URL
- `name` _Text, optional_ - ID given to a call. Defaults to &quot;pipeline_process&quot;.
  

**Returns**:

- `Dict` - response obtained by polling call

#### run

```python
def run(data: Union[Text, Dict],
        data_asset: Optional[Union[Text, Dict]] = None,
        name: Text = "pipeline_process",
        timeout: float = 20000.0,
        wait_time: float = 1.0,
        version: Optional[Text] = None,
        response_version: Text = "v2",
        **kwargs) -> Union[Dict, PipelineResponse]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/asset.py#L188)

Run the pipeline synchronously and wait for results.

This method executes the pipeline with the provided input data and waits
for completion. It handles both direct data input and data assets, with
support for polling and timeout.

**Arguments**:

- `data` _Union[Text, Dict]_ - The input data for the pipeline. Can be:
  - A string (file path, URL, or raw data)
  - A dictionary mapping node labels to input data
- `data_asset` _Optional[Union[Text, Dict]], optional_ - Data asset(s) to
  process. Can be a single asset ID or a dict mapping node labels
  to asset IDs. Defaults to None.
- `name` _Text, optional_ - Identifier for this pipeline run. Used for
  logging. Defaults to &quot;pipeline_process&quot;.
- `timeout` _float, optional_ - Maximum time in seconds to wait for
  completion. Defaults to 20000.0.
- `wait_time` _float, optional_ - Initial time in seconds between polling
  attempts. May increase over time. Defaults to 1.0.
- `version` _Optional[Text], optional_ - Specific pipeline version to run.
  Defaults to None.
- `response_version` _Text, optional_ - Response format version (&quot;v1&quot; or
  &quot;v2&quot;). Defaults to &quot;v2&quot;.
- `**kwargs` - Additional keyword arguments passed to the pipeline.
  

**Returns**:

  Union[Dict, PipelineResponse]: If response_version is:
  - &quot;v1&quot;: Dictionary with status, error (if any), and elapsed time
  - &quot;v2&quot;: PipelineResponse object with structured response data
  

**Raises**:

- `Exception` - If the pipeline execution fails, times out, or encounters
  errors during polling.
  

**Notes**:

  - The method starts with run_async and then polls for completion
  - wait_time may increase up to 60 seconds between polling attempts
  - For v2 responses, use PipelineResponse methods to access results

#### run\_async

```python
def run_async(data: Union[Text, Dict],
              data_asset: Optional[Union[Text, Dict]] = None,
              name: Text = "pipeline_process",
              batch_mode: bool = True,
              version: Optional[Text] = None,
              response_version: Text = "v2",
              **kwargs) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/asset.py#L425)

Runs asynchronously a pipeline call.

**Arguments**:

- `data` _Union[Text, Dict]_ - link to the input data
- `data_asset` _Optional[Union[Text, Dict]], optional_ - Data asset to be processed by the pipeline. Defaults to None.
- `name` _Text, optional_ - ID given to a call. Defaults to &quot;pipeline_process&quot;.
- `batch_mode` _bool, optional_ - Whether to run the pipeline in batch mode or online. Defaults to True.
- `version` _Optional[Text], optional_ - Version of the pipeline. Defaults to None.
- `response_version` _Text, optional_ - Version of the response. Defaults to &quot;v2&quot;.
- `kwargs` - A dictionary of keyword arguments. The keys are the argument names
  

**Returns**:

- `Dict` - polling URL in response

#### update

```python
def update(pipeline: Union[Text, Dict],
           save_as_asset: bool = False,
           api_key: Optional[Text] = None,
           name: Optional[Text] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/asset.py#L510)

Update Pipeline

**Arguments**:

- `pipeline` _Union[Text, Dict]_ - Pipeline as a Python dictionary or in a JSON file
- `save_as_asset` _bool, optional_ - Save as asset (True) or draft (False). Defaults to False.
- `api_key` _Optional[Text], optional_ - Team API Key to create the Pipeline. Defaults to None.
  

**Raises**:

- `Exception` - Make sure the pipeline to be save is in a JSON file.

#### delete

```python
def delete() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/asset.py#L574)

Delete this pipeline from the platform.

This method permanently removes the pipeline from the aiXplain platform.
The operation cannot be undone.

**Raises**:

- `Exception` - If deletion fails, which can happen if:
  - The pipeline doesn&#x27;t exist
  - The user doesn&#x27;t have permission to delete it
  - The API request fails
  - The server returns a non-200 status code
  

**Notes**:

  - This operation is permanent and cannot be undone
  - Only the pipeline owner can delete it
  - Uses the team API key for authentication

#### save

```python
def save(pipeline: Optional[Union[Text, Dict]] = None,
         save_as_asset: bool = False,
         api_key: Optional[Text] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/asset.py#L607)

Update and Save Pipeline

**Arguments**:

- `pipeline` _Optional[Union[Text, Dict]]_ - Pipeline as a Python dictionary or in a JSON file
- `save_as_asset` _bool, optional_ - Save as asset (True) or draft (False). Defaults to False.
- `api_key` _Optional[Text], optional_ - Team API Key to create the Pipeline. Defaults to None.
  

**Raises**:

- `Exception` - Make sure the pipeline to be save is in a JSON file.

#### deploy

```python
def deploy(api_key: Optional[Text] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/asset.py#L663)

Deploy the Pipeline.

This method overrides the deploy method in DeployableMixin to handle
Pipeline-specific deployment functionality.

**Arguments**:

- `api_key` _Optional[Text], optional_ - Team API Key to deploy the Pipeline. Defaults to None.

#### \_\_repr\_\_

```python
def __repr__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/asset.py#L682)

Return a string representation of the Pipeline instance.

**Returns**:

- `str` - A string in the format &quot;Pipeline: &lt;name&gt; (id=&lt;id&gt;)&quot;.

