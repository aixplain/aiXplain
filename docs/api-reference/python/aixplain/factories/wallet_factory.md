---
sidebar_label: wallet_factory
title: aixplain.factories.wallet_factory
---

### WalletFactory Objects

```python
class WalletFactory()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/wallet_factory.py#L8)

A factory class for retrieving wallet information.

This class provides functionality to fetch wallet details including total
and reserved balance information from the backend API.

**Attributes**:

- `backend_url` - The URL endpoint for the backend API.

#### get

```python
@classmethod
def get(cls, api_key: Text = config.TEAM_API_KEY) -> Wallet
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/wallet_factory.py#L20)

Retrieves the current wallet information from the backend.

This method fetches the wallet details including total balance and reserved balance
using the provided API key.

**Arguments**:

- `api_key` _Text, optional_ - The API key for authentication. Defaults to config.TEAM_API_KEY.
  

**Returns**:

- `Wallet` - A Wallet object containing the total and reserved balance information.
  

**Raises**:

- `Exception` - If the wallet information cannot be retrieved from the backend.

