# aixtend.factories package

## Submodules

## aixtend.factories.asset_factory module


### _class_ aixtend.factories.asset_factory.AssetFactory()
Bases: `object`


#### api_key(_ = '_ )

#### backend_url(_ = 'https://platform-api.aixplain.com_ )

#### _abstract_ get(asset_id: str)
Create a ‘Asset’ object from id


* **Parameters**

    **asset_id** (*str*) – ID of required asset.



* **Returns**

    Created ‘Asset’ object



* **Return type**

    [Asset](aixtend.modules.md#aixtend.modules.asset.Asset)


## aixtend.factories.benchmark_factory module


### _class_ aixtend.factories.benchmark_factory.BenchmarkFactory()
Bases: `object`


#### api_key(_ = '_ )

#### backend_url(_ = 'https://platform-api.aixplain.com_ )

#### _classmethod_ create_benchmark(name: str, dataset_list: List[[Dataset](aixtend.modules.md#aixtend.modules.dataset.Dataset)], model_list: List[[Model](aixtend.modules.md#aixtend.modules.model.Model)], metric_list: List[[Metric](aixtend.modules.md#aixtend.modules.metric.Metric)])
Creates a benchmark based on the information provided like name, dataset list, model list and score list.
Note: This only creates a benchmark. It needs to run seperately using start_benchmark_job.


* **Parameters**

    
    * **name** (*str*) – Unique Name of benchmark


    * **dataset_list** (*List**[*[*Dataset*](aixtend.modules.md#aixtend.modules.dataset.Dataset)*]*) – List of Datasets to be used for benchmarking


    * **model_list** (*List**[*[*Model*](aixtend.modules.md#aixtend.modules.model.Model)*]*) – List of Models to be used for benchmarking


    * **metric_list** (*List**[*[*Metric*](aixtend.modules.md#aixtend.modules.metric.Metric)*]*) – List of Metrics to be used for benchmarking



* **Returns**

    _description_



* **Return type**

    [Benchmark](aixtend.modules.md#aixtend.modules.benchmark.Benchmark)



#### _classmethod_ create_benchmark_from_id(benchmark_id: str)
Create a ‘Benchmark’ object from Benchmark id


* **Parameters**

    **benchmark_id** (*str*) – Benchmark ID of required Benchmark.



* **Returns**

    Created ‘Benchmark’ object



* **Return type**

    [Benchmark](aixtend.modules.md#aixtend.modules.benchmark.Benchmark)



#### _classmethod_ create_benchmark_job_from_id(job_id: str)
Create a ‘BenchmarkJob’ object from job id


* **Parameters**

    **job_id** (*str*) – ID of the required BenchmarkJob.



* **Returns**

    Created ‘BenchmarkJob’ object



* **Return type**

    [BenchmarkJob](aixtend.modules.md#aixtend.modules.benchmark_job.BenchmarkJob)



#### _classmethod_ download_results_as_csv(benchmarkJob: [BenchmarkJob](aixtend.modules.md#aixtend.modules.benchmark_job.BenchmarkJob), save_path: Optional[str] = None, returnDataFrame: bool = False)
Get the results of the benchmark job in a CSV format.

    The results can either be downloaded locally or returned in the form of pandas.DataFrame.

    Args:

        benchmarkJob (BenchmarkJob): ‘BenchmarkJob’ to get the results for
        save_path (str, optional): Path to save the CSV if returnDataFrame is False. If None, a ranmdom path is generated. @classmethod

defaults to None.

    returnDataFrame (bool, optional): If True, the result is returned as pandas.DataFrame else saved as a CSV file. @classmethod

defaults to False.

> Returns:

>     str/pandas.DataFrame: results as path of locally saved file if returnDataFrame is False else as a pandas dataframe


#### _classmethod_ start_benchmark_job(benchmark: [Benchmark](aixtend.modules.md#aixtend.modules.benchmark.Benchmark))
Start a new benchmarking job(run) from a already created benchmark.


* **Parameters**

    **benchmark** ([*Benchmark*](aixtend.modules.md#aixtend.modules.benchmark.Benchmark)) – ‘Benchmark’ object to start the run for



* **Returns**

    ‘BenchmarkJob’ created after starting the run



* **Return type**

    [BenchmarkJob](aixtend.modules.md#aixtend.modules.benchmark_job.BenchmarkJob)



#### _classmethod_ update_benchmark_info(benchmark: [Benchmark](aixtend.modules.md#aixtend.modules.benchmark.Benchmark))
Updates ‘Benchmark’ with the latest info


* **Parameters**

    **benchmark** ([*Benchmark*](aixtend.modules.md#aixtend.modules.benchmark.Benchmark)) – ‘Benchmark’ to update



* **Returns**

    updated ‘Benchmark’



* **Return type**

    [Benchmark](aixtend.modules.md#aixtend.modules.benchmark.Benchmark)



#### _classmethod_ update_benchmark_job_info(benchmarkJob: [BenchmarkJob](aixtend.modules.md#aixtend.modules.benchmark_job.BenchmarkJob))
Updates ‘BenchmarkJob’ with the latest info


* **Parameters**

    **benchmarkJob** ([*BenchmarkJob*](aixtend.modules.md#aixtend.modules.benchmark_job.BenchmarkJob)) – ‘BenchmarkJob’ to update



* **Returns**

    updated ‘BenchmarkJob’



* **Return type**

    [BenchmarkJob](aixtend.modules.md#aixtend.modules.benchmark_job.BenchmarkJob)


## aixtend.factories.dataset_factory module


### _class_ aixtend.factories.dataset_factory.DatasetFactory()
Bases: `AssetFactory`


#### api_key(_ = '_ )

#### backend_url(_ = 'https://platform-api.aixplain.com_ )

#### create(name: str, description: str, license: str, functions: List[str], data_url: str, fields: Dict[str, [FieldType](aixtend.modules.md#aixtend.modules.dataset.FieldType)], file_format: [FileFormat](aixtend.modules.md#aixtend.modules.dataset.FileFormat))
Asynchronous call to Upload a dataset to the user’s dashboard.


* **Parameters**

    
    * **name** (*str*) – dataset name


    * **description** (*str*) – dataset description


    * **license** (*str*) – dataset license


    * **functions** (*List**[**str**]*) – AI functions for which the dataset is designed


    * **data_url** (*str*) – link to the data


    * **fields** (*Dict**[**str**, **str**]*) – data field names and their types


    * **file_format** ([*FileFormat*](aixtend.modules.md#aixtend.modules.dataset.FileFormat)) – format of the file



#### _classmethod_ get(dataset_id: str)
Create a ‘Dataset’ object from dataset id


* **Parameters**

    **dataset_id** (*str*) – Dataset ID of required dataset.



* **Returns**

    Created ‘Dataset’ object



* **Return type**

    [Dataset](aixtend.modules.md#aixtend.modules.dataset.Dataset)



#### _classmethod_ get_assets_from_page(page_number: int, task: str, input_language: Optional[str] = None, output_language: Optional[str] = None)
Get the list of datasets from a given page. Additional task and language filters can be also be provided


* **Parameters**

    
    * **page_number** (*int*) – Page from which datasets are to be listed


    * **task** (*str*) – Task of listed datasets


    * **input_language** (*str**, **optional*) – Input language of listed datasets. Defaults to None.


    * **output_language** (*str**, **optional*) – Output language of listed datasets. Defaults to None.



* **Returns**

    List of datasets based on given filters



* **Return type**

    List[[Dataset](aixtend.modules.md#aixtend.modules.dataset.Dataset)]



#### _classmethod_ get_first_k_assets(k: int, task: str, input_language: Optional[str] = None, output_language: Optional[str] = None)
Gets the first k given datasets based on the provided task and language filters


* **Parameters**

    
    * **k** (*int*) – Number of datasets to get


    * **task** (*str*) – Task of listed datasets


    * **input_language** (*str**, **optional*) – Input language of listed datasets. Defaults to None.


    * **output_language** (*str**, **optional*) – Output language of listed datasets. Defaults to None.



* **Returns**

    List of datasets based on given filters



* **Return type**

    List[[Dataset](aixtend.modules.md#aixtend.modules.dataset.Dataset)]


## aixtend.factories.metric_factory module


### _class_ aixtend.factories.metric_factory.MetricFactory()
Bases: `object`


#### api_key(_ = '_ )

#### backend_url(_ = 'https://platform-api.aixplain.com_ )

#### _classmethod_ create_asset_from_id(metric_id: str)
Create a ‘Metric’ object from metric id


* **Parameters**

    **model_id** (*str*) – Model ID of required metric.



* **Returns**

    Created ‘Metric’ object



* **Return type**

    [Metric](aixtend.modules.md#aixtend.modules.metric.Metric)



#### _classmethod_ list_assets(task: str)
Get list of supported metrics for a given task


* **Parameters**

    **task** (*str*) – Task to get metric for



* **Returns**

    List of supported metrics



* **Return type**

    List[[Metric](aixtend.modules.md#aixtend.modules.metric.Metric)]


## aixtend.factories.model_factory module


### _class_ aixtend.factories.model_factory.ModelFactory()
Bases: `object`


#### api_key(_ = '_ )

#### backend_url(_ = 'https://platform-api.aixplain.com_ )

#### _classmethod_ create_asset_from_id(model_id: str)
Create a ‘Model’ object from model id


* **Parameters**

    **model_id** (*str*) – Model ID of required model.



* **Returns**

    Created ‘Model’ object



* **Return type**

    [Model](aixtend.modules.md#aixtend.modules.model.Model)



#### _classmethod_ get_assets_from_page(page_number: int, task: str, input_language: Optional[str] = None, output_language: Optional[str] = None)
Get the list of models from a given page. Additional task and language filters can be also be provided


* **Parameters**

    
    * **page_number** (*int*) – Page from which models are to be listed


    * **task** (*str*) – Task of listed model


    * **input_language** (*str**, **optional*) – Input language of listed model. Defaults to None.


    * **output_language** (*str**, **optional*) – Output langugage of listed model. Defaults to None.



* **Returns**

    List of models based on given filters



* **Return type**

    List[[Model](aixtend.modules.md#aixtend.modules.model.Model)]



#### _classmethod_ get_first_k_assets(k: int, task: str, input_language: Optional[str] = None, output_language: Optional[str] = None)
Gets the first k given models based on the provided task and language filters


* **Parameters**

    
    * **k** (*int*) – Number of models to get


    * **task** (*str*) – Task of listed model


    * **input_language** (*str**, **optional*) – Input language of listed model. Defaults to None.


    * **output_language** (*str**, **optional*) – Output language of listed model. Defaults to None.



* **Returns**

    List of models based on given filters



* **Return type**

    List[[Model](aixtend.modules.md#aixtend.modules.model.Model)]



#### _classmethod_ subscribe_to_asset(model: [Model](aixtend.modules.md#aixtend.modules.model.Model))
Subscribe to the given model


* **Parameters**

    **model** ([*Model*](aixtend.modules.md#aixtend.modules.model.Model)) – ‘Model’ object to subscribe to



#### _classmethod_ unsubscribe_to_asset(model: [Model](aixtend.modules.md#aixtend.modules.model.Model))
Unsubscribe to the given model


* **Parameters**

    **model** ([*Model*](aixtend.modules.md#aixtend.modules.model.Model)) – ‘Model’ object to unsubscribe to


## aixtend.factories.pipeline_factory module


### _class_ aixtend.factories.pipeline_factory.PipelineFactory()
Bases: `object`


#### _static_ create_from_api_key(api_key: str, url: str = 'https://platform-api.aixplain.com/assets/pipeline/execution/run')
params:
—

> api_key: API key of the pipeline
> url: API endpoint

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
