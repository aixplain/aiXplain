---
sidebar_label: core
title: aixplain.v2.core
---

Core module for aiXplain v2 API.

### Aixplain Objects

```python
class Aixplain()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L39)

Main class for the Aixplain API.

**Attributes**:

- `_instance` - Aixplain: The unique instance of the Aixplain class.
- `api_key` - str: The API key for the Aixplain API.
- `base_url` - str: The URL for the backend.
- `pipeline_url` - str: The URL for the pipeline.
- `model_url` - str: The URL for the model.
- `client` - AixplainClient: The client for the Aixplain API.
- `Model` - type: The model class.
- `Pipeline` - type: The pipeline class.
- `Agent` - type: The agent class.
- `Benchmark` - type: The benchmark class.
- `api_key`0 - type: The benchmark job class.

#### \_\_new\_\_

```python
def __new__(cls, *args, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L102)

Singleton pattern for the Aixplain class.

Otherwise, the environment variables will be overwritten in multiple instances.

TODO: This should be removed once the factory classes are removed.

#### \_\_init\_\_

```python
def __init__(api_key: str = None,
             backend_url: str = None,
             pipeline_url: str = None,
             model_url: str = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L114)

Initialize the Aixplain class.

**Arguments**:

- `api_key` - str: The API key for the Aixplain API.
- `backend_url` - str: The URL for the backend.
- `pipeline_url` - str: The URL for the pipeline.
- `model_url` - str: The URL for the model.

#### init\_client

```python
def init_client()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L148)

Initialize the client.

#### init\_env

```python
def init_env()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L155)

Initialize the environment variables.

This is required for the legacy use of the factory classes.

#### init\_resources

```python
def init_resources()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L165)

Initialize the resources.

We&#x27;re dynamically creating the classes here to avoid potential race
conditions when using class level attributes

