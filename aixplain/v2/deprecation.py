# Copyright 2024 aiXplain, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Deprecation helpers for v2 API field name migrations."""

import warnings
from typing import Dict


def deprecated_alias_getattr(self: object, name: str, aliases: Dict[str, str]) -> object:
    """Handle deprecated camelCase attribute access on dataclasses.

    This function is designed to be called from a dataclass ``__getattr__`` method.
    When a user accesses a deprecated camelCase name (e.g., ``obj.defaultValue``),
    it emits a ``DeprecationWarning`` and returns the value of the new snake_case
    attribute.

    Args:
        self: The dataclass instance.
        name: The attribute name that was not found via normal lookup.
        aliases: Mapping of ``{old_camelCase_name: new_snake_case_name}``.

    Returns:
        The value of the new attribute if *name* is a known alias.

    Raises:
        AttributeError: If *name* is not a known deprecated alias.
    """
    if name in aliases:
        new_name = aliases[name]
        warnings.warn(
            f"Attribute '{name}' is deprecated, use '{new_name}' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self, new_name)
    raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


def emit_kwarg_deprecation(old_name: str, new_name: str) -> None:
    """Emit a deprecation warning for a renamed keyword argument.

    Args:
        old_name: The deprecated camelCase keyword name.
        new_name: The replacement snake_case keyword name.
    """
    warnings.warn(
        f"Keyword argument '{old_name}' is deprecated, use '{new_name}' instead.",
        DeprecationWarning,
        stacklevel=3,
    )
