# aixtend.modules package

## Submodules

## aixtend.modules.asset module


### _class_ aixtend.modules.asset.Asset(id: str, name: str, description: str, supplier: Optional[str] = 'aiXplain', version: Optional[str] = '1.0')
Bases: `object`


#### to_dict()
Get the asset info as a Dictionary


* **Returns**

    Asset Information



* **Return type**

    dict


## aixtend.modules.benchmark module


### _class_ aixtend.modules.benchmark.Benchmark(id: str, name: str, dataset_list: List[Dataset], model_list: List[Model], metric_list: List[Metric], job_list: List[BenchmarkJob], description: str = '', supplier: Optional[str] = 'aiXplain', version: Optional[str] = '1.0', \*\*additional_info)
Bases: `Asset`

## aixtend.modules.benchmark_job module


### _class_ aixtend.modules.benchmark_job.BenchmarkJob(id: str, status: str, parentBenchmarkId: str, \*\*additional_info)
Bases: `object`


#### get_asset_info()
Get the Benchmark Job info as a Dictionary


* **Returns**

    Benchmark Job Information



* **Return type**

    dict


## aixtend.modules.dataset module


### _class_ aixtend.modules.dataset.DataFormat(value)
Bases: `Enum`

An enumeration.


#### DICT(_ = 'dict_ )

#### HUGGINGFACE_DATASETS(_ = 'huggingface_datasets_ )

#### PANDAS(_ = 'pandas_ )

### _class_ aixtend.modules.dataset.Dataset(id: str, name: str, description: str, data_url: Optional[str] = None, field_names: Optional[List[str]] = None, load_data: bool = False, data_format: Optional[DataFormat] = DataFormat.HUGGINGFACE_DATASETS, supplier: Optional[str] = 'aiXplain', version: Optional[str] = '1.0', \*\*additional_info)
Bases: `Asset`


#### get_data(fields: Optional[list] = None, start: Optional[int] = 0, offset: Optional[int] = 100, data_format: Optional[DataFormat] = DataFormat.PANDAS)
Get data fields from a dataset sample of size offset starting from the 

```
`
```

start\`th row.


* **Parameters**

    
    * **fields** (*list**, **optional*) – list of fields (columns). If None, selects all. Defaults to None.


    * **start** (*int**, **optional*) – start row index. Defaults to 0.


    * **offset** (*int**, **optional*) – number of rows. Defaults to 100.



* **Returns**

    data



* **Return type**

    Any



### _class_ aixtend.modules.dataset.FieldType(value)
Bases: `Enum`

An enumeration.


#### AUDIO(_ = 'audio_ )

#### IMAGE(_ = 'image_ )

#### LABEL(_ = 'label_ )

#### TEXT(_ = 'text_ )

#### VIDEO(_ = 'video_ )

### _class_ aixtend.modules.dataset.FileFormat(value)
Bases: `Enum`

An enumeration.


#### CSV(_ = 'csv_ )

#### JSON(_ = 'json_ )

#### PARQUET(_ = 'parquet_ )

#### XML(_ = 'xml_ )
## aixtend.modules.metric module


### _class_ aixtend.modules.metric.Metric(id: str, name: str, description: str, supplier: Optional[str] = 'aiXplain', version: Optional[str] = '1.0', \*\*additional_info)
Bases: `Asset`

## aixtend.modules.model module


### _class_ aixtend.modules.model.Model(id: str, name: str, description: str = '', api_key: Optional[str] = None, subscription_id: Optional[str] = None, url: str = 'https://models.aixplain.com/api/v1/execute', supplier: Optional[str] = 'aiXplain', version: Optional[str] = '1.0', \*\*additional_info)
Bases: `Asset`


#### poll(poll_url: str, name: str = 'model_process')
Poll the platform to check whether an asynchronous call is done.


* **Parameters**

    
    * **poll_url** (*str*) – polling


    * **name** (*str**, **optional*) – ID given to a call. Defaults to “model_process”.



* **Returns**

    response obtained by polling call



* **Return type**

    dict



#### run(data: Union[str, dict], name: str = 'model_process', timeout: float = 300)
Runs a model call.


* **Parameters**

    
    * **data** (*str*) – link to the input data


    * **name** (*str**, **optional*) – ID given to a call. Defaults to “model_process”.


    * **timeout** (*float**, **optional*) – total polling time. Defaults to 300.



* **Returns**

    parsed output from model



* **Return type**

    dict



#### run_async(data: Union[str, dict], name: str = 'model_process')
Runs asynchronously a model call.


* **Parameters**

    
    * **data** (*str*) – link to the input data


    * **name** (*str**, **optional*) – ID given to a call. Defaults to “model_process”.



* **Returns**

    polling URL



* **Return type**

    dict



#### to_dict()
Get the model info as a Dictionary


* **Returns**

    Model Information



* **Return type**

    dict


## aixtend.modules.pipeline module


### _class_ aixtend.modules.pipeline.Pipeline(api_key: str, url: str)
Bases: `object`


#### poll(poll_url: str, name: str = 'pipeline_process')
Poll the platform to check whether an asynchronous call is done.

params:
—

> poll_url: polling URL
> name: Optional. ID given to a call

return:
—

> resp: response obtained by polling call


#### run(data: Union[str, dict], name: str = 'pipeline_process', timeout: float = 20000.0)
Runs a pipeline call.

params:
—

> data: link to the input data
> name: Optional. ID given to a call
> timeout: total polling time


#### run_async(data: Union[str, dict], name: str = 'pipeline_process')
Runs asynchronously a pipeline call.

params:
—

> data: link to the input data
> name: Optional. ID given to a call

return:
—

> poll_url: polling URL

## Module contents

aiXplain SDK Library.
—

aiXplain SDK enables python programmers to add AI functions
to their software.

Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the “License”);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

> [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an “AS IS” BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
