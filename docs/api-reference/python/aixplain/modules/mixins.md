---
sidebar_label: mixins
title: aixplain.modules.mixins
---

Mixins for common functionality across different asset types.

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

Author: Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: November 25th 2024
Description:
    Mixins for common functionality across different asset types

### DeployableMixin Objects

```python
class DeployableMixin(ABC, Generic[T])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/mixins.py#L31)

A mixin that provides common deployment-related functionality for assets.

This mixin provides methods for:
1. Filtering items that are not onboarded
2. Validating if an asset is ready to be deployed
3. Deploying an asset

Classes that inherit from this mixin should:
1. Implement _validate_deployment_readiness to call the parent implementation with their specific asset type
2. Optionally override deploy() if they need special deployment handling

#### deploy

```python
def deploy() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/mixins.py#L62)

Deploy the asset.

This method validates that the asset is ready to be deployed and updates its status to ONBOARDED.
Classes that need special deployment handling should override this method.

**Raises**:

- `AlreadyDeployedError` - If the asset is already deployed
- `ValueError` - If the asset is not ready to be deployed

