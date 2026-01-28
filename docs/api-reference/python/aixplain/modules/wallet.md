---
sidebar_label: wallet
title: aixplain.modules.wallet
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

Author: aiXplain Team
Date: August 20th 2024
Description:
    Wallet Class

### Wallet Objects

```python
class Wallet()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/wallet.py#L25)

A class representing a wallet for managing credit balances.

This class provides functionality for managing credit balances in a wallet,
including total, reserved, and available balances. It is used to track and
manage credit resources in the aiXplain platform.

**Attributes**:

- `total_balance` _float_ - Total credit balance in the wallet.
- `reserved_balance` _float_ - Reserved credit balance in the wallet.
- `available_balance` _float_ - Available balance (total - reserved).

#### \_\_init\_\_

```python
def __init__(total_balance: float, reserved_balance: float)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/wallet.py#L37)

Initialize a new Wallet instance.

**Arguments**:

- `total_balance` _float_ - Total credit balance in the wallet.
- `reserved_balance` _float_ - Reserved credit balance in the wallet.

