---
sidebar_label: benchmark_job
title: aixplain.modules.benchmark_job
---

### BenchmarkJob Objects

```python
class BenchmarkJob()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/benchmark_job.py#L12)

Benchmark Job Represents a single run of an already created Benchmark.

**Attributes**:

- `id` _str_ - ID of the Benchmark Job.
- `status` _str_ - Status of the Benchmark Job.
- `benchmark_id` _str_ - ID of the associated parent Benchmark.
- `additional_info` _dict_ - Any additional information to be saved with the Benchmark Job.

#### \_\_init\_\_

```python
def __init__(id: Text, status: Text, benchmark_id: Text,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/benchmark_job.py#L23)

Create a Benchmark Job with the necessary information. Each Job is a run of a parent Benchmark

**Arguments**:

- `id` _Text_ - ID of the Benchmark Job
- `status` _Text_ - Status of the Benchmark Job
- `benchmark_id` _Text_ - ID of the associated parent Benchmark
- `**additional_info` - Any additional Benchmark Job info to be saved

#### check\_status

```python
def check_status() -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/benchmark_job.py#L81)

Check the current status of the benchmark job.

Fetches the latest status from the API and updates the local state.

**Returns**:

- `Text` - The current status of the benchmark job.

#### download\_results\_as\_csv

```python
def download_results_as_csv(save_path: Optional[Text] = None,
                            return_dataframe: bool = False)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/benchmark_job.py#L93)

Get the results of the benchmark job in a CSV format.
The results can either be downloaded locally or returned in the form of pandas.DataFrame.


**Arguments**:

- `save_path` _Text, optional_ - Path to save the CSV if return_dataframe is False. If None, a ranmdom path is generated. defaults to None.
- `return_dataframe` _bool_ - If True, the result is returned as pandas.DataFrame else saved as a CSV file. defaults to False.
  

**Returns**:

- `str/pandas.DataFrame` - results as path of locally saved file if return_dataframe is False else as a pandas dataframe

#### get\_scores

```python
def get_scores(
        return_simplified: bool = True,
        return_as_dataframe: bool = True) -> Union[Dict, pd.DataFrame, list]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/benchmark_job.py#L149)

Get the benchmark scores for all models.

**Arguments**:

- `return_simplified` _bool, optional_ - If True, returns a simplified version of scores.
  Defaults to True.
- `return_as_dataframe` _bool, optional_ - If True and return_simplified is True,
  returns results as a pandas DataFrame. Defaults to True.
  

**Returns**:

  Union[Dict, pd.DataFrame, list]: The benchmark scores in the requested format.
  - If return_simplified=False: Returns a dictionary with detailed model scores
  - If return_simplified=True and return_as_dataframe=True: Returns a pandas DataFrame
  - If return_simplified=True and return_as_dataframe=False: Returns a list of dictionaries
  

**Raises**:

- `Exception` - If there&#x27;s an error fetching or processing the scores.

#### get\_failuire\_rate

```python
def get_failuire_rate(
        return_as_dataframe: bool = True) -> Union[Dict, pd.DataFrame]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/benchmark_job.py#L197)

Calculate the failure rate for each model in the benchmark.

**Arguments**:

- `return_as_dataframe` _bool, optional_ - If True, returns results as a pandas DataFrame.
  Defaults to True.
  

**Returns**:

  Union[Dict, pd.DataFrame]: The failure rates for each model.
  - If return_as_dataframe=True: Returns a DataFrame with &#x27;Model&#x27; and &#x27;Failure Rate&#x27; columns
  - If return_as_dataframe=False: Returns a dictionary with model IDs as keys and failure rates as values
  

**Raises**:

- `Exception` - If there&#x27;s an error calculating the failure rates.

#### get\_all\_explanations

```python
def get_all_explanations() -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/benchmark_job.py#L236)

Get all explanations for the benchmark results.

**Returns**:

- `Dict` - A dictionary containing both metric-dependent and metric-independent explanations.
  The dictionary has two keys:
  - &#x27;metricInDependent&#x27;: List of metric-independent explanations
  - &#x27;metricDependent&#x27;: List of metric-dependent explanations
  

**Raises**:

- `Exception` - If there&#x27;s an error fetching the explanations.

#### get\_localized\_explanations

```python
def get_localized_explanations(metric_dependant: bool,
                               group_by_task: bool = False) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/benchmark_job.py#L261)

Get localized explanations for the benchmark results.

**Arguments**:

- `metric_dependant` _bool_ - If True, returns metric-dependent explanations.
  If False, returns metric-independent explanations.
- `group_by_task` _bool, optional_ - If True and metric_dependant is True,
  groups explanations by task. Defaults to False.
  

**Returns**:

- `Dict` - A dictionary containing the localized explanations.
  The structure depends on the input parameters:
  - If metric_dependant=False: Returns metric-independent explanations
  - If metric_dependant=True and group_by_task=False: Returns explanations grouped by score ID
  - If metric_dependant=True and group_by_task=True: Returns explanations grouped by task
  

**Raises**:

- `Exception` - If there&#x27;s an error fetching or processing the explanations.

