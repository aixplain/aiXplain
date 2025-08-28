__author__ = "aixplain"

"""
Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: aiXplain Team
Date: August 20th 2024
Description:
    Wallet Class
"""


class Wallet:
    """A class representing a wallet for managing credit balances.

    This class provides functionality for managing credit balances in a wallet,
    including total, reserved, and available balances. It is used to track and
    manage credit resources in the aiXplain platform.

    Attributes:
        total_balance (float): Total credit balance in the wallet.
        reserved_balance (float): Reserved credit balance in the wallet.
        available_balance (float): Available balance (total - reserved).
    """
    def __init__(self, total_balance: float, reserved_balance: float):
        """Initialize a new Wallet instance.

        Args:
            total_balance (float): Total credit balance in the wallet.
            reserved_balance (float): Reserved credit balance in the wallet.
        """
        self.total_balance = total_balance
        self.reserved_balance = reserved_balance
        self.available_balance = total_balance - reserved_balance
