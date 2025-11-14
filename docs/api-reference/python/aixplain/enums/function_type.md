---
sidebar_label: function_type
title: aixplain.enums.function_type
---

#### \_\_author\_\_

Copyright 2023 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: aiXplain team
Date: May 22th 2025
Description:
    Function Type Enum

### FunctionType Objects

```python
class FunctionType(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/function_type.py#L27)

Enumeration of function types in the aiXplain system.

This enum defines the different types of functions and services available
in the system, including AI models, data processing utilities, and
integration components.

**Attributes**:

- `AI` _str_ - Artificial Intelligence function type.
- `SEGMENTOR` _str_ - Data segmentation function type.
- `RECONSTRUCTOR` _str_ - Data reconstruction function type.
- `UTILITY` _str_ - Utility function type.
- `METRIC` _str_ - Metric/evaluation function type.
- `SEARCH` _str_ - Search function type.
- `INTEGRATION` _str_ - Integration connector function type. # i.e. slack
- `CONNECTION` _str_ - Connection function type. # slack - action
- `MCP_CONNECTION` _str_ - MCP connection function type.
- `MCPSERVER` _str_ - MCP server is for on-prem solution. It should be treated like a model. # ONPREM_MCP_MODEL

