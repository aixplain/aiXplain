---
sidebar_label: metric
title: aixplain.modules.metric
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
    Metric Class

### Metric Objects

```python
class Metric(Asset)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/metric.py#L28)

A class representing a metric for evaluating machine learning model outputs.

This class extends Asset to provide functionality for computing evaluation metrics
on one or more pieces of data. Each metric is typically associated with a specific
machine learning task and can require different inputs (e.g., reference text for
translation metrics).

**Attributes**:

- `id` _Text_ - ID of the metric.
- `name` _Text_ - Name of the metric.
- `supplier` _Text_ - Author/provider of the metric.
- `is_reference_required` _bool_ - Whether the metric requires reference data.
- `is_source_required` _bool_ - Whether the metric requires source data.
- `cost` _float_ - Cost per metric computation.
- `function` _Text_ - The function identifier for this metric.
- `normalization_options` _list_ - List of available normalization options.
- `description` _Text_ - Description of the metric.
- `version` _Text_ - Version of the metric implementation.
- `name`0 _dict_ - Additional metric-specific information.

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text,
             supplier: Text,
             is_reference_required: bool,
             is_source_required: bool,
             cost: float,
             function: Text,
             normalization_options: list = [],
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/metric.py#L50)

Initialize a new Metric instance.

**Arguments**:

- `id` _Text_ - ID of the metric.
- `name` _Text_ - Name of the metric.
- `supplier` _Text_ - Author/provider of the metric.
- `is_reference_required` _bool_ - Whether the metric requires reference data for computation.
- `is_source_required` _bool_ - Whether the metric requires source data for computation.
- `cost` _float_ - Cost per metric computation.
- `function` _Text_ - The function identifier for this metric.
- `normalization_options` _list, optional_ - List of available normalization options.
  Defaults to empty list.
- `**additional_info` - Additional metric-specific information to be stored.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/metric.py#L83)

Return a string representation of the Metric instance.

**Returns**:

- `str` - A string in the format &quot;&lt;Metric name&gt;&quot;.

#### add\_normalization\_options

```python
def add_normalization_options(normalization_options: List[str]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/metric.py#L91)

Add normalization options to be used during metric computation.

This method appends new normalization options to the existing list of options.
These options can be used to normalize inputs or outputs during benchmarking.

**Arguments**:

- `normalization_options` _List[str]_ - List of normalization options to add.
  Each option should be a valid normalization identifier.

#### run

```python
def run(hypothesis: Optional[Union[str, List[str]]] = None,
        source: Optional[Union[str, List[str]]] = None,
        reference: Optional[Union[str, List[str]]] = None) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/metric.py#L103)

Run the metric to calculate scores for the provided inputs.

This method computes metric scores based on the provided hypothesis, and optionally
source and reference data. The inputs can be either single strings or lists of strings.

**Arguments**:

- `hypothesis` _Optional[Union[str, List[str]]], optional_ - The hypothesis/output to evaluate.
  Can be a single string or a list of strings. Defaults to None.
- `source` _Optional[Union[str, List[str]]], optional_ - The source data for evaluation.
  Only used if is_source_required is True. Can be a single string or a list
  of strings. Defaults to None.
- `reference` _Optional[Union[str, List[str]]], optional_ - The reference data for evaluation.
  Only used if is_reference_required is True. Can be a single string or a list
  of strings. Defaults to None.
  

**Returns**:

- `dict` - A dictionary containing the computed metric scores and any additional
  computation metadata.
  

**Notes**:

  The method automatically handles conversion of single strings to lists and
  proper formatting of references for multi-reference scenarios.

