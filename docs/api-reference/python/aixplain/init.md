---
sidebar_label: aixplain
title: aixplain
---

aiXplain SDK Library.

aiXplain SDK enables python programmers to add AI functions
to their software.

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

#### \_\_getattr\_\_

```python
def __getattr__(name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/__init__.py#L65)

Lazily construct the deprecated module-level ``aixplain_v2`` client.

Constructing it at import time and swallowing the failure left a public
symbol bound to ``None``, so a missing credential surfaced much later as
``AttributeError: &#x27;NoneType&#x27; object has no attribute &#x27;Agent&#x27;`` instead of the
actionable message ``Aixplain()`` already raises (BUG-946). Deferring the
construction to first access keeps ``import aixplain`` working without a key
-- which ``aixplain --help`` and unit-test collection rely on -- while
letting the real error reach whoever actually asks for the client.

**Arguments**:

- ``2 _str_ - Attribute being looked up on the package.
  

**Returns**:

- ``3 - The lazily constructed client, cached in module globals.
  

**Raises**:

- ``4 - If ``name`` is anything other than ``aixplain_v2``.

#### \_\_dir\_\_

```python
def __dir__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/__init__.py#L98)

Keep the lazily provided ``aixplain_v2`` discoverable via ``dir()``.

