---
sidebar_label: model_with_params
title: aixplain.modules.agent.model_with_params
---

A generic class that wraps a model with extra parameters.

This is an abstract base class that must be extended by specific model wrappers.

Example usage:

class MyModel(ModelWithParams):
    model_id: Text = &quot;my_model&quot;
    extra_param: int = 10

    @field_validator(&quot;extra_param&quot;)
    def validate_extra_param(cls, v: int) -&gt; int:
        if v &lt; 0:
            raise ValueError(&quot;Extra parameter must be positive&quot;)
        return v

### ModelWithParams Objects

```python
class ModelWithParams(BaseModel, ABC)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/model_with_params.py#L25)

A generic class that wraps a model with extra parameters.

The extra parameters are not part of the model&#x27;s input/output parameters.
This is an abstract base class that must be extended by specific model wrappers.

**Attributes**:

- `model_id` - The ID of the model to wrap.

#### validate\_model\_id

```python
@field_validator("model_id")
def validate_model_id(cls, v: Text) -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/model_with_params.py#L43)

Validate the model_id field.

This validator ensures that the model_id is not empty or whitespace-only.

**Arguments**:

- `cls` - The class (automatically provided by pydantic).
- `v` _Text_ - The value to validate.
  

**Returns**:

- `Text` - The validated model ID.
  

**Raises**:

- `ValueError` - If the model ID is empty or contains only whitespace.

#### \_\_new\_\_

```python
def __new__(cls, *args, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/model_with_params.py#L62)

Create a new instance of a ModelWithParams subclass.

This method prevents direct instantiation of the abstract base class while
allowing subclasses to be instantiated normally.

**Arguments**:

- `cls` - The class being instantiated.
- `*args` - Positional arguments for instance creation.
- `**kwargs` - Keyword arguments for instance creation.
  

**Returns**:

- `ModelWithParams` - A new instance of a ModelWithParams subclass.
  

**Raises**:

- `TypeError` - If attempting to instantiate ModelWithParams directly.

