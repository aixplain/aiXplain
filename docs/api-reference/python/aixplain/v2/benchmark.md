---
sidebar_label: benchmark
title: aixplain.v2.benchmark
---

### BenchmarkCreateParams Objects

```python
class BenchmarkCreateParams(BareCreateParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/benchmark.py#L18)

Parameters for creating a benchmark.

**Attributes**:

- `name` - str: The name of the benchmark.
- `dataset_list` - List[&quot;Dataset&quot;]: The list of datasets.
- `model_list` - List[&quot;Model&quot;]: The list of models.
- `metric_list` - List[&quot;Metric&quot;]: The list of metrics.

### Benchmark Objects

```python
class Benchmark(BaseResource, GetResourceMixin[BareGetParams, "Benchmark"],
                CreateResourceMixin[BenchmarkCreateParams, "Benchmark"])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/benchmark.py#L34)

Resource for benchmarks.

#### list\_normalization\_options

```python
@classmethod
def list_normalization_options(cls, metric: "Metric",
                               model: "Model") -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/benchmark.py#L56)

List the normalization options for a metric and a model.

**Arguments**:

- `metric` - &quot;Metric&quot;: The metric.
- `model` - &quot;Model&quot;: The model.
  

**Returns**:

- `List[str]` - The list of normalization options.

### BenchmarkJob Objects

```python
class BenchmarkJob(BaseResource, GetResourceMixin[BareGetParams,
                                                  "BenchmarkJob"])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/benchmark.py#L72)

Resource for benchmark jobs.

#### get\_scores

```python
def get_scores() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/benchmark.py#L86)

Get the scores for a benchmark job.

**Returns**:

- `dict` - The scores.

