"""Wire encoding of an agent's ``expectedOutput``.

Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
from typing import Any

from pydantic import BaseModel

from .exceptions import ValidationError


def expected_output_to_wire(value: Any) -> Any:
    """Return ``value`` as the string the backend requires for ``expectedOutput``.

    The one encoder for every path that sends it: ``Agent.build_save_payload``,
    ``Agent.build_run_payload`` and ``ExecutionConfig.to_api_dict``. The run endpoints
    reject a non-string with ``400 executionParams.expectedOutput must be a string``, and
    an object persisted on save reaches the engine as a Python repr rather than JSON.

    A Pydantic class becomes its JSON schema and a Pydantic instance its JSON. Any
    other value -- a dict, list, tuple, number or bool -- is JSON-encoded. Strings and
    ``None`` pass through unchanged. Non-ASCII text stays readable on every branch,
    as Pydantic already leaves it.

    Args:
        value: The ``expected_output`` the caller set or passed.

    Returns:
        A JSON string, or ``value`` itself when it is a string or ``None``.

    Raises:
        ValidationError: If ``value`` cannot be encoded as JSON.
    """
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, type) and issubclass(value, BaseModel):
        return json.dumps(value.model_json_schema(), ensure_ascii=False)
    if isinstance(value, BaseModel):
        return value.model_dump_json()
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError) as error:
        raise ValidationError(
            f"expected_output must be a string, a dict, a list or a Pydantic model; "
            f"{type(value).__name__} cannot be sent as JSON: {error}"
        ) from error
