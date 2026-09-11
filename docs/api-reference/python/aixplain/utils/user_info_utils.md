---
sidebar_label: user_info_utils
title: aixplain.utils.user_info_utils
---

Client-side run metadata attached to agent execution payloads.

Agent runs carry a ``metaData`` object built by :func:`build_run_metadata`. It
reports the caller&#x27;s environment to the aiXplain backend so runs can be
locale-aware: ``region``, ``language`` and ``timezone``, plus the public
``ipAddress`` and city-level ``latitude`` / ``longitude`` they are derived from.

Those values come from a single ``https://ipinfo.io/json`` request made from the
machine running the SDK, cached once per process and skipped silently on failure.
See ``docs/run-metadata.md`` for the user-facing disclosure: every field, why it
is collected, which call sites send it, and what happens when the lookup is
blocked.

Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

#### build\_run\_metadata

```python
def build_run_metadata() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/user_info_utils.py#L105)

Build the ``metaData`` object sent with agent run payloads.

The returned dict is forwarded verbatim to the backend by the direct v2 agent
run path (:meth:`aixplain.v2.agent.Agent.build_run_payload`) and by the legacy
v1 agent / team-agent run and session-bootstrap paths. v2 runs routed through
a session post to ``/v1/sessions/\{id}/messages`` instead and carry no
``metaData``. It is derived from one cached ``https://ipinfo.io/json`` lookup
(see :func:`_fetch_ipinfo`).

Keys, all present on every call:

* ``userAgent`` — always ``&quot;sdk&quot;``, marking the traffic as SDK-originated.
* ``region`` / ``language`` — locale derived from the lookup&#x27;s country code,
used for locale-aware agent execution.
* ``ipAddress`` — the SDK host&#x27;s public IP address.
* ``latitude`` / ``longitude`` — city-level coordinates for that IP.
* ``timezone`` — IANA timezone name for that IP.

Every key except ``userAgent`` is ``None`` when the lookup failed, was blocked
or omitted the underlying field; a run is never blocked by it.
``docs/run-metadata.md`` carries the user-facing disclosure.

**Returns**:

  Dict[str, Any]: The run payload&#x27;s ``metaData`` value.

