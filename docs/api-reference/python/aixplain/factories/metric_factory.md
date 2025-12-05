---
sidebar_label: metric_factory
title: aixplain.factories.metric_factory
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
Date: December 1st 2022
Description:
    Metric Factory Class

### MetricFactory Objects

```python
class MetricFactory()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/metric_factory.py#L33)

A static factory class for creating and managing Metric objects.

This class provides functionality to create, retrieve, and list Metric objects
through the backend API. It includes methods for fetching individual metrics
by ID and listing metrics with various filtering options.

**Attributes**:

- `backend_url` _str_ - The URL endpoint for the backend API.

#### get

```python
@classmethod
def get(cls, metric_id: Text) -> Metric
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/metric_factory.py#L67)

Create a Metric object from a metric ID.

**Arguments**:

- `metric_id` _Text_ - The unique identifier of the metric to retrieve.
  

**Returns**:

- `Metric` - The retrieved Metric object.
  

**Raises**:

- `Exception` - If the metric creation fails, with status code and error message.

#### list

```python
@classmethod
def list(cls,
         model_id: Text = None,
         is_source_required: Optional[bool] = None,
         is_reference_required: Optional[bool] = None,
         page_number: int = 0,
         page_size: int = 20) -> List[Metric]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/metric_factory.py#L100)

Get a list of supported metrics based on the given filters.

**Arguments**:

- `model_id` _Text, optional_ - ID of model for which metrics are to be used. Defaults to None.
- `is_source_required` _bool, optional_ - Filter metrics that require source input. Defaults to None.
- `is_reference_required` _bool, optional_ - Filter metrics that require reference input. Defaults to None.
- `page_number` _int, optional_ - Page number for pagination. Defaults to 0.
- `page_size` _int, optional_ - Number of items per page. Defaults to 20.
  

**Returns**:

- `Dict` - A dictionary containing:
  - results (List[Metric]): List of filtered metrics
  - page_total (int): Number of items in the current page
  - page_number (int): Current page number
  - total (int): Total number of items matching the filters
  

**Raises**:

- `Exception` - If there is an error retrieving the metrics list.

