---
sidebar_label: pipeline
title: aixplain.v2.pipeline
---

### PipelineListParams Objects

```python
class PipelineListParams(BareListParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/pipeline.py#L18)

Parameters for listing pipelines.

**Attributes**:

- `functions` - Union[Function, List[Function]]: The functions of the pipeline.
- `suppliers` - Union[Supplier, List[Supplier]]: The suppliers of the pipeline.
- `models` - Union[Model, List[Model]]: The models of the pipeline.
- `input_data_types` - Union[DataType, List[DataType]]: The input data types of the pipeline.
- `output_data_types` - Union[DataType, List[DataType]]: The output data types of the pipeline.
- `drafts_only` - bool: Whether to list only drafts.

### Pipeline Objects

```python
class Pipeline(BaseResource, ListResourceMixin[PipelineListParams, "Pipeline"],
               GetResourceMixin[BareGetParams, "Pipeline"],
               CreateResourceMixin[PipelineCreateParams, "Pipeline"])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/pipeline.py#L44)

Resource for pipelines.

**Attributes**:

- `RESOURCE_PATH` - str: The resource path.

