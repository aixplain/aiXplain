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
    def __init__(self, total_balance: float, reserved_balance: float):
        """
        Args:
            total_balance (float): total credit balance
            reserved_balance (float): reserved credit balance
            available_balance (float): available balance (total - credit)
        """
        self.total_balance = total_balance
        self.reserved_balance = reserved_balance
        self.available_balance =  total_balance-reserved_balance