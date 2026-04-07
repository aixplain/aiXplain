---
sidebar_label: core
title: aixplain.v2.core
---

Core module for aiXplain v2 API.

### Aixplain Objects

```python
class Aixplain()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L33)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L78)

Initialize the Aixplain class.

**Arguments**:

- `api_key` _str, optional_ - The API key. Falls back to TEAM_API_KEY or AIXPLAIN_API_KEY env var.
- `backend_url` _str, optional_ - The backend URL. Falls back to BACKEND_URL env var.
- `pipeline_url` _str, optional_ - The pipeline execution URL. Falls back to PIPELINES_RUN_URL env var.
- `model_url` _str, optional_ - The model execution URL. Falls back to MODELS_RUN_URL env var.

#### init\_client

```python
def init_client() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L113)

Initialize the client.

#### init\_resources

```python
def init_resources() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/core.py#L120)

Initialize the resources.

We&#x27;re dynamically creating the classes here to avoid potential race
conditions when using class level attributes

