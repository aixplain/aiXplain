---
sidebar_label: rlm
title: aixplain.v1.modules.model.rlm
---

RLM (Recursive Language Model) module for aiXplain SDK v1.

#### \_\_author\_\_

Copyright 2026 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: aiXplain Team
Description:
    RLM (Recursive Language Model) — orchestrates long-context analysis via
    an iterative REPL sandbox. The orchestrator model plans and writes Python
    code to chunk and explore a large context; a worker model handles per-chunk
    analysis via llm_query() calls injected into the sandbox session.

### RLM Objects

```python
class RLM(Model)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L157)

Recursive Language Model — long-context analysis via an iterative REPL sandbox.

RLM wraps two aiXplain models:

- An **orchestrator** (powerful, expensive): plans and writes Python code to
explore the context iteratively in a managed sandbox environment.
- A **worker** (fast, cheap): called via ``llm_query()`` inside the sandbox
to perform focused analysis on individual context chunks.

The sandbox is an aiXplain managed Python execution environment. Each
``run()`` call gets its own isolated session (UUID), so variables persist
across REPL iterations within a single run but are cleaned up afterwards.

Example usage::

from aixplain.factories import ModelFactory

rlm = ModelFactory.create_rlm(
orchestrator_model_id=&quot;&lt;orchestrator-model-id&gt;&quot;,
worker_model_id=&quot;&lt;worker-model-id&gt;&quot;,
)
response = rlm.run(data=\{
&quot;context&quot;: very_long_document,
&quot;query&quot;: &quot;What are the key findings?&quot;,
})
print(response.data)
print(f&quot;Completed in \{response[&#x27;iterations_used&#x27;]} iterations.&quot;)

**Attributes**:

- `orchestrator` _Model_ - Root LLM that plans and writes REPL code.
- `worker` _Model_ - Sub-LLM used inside the sandbox via ``llm_query()``.
- `max_iterations` _int_ - Maximum orchestrator loop iterations before a
  forced final answer is requested.

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text = "RLM",
             description:
             Text = "Recursive Language Model for long-context analysis.",
             orchestrator: Optional[Model] = None,
             worker: Optional[Model] = None,
             max_iterations: int = 10,
             api_key: Optional[Text] = None,
             supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L196)

Initialize a new RLM instance.

**Arguments**:

- `id` _Text_ - Identifier for this RLM instance.
- `name` _Text, optional_ - Display name. Defaults to &quot;RLM&quot;.
- `description` _Text, optional_ - Description. Defaults to a generic string.
- `orchestrator` _Model, optional_ - Root LLM that drives the REPL loop.
  Must be set before calling ``run()``. Defaults to None.
- `worker` _Model, optional_ - Sub-LLM called inside the sandbox via
  ``llm_query()``. Must be set before calling ``run()``. Defaults to None.
- `name`1 _int, optional_ - Maximum orchestrator iterations.
  Defaults to 10.
- `name`2 _Text, optional_ - API key. Defaults to ``config.TEAM_API_KEY``.
- `name`5 _Union[Dict, Text, Supplier, int], optional_ - Supplier.
  Defaults to &quot;aiXplain&quot;.
- `name`6 - Additional metadata stored on the instance.

#### run

```python
def run(data: Union[Text, Dict],
        name: Text = "rlm_process",
        timeout: float = 600,
        parameters: Optional[Dict] = None,
        wait_time: float = 0.5,
        stream: bool = False) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L583)

Run the RLM orchestration loop over a (potentially large) context.

A fresh sandbox session is created for each call. The orchestrator is
called iteratively; each iteration it may execute code blocks in the
sandbox (with outputs fed back into the conversation) and eventually
declare a final answer via ``FINAL(...)`` or ``FINAL_VAR(...)``.

**Arguments**:

- `data` _Union[Text, Dict]_ - Input data. Accepted formats:
  
  - ``str`` (raw text): Treated directly as the context content;
  a default query is used.
  - ``str`` (HTTP/HTTPS URL): Content is downloaded automatically.
  ``.json`` URLs or ``application/json`` responses are parsed into
  a dict/list; all other content is decoded as plain text.
  - ``str`` (file path): If the string points to an existing file,
  the file is read automatically. ``.json`` files are parsed into
  a dict/list; all other text formats are read as a plain string.
  - ``pathlib.Path``: Resolved and read exactly like a file-path string.
  - ``dict``: Must contain ``&quot;context&quot;`` (required) and optionally
  ``&quot;query&quot;`` (defaults to a generic analysis prompt). The value
  of ``&quot;context&quot;`` itself may also be a URL, a file path, or a
  ``pathlib.Path`` — it will be resolved the same way.
  
- ``9 _Text, optional_ - Identifier used in log messages.
  Defaults to ``&quot;rlm_process&quot;``.
- ``2 _float, optional_ - Maximum total wall-clock time in seconds.
  Defaults to 600.
- ``3 _Optional[Dict], optional_ - Reserved for future use.
- ``4 _float, optional_ - Kept for API compatibility. Unused.
- ``5 _bool, optional_ - Unsupported. Must be False.
  

**Returns**:

- ``6 - Standard response with:
  
  - ``data``: The final answer string.
  - ``completed``: True on success.
  - ``run_time``: Total elapsed seconds.
  - ``used_credits``: Total credits consumed across all
  orchestrator calls, sandbox executions, and worker
  ``llm_query()`` invocations.
  - ``iterations_used``: Number of orchestrator iterations (via
  ``response[&quot;iterations_used&quot;]``).
  

**Raises**:

- ``1 - If ``orchestrator`` or ``worker`` models are not set,
  or if ``stream=True``.
- ``8 - If ``data`` is a dict missing the ``&quot;context&quot;`` key,
  or an unsupported type.

#### run\_async

```python
def run_async(data: Union[Text, Dict],
              name: Text = "rlm_process",
              parameters: Optional[Dict] = None) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L764)

Not supported for RLM.

**Raises**:

- `NotImplementedError` - Always. Use ``run()`` instead.

#### run\_stream

```python
def run_stream(data: Union[Text, Dict], parameters: Optional[Dict] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L777)

Not supported for RLM.

**Raises**:

- `NotImplementedError` - Always.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict) -> "RLM"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L786)

Create an RLM instance from a dictionary representation.

Reconstructs the RLM from a dict produced by ``to_dict()``. The
orchestrator and worker models are fetched from the aiXplain platform
using their stored IDs, so a valid API key and network access are
required.

**Arguments**:

- `data` _Dict_ - Dictionary as produced by ``to_dict()``, containing:
  - id: RLM instance identifier.
  - name: Display name.
  - description: Description string.
  - api_key: API key for authentication.
  - supplier: Supplier information.
  - orchestrator_model_id: ID of the orchestrator model.
  - worker_model_id: ID of the worker model.
  - max_iterations: Maximum orchestrator loop iterations.
  - additional_info: Extra metadata (optional).
  

**Returns**:

- `RLM` - A fully configured RLM instance with orchestrator and worker
  models loaded, ready to call ``run()``.
  

**Raises**:

- `Exception` - If either model ID cannot be fetched from the platform.

#### to\_dict

```python
def to_dict() -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L836)

Convert the RLM instance to a dictionary representation.

Extends the base ``Model.to_dict()`` with RLM-specific fields:
orchestrator model ID, worker model ID, and max_iterations.
The orchestrator and worker are stored as their model IDs (not full
objects) so the dict is JSON-serializable and can be used to
reconstruct the instance via ``ModelFactory.create_rlm()``.

**Returns**:

- `Dict` - A dictionary containing all base model fields plus:
  - orchestrator_model_id: ID of the orchestrator model.
  - worker_model_id: ID of the worker model.
  - max_iterations: Maximum orchestrator loop iterations.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L857)

Return a string representation of this RLM instance.

