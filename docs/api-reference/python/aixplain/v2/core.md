---
sidebar_label: core
title: aixplain.v2.core
---

Core module for aiXplain v2 API.

### Aixplain Objects

```python
class Aixplain()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L26)

Main class for the Aixplain API.

This class can be instantiated multiple times with different API keys,
allowing for multi-instance usage with different authentication contexts.

#### \_\_init\_\_

```python
def __init__(api_key: Optional[str] = None,
             backend_url: Optional[str] = None,
             pipeline_url: Optional[str] = None,
             model_url: Optional[str] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L70)

Initialize the Aixplain class.

**Arguments**:

- `api_key` - str: The API key for the Aixplain API.
- `backend_url` - str: The URL for the backend.
- `pipeline_url` - str: The URL for the pipeline.
- `model_url` - str: The URL for the model.

#### init\_client

```python
def init_client() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L100)

Initialize the client.

#### init\_resources

```python
def init_resources() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L107)

Initialize the resources.

We&#x27;re dynamically creating the classes here to avoid potential race
conditions when using class level attributes

