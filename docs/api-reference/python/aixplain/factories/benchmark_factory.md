---
sidebar_label: benchmark_factory
title: aixplain.factories.benchmark_factory
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
Date: December 2nd 2022
Description:
    Benchmark Factory Class

### BenchmarkFactory Objects

```python
class BenchmarkFactory()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/benchmark_factory.py#L39)

Factory class for creating and managing benchmarks in the aiXplain platform.

This class provides functionality for creating benchmarks, managing benchmark jobs,
retrieving results, and configuring normalization options. Benchmarks can be used
to evaluate and compare multiple models using specified datasets and metrics.

**Attributes**:

- `backend_url` _str_ - Base URL for the aiXplain backend API.

#### get

```python
@classmethod
def get(cls, benchmark_id: str) -> Benchmark
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/benchmark_factory.py#L121)

Retrieve a benchmark by its ID.

This method fetches a benchmark and all its associated components
(models, datasets, metrics, jobs) from the platform.

**Arguments**:

- `benchmark_id` _str_ - Unique identifier of the benchmark to retrieve.
  

**Returns**:

- `Benchmark` - Retrieved benchmark object with all components loaded.
  

**Raises**:

- `Exception` - If:
  - Benchmark ID is invalid
  - Authentication fails
  - Service is unavailable

#### get\_job

```python
@classmethod
def get_job(cls, job_id: Text) -> BenchmarkJob
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/benchmark_factory.py#L170)

Retrieve a benchmark job by its ID.

**Arguments**:

- `job_id` _Text_ - Unique identifier of the benchmark job to retrieve.
  

**Returns**:

- `BenchmarkJob` - Retrieved benchmark job object with its current status.
  

**Raises**:

- `Exception` - If the job ID is invalid or the request fails.

#### create

```python
@classmethod
def create(cls, name: str, dataset_list: List[Dataset],
           model_list: List[Model], metric_list: List[Metric]) -> Benchmark
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/benchmark_factory.py#L254)

Create a new benchmark configuration.

This method creates a new benchmark that can be used to evaluate and compare
multiple models using specified datasets and metrics. Note that this only
creates the benchmark configuration - you need to run it separately using
start_benchmark_job.

**Arguments**:

- `name` _str_ - Unique name for the benchmark.
- `dataset_list` _List[Dataset]_ - List of datasets to use for evaluation.
  Currently only supports a single dataset.
- `model_list` _List[Model]_ - List of models to evaluate. All models must
  either have additional configuration info or none should have it.
- `metric_list` _List[Metric]_ - List of metrics to use for evaluation.
  Must provide at least one metric.
  

**Returns**:

- `Benchmark` - Created benchmark object ready for execution.
  

**Raises**:

- `Exception` - If:
  - No dataset is provided or multiple datasets are provided
  - No metrics are provided
  - No models are provided
  - Model configuration is inconsistent
  - Request fails or returns an error

#### list\_normalization\_options

```python
@classmethod
def list_normalization_options(cls, metric: Metric, model: Model) -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/benchmark_factory.py#L326)

List supported normalization options for a metric-model pair.

This method retrieves the list of normalization options that can be used
when evaluating a specific model with a specific metric in a benchmark.

**Arguments**:

- `metric` _Metric_ - Metric to get normalization options for.
- `model` _Model_ - Model to check compatibility with.
  

**Returns**:

- `List[str]` - List of supported normalization option identifiers.
  

**Raises**:

- `Exception` - If:
  - Metric or model is invalid
  - Request fails
  - Service is unavailable

#### get\_benchmark\_job\_scores

```python
@classmethod
def get_benchmark_job_scores(cls, job_id: Text) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/benchmark_factory.py#L370)

Retrieve and format benchmark job scores.

This method fetches the scores from a benchmark job and formats them into
a pandas DataFrame, with model names properly formatted to include supplier
and version information.

**Arguments**:

- `job_id` _Text_ - Unique identifier of the benchmark job.
  

**Returns**:

- `pandas.DataFrame` - DataFrame containing benchmark scores with formatted
  model names.
  

**Raises**:

- `Exception` - If the job ID is invalid or the request fails.

