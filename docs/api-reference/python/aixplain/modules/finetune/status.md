---
sidebar_label: status
title: aixplain.modules.finetune.status
---

#### \_\_author\_\_

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

Author: Duraikrishna Selvaraju, Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: February 21st 2024
Description:
    FinetuneCost Class

### FinetuneStatus Objects

```python
@dataclass_json

@dataclass
class FinetuneStatus(object)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/finetune/status.py#L32)

Status information for a fine-tuning job.

This class encapsulates the status of a fine-tuning job, including the overall
status of the job, the status of the model, and various training metrics.

**Attributes**:

- `status` _AssetStatus_ - Overall status of the fine-tuning job.
- `model_status` _AssetStatus_ - Status of the fine-tuned model.
- `epoch` _Optional[float]_ - Current training epoch.
- `training_loss` _Optional[float]_ - Training loss at the current epoch.
- `validation_loss` _Optional[float]_ - Validation loss at the current epoch.

