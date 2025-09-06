---
sidebar_label: model_response_streamer
title: aixplain.modules.model.model_response_streamer
---

### ModelResponseStreamer Objects

```python
class ModelResponseStreamer()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/model_response_streamer.py#L7)

A class representing a streamer for model responses.

This class provides an iterator interface for streaming model responses.
It handles the conversion of JSON-like strings into ModelResponse objects
and manages the response status.

#### \_\_init\_\_

```python
def __init__(iterator: Iterator)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/model_response_streamer.py#L15)

Initialize a new ModelResponseStreamer instance.

**Arguments**:

- `iterator` _Iterator_ - An iterator that yields JSON-like strings.

#### \_\_next\_\_

```python
def __next__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/model_response_streamer.py#L24)

Return the next chunk of the response.

**Returns**:

- `ModelResponse` - A ModelResponse object containing the next chunk of the response.

#### \_\_iter\_\_

```python
def __iter__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/model_response_streamer.py#L41)

Return the iterator for the ModelResponseStreamer.

**Returns**:

- `Iterator` - The iterator for the ModelResponseStreamer.

