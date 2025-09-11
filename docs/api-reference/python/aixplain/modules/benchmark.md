---
sidebar_label: benchmark
title: aixplain.modules.benchmark
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
Date: October 25th 2022
Description:
    Benchmark Class

### Benchmark Objects

```python
class Benchmark(Asset)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/benchmark.py#L32)

Benchmark is a powerful tool for benchmarking machine learning models and evaluating their performance on specific tasks.
It represents a collection of Models, Datasets and Metrics to run associated Benchmark Jobs.

**Attributes**:

- `id` _str_ - ID of the Benchmark.
- `name` _str_ - Name of the Benchmark.
- `model_list` _List[Model]_ - List of Models to be used for benchmarking.
- `dataset_list` _List[Dataset]_ - List of Datasets to be used for benchmarking.
- `metric_list` _List[Metric]_ - List of Metrics to be used for benchmarking.
- `job_list` _List[BenchmarkJob]_ - List of associated Benchmark Jobs.
- `additional_info` _dict_ - Any additional information to be saved with the Benchmark.

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text,
             dataset_list: List[Dataset],
             model_list: List[Model],
             metric_list: List[Metric],
             job_list: List[BenchmarkJob],
             description: Text = "",
             supplier: Text = "aiXplain",
             version: Text = "1.0",
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/benchmark.py#L46)

Create a Benchmark with the necessary information.

**Arguments**:

- `id` _Text_ - ID of the Benchmark.
- `name` _Text_ - Name of the Benchmark.
- `dataset_list` _List[Dataset]_ - List of Datasets to be used for benchmarking.
- `model_list` _List[Model]_ - List of Models to be used for benchmarking.
- `metric_list` _List[Metric]_ - List of Metrics to be used for benchmarking.
- `job_list` _List[BenchmarkJob]_ - List of associated Benchmark Jobs.
- `description` _Text, optional_ - Description of the Benchmark. Defaults to &quot;&quot;.
- `supplier` _Text, optional_ - Author of the Benchmark. Defaults to &quot;aiXplain&quot;.
- `version` _Text, optional_ - Benchmark version. Defaults to &quot;1.0&quot;.
- `**additional_info` - Any additional Benchmark info to be saved.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/benchmark.py#L83)

Return a string representation of the Benchmark instance.

**Returns**:

- `str` - A string in the format &quot;&lt;Benchmark name&gt;&quot;.

#### start

```python
def start() -> BenchmarkJob
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/benchmark.py#L91)

Start a new benchmark job (run) for the current benchmark.

This method initiates a new benchmark job using the configured models,
datasets, and metrics. It communicates with the backend API to create
and start the job.

**Returns**:

- `BenchmarkJob` - A new BenchmarkJob instance representing the started job.
  Returns None if the job creation fails.
  

**Raises**:

- `Exception` - If there&#x27;s an error creating or starting the benchmark job.
  The error is logged and None is returned.

