---
sidebar_label: metric
title: aixplain.v2.metric
---

### MetricListParams Objects

```python
class MetricListParams(BaseListParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/metric.py#L13)

Parameters for listing metrics.

**Attributes**:

- `model_id` - str: The model ID.
- `is_source_required` - bool: Whether the source is required.
- `is_reference_required` - bool: Whether the reference is required.

### Metric Objects

```python
class Metric(BaseResource, ListResourceMixin[MetricListParams, "Metric"],
             GetResourceMixin[BareGetParams, "Metric"])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/metric.py#L27)

Resource for metrics.

