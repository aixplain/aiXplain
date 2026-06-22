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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L378)

Recursive Language Model — long-context analysis with two execution modes.

RLM wraps two aiXplain models:

- An **orchestrator** (powerful, expensive): plans and writes Python code to
explore the context iteratively in a managed sandbox environment.
Used by ``mode=&quot;recursive&quot;``.
- A **worker** (fast, cheap): called per chunk in both modes. In recursive
mode it&#x27;s invoked via ``llm_query()`` inside the sandbox; in parallel
mode it&#x27;s called directly, concurrently across chunks.

Three run modes are available via the ``mode`` argument to ``run()``:

- ``&quot;parallel&quot;`` (cheap, fast, deterministic): chunk the context to a
comfortable fraction of the worker&#x27;s window (to mitigate context rot),
call the worker in parallel on every chunk, then reduce the partial
answers into a final answer. No orchestrator, no sandbox. Best for
summarize/extract queries.
- ``&quot;rag&quot;`` (cheapest at query time): chunk the context into small
retrieval-grade pieces, upsert them into an aIR vector index, retrieve
the top-k most relevant chunks for the query, then make a single worker
call to synthesize an answer. The win is amortizing the upfront index
build across many queries: set ``rag_index_id`` to reuse a pre-built
index and skip create + upsert + delete on each call. Best for
needle-in-haystack questions on very large contexts.
- ``&quot;recursive&quot;`` (adaptive, expensive): the original iterative REPL loop
where the orchestrator drives chunking and analysis. Best for multi-hop
reasoning or queries that need to compare information across chunks.
- ``&quot;auto&quot;`` (default): picks ``&quot;recursive&quot;`` if the query reads like
multi-hop reasoning (e.g., contains words like &quot;compare across&quot;,
&quot;inconsistencies&quot;, &quot;verify against&quot;); otherwise ``&quot;parallel&quot;``.
``&quot;rag&quot;`` is opt-in only — auto never picks it because it only beats
``parallel`` when the index is reused across many calls.

The recursive mode&#x27;s sandbox is an aiXplain managed Python execution
environment. Each recursive ``run()`` call gets its own isolated session
(UUID), so variables persist across REPL iterations within a single run
but are cleaned up afterwards.

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

- ``8 _Model_ - Root LLM that plans and writes REPL code.
- ``9 _Model_ - Sub-LLM used inside the sandbox via ``llm_query()``.
- ``2 _int_ - Maximum orchestrator loop iterations before a
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
             rag_index_id: Optional[Text] = None,
             rag_top_k: int = _RAG_DEFAULT_TOP_K,
             rag_max_chunk_chars: int = _RAG_DEFAULT_MAX_CHUNK_CHARS,
             **additional_info) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L443)

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
- `name`6 _Text, optional_ - ID of a pre-built aIR index for
  ``mode=&quot;rag&quot;``. When set, the index is reused (skipping
  create + upsert + delete on each ``run()``). When ``None``,
  an ephemeral index is created per RAG run and deleted
  afterwards. Defaults to ``None``.
- `description`5 _int, optional_ - Number of chunks retrieved from the
  aIR index per query in ``mode=&quot;rag&quot;``. Defaults to 10.
- `description`8 _int, optional_ - Upper bound on a single RAG
  chunk (chars), to stay under the embedding model&#x27;s input
  limit. Default ~30K chars is a generic middle ground that
  fits 8K-token models (ada-002, text-embedding-3, BGE-M3).
  Tune down for 512-token models (multilingual-E5, Jina CLIP)
  or up when the backing model supports it. Defaults to 30000.
- `description`9 - Additional metadata stored on the instance.

#### run

```python
def run(data: Union[Text, Dict],
        name: Text = "rlm_process",
        timeout: float = 600,
        parameters: Optional[Dict] = None,
        wait_time: float = 0.5,
        stream: bool = False,
        mode: Text = "auto") -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L1177)

Run the RLM over a (potentially large) context, dispatching by mode.

``mode`` selects the execution strategy:

- ``&quot;parallel&quot;``: deterministic chunk + parallel worker calls + reduce.
Cheap, fast, predictable. No orchestrator or sandbox needed. Best for
summarize/extract queries. Chunks are sized to a comfortable fraction
of the worker&#x27;s window to mitigate context rot.
- ``&quot;rag&quot;``: chunk + upsert to an aIR vector index + top-k retrieve +
single worker synthesis. If ``self.rag_index_id`` is set, the index
is reused (cheapest path); otherwise a temporary index is created
and deleted per run. Best for needle-in-haystack queries on very
large reusable contexts.
- ``&quot;recursive&quot;``: the iterative REPL loop where the orchestrator drives
chunking and analysis in a sandbox. Expensive but adaptive. Best for
multi-hop reasoning that needs to compare information across chunks.
- ``&quot;auto&quot;`` (default): picks ``&quot;recursive&quot;`` when the query reads like
multi-hop reasoning (keywords such as &quot;compare across&quot;,
&quot;inconsistencies&quot;, &quot;verify against&quot;, &quot;step by step&quot;); otherwise
``&quot;parallel&quot;``. ``&quot;rag&quot;`` is opt-in only.

**Arguments**:

- ``8 _Union[Text, Dict]_ - Input data. Accepted formats:
  
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
  
- ``3 _Text, optional_ - Identifier used in log messages.
  Defaults to ``&quot;rlm_process&quot;``.
- ``6 _float, optional_ - Maximum total wall-clock time in seconds.
  Applies to ``&quot;recursive&quot;`` mode only. Defaults to 600.
- ``9 _Optional[Dict], optional_ - Reserved for future use.
- ``0 _float, optional_ - Kept for API compatibility. Unused.
- ``1 _bool, optional_ - Unsupported. Must be False.
- ``2 _Text, optional_ - ``&quot;auto&quot;``, ``&quot;parallel&quot;``, or
  ``&quot;recursive&quot;``. Defaults to ``&quot;auto&quot;``.
  

**Returns**:

- ``1 - Standard response with:
  
  - ``data``: The final answer string.
  - ``completed``: True on success.
  - ``run_time``: Total elapsed seconds.
  - ``used_credits``: Total credits consumed across all model calls.
  - ``iterations_used``: Recursive mode → orchestrator iterations.
  Parallel mode → worker calls made in the map step
  (i.e. number of chunks), or 1 for the single-call fast path.
  

**Raises**:

- ``2 - If ``worker`` is not set, ``stream=True``, or
  ``mode`` is invalid. ``recursive`` mode additionally requires
  ``orchestrator`` to be set.
- ``3 - If ``data`` is a dict missing the ``&quot;context&quot;`` key,
  or an unsupported type.

#### run\_async

```python
def run_async(data: Union[Text, Dict],
              name: Text = "rlm_process",
              parameters: Optional[Dict] = None) -> ModelResponse
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L1404)

Not supported for RLM.

**Raises**:

- `NotImplementedError` - Always. Use ``run()`` instead.

#### run\_stream

```python
def run_stream(data: Union[Text, Dict], parameters: Optional[Dict] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L1417)

Not supported for RLM.

**Raises**:

- `NotImplementedError` - Always.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict) -> "RLM"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L1426)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L1476)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v1/modules/model/rlm.py#L1497)

Return a string representation of this RLM instance.

